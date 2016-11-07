# -*- Mode: Python; test-case-name: morituri.test.test_program_sox -*-

import os
import tempfile

from morituri.common import common
from morituri.extern.task import task
from morituri.program.soxi import AudioLengthTask
from morituri.test import common as tcommon

class AudioLengthTestCase(tcommon.TestCase):

    def testLength(self):
        path = os.path.join(os.path.dirname(__file__), u'track.flac')
        t = AudioLengthTask(path)
        runner = task.SyncRunner()
        runner.run(t, verbose=False)
        self.assertEquals(t.length, 10 * common.SAMPLES_PER_FRAME)


class AudioLengthPathTestCase(tcommon.TestCase):

    def _testSuffix(self, suffix):
        self.runner = task.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(suffix=suffix)
        t = AudioLengthTask(path)
        e = self.assertRaises(task.TaskException, self.runner.run,
            t, verbose=False)
        self.failUnless(isinstance(e.exception, gstreamer.GstException),
            "%r is not a gstreamer.GstException" % e.exceptionMessage)
        self.assertEquals(e.exception.gerror.domain, gst.STREAM_ERROR)
        # our empty file triggers TYPE_NOT_FOUND
        self.assertEquals(e.exception.gerror.code,
            gst.STREAM_ERROR_TYPE_NOT_FOUND)
        os.unlink(path)

class NormalAudioLengthPathTestCase(AudioLengthPathTestCase):

    def testSingleQuote(self):
        self._testSuffix(u"morituri.test.Guns 'N Roses")

    def testDoubleQuote(self):
        # This test makes sure we can checksum files with double quote in
        # their name
        self._testSuffix(u'morituri.test.12" edit')


class UnicodeAudioLengthPathTestCase(AudioLengthPathTestCase,
        tcommon.UnicodeTestMixin):

    def testUnicodePath(self):
        # this test makes sure we can checksum a unicode path
        self._testSuffix(u'morituri.test.B\xeate Noire.empty')
