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

    def testErrorClassification(self):
        for line in self._handle.readlines():
            self._parser.parse(line)

        counts = self._parser.getEventCounts()
        # Routine callbacks (read/wrote/verify/finished) are not recorded
        self.assertNotIn('read', counts)
        self.assertNotIn('wrote', counts)
        self.assertNotIn('verify', counts)

        self.assertEqual(counts.get('jitter'), 338)
        self.assertEqual(counts.get('overlap'), 24)
        self.assertEqual(counts.get('transport error'), 24)
        self.assertEqual(counts.get('skip'), 1)
        self.assertEqual(counts.get('scsi_read error'), 216)

        # corrections = jitter + overlap
        self.assertEqual(self._parser.corrections, 338 + 24)
        # Overlapping transport/raw evidence uses max, plus the skip.
        self.assertEqual(self._parser.severeErrors, max(24, 216) + 1)

        positions = self._parser.getSuspiciousPositions()
        self.assertTrue(positions)
        for start, end in positions:
            self.assertGreaterEqual(start, 0)
            self.assertLessEqual(end, 10800)
            self.assertLessEqual(start, end)


class CleanRipTestCase(common.TestCase):

    def setUp(self):
        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia.progress.strokes')
        self._parser = cdparanoia.ProgressParser(start=0, stop=0)
        with open(path) as handle:
            for line in handle.readlines():
                self._parser.parse(line)

    def testNoSevereErrorsOnCleanRip(self):
        # A 100% quality rip still emits a couple of [correction] lines
        # outside the ripped range; those are not severe and not positions.
        self.assertEqual(self._parser.severeErrors, 0)
        self.assertEqual(self._parser.getSuspiciousPositions(), [])
        counts = self._parser.getEventCounts()
        self.assertEqual(counts.get('correction'), 2)
        self.assertNotIn('jitter', counts)
        self.assertNotIn('skip', counts)
        self.assertNotIn('transport error', counts)


class VersionTestCase(common.TestCase):

    def testGetVersion(self):
        v = cdparanoia.getCdParanoiaVersion()
        self.assertTrue(v)


class AnalyzeFileTask(cdparanoia.AnalyzeTask):

    def __init__(self, path):
        self.command = ['cat', path]

    def readbytesout(self, bytes_stdout):
        self.readbyteserr(bytes_stdout)


class CacheTestCase(common.TestCase):

    def testDefeatsCache(self):
        self.runner = task.SyncRunner(verbose=False)

        path = os.path.join(os.path.dirname(__file__),
                            'cdparanoia', 'PX-L890SA.cdparanoia-A.stderr')
        t = AnalyzeFileTask(path)
        self.runner.run(t)
        self.assertTrue(t.defeatsCache)


class EventSemanticsTestCase(common.TestCase):
    @staticmethod
    def parse(output, start=0, stop=1000):
        parser = cdparanoia.ProgressParser(start, stop)
        for line in output.splitlines():
            parser.parse(line)
        return parser

    def testOverlapWindowNeverBecomesPosition(self):
        parser = self.parse('##: 9 [overlap] @ 117600\n'
                            '##: 9 [overlap] @ 235200')
        self.assertEqual(parser.getEventCounts(), {'overlap': 2})
        self.assertEqual(parser.corrections, 2)
        self.assertEqual(parser.getSuspiciousPositions(), [])

    def testEstablishedPositionsAreTrackRelative(self):
        for name in ('jitter', 'correction', 'dropped', 'duped', 'drift',
                     'transport error', 'cache error', 'skip'):
            with self.subTest(name=name):
                parser = self.parse('##: 2 [%s] @ 235200' % name,
                                    start=150)
                self.assertEqual(parser.getEventCounts(), {name: 1})
                self.assertEqual(parser.getSuspiciousPositions(), [(50, 50)])

    def testUnsupportedAndUnknownArgumentsAreNotPositions(self):
        for name in ('scratch', 'scratch repair', 'backoff', 'new callback'):
            with self.subTest(name=name):
                parser = self.parse('##: 4 [%s] @ 235200' % name)
                self.assertEqual(parser.getEventCounts(), {name: 1})
                self.assertEqual(parser.getSuspiciousPositions(), [])

    def testRawFailureThenSuccessfulReadHasNoInventedPosition(self):
        parser = self.parse('##: 0 [read] @ 117600\n'
                            'scsi_read error: sector=200 length=1 retry=0\n'
                            '##: 0 [read] @ 236376\n'
                            '##: 14 [wrote] @ 235199')
        self.assertEqual(parser.errors, 1)
        self.assertEqual(parser.severeErrors, 1)
        self.assertEqual(parser.getSuspiciousPositions(), [])
        self.assertEqual(cdparanoia.classify_cdparanoia_events(
            parser.getEventCounts()), (1, 0, []))

    def testRepeatedRetriesAndTransportReportsAreNotAdded(self):
        for callbacks_first in (False, True):
            with self.subTest(callbacks_first=callbacks_first):
                raw = '\n'.join('scsi_read error: sector=200 length=1 '
                                'retry=%d' % i for i in range(9))
                callback = '##: 12 [transport error] @ 235200'
                output = (callback + '\n' + raw if callbacks_first else
                          raw + '\n' + callback)
                parser = self.parse(output)
                self.assertEqual(parser.getEventCounts(),
                                 {'transport error': 1, 'scsi_read error': 9})
                self.assertEqual(parser.severeErrors, 9)
                self.assertEqual(parser.getSuspiciousPositions(), [(200, 200)])

    def testMixedEventsRetainOnlyEstablishedPositions(self):
        parser = self.parse('##: 9 [overlap] @ 117600\n'
                            'scsi_read error: sector=200 length=1 retry=0\n'
                            '##: 12 [transport error] @ 235200\n'
                            '##: 2 [jitter] @ 352800\n'
                            '##: 6 [skip] @ 470400')
        self.assertEqual(parser.severeErrors, 2)
        self.assertEqual(parser.corrections, 2)
        self.assertEqual(parser.getSuspiciousPositions(),
                         [(200, 200), (300, 300), (400, 400)])
        self.assertEqual(cdparanoia.classify_cdparanoia_events(
            parser.getEventCounts()), (2, 2, ['skip']))

    def testInvalidAndOutOfRangePositionsAreExcluded(self):
        parser = self.parse('##: 2 [jitter] @ -1176\n'
                            '##: 2 [jitter] @ 1177176')
        self.assertEqual(parser.corrections, 2)
        self.assertEqual(parser.getSuspiciousPositions(), [])

    def testAbortLimitRemainsForEachSevereChannel(self):
        from unittest.mock import Mock
        from whipper.image.table import Table
        for line in ('scsi_read error: sector=200 length=1 retry=0',
                     '##: 12 [transport error] @ 235200',
                     '##: 6 [skip] @ 235200'):
            with self.subTest(line=line):
                read_task = cdparanoia.ReadTrackTask(
                    'unused.wav', Table(), 0, 1000, False)
                read_task._popen = Mock()
                read_task.schedule = Mock()
                read_task._popen.recv_err.return_value = (
                    (line + '\n') * 100).encode()
                read_task._read(Mock())
                read_task._popen.terminate.assert_not_called()
                read_task._popen.recv_err.return_value = (line + '\n').encode()
                read_task._read(Mock())
                read_task._popen.terminate.assert_called_once_with()

    def testCorrectionWarningsDoNotPromisePositions(self):
        from unittest.mock import patch
        from whipper.image.table import Table
        read_task = cdparanoia.ReadTrackTask(
            'unused.wav', Table(), 0, 1000, False)
        read_task.corrections = 1
        read_task.severeErrors = 1
        with patch.object(cdparanoia.logger, 'warning') as warning:
            read_task._report_cdparanoia_errors()
        messages = [call.args[0] for call in warning.call_args_list]
        self.assertIn('recovery is not established', messages[0])
        self.assertIn('available positions', messages[1])

    def testTestAndCopyAggregationPreservesCountsAndMergesPositions(self):
        from whipper.image.table import Table
        passes = []
        for output in (
                '##: 9 [overlap] @ 117600\n'
                '##: 2 [jitter] @ 235200\n'
                'scsi_read error: sector=200 length=1 retry=0',
                '##: 9 [overlap] @ 117600\n'
                '##: 12 [transport error] @ 247080\n'
                '##: 6 [skip] @ 470400'):
            parser = self.parse(output, start=150)
            read_task = cdparanoia.ReadTrackTask(
                'unused.wav', Table(), 150, 1000, False)
            read_task.errorCounts = parser.getEventCounts()
            read_task.suspiciousPositions = parser.getSuspiciousPositions()
            read_task.corrections = parser.corrections
            read_task.severeErrors = parser.severeErrors
            passes.append(read_task)
        combined = cdparanoia.ReadVerifyTrackTask.__new__(
            cdparanoia.ReadVerifyTrackTask)
        combined.tasks = passes
        combined._aggregate_cdparanoia_errors()
        self.assertEqual(combined.errorCounts, {
            'overlap': 2, 'jitter': 1, 'scsi_read error': 1,
            'transport error': 1, 'skip': 1})
        self.assertEqual(combined.corrections, 3)
        self.assertEqual(combined.severeErrors, 3)
        self.assertEqual(combined.suspiciousPositions, [(50, 60), (250, 250)])

    def testDistinctFailureSectorsDoNotSuppressAbort(self):
        parser = self.parse(
            ('scsi_read error: sector=200 length=1 retry=0\n' * 60) +
            ('##: 12 [transport error] @ 470400\n' * 60))
        self.assertEqual(parser.severeErrors, 120)
        self.assertGreater(parser.severeErrors,
                           cdparanoia.ReadTrackTask._MAXERROR)

    def testUnlocatedRawFailuresCannotSuppressTransportFailures(self):
        parser = self.parse('scsi_read error: unknown format\n'
                            '##: 12 [transport error] @ 235200')
        self.assertEqual(parser.severeErrors, 2)
