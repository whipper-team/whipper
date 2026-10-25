"""Disc-read outcomes must agree with artifacts and recovery state."""
import contextlib
import io
import os
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from whipper.command import cd
from whipper.common import config, program
from whipper.image import cue, table
from whipper.result.logger import WhipperLogger
from whipper.result.result import TrackResult


class PartialRipTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.prog = program.Program(config.Config())
        self.prog.getRipResult()
        self.table = table.Table()
        for number, start in enumerate((150, 900, 1800), 1):
            track = table.Track(number)
            track.index(1, absolute=start)
            self.table.tracks.append(track)
        self.table.tracks[1].index(0, absolute=825)
        self.table.leadout = 2700
        self.prog.result.table = self.table
        self.rip = object.__new__(cd.Rip)
        self.rip.program = self.prog
        self.rip.itable = self.table
        self.rip.runner = mock.Mock()
        self.rip.mbdiscid = 'disc'
        self.rip.device = '/dev/never-opened'
        self.rip.logger = WhipperLogger()
        self.rip.skipped_tracks = []
        self.rip.options = SimpleNamespace(
            working_directory=None, output_directory=self.tmp.name,
            offset=6, overread=False, logger=None, disc_template='disc',
            track_template='track', cover_art='none', max_retries=1,
            keep_going=False)
        self.attempts = []
        self.failed_number = None
        self.error = RuntimeError
        self.crcs = (0x1234, 0x1234)
        self.fail_once = False
        self.htoa_silent = False

        def get_path(outdir, template, discid, metadata, track_number=None):
            return os.path.join(outdir, 'disc' if track_number is None else
                                '%02d' % track_number)

        def read_task(path, *args, **kwargs):
            number = int(Path(path).stem)
            return SimpleNamespace(
                path=path, number=number, testchecksum=self.crcs[0],
                copychecksum=self.crcs[1],
                peak=0 if number == 0 and self.htoa_silent else 100,
                quality=1.0, testspeed=1.0, copyspeed=1.0,
                testduration=1.0, copyduration=1.0)

        def run(task):
            self.attempts.append(task.number)
            Path(task.path).write_bytes(b'preserved audio %d' % task.number)
            if task.number == self.failed_number:
                if self.fail_once:
                    self.failed_number = None
                raise self.error('simulated read failure')

        self.rip.runner.run.side_effect = run
        for patcher in (
                mock.patch.object(self.prog, 'getPath', side_effect=get_path),
                mock.patch.object(self.prog, 'getTagList', return_value={}),
                mock.patch.object(program.cdparanoia, 'ReadVerifyTrackTask',
                                  side_effect=read_task),
                mock.patch.object(cd.accurip, 'print_report')):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.verify_image = mock.patch.object(self.prog, 'verifyImage').start()
        self.addCleanup(mock.patch.stopall)

    def invoke(self, error=None):
        # cdrdao supplies indexes in chronological order.
        for track in self.table.tracks:
            track.indexes = dict(sorted(track.indexes.items()))
        with contextlib.redirect_stdout(io.StringIO()):
            if error:
                with self.assertRaises(error):
                    self.rip.doCommand()
            else:
                return self.rip.doCommand()

    def artifacts(self, completed, partial=True):
        cue_text = (self.directory / 'disc.cue').read_text()
        playlist = (self.directory / 'disc.m3u').read_text()
        suffix = 'partial.log' if partial else 'log'
        log = (self.directory / ('disc.' + suffix)).read_text()
        referenced = {int(Path(p).stem) for p in
                      re.findall(r'^FILE "([^"]+)" WAVE$', cue_text, re.M)}
        # HTOA without track 1 cannot be expressed as a playable cue track.
        expected_cue = set(completed)
        if 1 not in completed:
            expected_cue.discard(0)
        self.assertEqual(referenced, expected_cue)
        self.assertEqual({int(Path(p).stem) for p in playlist.splitlines()
                          if p and not p.startswith('#')}, set(completed))
        tracks = {int(n) for n in re.findall(
            r'^  TRACK (\d+) AUDIO$', cue_text, re.M)}
        self.assertEqual(tracks, set(completed) - {0})
        for number in completed:
            result = self.prog.result.getTrackResult(number)
            self.assertTrue(result.isComplete())
            self.assertEqual(Path(result.filename).read_bytes(),
                             b'preserved audio %d' % number)
            self.assertIn("Test CRC: '00001234'", log)
            self.assertIn("Copy CRC: '00001234'", log)
        if partial:
            self.assertFalse((self.directory / 'disc.log').exists())
            self.assertIn('INCOMPLETE RIP', log)
            self.assertNotIn('End of status report', log)
            self.assertNotIn('SHA-256 hash:', log)
            self.assertNotIn('No errors occurred', log)
            self.assertIn('REM INCOMPLETE_RIP', cue_text)
            self.assertIn('REM ORIGINAL_TRACK 02 START 900 LENGTH 900 '
                          'PREGAP 75', cue_text)
            self.assertFalse(self.prog.result.complete)
            self.verify_image.assert_not_called()
        else:
            self.assertTrue(self.prog.result.complete)
            self.assertIn('End of status report', log)
            self.assertIn('No errors occurred', log)
            self.verify_image.assert_called_once()
        return cue_text, log

    def testAbortOnFirstMiddleAndFinalTrack(self):
        for failed in (1, 2, 3):
            with self.subTest(failed=failed):
                self.failed_number = failed
                self.attempts.clear()
                for path in self.directory.iterdir():
                    path.unlink()
                self.invoke(RuntimeError)
                self.artifacts(list(range(1, failed)))
                self.assertEqual(self.attempts, list(range(1, failed + 1)))
                failed_result = self.prog.result.getTrackResult(failed)
                self.assertEqual(failed_result.status, 'failed')
                for number in range(failed + 1, 4):
                    self.assertEqual(
                        self.prog.result.getTrackResult(number).status,
                        'pending')
                # Even incomplete read output is preserved for diagnosis.
                self.assertTrue((self.directory /
                                 ('%02d.flac' % failed)).exists())

    def testKeepGoingPreservesNumberingAndMissingPregap(self):
        self.rip.options.keep_going = True
        self.failed_number = 1
        self.assertEqual(self.invoke(), 5)
        cue_text, log = self.artifacts([2, 3])
        self.assertIn('REM UNAVAILABLE_PREGAP 00:01:00', cue_text)
        self.assertNotIn('    PREGAP ', cue_text)
        self.assertNotIn('    INDEX 00', cue_text)
        self.assertIn('Track not completed (failed)', log)
        self.assertEqual(self.prog.result.getTrackResult(1).status, 'failed')
        # Parsing keeps the original track numbers and file-relative starts.
        parsed = cue.CueFile(str(self.directory / 'disc.cue'))
        parsed.parse()
        self.assertEqual([t.number for t in parsed.table.tracks], [2, 3])
        self.assertEqual(parsed.table.tracks[0].indexes[1].relative, 0)

    def testKeepGoingMiddleFailure(self):
        self.rip.options.keep_going = True
        self.failed_number = 2
        self.assertEqual(self.invoke(), 5)
        self.artifacts([1, 3])

    def testCompletedPregapUsesPreviousCompletedFile(self):
        self.failed_number = 3
        self.invoke(RuntimeError)
        cue_text, _ = self.artifacts([1, 2])
        self.assertIn('    INDEX 00 00:09:00', cue_text)
        self.assertIn('    INDEX 01 00:00:00', cue_text)

    def testFailedHiddenAudio(self):
        self.table.tracks[0].index(0, absolute=0)
        self.failed_number = 0
        self.invoke(RuntimeError)
        self.artifacts([])
        self.assertEqual(self.prog.result.getTrackResult(0).status, 'failed')

    def testKeepGoingAfterFailedHiddenAudio(self):
        self.table.tracks[0].index(0, absolute=0)
        self.failed_number = 0
        self.rip.options.keep_going = True
        self.assertEqual(self.invoke(), 5)
        cue_text, _ = self.artifacts([1, 2, 3])
        self.assertIn('REM UNAVAILABLE_PREGAP 00:02:00', cue_text)
        self.assertNotIn('    PREGAP ', cue_text)

    def testCompletedHiddenAudioSurvivesTrackOneFailure(self):
        self.table.tracks[0].index(0, absolute=0)
        self.failed_number = 1
        self.invoke(RuntimeError)
        self.artifacts([0])

    def testInterruptedRead(self):
        self.failed_number = 2
        self.error = KeyboardInterrupt
        self.invoke(KeyboardInterrupt)
        self.artifacts([1])
        self.assertEqual(self.prog.result.getTrackResult(2).status,
                         'interrupted')

    def testIncompleteOrMismatchedCRCs(self):
        for crcs in ((None, None), (0x1234, None), (None, 0x1234), (1, 2)):
            with self.subTest(crcs=crcs):
                self.crcs = crcs
                for path in self.directory.iterdir():
                    path.unlink()
                self.invoke(RuntimeError)
                _, log = self.artifacts([])
                self.assertNotIn('Copy OK', log)
                if crcs[0] == 0x1234:
                    self.assertIn("Test CRC: '00001234'", log)
                if crcs[1] == 0x1234:
                    self.assertIn("Copy CRC: '00001234'", log)

    def testDataTrackIsExplicitlySkipped(self):
        self.table.tracks[2].audio = False
        self.invoke()
        skipped = self.prog.result.getTrackResult(3)
        self.assertEqual(skipped.status, 'skipped')
        self.assertFalse(skipped.isComplete())
        self.assertTrue(self.prog.result.complete)
        self.assertNotIn('03.flac',
                         (self.directory / 'disc.m3u').read_text())
        self.assertNotIn('TRACK 03',
                         (self.directory / 'disc.cue').read_text())
        self.assertIn('Track not ripped (skipped)',
                      (self.directory / 'disc.log').read_text())
        # AccurateRip arrays retain audio-track positions when data is skipped.
        checksums = {'v1': ['a', 'b'], 'v2': ['c', 'd']}
        with mock.patch.object(
                cd.accurip, '_assign_checksums_and_confidences') as assign, \
                mock.patch.object(cd.accurip, '_match_responses'):
            cd.accurip.verify_result(self.prog.result, ['entry'], checksums)
        self.assertEqual([t.number for t in assign.call_args[0][0]], [1, 2])

    def testMatchingCRCsWithoutAudioOutputAreNotCompletion(self):
        # ReadVerifyTrackTask.stop can swallow an output-move failure after
        # its CRCs have been collected. A successful runner is insufficient.
        self.rip.runner.run.side_effect = lambda task: None
        self.invoke(RuntimeError)
        self.artifacts([])
        failed = self.prog.result.getTrackResult(1)
        self.assertTrue(failed.hasMatchingCRCs())
        self.assertEqual(failed.status, 'failed')
        self.assertFalse(failed.isComplete())

    def testSuccessfulFullDisc(self):
        self.invoke()
        self.artifacts([1, 2, 3], partial=False)

    def testRetryClearsEarlierCRCs(self):
        self.failed_number = 2
        self.fail_once = True
        self.rip.options.max_retries = 2
        self.invoke()
        self.artifacts([1, 2, 3], partial=False)
        self.assertEqual(self.attempts, [1, 2, 2, 3])

    def testSilentHiddenAudioIsSuccessfulButNotReferenced(self):
        self.table.tracks[0].index(0, absolute=0)
        self.htoa_silent = True
        self.invoke()
        self.artifacts([1, 2, 3], partial=False)
        self.assertTrue(self.prog.result.getTrackResult(0).isComplete())
        self.assertIsNone(self.prog.result.getTrackResult(0).filename)

    def testDiagnosticFailureDoesNotSuppressLogOrOriginalException(self):
        self.failed_number = 2
        with mock.patch.object(self.prog, 'writeCue',
                               side_effect=OSError('disk full')):
            self.invoke(RuntimeError)
        self.assertTrue((self.directory / 'disc.partial.log').exists())
        self.assertTrue((self.directory / '01.flac').exists())
        self.assertTrue((self.directory / 'disc.m3u').exists())

    def testResumeAfterAbortKeepsCompletedAudioAndCRCs(self):
        self.failed_number = 2
        self.invoke(RuntimeError)
        original = (self.directory / '01.flac').read_bytes()
        self.artifacts([1])
        self.failed_number = None
        self.attempts.clear()
        # The file/CRC reuse gate is supplied by verifyTrack, independently
        # hardened by #707. Failed output must still enter its rejection path.
        with mock.patch.object(self.prog, 'verifyTrack',
                               side_effect=lambda runner, t:
                               t.hasMatchingCRCs()):
            self.invoke()
        self.artifacts([1, 2, 3], partial=False)
        self.assertEqual(self.attempts, [2, 3])
        self.assertEqual((self.directory / '01.flac').read_bytes(), original)


class CRCLogTestCase(unittest.TestCase):
    def testMissingCRCsNeverReportCopyOK(self):
        logger = WhipperLogger()
        for test, copy in ((None, None), (1, None), (None, 1), (1, 2)):
            track = TrackResult()
            track.testcrc, track.copycrc = test, copy
            logged, _, _ = logger.trackLog(track)
            self.assertNotEqual(logged['Status'], 'Copy OK')
        track.testcrc = track.copycrc = 0
        logged, _, _ = logger.trackLog(track)
        self.assertEqual(logged['Status'], 'Copy OK')
