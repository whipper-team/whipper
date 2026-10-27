from __future__ import print_function
import hashlib
import os
import re
import unittest
from unittest.mock import patch

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


class LogPathTestCase(unittest.TestCase):
    def makeResult(self, filenames):
        rip = RipResult()
        rip.table = MockImageTable()
        for number, filename in enumerate(filenames, 1):
            track = TrackResult()
            track.number = number
            track.filename = filename
            rip.tracks.append(track)
        return rip

    def assertLog(self, rip, expected, directory=None):
        original = [t.filename for t in rip.tracks]
        text = WhipperLogger().log(rip, 0, output_directory=directory)
        yaml = YAML(typ='rt', pure=True)
        parsed = yaml.load(text)
        self.assertEqual([t['Filename'] for t in parsed['Tracks'].values()],
                         expected)
        self.assertEqual([t.filename for t in rip.tracks], original)
        self.assertEqual(yaml.dump(parsed), text)
        body, digest = text.rsplit('\nSHA-256 hash: ', 1)
        calculated = hashlib.sha256(body.encode('utf-8')).hexdigest().upper()
        self.assertEqual(calculated, digest.strip())
        return parsed

    def testAbsolutePathsAndHierarchy(self):
        for directory in ('/home/private-user/Music/Album',
                          '/mnt/private-volume/Album'):
            with self.subTest(directory=directory):
                names = ['Disc 1/01. Étoile.flac', 'Disc 2/01. Étoile.flac']
                rip = self.makeResult([os.path.join(directory, n)
                                       for n in names])
                self.assertLog(rip, names, directory)

    def testOutsidePaths(self):
        directory = '/home/private-user/Music/Album'
        paths = ['/home/other-user/private/01.flac',
                 directory + '-private/02.flac',
                 directory + '/../private/03.flac']
        self.assertLog(self.makeResult(paths),
                       ['01.flac', '02.flac', '03.flac'], directory)

    def testRelativePathsUseWorkingDirectory(self):
        with patch('os.getcwd', return_value='/synthetic/work'):
            rip = self.makeResult(['Album/Disc 1/01.flac',
                                   './Album/Disc 2/01.flac',
                                   '../private-user/02.flac'])
            expected = ['Disc 1/01.flac', 'Disc 2/01.flac', '02.flac']
            self.assertLog(rip, expected, 'Album')

    def testNoDirectoryContext(self):
        rip = self.makeResult(['./Album/Disc 1/01.flac',
                               '/home/private-user/Music/02.flac',
                               '../../private-user/03.flac',
                               'Disc 1/../Disc 2/04.flac'])
        self.assertLog(rip, ['./Album/Disc 1/01.flac', '02.flac', '03.flac',
                             'Disc 2/04.flac'])

    def testHTOAAndPartialLog(self):
        directory = '/mnt/private-volume/Album'
        rip = self.makeResult([directory + '/00. Hidden.flac',
                               directory + '/Disc 1/01.flac', None])
        rip.tracks[0].number = 0
        rip.tracks[1].number = 1
        rip.tracks[2].number = 2
        rip.tracks[-1].skipped = True
        parsed = self.assertLog(rip, ['00. Hidden.flac', 'Disc 1/01.flac'],
                                directory)
        self.assertEqual(list(parsed['Tracks']), [0, 1])

    def testMissingFilenameInTrackDiagnostics(self):
        for filename in (None, ''):
            with self.subTest(filename=filename):
                track = TrackResult()
                track.filename = filename
                logged, _, _ = WhipperLogger().trackLog(track, '/rip')
                self.assertEqual(logged['Filename'], filename)
