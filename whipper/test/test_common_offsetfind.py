"""Independent checksum vectors, window failures, and read-span regressions."""

import array
import os
import struct
import tempfile
import unittest
from unittest import mock
import wave

from whipper.common import accurip, common, offsetfind
from whipper.extern.task import task
from whipper.program import cdparanoia


class FakeTable:
    tracks = [1, 2, 3]

    def getTrackStart(self, track):
        return [32, 2000, 4000][track - 1]

    def getTrackEnd(self, track):
        return [1999, 3999, 6000][track - 1]


class ChecksumTest(unittest.TestCase):
    def test_parse_offset_field(self):
        raw = struct.pack('<BIIIBII', 1, 1, 2, 3, 8, 0xdeadbeef, 0x12345678)
        response = accurip._AccurateRipResponse(raw)
        self.assertEqual(response.checksums, ['deadbeef'])
        self.assertEqual(response.confidences, [8])
        self.assertEqual(response.offsetfind_checksums, ['12345678'])

    def test_independent_sparse_vector(self):
        pcm = array.array('h', [0] * 1176)
        pcm[0:2] = array.array('h', [-1, -32768])
        pcm[-2:] = array.array('h', [3, 1])
        # Packed nonzero samples: 0x8000ffff at position 1 and 0x10003
        # at 588. Direct integer products, reduced modulo 2**32:
        # local: 1*A + 588*B; track: 264601*A + 265188*B.
        self.assertEqual(offsetfind.offsetfind_crcs(pcm, 0),
                         (0x824d06e3, 0x95851a13))

    def test_positive_negative_zero_offsets_and_order(self):
        for offset in (-102, 0, 102):
            pcm = array.array('h', [0] * (1000 * 2))
            start = 200 + offset
            pcm[start * 2] = 1
            pcm[(start + 587) * 2] = 2
            # 1*1 + 588*2 = 1177; position weights add 264600*3.
            for checksum in (1177, 794977):
                self.assertEqual(offsetfind.match_offsets(
                    pcm, offsetfind.FRAME450 - 200, range(-150, 151),
                    [checksum]), [offset])
            self.assertEqual(offsetfind.match_offsets(
                pcm, offsetfind.FRAME450 - 200, [offset + 1], [1177]), [])

    def test_ambiguous_matches_preserve_candidate_order(self):
        pcm = array.array('h', [1, 0] * 600)
        # Sum of integers 1..588, independent of the tested implementation.
        self.assertEqual(offsetfind.match_offsets(
            pcm, offsetfind.FRAME450, [5, 0, 4], [173166]), [5, 0, 4])

    def test_absent_or_zero_crc_does_not_read(self):
        for values in ([], ['00000000'], ['invalid']):
            response = mock.Mock(offsetfind_checksums=values)
            with mock.patch.object(offsetfind, 'read_window') as read:
                self.assertEqual(offsetfind.find_offsets(
                    mock.Mock(), FakeTable(), '/dev/cd0', [response]), [])
                read.assert_not_called()

    def test_search_does_not_escape_allowed_offsets(self):
        pcm = array.array('h', [1, 0] * 600)
        response = mock.Mock(offsetfind_checksums=['0002a46e'])
        with mock.patch.object(offsetfind, 'read_window',
                               return_value=(pcm, offsetfind.FRAME450)):
            self.assertEqual(offsetfind.find_offsets(
                mock.Mock(), FakeTable(), '/dev/cd0', [response],
                allowed_offsets=[5, 0]), [5, 0])


class WindowTest(unittest.TestCase):
    def test_short_track_does_not_create_temporary_file(self):
        table = mock.Mock()
        table.getTrackStart.return_value = 0
        table.getTrackEnd.return_value = 300
        with mock.patch.object(offsetfind.tempfile, 'mkstemp') as create:
            self.assertEqual(offsetfind.read_window(
                mock.Mock(), table, '/dev/cd0', 0, 3000), (None, None))
            create.assert_not_called()

    def test_cleanup_on_success_failure_and_missing_dependency(self):
        errors = [None, OSError('bad WAV'),
                  task.TaskException(common.MissingDependencyException(
                      'cd-paranoia')),
                  task.TaskException(ValueError('read failed')),
                  task.TaskException(cdparanoia.ReadTimeoutError(
                      'inactivity', 120)),
                  task.TaskException(cdparanoia.ReadCleanupError(
                      'cannot reap'))]
        for error in errors:
            runner = mock.Mock()
            if isinstance(error, task.TaskException):
                runner.run.side_effect = error
            with mock.patch.object(offsetfind, '_read_pcm',
                                   return_value=array.array('h'),
                                   side_effect=(error if isinstance(
                                       error, OSError) else None)), \
                    mock.patch.object(offsetfind.cdparanoia,
                                      'ReadTrackTask') as reader:
                if isinstance(error, task.TaskException) and isinstance(
                        error.exception, (common.MissingDependencyException,
                                          cdparanoia.ReadCleanupError)):
                    with self.assertRaises(task.TaskException):
                        offsetfind.read_window(runner, FakeTable(),
                                               '/dev/cd0', 0, 3000)
                else:
                    result = offsetfind.read_window(
                        runner, FakeTable(), '/dev/cd0', 0, 3000)
                    self.assertEqual(result[0] is None, error is not None)
                path = reader.call_args[0][0]
                self.assertFalse(os.path.exists(path))
                self.assertEqual(reader.call_args[1]['offset'], 0)
                self.assertFalse(reader.call_args[1]['overread'])
                self.assertEqual(reader.call_args[1]['read_timeout'], 1800.0)
                self.assertEqual(reader.call_args[1]['idle_timeout'], 120.0)

    def test_timeout_yields_no_hints_and_custom_limits_reach_reader(self):
        runner = mock.Mock()
        runner.run.side_effect = task.TaskException(
            cdparanoia.ReadTimeoutError('inactivity', 300))
        response = mock.Mock(offsetfind_checksums=['12345678'])
        with mock.patch.object(offsetfind.cdparanoia, 'ReadTrackTask') as read:
            self.assertEqual(offsetfind.find_offsets(
                runner, FakeTable(), '/dev/cd0', [response],
                read_timeout=3600, idle_timeout=300), [])
            self.assertEqual(read.call_args[1]['read_timeout'], 3600)
            self.assertEqual(read.call_args[1]['idle_timeout'], 300)
            self.assertFalse(os.path.exists(read.call_args[0][0]))

    def test_little_endian_wav_and_big_endian_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'window.wav')
            raw = struct.pack('<hhhh', -1, 2, -32768, 32767)
            with wave.open(path, 'wb') as handle:
                handle.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
                handle.writeframes(raw)
            self.assertEqual(list(offsetfind._read_pcm(path)),
                             [-1, 2, -32768, 32767])
            with mock.patch.object(wave.sys, 'byteorder', 'big'), \
                    mock.patch.object(offsetfind.array, 'array') as create:
                offsetfind._read_pcm(path)
                create.return_value.frombytes.assert_called_once_with(
                    struct.pack('>hhhh', -1, 2, -32768, 32767))
                create.return_value.byteswap.assert_not_called()

    def test_invalid_wav_format(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'mono.wav')
            with wave.open(path, 'wb') as handle:
                handle.setparams((1, 2, 44100, 0, 'NONE', 'not compressed'))
                handle.writeframes(b'\0\0')
            with self.assertRaises(ValueError):
                offsetfind._read_pcm(path)


class SpanTest(unittest.TestCase):
    def test_midtrack_fulltrack_cross_track_and_htoa(self):
        cases = [
            (482, 498, '1[00:00:06.00]-1[00:00:06.16]'),
            (32, 1999, '1[00:00:00.00]-1[00:00:26.17]'),
            (1999, 2000, '1[00:00:26.17]-2[00:00:00.00]'),
            (0, 31, '0[00:00:00.00]-0[00:00:00.31]'),
            (0, 32, '0[00:00:00.00]-1[00:00:00.00]'),
        ]
        for start, stop, span in cases:
            reader = cdparanoia.ReadTrackTask(
                '/tmp/test.wav', FakeTable(), start, stop,
                device='/dev/sr0', overread=False, offset=0)
            with mock.patch.object(cdparanoia.asyncsub, 'Popen',
                                   side_effect=RuntimeError('captured')
                                   ) as run:
                with self.assertRaises(RuntimeError):
                    reader.start(mock.Mock())
                self.assertIn(span, run.call_args[0][0])
