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
        self.assertEqual(q, '99.6 %')


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
        self.assertEqual(q, '100.0 %')


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
        self.assertEqual(q, '79.6 %')


class VersionTestCase(common.TestCase):

    def testGetVersion(self):
        v = cdparanoia.getCdParanoiaVersion()
        self.assertTrue(v)


class AnalyzeFileTask(cdparanoia.AnalyzeTask):

    def __init__(self, path):
        self._output = []
        self.cwd = None
        self.command = ['cat', path]

    def readbytesout(self, bytes_stdout):
        self.readbyteserr(bytes_stdout)


class AnalyzeOutputTestCase(common.TestCase):
    """Issue #608: AnalyzeTask must tolerate bytes/str process output."""

    def testJoinedOutputDecodesBytes(self):
        out = cdparanoia.AnalyzeTask._joined_output(
            [b'Drive tests OK', b' with Paranoia.'])
        self.assertEqual(out, 'Drive tests OK with Paranoia.')

    def testJoinedOutputAcceptsMixedTypes(self):
        out = cdparanoia.AnalyzeTask._joined_output(
            [b'bytes', ' and ', b'\xffinvalid'])
        self.assertIn('bytes', out)
        self.assertIn(' and ', out)
        # invalid utf-8 must not raise
        self.assertIsInstance(out, str)

    def testFailedWithBytesDoesNotRaise(self):
        task = AnalyzeFileTask.__new__(AnalyzeFileTask)
        task._output = [b'WARNING! PARANOIA MAY NOT BE', b'\naborting test.']
        task.cwd = None
        # failed() must not TypeError on bytes
        task.failed()
        self.assertIs(task.defeatsCache, False)

    def testFailedWithStringOutput(self):
        task = AnalyzeFileTask.__new__(AnalyzeFileTask)
        task._output = ['WARNING! PARANOIA MAY NOT BE', '\naborting test.']
        task.cwd = None
        task.failed()
        self.assertIs(task.defeatsCache, False)

    def testDoneDetectsOk(self):
        task = AnalyzeFileTask.__new__(AnalyzeFileTask)
        task._output = [b'Drive tests OK with Paranoia.']
        task.cwd = None
        task.done()
        self.assertIs(task.defeatsCache, True)

    def testInstancesDoNotShareOutputBuffers(self):
        class Dummy(cdparanoia.AnalyzeTask):
            def __init__(self):
                self._output = []
                self.cwd = None
                self.command = []

        a = Dummy()
        b = Dummy()
        a.readbyteserr(b'from-a')
        self.assertEqual(a._output, [b'from-a'])
        self.assertEqual(b._output, [])


class CacheTestCase(common.TestCase):

    def testDefeatsCache(self):
        self.runner = task.SyncRunner(verbose=False)

        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia', 'PX-L890SA.cdparanoia-A.stderr')
        t = AnalyzeFileTask(path)
        self.runner.run(t)
        self.assertTrue(t.defeatsCache)
