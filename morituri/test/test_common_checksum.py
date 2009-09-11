# -*- Mode: Python; test-case-name: morituri.test.test_common_checksum -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest
import tempfile

import gobject
gobject.threads_init()

import gst

from morituri.common import task, checksum

def h(i):
    return "0x%08x" % i

class EmptyTestCase(unittest.TestCase):
    def testEmpty(self):
        # this test makes sure that checksumming empty files doesn't hang
        self.runner = task.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp(suffix='morituri.test.empty')
        checksumtask = checksum.ChecksumTask(path) 
        # FIXME: do we want a specific error for this ?
        self.assertRaises(gst.QueryError, self.runner.run,
            checksumtask, verbose=False)
        os.unlink(path)
