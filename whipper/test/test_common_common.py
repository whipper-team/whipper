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


class TruncateFilenameTestCase(tcommon.TestCase):
    """Issue #453 / PR #672: path components must respect NAME_MAX."""

    def testShortPathUnchanged(self):
        path = os.path.join('/tmp', 'Artist - Album', '01. Track.flac')
        self.assertEqual(common.truncate_filename(path), path)

    def testLongFilenameTruncatedWithExtension(self):
        long_name = 'a' * 400
        path = os.path.join('/tmp', long_name + '.flac')
        result = common.truncate_filename(path)
        base = os.path.basename(result)
        self.assertLessEqual(len(base.encode('utf-8')), 255)
        self.assertTrue(base.endswith('.flac'))

    def testLongDirectoryNameTruncated(self):
        long_dir = 'D' * 400
        result = common.truncate_filename(
            os.path.join('/tmp', long_dir), has_file_ext=False)
        self.assertLessEqual(len(os.path.basename(result).encode('utf-8')),
                             255)

    def testReserveRoomForExtension(self):
        long_name = 'b' * 400
        path = os.path.join('/tmp', long_name)
        result = common.truncate_filename(path, has_file_ext=False,
                                          reserve=8)
        base = os.path.basename(result)
        # Leave room for e.g. '.flac' (5) plus margin
        self.assertLessEqual(len(base.encode('utf-8')), 255 - 8)

    def testMissingParentDoesNotCrash(self):
        path = os.path.join('/tmp', 'does-not-exist-xyz', 'n' * 400 + '.flac')
        result = common.truncate_filename(path)
        self.assertLessEqual(len(os.path.basename(result).encode('utf-8')),
                             255)

    def testTruncatePathComponents(self):
        long_dir = 'L' * 300
        long_file = 'F' * 300
        path = os.path.join(long_dir, long_file)
        result = common.truncate_path_components(path)
        parts = result.split(os.sep)
        for part in parts:
            if part:
                self.assertLessEqual(len(part.encode('utf-8')), 255)
        self.assertEqual(len(parts), 2)
