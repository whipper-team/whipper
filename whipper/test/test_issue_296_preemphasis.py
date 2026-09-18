# -*- Mode: Python; test-case-name: whipper.test.test_issue_296_preemphasis -*-
# vi:si:et:sw=4:sts=4:ts=4

"""Issue #296: report TOC and subcode pre-emphasis flags."""

import os
import tempfile
import unittest
from unittest import mock

from whipper.image import table as table_mod
from whipper.image import toc as toc_mod
from whipper.program import cdrdao
from whipper.result import logger as logger_mod
from whipper.result.result import RipResult, TrackResult


class ProgressParserPreEmphasisTestCase(unittest.TestCase):

    def _parse_lines(self, lines):
        p = cdrdao.ProgressParser()
        for line in lines:
            p.parse(line)
        return p

    def testMismatchRecordedPerTrack(self):
        p = self._parse_lines([
            '----------------------------------------------------------',
            'Analyzing track 2 (AUDIO): start 04:25:30, length 05:00:50...',
            'Pre-emphasis flag of track differs from TOC - '
            'toc file contains TOC setting.',
            'Track 2 finished, found 3 Q sub-channels with CRC errors',
        ])
        self.assertEqual(p.currentTrack, 2)
        self.assertTrue(p.preEmphasisMismatch.get(2))
        # TOC said False/None; subcode differs → True if TOC is False
        self.assertIs(p.subcodePreEmphasis(2, False), True)
        self.assertIs(p.subcodePreEmphasis(2, True), False)
        self.assertIsNone(p.subcodePreEmphasis(2, None))

    def testControlMatchMeansSubcodeEqualsToc(self):
        p = self._parse_lines([
            'Analyzing track 1 (AUDIO): start 00:00:00, length 04:25:30...',
            'Control nibbles of track match CD-TOC settings.',
        ])
        self.assertTrue(p.controlMatch.get(1))
        self.assertIs(p.subcodePreEmphasis(1, False), False)
        self.assertIs(p.subcodePreEmphasis(1, True), True)

    def testNoDiagnosticsMeansUnknown(self):
        p = self._parse_lines([
            'Analyzing track 3 (AUDIO): start 09:26:05, length 04:58:12...',
            'Track 3 finished, found 6 Q sub-channels with CRC errors',
        ])
        self.assertIsNone(p.subcodePreEmphasis(3, False))
        self.assertIsNone(p.preEmphasisMismatch.get(3))

    def testChannelMismatchRecorded(self):
        p = self._parse_lines([
            'Analyzing track 4 (AUDIO): start 14:24:17, length 04:06:53...',
            '2-/4-channel-audio  flag of track differs from TOC - '
            'toc file contains TOC setting.',
        ])
        self.assertTrue(p.channelMismatch.get(4))


class ApplySubcodeTestCase(unittest.TestCase):

    def testApplyOntoTableTracks(self):
        task = cdrdao.ReadTOCTask.__new__(cdrdao.ReadTOCTask)
        task._parser = cdrdao.ProgressParser()
        for line in [
            'Analyzing track 1 (AUDIO): start 00:00:00, length 04:25:30...',
            'Control nibbles of track match CD-TOC settings.',
            'Analyzing track 2 (AUDIO): start 04:25:30, length 05:00:50...',
            'Pre-emphasis flag of track differs from TOC - '
            'toc file contains TOC setting.',
        ]:
            task._parser.parse(line)

        tbl = table_mod.Table()
        t1 = table_mod.Track(1)
        t1.pre_emphasis = False
        t2 = table_mod.Track(2)
        t2.pre_emphasis = False
        tbl.tracks.extend([t1, t2])

        task._applySubcodePreEmphasis(tbl)
        self.assertIs(t1.pre_emphasis_subcode, False)
        self.assertIs(t1.pre_emphasis_conflict, False)
        self.assertIs(t2.pre_emphasis_subcode, True)
        self.assertTrue(t2.pre_emphasis_conflict)
        self.assertIs(t2.pre_emphasis_toc, False)


class TocPreEmphasisParseTestCase(unittest.TestCase):

    def testExplicitNoPreEmphasis(self):
        toc = """CD_DA

TRACK AUDIO
NO PRE_EMPHASIS
FILE "a.wav" 0 00:00:00
INDEX 00:00:00

TRACK AUDIO
PRE_EMPHASIS
FILE "a.wav" 00:01:00 00:01:00
INDEX 00:00:00
"""
        fd, path = tempfile.mkstemp(suffix='.toc')
        os.close(fd)
        with open(path, 'w') as f:
            f.write(toc)
        self.addCleanup(lambda p=path: os.path.exists(p) and os.unlink(p))
        t = toc_mod.TocFile(path)
        t.parse()
        self.assertIs(t.table.tracks[0].pre_emphasis, False)
        self.assertIs(t.table.tracks[1].pre_emphasis, True)


class _MockImageTrack:
    def __init__(self, number, start, end):
        self.number = number
        self.absolute = self.start = start
        self.end = end
        self.path = None

    def getIndex(self, num):
        if num == 0:
            raise KeyError(num)
        return self


class _MockImageTable:
    def __init__(self):
        self.tracks = [_MockImageTrack(1, 0, 100)]

    @staticmethod
    def getCDDBDiscId():
        return "c30bde0d"

    @staticmethod
    def getMusicBrainzDiscId():
        return "eyjySLXGdKigAjY3_C0nbBmNUHc-"

    @staticmethod
    def getMusicBrainzSubmitURL():
        return "https://musicbrainz.org/"

    @staticmethod
    def getTrackLength(number):
        return 100

    @staticmethod
    def getTrackEnd(number):
        return 99


class LoggerPreEmphasisTestCase(unittest.TestCase):

    def testLogReportsSubcodeAndConflict(self):
        rip = RipResult()
        rip.offset = 0
        rip.overread = False
        rip.isCdr = False
        rip.table = _MockImageTable()
        rip.artist = "Artist"
        rip.title = "Title"
        rip.vendor = "VEN"
        rip.model = "MOD"
        rip.release = "1"
        rip.cdrdaoVersion = "1.2.4"
        rip.cdparanoiaVersion = "cdparanoia III 10.2"
        rip.cdparanoiaDefeatsCache = True
        tr = TrackResult()
        tr.number = 1
        tr.filename = "./01.flac"
        tr.peak = 1000
        tr.quality = 1.0
        tr.copyspeed = 2.0
        tr.testduration = 1
        tr.copyduration = 1
        tr.testcrc = 0x1
        tr.copycrc = 0x1
        tr.pre_emphasis = False
        tr.pre_emphasis_toc = False
        tr.pre_emphasis_subcode = True
        tr.pre_emphasis_conflict = True
        tr.AR = {
            "v1": {"DBConfidence": None, "DBCRC": None, "CRC": None},
            "v2": {"DBConfidence": None, "DBCRC": None, "CRC": None},
        }
        rip.tracks.append(tr)
        log = logger_mod.WhipperLogger().log(rip, epoch=0)
        self.assertIn("Pre-emphasis:", log)
        self.assertIn("Pre-emphasis (subcode):", log)
        self.assertIn("Pre-emphasis conflict:", log)
        self.assertIn("TOC=False, subcode=True", log)

    def testLogCleanNoSubcodeFieldsWhenUnknown(self):
        rip = RipResult()
        rip.offset = 0
        rip.overread = False
        rip.isCdr = False
        rip.table = _MockImageTable()
        rip.artist = "Artist"
        rip.title = "Title"
        rip.vendor = "VEN"
        rip.model = "MOD"
        rip.release = "1"
        rip.cdrdaoVersion = "1.2.4"
        rip.cdparanoiaVersion = "cdparanoia III 10.2"
        rip.cdparanoiaDefeatsCache = True
        tr = TrackResult()
        tr.number = 1
        tr.filename = "./01.flac"
        tr.peak = 1000
        tr.quality = 1.0
        tr.copyspeed = 2.0
        tr.testduration = 1
        tr.copyduration = 1
        tr.testcrc = 0x1
        tr.copycrc = 0x1
        tr.pre_emphasis = False
        tr.pre_emphasis_toc = False
        tr.pre_emphasis_subcode = None
        tr.pre_emphasis_conflict = False
        tr.AR = {
            "v1": {"DBConfidence": None, "DBCRC": None, "CRC": None},
            "v2": {"DBConfidence": None, "DBCRC": None, "CRC": None},
        }
        rip.tracks.append(tr)
        log = logger_mod.WhipperLogger().log(rip, epoch=0)
        self.assertIn("Pre-emphasis:", log)
        self.assertNotIn("Pre-emphasis (subcode):", log)
        self.assertNotIn("Pre-emphasis conflict:", log)
