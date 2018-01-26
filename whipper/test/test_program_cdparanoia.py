# -*- Mode: Python; test-case-name: whipper.test.test_program_cdparanoia -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

from whipper.extern.task import task

from whipper.program import cdparanoia

from whipper.test import common


class ParseTestCase(common.TestCase):

    def setUp(self):
        # report from Afghan Whigs - Sweet Son Of A Bitch
        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia.progress')
        self._parser = cdparanoia.ProgressParser(start=45990, stop=47719)

        self._handle = open(path)

    def testParse(self):
        for line in self._handle.readlines():
            self._parser.parse(line)

        q = '%.01f %%' % (self._parser.getTrackQuality() * 100.0, )
        self.assertEquals(q, '99.6 %')


class Parse1FrameTestCase(common.TestCase):

    def setUp(self):
        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia.progress.strokes')
        self._parser = cdparanoia.ProgressParser(start=0, stop=0)

        self._handle = open(path)

    def testParse(self):
        for line in self._handle.readlines():
            self._parser.parse(line)

        q = '%.01f %%' % (self._parser.getTrackQuality() * 100.0, )
        self.assertEquals(q, '100.0 %')


class ErrorTestCase(common.TestCase):

    def setUp(self):
        # report from a rip with offset -1164 causing scsi errors
        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia.progress.error')
        self._parser = cdparanoia.ProgressParser(start=0, stop=10800)

        self._handle = open(path)

    def testParse(self):
        for line in self._handle.readlines():
            self._parser.parse(line)

        q = '%.01f %%' % (self._parser.getTrackQuality() * 100.0, )
        self.assertEquals(q, '79.6 %')


class VersionTestCase(common.TestCase):

    def testGetVersion(self):
        v = cdparanoia.getCdParanoiaVersion()
        self.failUnless(v)


class AnalyzeFileTask(cdparanoia.AnalyzeTask):

    def __init__(self, path):
        self.command = ['cat', path]

    def readbytesout(self, bytes):
        self.readbyteserr(bytes)


class CacheTestCase(common.TestCase):

    def testDefeatsCache(self):
        self.runner = task.SyncRunner(verbose=False)

        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia', 'PX-L890SA.cdparanoia-A.stderr')
        t = AnalyzeFileTask(path)
        self.runner.run(t)
        self.failUnless(t.defeatsCache)
