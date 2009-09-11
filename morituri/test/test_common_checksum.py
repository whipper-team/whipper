# -*- Mode: Python; test-case-name: morituri.test.test_common_checksum -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest
import tempfile

import gobject
gobject.threads_init()

import gst

from morituri.common import task, checksum

from morituri.test import common

def h(i):
    return "0x%08x" % i

class EmptyTestCase(unittest.TestCase):
    def testEmpty(self):
        # this test makes sure that checksumming empty files doesn't hang
        self.runner = task.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(suffix=u'morituri.test.empty')
        checksumtask = checksum.ChecksumTask(path) 
        # FIXME: do we want a specific error for this ?
        self.assertRaises(gst.QueryError, self.runner.run,
            checksumtask, verbose=False)
        os.unlink(path)

    def testUnicodePath(self):
        # this test makes sure we can checksum a unicode path
        self.runner = task.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(
            suffix=u'morituri.test.B\xeate Noire.empty')
        checksumtask = checksum.ChecksumTask(path) 
        self.assertRaises(gst.QueryError, self.runner.run,
            checksumtask, verbose=False)
        os.unlink(path)
