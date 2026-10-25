"""AccurateRip positions survive unavailable cue sources."""

import os
import struct
import tempfile
import unittest
import wave
from types import SimpleNamespace
from unittest import mock

from whipper.common import accurip, program
from whipper.extern.task.task import SyncRunner, TaskException
from whipper.program.arc import accuraterip_checksum
from whipper.result.result import RipResult, TrackResult


class AccurateRipPositionsTestCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = directory.name
        self.paths = []
        for n in range(1, 4):
            path = os.path.join(self.directory, '%d.wav' % n)
            with wave.open(path, 'wb') as audio:
                audio.setnchannels(2)
                audio.setsampwidth(2)
                audio.setframerate(44100)
                audio.writeframes(struct.pack('<hh', n * 101, n * 203) * 5880)
            self.paths.append(path)
        self.expected = accurip.calculate_checksums(self.paths)
        self.response = SimpleNamespace(
            checksums=self.expected['v1'], confidences=[11, 22, 33],
            cddbDiscId='synthetic', num_tracks=3)

    def verify(self, missing=(), htoa=False, unreadable=False, absent=False):
        tracks = []
        result = RipResult()
        for number in ([0] if htoa else []) + [1, 2, 3]:
            path = 'htoa.wav' if number == 0 else '%d.wav' % number
            if number in missing:
                path = None
            tracks.append(SimpleNamespace(
                number=number,
                indexes={1: SimpleNamespace(path=path, relative=0)}))
            track = TrackResult()
            track.number = number
            result.tracks.append(track)
        if unreadable:
            with open(self.paths[1], 'wb') as audio:
                audio.write(b'not an audio file\xff')
        if absent:
            os.unlink(self.paths[1])
        cue_image = SimpleNamespace(cue=SimpleNamespace(
            table=SimpleNamespace(tracks=tracks),
            getTrackLength=lambda track: 10))
        instance = program.Program.__new__(program.Program)
        instance.cuePath = os.path.join(self.directory, 'disc.cue')
        instance.skipped_tracks = None
        instance.result = result
        with mock.patch.object(program.image, 'Image',
                               return_value=cue_image), \
                mock.patch.object(accurip, 'get_db_entry',
                                  return_value=[self.response]), \
                mock.patch.object(accurip, 'accuraterip_checksum',
                                  wraps=accuraterip_checksum) as compute:
            success = instance.verifyImage(mock.Mock(), mock.Mock())
        unavailable = set(missing)
        if unreadable or absent:
            unavailable.add(2)
        self.assertEqual(success, not unavailable)
        expected_calls = [mock.call(path, n, 3)
                          for n, path in enumerate(self.paths, 1)
                          if n not in missing and not (absent and n == 2)]
        self.assertEqual(compute.call_args_list, expected_calls)
        ordinary = [t for t in result.tracks if t.number != 0]
        for n, track in enumerate(ordinary, 1):
            for version in ('v1', 'v2'):
                expected = (None if n in unavailable else
                            self.expected[version][n - 1])
                self.assertEqual(track.AR[version]['CRC'], expected)
            self.assertEqual(track.AR['v1']['DBConfidence'],
                             None if n in unavailable else n * 11)
            self.assertEqual(track.AR['v1']['DBCRC'],
                             None if n in unavailable else
                             self.response.checksums[n - 1])
        if htoa:
            self.assertIsNone(result.tracks[0].AR['v1']['CRC'])

    def test_complete_disc(self):
        self.verify()

    def test_missing_first(self):
        self.verify(missing=(1,))

    def test_missing_middle(self):
        self.verify(missing=(2,))

    def test_missing_final(self):
        self.verify(missing=(3,))

    def test_multiple_missing(self):
        self.verify(missing=(1, 3))

    def test_all_missing(self):
        self.verify(missing=(1, 2, 3))

    def test_htoa(self):
        self.verify(htoa=True)

    def test_htoa_with_missing_track(self):
        self.verify(missing=(1,), htoa=True)

    def test_unreadable_audio(self):
        self.verify(unreadable=True)

    def test_absent_file(self):
        self.verify(absent=True)

    def test_missing_and_empty_paths(self):
        self.assertEqual(accurip.calculate_checksums([None, '', '/missing']),
                         {'v1': [None] * 3, 'v2': [None] * 3})

    def test_unreadable_source_oserror(self):
        with mock.patch.object(accurip, 'accuraterip_checksum',
                               side_effect=PermissionError('unreadable')):
            self.assertEqual(accurip.calculate_checksums(self.paths),
                             {'v1': [None] * 3, 'v2': [None] * 3})

    def test_reverification_clears_old_matches(self):
        result = RipResult()
        for n in range(1, 4):
            track = TrackResult()
            track.number = n
            result.tracks.append(track)
        self.assertTrue(accurip.verify_result(
            result, [self.response], self.expected))
        partial = {v: list(sums) for v, sums in self.expected.items()}
        for sums in partial.values():
            sums[1] = None
        self.assertFalse(accurip.verify_result(
            result, [self.response], partial))
        for v in ('v1', 'v2'):
            self.assertIsNone(result.tracks[1].AR[v]['DBCRC'])
            self.assertIsNone(result.tracks[1].AR[v]['DBConfidence'])

    def test_all_unavailable_clears_old_matches(self):
        result = RipResult()
        for n in range(1, 4):
            track = TrackResult()
            track.number = n
            result.tracks.append(track)
        self.assertTrue(accurip.verify_result(
            result, [self.response], self.expected))
        self.assertFalse(accurip.verify_result(
            result, [self.response], {'v1': [None] * 3, 'v2': [None] * 3}))
        for track in result.tracks:
            self.assertIsNone(track.AR['v1']['DBCRC'])
            self.assertIsNone(track.AR['v2']['DBCRC'])

    def test_real_cue_and_runner(self):
        cue_path = os.path.join(self.directory, 'disc.cue')
        with open(cue_path, 'w') as cue:
            for n in range(1, 4):
                cue.write('FILE "%d.wav" WAVE\n'
                          '  TRACK %02d AUDIO\n'
                          '    INDEX 01 00:00:00\n' % (n, n))
        instance = program.Program.__new__(program.Program)
        instance.cuePath = cue_path
        instance.result = RipResult()
        for n in range(1, 4):
            track = TrackResult()
            track.number = n
            instance.result.tracks.append(track)
        with mock.patch.object(accurip, 'get_db_entry',
                               return_value=[self.response]):
            self.assertTrue(instance.verifyImage(SyncRunner(), mock.Mock()))
            # The final FILE needs a real soxi length scan. Failure must still
            # record available tracks and clear the preceding successful match.
            with open(self.paths[2], 'wb') as source:
                source.write(b'unreadable audio')
            self.assertFalse(instance.verifyImage(SyncRunner(), mock.Mock()))
        for track in instance.result.tracks[:2]:
            self.assertEqual(track.AR['v1']['DBConfidence'], track.number * 11)
        self.assertIsNone(instance.result.tracks[2].AR['v1']['CRC'])
        self.assertIsNone(instance.result.tracks[2].AR['v1']['DBCRC'])

    def test_unexpected_length_errors_propagate(self):
        cue_image = SimpleNamespace(cue=SimpleNamespace(
            table=SimpleNamespace(tracks=[])))
        instance = program.Program.__new__(program.Program)
        instance.cuePath = os.path.join(self.directory, 'disc.cue')
        runner = mock.Mock()
        runner.run.side_effect = TaskException(ValueError('unexpected'))
        with mock.patch.object(program.image, 'Image', return_value=cue_image):
            with self.assertRaises(TaskException):
                instance.verifyImage(runner, mock.Mock())
