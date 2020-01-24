from __future__ import print_function
import hashlib
import os
import re
import unittest
import ruamel.yaml

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

    def getCDDBDiscId(self):
        return "c30bde0d"

    def getMusicBrainzDiscId(self):
        return "eyjySLXGdKigAjY3_C0nbBmNUHc-"

    def getMusicBrainzSubmitURL(self):
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
                            r'[\d]+\.[\d]+\.[\d]+(\+d\d{8}|\.dev[\w\.\+]+)? '
                            r'\(internal logger\)'
                        ))
        for versionScheme in versionSchemes:
            self.assertRegex(versionScheme, created_by_re)
        self.assertRegex(
            actualLines[1],
            re.compile((
                r'Log creation date: '
                r'20[\d]{2}\-[\d]{2}\-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}Z'
            ))
        )

        yaml = ruamel.yaml.YAML()
        parsedLog = yaml.load(actual)
        self.assertEqual(
            actual,
            ruamel.yaml.dump(
                parsedLog,
                default_flow_style=False,
                width=4000,
                Dumper=ruamel.yaml.RoundTripDumper
            )
        )
        log_body = "\n".join(actualLines[:-1]).encode()
        self.assertEqual(
            parsedLog['SHA-256 hash'],
            hashlib.sha256(log_body).hexdigest().upper()
        )
