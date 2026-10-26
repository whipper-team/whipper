from __future__ import print_function
import hashlib
import os
import re
import unittest

from whipper.common.yaml import YAML
from whipper.result.result import TrackResult, RipResult
from whipper.result.logger import WhipperLogger


class MockImageTrack:
    def __init__(self, number, start, end):
        self.number = number
        self.absolute = self.start = start
        self.end = end

    def getIndex(self, num):
        if num == 0:
            raise KeyError
        else:
            return self


class MockImageTable:
    """Mock of whipper.image.table.Table, with fake information."""
    def __init__(self):
        self.tracks = [
            MockImageTrack(1, 0,  16263),
            MockImageTrack(2, 16264, 33487)
        ]

    @staticmethod
    def getCDDBDiscId():
        return "c30bde0d"

    @staticmethod
    def getMusicBrainzDiscId():
        return "eyjySLXGdKigAjY3_C0nbBmNUHc-"

    @staticmethod
    def getMusicBrainzSubmitURL():
        return (
            "https://musicbrainz.org/cdtoc/attach?toc=1+13+228039+150+16414+"
            "33638+51378+69369+88891+104871+121645+138672+160748+178096+194680"
            "+212628&tracks=13&id=eyjySLXGdKigAjY3_C0nbBmNUHc-"
        )

    def getTrackLength(self, number):
        return self.tracks[number-1].end - self.tracks[number-1].start + 1

    def getTrackEnd(self, number):
        return self.tracks[number-1].end


class LoggerTestCase(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__))

    def testLogger(self):
        ripResult = RipResult()
        ripResult.offset = 6
        ripResult.overread = False
        ripResult.isCdr = False
        ripResult.table = MockImageTable()
        ripResult.artist = "Example - Symbol - Artist"
        ripResult.title = "Album With: - Dashes"
        ripResult.vendor = "HL-DT-STBD-RE  "
        ripResult.model = "WH14NS40"
        ripResult.release = "1.03"
        ripResult.cdrdaoVersion = "1.2.4"
        ripResult.cdparanoiaVersion = (
            "cdparanoia III 10.2 "
            "libcdio 2.0.0 x86_64-pc-linux-gnu"
        )
        ripResult.cdparanoiaDefeatsCache = True

        trackResult = TrackResult()
        trackResult.number = 1
        trackResult.filename = (
            "./soundtrack/Various Artists - Shark Tale - Motion Picture "
            "Soundtrack/01. Sean Paul & Ziggy Marley - Three Little Birds.flac"
        )
        trackResult.pregap = 0
        trackResult.peak = 29503
        trackResult.quality = 1
        trackResult.copyspeed = 7
        trackResult.testduration = 10
        trackResult.copyduration = 10
        trackResult.testcrc = 0x0025D726
        trackResult.copycrc = 0x0025D726
        trackResult.AR = {
            "v1": {
                "DBConfidence": 14,
                "DBCRC": "95E6A189",
                "CRC": "95E6A189"
            },
            "v2": {
                "DBConfidence": 11,
                "DBCRC": "113FA733",
                "CRC": "113FA733"
            }
        }
        ripResult.tracks.append(trackResult)

        trackResult = TrackResult()
        trackResult.number = 2
        trackResult.filename = (
            "./soundtrack/Various Artists - Shark Tale - Motion Picture "
            "Soundtrack/02. Christina Aguilera feat. Missy Elliott - Car "
            "Wash (Shark Tale mix).flac"
        )
        trackResult.pregap = 0
        trackResult.peak = 31862
        trackResult.quality = 1
        trackResult.copyspeed = 7.7
        trackResult.testduration = 10
        trackResult.copyduration = 10
        trackResult.testcrc = 0xF77C14CB
        trackResult.copycrc = 0xF77C14CB
        trackResult.AR = {
            "v1": {
                "DBConfidence": 14,
                "DBCRC": "0B3316DB",
                "CRC": "0B3316DB"
            },
            "v2": {
                "DBConfidence": 10,
                "DBCRC": "A0AE0E57",
                "CRC": "A0AE0E57"
            }
        }
        ripResult.tracks.append(trackResult)
        logger = WhipperLogger()
        actual = logger.log(ripResult)
        actualLines = actual.splitlines()
        with open(os.path.join(self.path,
                               'test_result_logger.log'), 'r') as f:
            expectedLines = f.read().splitlines()
        # do not test on version line, date line, or SHA-256 hash line
        self.assertListEqual(actualLines[2:-1], expectedLines[2:-1])

        # RegEX updated to support all the 4 cases of the versioning scheme:
        # https://github.com/pypa/setuptools_scm/#default-versioning-scheme
        versionSchemes = [
            actualLines[0],  # 'Log created by: whipper 0.7.4.dev87+gb71ec9f.d20191026 (internal logger)'  # noqa: E501
            'Log created by: whipper 0.7.4.dev87+gb71ec9f (internal logger)',
            'Log created by: whipper 0.7.4+d20191026 (internal logger)',
            'Log created by: whipper 0.7.4 (internal logger)'
        ]
        created_by_re = re.compile((
                            r'Log created by: whipper '
                            r'[\d]+\.[\d]+\.[\d]+(\+d\d{8}|\.dev[\w.+]+)? '
                            r'\(internal logger\)'
                        ))
        for versionScheme in versionSchemes:
            self.assertRegex(versionScheme, created_by_re)
        self.assertRegex(
            actualLines[1],
            re.compile((
                r'Log creation date: '
                r'20[\d]{2}-[\d]{2}-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}Z'
            ))
        )

        yaml = YAML(
            typ='rt',
            pure=True
        )
        parsedLog = yaml.load(actual)
        self.assertEqual(
            actual,
            yaml.dump(parsedLog)
        )
        log_body = "\n".join(actualLines[:-1]).encode()
        self.assertEqual(
            parsedLog['SHA-256 hash'],
            hashlib.sha256(log_body).hexdigest().upper()
        )

    def testLoggerReportsCdparanoiaErrors(self):
        """Suspicious positions and non-fatal events appear in the log."""
        ripResult = RipResult()
        ripResult.offset = 6
        ripResult.overread = False
        ripResult.isCdr = False
        ripResult.table = MockImageTable()
        ripResult.artist = "Example Artist"
        ripResult.title = "Example Album"
        ripResult.vendor = "HL-DT-ST"
        ripResult.model = "DVDRAM"
        ripResult.release = "1.00"
        ripResult.cdrdaoVersion = "1.2.4"
        ripResult.cdparanoiaVersion = "cdparanoia III 10.2"
        ripResult.cdparanoiaDefeatsCache = True

        trackResult = TrackResult()
        trackResult.number = 1
        trackResult.filename = "./01 - Example.flac"
        trackResult.pregap = 0
        trackResult.peak = 29503
        trackResult.quality = 0.80
        trackResult.copyspeed = 2.0
        trackResult.testduration = 10
        trackResult.copyduration = 10
        trackResult.testcrc = 0x0025D726
        trackResult.copycrc = 0x0025D726
        trackResult.cdparanoiaEvents = {
            "jitter": 3,
            "transport error": 1,
            "skip": 0,
            "scsi_read error": 2,
        }
        trackResult.suspiciousPositions = [(90, 91), (4500, 4510)]
        trackResult.AR = {
            "v1": {"DBConfidence": None, "DBCRC": None, "CRC": None},
            "v2": {"DBConfidence": None, "DBCRC": None, "CRC": None},
        }
        ripResult.tracks.append(trackResult)

        log = WhipperLogger().log(ripResult, epoch=0)
        self.assertIn("cdparanoia events:", log)
        self.assertIn("jitter: 3", log)
        self.assertIn("transport error: 1", log)
        self.assertIn("scsi_read error: 2", log)
        # zero-valued events are omitted
        self.assertNotIn("skip:", log)
        # track-relative positions in MSF
        self.assertIn("Suspicious positions:", log)
        self.assertIn("00:01:15 - 00:01:16", log)
        self.assertIn("01:00:00 - 01:00:10", log)
        # matching CRCs but severe cdparanoia errors reported
        self.assertIn("Copy OK (cdparanoia reported severe recoverable", log)
        self.assertIn("Health status: There were errors", log)
        self.assertIn("cdparanoia health:", log)
        self.assertNotIn("definitely lossy", log)

    def testLoggerCorrectionsOnlyHealth(self):
        """Corrections without severe events keep 'No errors occurred'."""
        from whipper.program.cdparanoia import classify_cdparanoia_events
        severe, corrections, lossy = classify_cdparanoia_events(
            {"jitter": 3, "overlap": 1})
        self.assertEqual(severe, 0)
        self.assertEqual(corrections, 4)
        self.assertEqual(lossy, [])

        ripResult = RipResult()
        ripResult.offset = 0
        ripResult.overread = False
        ripResult.isCdr = False
        ripResult.table = MockImageTable()
        ripResult.artist = "A"
        ripResult.title = "T"
        ripResult.vendor = "V"
        ripResult.model = "M"
        ripResult.release = "1"
        ripResult.cdrdaoVersion = "1.2.4"
        ripResult.cdparanoiaVersion = "cdparanoia III 10.2"
        ripResult.cdparanoiaDefeatsCache = True

        trackResult = TrackResult()
        trackResult.number = 1
        trackResult.filename = "./01.flac"
        trackResult.peak = 1000
        trackResult.quality = 0.95
        trackResult.copyspeed = 2.0
        trackResult.testduration = 1
        trackResult.copyduration = 1
        trackResult.testcrc = 0x11111111
        trackResult.copycrc = 0x11111111
        trackResult.cdparanoiaEvents = {"jitter": 3, "overlap": 1}
        trackResult.suspiciousPositions = [(10, 12)]
        trackResult.AR = {
            "v1": {"DBConfidence": None, "DBCRC": None, "CRC": None},
            "v2": {"DBConfidence": None, "DBCRC": None, "CRC": None},
        }
        ripResult.tracks.append(trackResult)

        log = WhipperLogger().log(ripResult, epoch=0)
        self.assertIn("Health status: No errors occurred", log)
        self.assertIn("cdparanoia health: corrections only", log)
        self.assertIn("Status: Copy OK\n", log)
        self.assertIn("Suspicious positions:", log)

    def testClassifyCdparanoiaEvents(self):
        from whipper.program.cdparanoia import classify_cdparanoia_events
        severe, corrections, lossy = classify_cdparanoia_events({
            "read": 10,
            "jitter": 5,
            "skip": 2,
            "scratch": 1,
            "transport error": 1,
            "scsi_read error": 3,
            "drift": 2,
            "unknown_event": 4,
        })
        # skip + unsupported scratch + max(transport, scsi)
        self.assertEqual(severe, 2 + 1 + max(1, 3))
        # jitter + drift + unknown
        self.assertEqual(corrections, 5 + 2 + 4)
        # only definitely-lossy names (alphabetical)
        self.assertEqual(lossy, ["skip"])

    def testClassifyTransportErrorNotInLossyNames(self):
        """#294: transport error may be recovered ('e' in progress bar)."""
        from whipper.program.cdparanoia import classify_cdparanoia_events
        severe, corrections, lossy = classify_cdparanoia_events(
            {"transport error": 2})
        self.assertEqual(severe, 2)
        self.assertEqual(corrections, 0)
        self.assertEqual(lossy, [])

    def testLoggerTransportErrorOnlyHealth(self):
        """Severe recoverable events still set 'There were errors'."""
        ripResult = RipResult()
        ripResult.offset = 0
        ripResult.overread = False
        ripResult.isCdr = False
        ripResult.table = MockImageTable()
        ripResult.artist = "A"
        ripResult.title = "T"
        ripResult.vendor = "V"
        ripResult.model = "M"
        ripResult.release = "1"
        ripResult.cdrdaoVersion = "1.2.4"
        ripResult.cdparanoiaVersion = "cdparanoia III 10.2"
        ripResult.cdparanoiaDefeatsCache = True

        trackResult = TrackResult()
        trackResult.number = 1
        trackResult.filename = "./01.flac"
        trackResult.peak = 1000
        trackResult.quality = 1
        trackResult.copyspeed = 2.0
        trackResult.testduration = 1
        trackResult.copyduration = 1
        trackResult.testcrc = 0x22222222
        trackResult.copycrc = 0x22222222
        trackResult.cdparanoiaEvents = {"transport error": 2}
        trackResult.suspiciousPositions = [(5, 6)]
        trackResult.AR = {
            "v1": {"DBConfidence": None, "DBCRC": None, "CRC": None},
            "v2": {"DBConfidence": None, "DBCRC": None, "CRC": None},
        }
        ripResult.tracks.append(trackResult)

        log = WhipperLogger().log(ripResult, epoch=0)
        self.assertIn("Health status: There were errors", log)
        self.assertIn("cdparanoia health: severe recoverable errors", log)
        self.assertIn("Copy OK (cdparanoia reported severe recoverable",
                      log)

    def testLoggerCleanTrackStatusUnchanged(self):
        ripResult = RipResult()
        ripResult.offset = 0
        ripResult.overread = False
        ripResult.isCdr = False
        ripResult.table = MockImageTable()
        ripResult.artist = "Example Artist"
        ripResult.title = "Example Album"
        ripResult.vendor = "HL-DT-ST"
        ripResult.model = "DVDRAM"
        ripResult.release = "1.00"
        ripResult.cdrdaoVersion = "1.2.4"
        ripResult.cdparanoiaVersion = "cdparanoia III 10.2"
        ripResult.cdparanoiaDefeatsCache = True

        trackResult = TrackResult()
        trackResult.number = 1
        trackResult.filename = "./01 - Example.flac"
        trackResult.pregap = 0
        trackResult.peak = 29503
        trackResult.quality = 1
        trackResult.copyspeed = 7
        trackResult.testduration = 10
        trackResult.copyduration = 10
        trackResult.testcrc = 0x0025D726
        trackResult.copycrc = 0x0025D726
        trackResult.AR = {
            "v1": {"DBConfidence": None, "DBCRC": None, "CRC": None},
            "v2": {"DBConfidence": None, "DBCRC": None, "CRC": None},
        }
        ripResult.tracks.append(trackResult)

        log = WhipperLogger().log(ripResult, epoch=0)
        self.assertNotIn("cdparanoia events:", log)
        self.assertNotIn("Suspicious positions:", log)
        self.assertIn("Status: Copy OK\n", log)
        self.assertIn("Health status: No errors occurred", log)
        self.assertIn("cdparanoia health: clean", log)

    def testOutputFixturesThroughFinalHealth(self):
        from whipper.program.cdparanoia import ProgressParser
        fixtures = [
            ('##: 9 [overlap] @ 117600', 'corrections only', False, False),
            ('##: 2 [jitter] @ 235200', 'corrections only', False, True),
            ('scsi_read error: sector=200 length=1 retry=0\n'
             '##: 0 [read] @ 236376',
             'severe recoverable errors', True, False),
            ('scsi_read error: sector=200 length=1 retry=0\n'
             'scsi_read error: sector=200 length=1 retry=1\n'
             '##: 12 [transport error] @ 235200',
             'severe recoverable errors', True, True),
            ('##: 6 [skip] @ 235200',
             'definitely lossy (uncorrected/skipped): skip', True, True),
            ('##: 9 [overlap] @ 117600\n'
             '##: 2 [jitter] @ 235200\n'
             'scsi_read error: sector=200 length=1 retry=0\n'
             '##: 12 [transport error] @ 235200\n'
             '##: 6 [skip] @ 352800',
             'definitely lossy (uncorrected/skipped): skip', True, True),
        ]
        logger = WhipperLogger()
        for output, health, severe, positioned in fixtures:
            for matching in (True, False):
                with self.subTest(output=output, matching=matching):
                    parser = ProgressParser(150, 1000)
                    for line in output.splitlines():
                        parser.parse(line)
                    rip = RipResult()
                    rip.table = MockImageTable()
                    track = TrackResult()
                    track.number = 1
                    track.filename = './01.flac'
                    track.peak = 1000
                    track.testduration = track.copyduration = 1
                    track.testcrc = 123
                    track.copycrc = 123 if matching else 456
                    track.cdparanoiaEvents = parser.getEventCounts()
                    track.cdparanoiaSevereErrors = parser.severeErrors
                    track.suspiciousPositions = parser.getSuspiciousPositions()
                    track.AR = {
                        v: {'DBCRC': None, 'CRC': None, 'DBConfidence': None}
                        for v in ('v1', 'v2')}
                    rip.tracks.append(track)
                    parsed = YAML(typ='rt', pure=True).load(
                        logger.log(rip, epoch=0))
                    report = parsed['Conclusive status report']
                    self.assertTrue(report['cdparanoia health'].startswith(
                        health))
                    expected = ('There were errors' if severe or not matching
                                else 'No errors occurred')
                    self.assertEqual(report['Health status'], expected)
                    logged = parsed['Tracks'][1]
                    self.assertEqual(dict(logged['cdparanoia events']),
                                     parser.getEventCounts())
                    self.assertEqual('Suspicious positions' in logged,
                                     positioned)
                    if not matching:
                        self.assertEqual(logged['Status'],
                                         'Error, CRC mismatch')
                    elif 'skip' in parser.getEventCounts():
                        self.assertIn('WARNING: uncorrected/skipped sectors: '
                                      'skip', logged['Status'])
                    elif severe:
                        self.assertIn('recovery unverified', logged['Status'])
                        self.assertNotIn('uncorrected/skipped',
                                         logged['Status'])
                    else:
                        self.assertEqual(logged['Status'], 'Copy OK')

    def testLoggerUsesPerPassSevereCount(self):
        track = TrackResult()
        track.filename = './01.flac'
        track.peak = 1000
        track.testcrc = track.copycrc = 123
        track.cdparanoiaEvents = {
            'scsi_read error': 1, 'transport error': 1, 'skip': 1}
        track.cdparanoiaSevereErrors = 3
        logger = WhipperLogger()
        logger._reset_counters()
        logged, _, _ = logger.trackLog(track)
        self.assertEqual(logger._cdparanoiaSevereCount, 3)
        self.assertIn('WARNING: uncorrected/skipped sectors: skip',
                      logged['Status'])
