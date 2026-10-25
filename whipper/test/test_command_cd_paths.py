"""Template hierarchy and no-clobber checks without an optical drive."""

import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from whipper.command.cd import (
    Rip, DEFAULT_DISC_TEMPLATE, DEFAULT_TRACK_TEMPLATE,
)
from whipper.common import common, program, config, mbngs
from whipper.program import cdparanoia
from whipper.result import result


class TrackPathsTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.disc = os.path.join(self.root, 'Artist/Album/Disc 1/disc')

    def align(self, track, template='folder/%n'):
        return common.align_track_path(
            os.path.join(self.root, track), self.disc, template, self.root)[0]

    def testSharedArtistAlbumAndDiscPrefixes(self):
        for prefix in ('', 'Artist/', 'Artist/Album/',
                       'Artist/Album/Disc 1/'):
            with self.subTest(prefix=prefix):
                self.assertEqual(self.align(prefix + 'Solo/Title.flac'),
                                 os.path.join(os.path.dirname(self.disc),
                                              'Solo/Title.flac'))

    def testSameBasenameDifferentDirectories(self):
        paths = {}
        for number, artist in enumerate(('Solo', 'Duo'), 1):
            path = self.align(artist + '/Title.flac')
            common.check_track_path(path, number, paths)
        self.assertEqual(len(paths), 2)

    def testRelativeOutputAndNormalizedBoundaries(self):
        root = os.path.relpath(self.root)
        path, _ = common.align_track_path(
            root + '/Artist/Album/Disc 10/./Title.flac',
            root + '/Artist/Album/Disc 1/disc', '%A/%d/Disc 10/%n', root)
        self.assertEqual(
            path, root + '/Artist/Album/Disc 1/Disc 10/Title.flac')

    def testTraversalAndSymlinkEscape(self):
        for track in ('../Title.flac', 'Artist/../../Title.flac'):
            with self.subTest(track=track), self.assertRaises(ValueError):
                self.align(track)
        os.makedirs(os.path.dirname(self.disc))
        os.symlink(self.root,
                   os.path.join(os.path.dirname(self.disc), 'escape'))
        with self.assertRaises(ValueError):
            self.align('escape/Title.flac')

    def testDefaultTemplatesWithSyntheticMetadata(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Artist'
        md.releaseTitle = 'Album'
        md.tracks = [SimpleNamespace(artist='Solo', sortName='Solo',
                                     title='Title')]
        for root in (self.root, os.path.relpath(self.root), '.'):
            disc = prog.getPath(root, DEFAULT_DISC_TEMPLATE, 'id', md)
            track = prog.getPath(root, DEFAULT_TRACK_TEMPLATE, 'id', md, 1)
            self.assertEqual(common.align_track_path(
                track + '.flac', disc, DEFAULT_TRACK_TEMPLATE, root),
                (track + '.flac', False))

    def testExistingFileAndPartArePreserved(self):
        path = self.align('Title.flac')
        os.makedirs(os.path.dirname(path))
        for target in (path, path + '.part'):
            with self.subTest(target=target):
                with open(target, 'wb') as handle:
                    handle.write(b'original audio')
                with self.assertRaises(FileExistsError):
                    common.check_track_path(path, 1, {})
                with open(target, 'rb') as handle:
                    self.assertEqual(handle.read(), b'original audio')
                os.unlink(target)

    def testFilesystemAliasesFailBeforeAudio(self):
        # Determine the fixture filesystem's actual naming rules.
        for first, second in [('Title', 'title'), ('Café', 'Cafe\u0301')]:
            probe = os.path.join(self.root, first)
            open(probe, 'w').close()
            aliases = os.path.exists(os.path.join(self.root, second))
            os.unlink(probe)
            paths = {1: self.align(first + '.flac'),
                     2: self.align(second + '.flac')}
            before = os.listdir(self.root)
            if aliases:
                with self.assertRaisesRegex(ValueError, 'tracks 1 and 2'):
                    common.check_track_path_aliases(
                        paths, os.path.dirname(self.disc))
            else:
                common.check_track_path_aliases(
                    paths, os.path.dirname(self.disc))
            self.assertEqual(os.listdir(self.root), before)

    def testRecordedTrackCanBeVerifiedAgain(self):
        path = self.align('Title.flac')
        os.makedirs(os.path.dirname(path))
        open(path, 'wb').close()
        common.check_track_path(path, 1, {}, SimpleNamespace(filename=path))


class RipPreflightTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.command = Rip.__new__(Rip)
        cmd = self.command
        cmd.options = SimpleNamespace(
            working_directory=self.root, output_directory=self.root,
            offset=0, overread=False, logger='test', disc_template='disc/disc',
            track_template='%n', cover_art='none', max_retries=2,
            keep_going=False)
        cmd.program = Mock()
        cmd.program.metadata = None
        cmd.program.result = result.RipResult()
        cmd.program.getHTOA.return_value = None
        cmd.program.getTagList.return_value = {}
        cmd.program.getPath.side_effect = lambda root, template, *a, **kw: (
            os.path.join(root, 'disc/disc') if template == 'disc/disc'
            else os.path.join(root, 'Same' if template == '%n'
                              else str(kw['track_number'])))
        cmd.itable = SimpleNamespace(
            tracks=[Mock(audio=True), Mock(audio=True)])
        cmd.runner = Mock()
        cmd.mbdiscid = 'synthetic'
        cmd.device = '/unused'
        cmd.skipped_tracks = []

    def testDuplicateTitlesFailBeforeAnyAudio(self):
        with self.assertRaisesRegex(ValueError, 'tracks 1 and 2.*destination'):
            self.command.doCommand()
        self.command.program.ripTrack.assert_not_called()
        self.command.program.verifyTrack.assert_not_called()

    def testHTOAAlsoParticipatesInPreflight(self):
        self.command.program.getHTOA.return_value = (0, 100)
        with self.assertRaisesRegex(ValueError, 'tracks 0 and 1'):
            self.command.doCommand()
        self.command.program.ripTrack.assert_not_called()

    def testCaseAliasesFailAtCommandPreflight(self):
        probe = os.path.join(self.root, 'Title')
        open(probe, 'w').close()
        if not os.path.exists(os.path.join(self.root, 'title')):
            self.skipTest('fixture filesystem is case sensitive')
        os.unlink(probe)
        cmd = self.command
        cmd.options.track_template = '%t'
        cmd.program.getPath.side_effect = lambda root, template, *a, **kw: (
            os.path.join(root, 'disc/disc') if template == 'disc/disc'
            else os.path.join(root, 'Title' if kw['track_number'] == 1
                              else 'title'))
        with self.assertRaisesRegex(ValueError, 'tracks 1 and 2'):
            cmd.doCommand()
        cmd.program.ripTrack.assert_not_called()
        cmd.program.verifyTrack.assert_not_called()

    def testExistingSecondTrackFailsBeforeFirstTrack(self):
        cmd = self.command
        cmd.options.track_template = '%t'
        os.makedirs(os.path.join(self.root, 'disc'))
        path = os.path.join(self.root, 'disc/2.flac')
        with open(path, 'wb') as handle:
            handle.write(b'keep me')
        with self.assertRaisesRegex(FileExistsError, 'track 2.*exists'):
            cmd.doCommand()
        cmd.program.ripTrack.assert_not_called()
        cmd.program.verifyTrack.assert_not_called()
        with open(path, 'rb') as handle:
            self.assertEqual(handle.read(), b'keep me')

    def testRetryErrorsRetainCauseAndAttemptLogs(self):
        cmd = self.command
        cmd.options.track_template = '%t'
        cmd.program.ripTrack.side_effect = OSError('synthetic read failure')
        with self.assertLogs('whipper.command.cd', level='WARNING') as logs:
            with self.assertRaisesRegex(RuntimeError,
                                        'after 2 attempt.*synthetic read'):
                cmd.doCommand()
        self.assertEqual(cmd.program.ripTrack.call_count, 2)
        self.assertIn('try 1: synthetic read failure', '\n'.join(logs.output))
        self.assertIn('try 2: synthetic read failure', '\n'.join(logs.output))
        self.assertTrue(os.path.isdir(os.path.join(self.root, 'disc')))


class PublishTestCase(unittest.TestCase):
    def testFileAppearingAfterPreflightIsNeverReplaced(self):
        with tempfile.TemporaryDirectory() as root:
            job = cdparanoia.ReadVerifyTrackTask.__new__(
                cdparanoia.ReadVerifyTrackTask)
            job.path = os.path.join(root, 'track.flac')
            job._tmppath = job.path + '.part'
            job._tmpwavpath = os.path.join(root, 'audio.wav')
            for path, data in ((job.path, b'original'),
                               (job._tmppath, b'new'),
                               (job._tmpwavpath, b'wav')):
                with open(path, 'wb') as handle:
                    handle.write(data)
            job.exception = None
            job.tasks = [Mock(checksum=123, quality=1.0) for _ in range(7)]
            with patch.object(cdparanoia.task.MultiSeparateTask, 'stop'):
                job.stop()
            self.assertIsInstance(job.exception, FileExistsError)
            with open(job.path, 'rb') as handle:
                self.assertEqual(handle.read(), b'original')
            self.assertFalse(os.path.exists(job._tmppath))
