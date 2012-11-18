# -*- Mode: Python; test-case-name: morituri.test.test_common_checksum -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile

import gobject
gobject.threads_init()

from morituri.common import checksum, task as ctask

from morituri.extern.task import task, gstreamer

from morituri.test import common as tcommon


def h(i):
    return "0x%08x" % i


class EmptyTestCase(tcommon.TestCase):

    def testEmpty(self):
        # this test makes sure that checksumming empty files doesn't hang
        self.runner = ctask.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(suffix=u'morituri.test.empty')
        checksumtask = checksum.ChecksumTask(path)
        # FIXME: do we want a specific error for this ?
        e = self.assertRaises(task.TaskException, self.runner.run,
            checksumtask, verbose=False)
        self.failUnless(isinstance(e.exception, gstreamer.GstException))
        os.unlink(path)


class PathTestCase(tcommon.TestCase):

    def _testSuffix(self, suffix):
        self.runner = ctask.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(suffix=suffix)
        checksumtask = checksum.ChecksumTask(path)
        e = self.assertRaises(task.TaskException, self.runner.run,
            checksumtask, verbose=False)
        self.failUnless(isinstance(e.exception, gstreamer.GstException))
        os.unlink(path)


class UnicodePathTestCase(PathTestCase, tcommon.UnicodeTestMixin):

    def testUnicodePath(self):
        # this test makes sure we can checksum a unicode path
        self._testSuffix(u'morituri.test.B\xeate Noire.empty')


class NormalPathTestCase(PathTestCase):

    def testSingleQuote(self):
        self._testSuffix(u"morituri.test.Guns 'N Roses")

    def testDoubleQuote(self):
        # This test makes sure we can checksum files with double quote in
        # their name
        self._testSuffix(u'morituri.test.12" edit')

    def testBackSlash(self):
        # This test makes sure we can checksum files with a backslash in
        # their name
        self._testSuffix(u'morituri.test.40 Years Back\\Come')
