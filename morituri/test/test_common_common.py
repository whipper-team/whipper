# -*- Mode: Python; test-case-name: morituri.test.test_common_common -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile

from morituri.common import common

from morituri.test import common as tcommon


class ShrinkTestCase(tcommon.TestCase):

    def testSufjan(self):
        path = (u'morituri/Sufjan Stevens - Illinois/02. Sufjan Stevens - '
                 'The Black Hawk War, or, How to Demolish an Entire '
                 'Civilization and Still Feel Good About Yourself in the '
                 'Morning, or, We Apologize for the Inconvenience but '
                 'You\'re Going to Have to Leave Now, or, "I Have Fought '
                 'the Big Knives and Will Continue to Fight Them Until They '
                 'Are Off Our Lands!".flac')

        shorter = common.shrinkPath(path)
        self.failUnless(os.path.splitext(path)[0].startswith(
            os.path.splitext(shorter)[0]))
        self.failIfEquals(path, shorter)


class FramesTestCase(tcommon.TestCase):

    def testFrames(self):
        self.assertEquals(common.framesToHMSF(123456), '00:27:26.06')


class FormatTimeTestCase(tcommon.TestCase):

    def testFormatTime(self):
        self.assertEquals(common.formatTime(7202), '02:00:02.000')


class GetRelativePathTestCase(tcommon.TestCase):

    def testRelativeOutputDirectory(self):
        directory = '.Placebo - Black Market Music (2000)'
        cue = './' + directory + '/Placebo - Black Market Music (2000)'
        track = './' + directory + '/01. Placebo - Taste in Men.flac'

        self.assertEquals(common.getRelativePath(track, cue),
            '01. Placebo - Taste in Men.flac')


class GetRealPathTestCase(tcommon.TestCase):

    def testRealWithBackslash(self):
        fd, path = tempfile.mkstemp(suffix=u'back\\slash.flac')
        refPath = os.path.join(os.path.dirname(path), 'fake.cue')

        self.assertEquals(common.getRealPath(refPath, path),
            path)

        # same path, but with wav extension, will point to flac file
        wavPath = path[:-4] + 'wav'
        self.assertEquals(common.getRealPath(refPath, wavPath),
            path)

        os.close(fd)
        os.unlink(path)
