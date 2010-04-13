# -*- Mode: Python; test-case-name: morituri.test.test_common_encode -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile

import gobject
gobject.threads_init()

import gst

from morituri.test import common

from morituri.common import task, encode, log

from morituri.test import common

class PathTestCase(common.TestCase):
    def _testSuffix(self, suffix):
        self.runner = task.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(
            suffix=suffix)
        encodetask = encode.EncodeTask(path, path + '.out',
            encode.WavProfile())
        e = self.assertRaises(task.TaskException, self.runner.run,
            encodetask, verbose=False)
        self.failUnless(isinstance(e.exception, gst.QueryError),
            "%r is not a gst.QueryError" % e.exception)
        os.close(fd)
        os.unlink(path)
        os.unlink(path + '.out')

    def testUnicodePath(self):
        # this test makes sure we can checksum a unicode path
        self._testSuffix(u'.morituri.test_encode.B\xeate Noire')

    def testSingleQuote(self):
        self._testSuffix(u".morituri.test_encode.Guns 'N Roses")

    def testDoubleQuote(self):
        self._testSuffix(u'.morituri.test_encode.12" edit')

class TagReadTestCase(common.TestCase):
    def testRead(self):
        path = os.path.join(os.path.dirname(__file__), u'track.flac')
        self.runner = task.SyncRunner(verbose=False)
        t = encode.TagReadTask(path)
        self.runner.run(t)
        self.failUnless(t.taglist)
        self.assertEquals(t.taglist['audio-codec'], 'FLAC')
        self.assertEquals(t.taglist['description'], 'audiotest wave')
