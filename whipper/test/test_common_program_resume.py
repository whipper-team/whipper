"""Resume checks use real decoded audio, without an optical drive."""

import binascii
import os
from pathlib import Path
import struct
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import wave

from whipper.command import cd
from whipper.common import common, config, program
from whipper.extern.task import task
from whipper.image import table
from whipper.result import result


class VerifyTrackResumeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.prog = program.Program(config.Config())
        self.prog.getRipResult()
        self.table = self.prog.result.table = table.Table()
        # Vary lengths and include a pregap owned by the preceding track.
        for number, start in enumerate((0, 3, 8), 1):
            track = table.Track(number, audio=True)
            track.index(1, absolute=start)
            self.table.tracks.append(track)
        self.table.tracks[1].index(0, absolute=2)
        self.table.leadout = 15
        self.runner = task.SyncRunner(verbose=False)

    def audio(self, samples, extension='wav', number=1):
        path = Path(self.tmp.name) / ('%02d.wav' % number)
        data = b'\x01\x02\x03\x04' * samples
        with wave.open(str(path), 'wb') as audio:
            audio.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
            audio.writeframes(data)
        if extension == 'flac':
            flac = path.with_suffix('.flac')
            subprocess.run(['flac', '--silent', '-f', '--force-raw-format',
                            '--endian=little', '--sign=signed', '--channels=2',
                            '--bps=16', '--sample-rate=44100', '-o', str(flac),
                            '-'], input=data, check=True)
            path = flac
        track = result.TrackResult()
        track.number = number
        track.filename = str(path)
        return track, binascii.crc32(data) & 0xffffffff

    def verify(self, track):
        return self.prog.verifyTrack(self.runner, track)

    def testReuseCompleteAudioWithoutPriorCrc(self):
        for extension in ('wav', 'flac'):
            with self.subTest(extension=extension):
                track, crc = self.audio(3 * 588, extension)
                self.assertTrue(self.verify(track))
                self.assertEqual((track.testcrc, track.copycrc), (crc, crc))

    def testRejectEmptyAndShortAudioWithoutRecordingCrc(self):
        for extension in ('wav', 'flac'):
            for samples in (0, 588, 3 * 588 - 1):
                with self.subTest(extension=extension, samples=samples):
                    track, _ = self.audio(samples, extension)
                    self.assertFalse(self.verify(track))
                    self.assertIsNone(track.testcrc)
                    self.assertIsNone(track.copycrc)

    def testRejectLengthMismatchEvenWithMatchingCrc(self):
        for samples in (3 * 588 - 1, 3 * 588 + 1, 4 * 588):
            with self.subTest(samples=samples):
                track, crc = self.audio(samples)
                track.testcrc = track.copycrc = crc
                self.assertFalse(self.verify(track))
                self.assertEqual((track.testcrc, track.copycrc), (crc, crc))

    def testKnownCrcMustStillMatch(self):
        for extension in ('wav', 'flac'):
            for matches in (True, False):
                with self.subTest(extension=extension, matches=matches):
                    track, crc = self.audio(3 * 588, extension)
                    prior = crc if matches else crc ^ 1
                    track.testcrc = track.copycrc = prior
                    self.assertEqual(self.verify(track), matches)
                    self.assertEqual((track.testcrc, track.copycrc),
                                     (prior, prior))

    def testRejectCorruptFiles(self):
        for extension in ('wav', 'flac'):
            with self.subTest(extension=extension):
                track, _ = self.audio(3 * 588, extension)
                Path(track.filename).write_bytes(b'not audio')
                self.assertFalse(self.verify(track))
                self.assertIsNone(track.testcrc)
                self.assertIsNone(track.copycrc)

    def testRejectTruncatedWavWithCompleteHeader(self):
        track, _ = self.audio(3 * 588)
        with open(track.filename, 'r+b') as audio:
            audio.truncate(os.path.getsize(track.filename) - 4)
        self.assertFalse(self.verify(track))
        self.assertIsNone(track.testcrc)

    def testRejectWavChunkOutsideRiffBoundary(self):
        track, _ = self.audio(3 * 588)
        Path(track.filename).write_bytes(
            b'RIFF' + struct.pack('<I', 12) + b'WAVEJUNK' +
            struct.pack('<I', 0x100))
        self.assertFalse(self.verify(track))
        self.assertIsNone(track.testcrc)
        self.assertIsNone(track.copycrc)

    def testRejectWrongAudioFormat(self):
        track, _ = self.audio(3 * 588)
        for channels, width, rate in ((1, 2, 44100), (2, 1, 44100),
                                      (2, 2, 48000)):
            with self.subTest(channels=channels, width=width, rate=rate):
                with wave.open(track.filename, 'wb') as audio:
                    audio.setparams((channels, width, rate, 0, 'NONE', 'PCM'))
                    audio.writeframes(b'\x00' * (3 * 588 * channels * width))
                self.assertFalse(self.verify(track))

    def testOffsetsAndOverreadDoNotChangeOutputLength(self):
        for offset in (-1024, -1, 0, 1, 1024):
            for overread in (False, True):
                with self.subTest(offset=offset, overread=overread):
                    self.prog.result.offset = offset
                    self.prog.result.overread = overread
                    track, _ = self.audio(3 * 588)
                    self.assertTrue(self.verify(track))
                    track, _ = self.audio(3 * 588 - 1)
                    self.assertFalse(self.verify(track))

    def testHiddenAudioUsesItsOwnRange(self):
        self.table.tracks[0].index(0, absolute=0)
        self.table.tracks[0].indexes[1].absolute = 2
        track, _ = self.audio(2 * 588, number=0)
        self.assertTrue(self.verify(track))
        track, _ = self.audio(2 * 588 - 1, number=0)
        self.assertFalse(self.verify(track))

    def testSessionGapIsNotAudio(self):
        gap = self.table._getSessionGap(2)
        self.table.tracks[2].session = 2
        self.table.tracks[2].indexes[1].absolute += gap
        self.table.leadout += gap
        track, _ = self.audio(5 * common.SAMPLES_PER_FRAME, number=2)
        self.assertTrue(self.verify(track))

    def testUnexpectedTaskErrorsStillPropagate(self):
        track, _ = self.audio(3 * 588)
        with mock.patch.object(self.runner, 'run',
                               side_effect=task.TaskException(
                                   FileNotFoundError('missing decoder'))):
            with self.assertRaises(task.TaskException):
                self.verify(track)

    def testCommandResumesMultipleTracksAndRetriesRejectedAudio(self):
        """Exercise the real cd rip reuse/unlink/rip loop twice."""
        for number, samples in ((1, 3 * 588), (2, 588), (3, 7 * 588)):
            self.audio(samples, 'flac', number)
        preserved = {n: (Path(self.tmp.name) / ('%02d.flac' % n)).read_bytes()
                     for n in (1, 3)}
        rip = object.__new__(cd.Rip)
        rip.program = self.prog
        rip.itable = self.table
        rip.runner = self.runner
        rip.mbdiscid, rip.device, rip.logger = 'disc', '/dev/unused', None
        rip.skipped_tracks = []
        rip.options = SimpleNamespace(
            working_directory=None, output_directory=self.tmp.name,
            offset=6, overread=False, logger=None, disc_template='disc',
            track_template='track', cover_art='none', max_retries=2,
            keep_going=False)

        def get_path(outdir, template, discid, metadata, track_number=None):
            name = ('disc' if track_number is None else
                    '%02d' % track_number)
            return os.path.join(outdir, name)

        attempts = []

        def rerip(runner, track, **kwargs):
            attempts.append(track.number)
            self.assertFalse(os.path.exists(track.filename))
            if len(attempts) == 1:
                raise RuntimeError('transient drive read failure')
            complete, crc = self.audio(5 * 588, 'flac', track.number)
            self.assertEqual(track.filename, complete.filename)
            track.testcrc = track.copycrc = crc

        with mock.patch.object(self.prog, 'getPath', side_effect=get_path), \
                mock.patch.object(self.prog, 'ripTrack', side_effect=rerip), \
                mock.patch.object(self.prog, 'getTagList', return_value={}), \
                mock.patch.object(self.prog, 'writeCue'), \
                mock.patch.object(self.prog, 'write_m3u'), \
                mock.patch.object(self.prog, 'verifyImage'), \
                mock.patch.object(self.prog, 'writeLog'), \
                mock.patch.object(cd.accurip, 'print_report'):
            rip.doCommand()
            rip.doCommand()
        self.assertEqual(attempts, [2, 2])
        self.assertEqual([t.number for t in self.prog.result.tracks],
                         [1, 2, 3])
        for track in self.prog.result.tracks:
            self.assertIsNotNone(track.testcrc)
            self.assertEqual(track.testcrc, track.copycrc)
            self.assertTrue(self.verify(track))
        for number, data in preserved.items():
            self.assertEqual((Path(self.tmp.name) /
                              ('%02d.flac' % number)).read_bytes(), data)
