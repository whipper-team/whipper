# -*- Mode: Python; test-case-name: whipper.test.test_program_sox -*-

import os
import tempfile

from whipper.common import common
from whipper.extern.task import task
from whipper.program.soxi import AudioLengthTask
from whipper.test import common as tcommon

base_track_file = os.path.join(os.path.dirname(__file__), u'track.flac')
base_track_length = 10 * common.SAMPLES_PER_FRAME


class AudioLengthTestCase(tcommon.TestCase):

    def testLength(self):
        path = base_track_file
        t = AudioLengthTask(path)
        runner = task.SyncRunner()
        runner.run(t, verbose=False)
        self.assertEqual(t.length, base_track_length)


class AudioLengthPathTestCase(tcommon.TestCase):

    def _testSuffix(self, suffix):
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as temptrack:
            temptrack.write(open(base_track_file, "rb").read())

        t = AudioLengthTask(path)
        runner = task.SyncRunner()
        runner.run(t, verbose=False)
        self.assertEqual(t.length, base_track_length)
        os.unlink(path)


class NormalAudioLengthPathTestCase(AudioLengthPathTestCase):

    def testSingleQuote(self):
        self._testSuffix(u"whipper.test.Guns 'N Roses.flac")

    def testDoubleQuote(self):
        # This test makes sure we can checksum files with double quote in
        # their name
        self._testSuffix(u'whipper.test.12" edit.flac')


class UnicodeAudioLengthPathTestCase(AudioLengthPathTestCase,
                                     tcommon.UnicodeTestMixin):

    def testUnicodePath(self):
        # this test makes sure we can checksum a unicode path
        self._testSuffix(u'whipper.test.B\xeate Noire.empty.flac')


class AbsentFileAudioLengthPathTestCase(AudioLengthPathTestCase):
    def testAbsentFile(self):
        tempdir = tempfile.mkdtemp()
        path = os.path.join(tempdir, u"nonexistent.flac")

        t = AudioLengthTask(path)
        runner = task.SyncRunner()
        self.assertRaises(task.TaskException, runner.run,
                          t, verbose=False)

        os.rmdir(tempdir)
