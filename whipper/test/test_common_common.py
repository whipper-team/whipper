# -*- Mode: Python; test-case-name: whipper.test.test_common_common -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile

from whipper.common import common

from whipper.test import common as tcommon


class ShrinkTestCase(tcommon.TestCase):

    def testSufjan(self):
        path = ('whipper/Sufjan Stevens - Illinois/02. Sufjan Stevens - '
                'The Black Hawk War, or, How to Demolish an Entire '
                'Civilization and Still Feel Good About Yourself in the '
                'Morning, or, We Apologize for the Inconvenience but '
                'You\'re Going to Have to Leave Now, or, "I Have Fought '
                'the Big Knives and Will Continue to Fight Them Until They '
                'Are Off Our Lands!".flac')

        shorter = common.shrinkPath(path)
        self.assertTrue(os.path.splitext(path)[0].startswith(
            os.path.splitext(shorter)[0]))
        self.failIfEquals(path, shorter)


class FramesTestCase(tcommon.TestCase):

    def testFrames(self):
        self.assertEqual(common.framesToHMSF(123456), '00:27:26.06')


class FormatTimeTestCase(tcommon.TestCase):

    def testFormatTime(self):
        self.assertEqual(common.formatTime(7202), '02:00:02.000')


class GetRelativePathTestCase(tcommon.TestCase):

    def testRelativeOutputDirectory(self):
        directory = '.Placebo - Black Market Music (2000)'
        cue = './' + directory + '/Placebo - Black Market Music (2000)'
        track = './' + directory + '/01. Placebo - Taste in Men.flac'

        self.assertEqual(common.getRelativePath(track, cue),
                         '01. Placebo - Taste in Men.flac')


class GetRealPathTestCase(tcommon.TestCase):

    def testRealWithBackslash(self):
        fd, path = tempfile.mkstemp(suffix='back\\slash.flac')
        refPath = os.path.join(os.path.dirname(path), 'fake.cue')

        self.assertEqual(common.getRealPath(refPath, path), path)

        # same path, but with wav extension, will point to flac file
        wavPath = path[:-4] + 'wav'
        self.assertEqual(common.getRealPath(refPath, wavPath), path)

        os.close(fd)
        os.unlink(path)


class AlignTrackPathTestCase(tcommon.TestCase):
    """Issue #692: track files must land in the disc output directory."""

    def testPathIsWithin(self):
        self.assertTrue(common.path_is_within(
            '/tmp/disc/01.flac', '/tmp/disc'))
        self.assertFalse(common.path_is_within(
            '/tmp/other/01.flac', '/tmp/disc'))
        self.assertFalse(common.path_is_within(
            '/tmp/disc', '/tmp/disc'))
        self.assertFalse(common.path_is_within('', '/tmp/disc'))

    def testAlreadyUnderDiscDirUnchanged(self):
        disc = '/out/Artist - Album/Artist - Album'
        track = '/out/Artist - Album/01. Title.flac'
        path, aligned = common.align_track_path(
            track, disc, '%r/%A - %d/%t. %a - %n', '/out')
        self.assertEqual(path, track)
        self.assertFalse(aligned)

    def testBasenameTemplateJoinedUnderDiscDir(self):
        """--track-template '%t. %n' without a directory prefix."""
        disc = '/out/Artist - Album/Artist - Album'
        track = '/out/01. Speed of Life.flac'
        path, aligned = common.align_track_path(
            track, disc, '%t. %n', '/out')
        self.assertTrue(aligned)
        self.assertEqual(
            path,
            '/out/Artist - Album/01. Speed of Life.flac')

    def testHierarchicalTemplateOutsideDiscDirPreservesDirectories(self):
        disc = '/out/Artist - Album/Artist - Album'
        track = '/out/subdir/01. Title.flac'
        path, aligned = common.align_track_path(
            track, disc, 'subdir/%t. %n', '/out')
        self.assertTrue(aligned)
        self.assertEqual(
            path,
            '/out/Artist - Album/subdir/01. Title.flac')
