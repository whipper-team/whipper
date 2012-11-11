# -*- Mode: Python; test-case-name: morituri.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import pickle

import unittest

from morituri.result import result
from morituri.common import program, accurip, musicbrainzngs
from morituri.rip import cd


class TrackImageVerifyTestCase(unittest.TestCase):
    # example taken from a rip of Luke Haines Is Dead, disc 1
    # AccurateRip database has 0 confidence for 1st track
    # Rip had a wrong result for track 9

    def testVerify(self):
        path = os.path.join(os.path.dirname(__file__),
            'dBAR-020-002e5023-029d8e49-040eaa14.bin')
        data = open(path, "rb").read()
        responses = accurip.getAccurateRipResponses(data)

        # these crc's were calculated from an actual rip
        checksums = [1644890007, 2945205445, 3983436658, 1528082495,
        1203704270, 1163423644, 3649097244, 100524219, 1583356174, 373652058,
        1842579359, 2850056507, 1329730252, 2526965856, 2525886806, 209743350,
        3184062337, 2099956663, 2943874164, 2321637196]

        prog = program.Program()
        prog.result = result.RipResult()
        # fill it with empty trackresults
        for i, c in enumerate(checksums):
            r = result.TrackResult()
            r.number = i + 1
            prog.result.tracks.append(r)

        prog._verifyImageWithChecksums(responses, checksums)

        # now check if the results were filled in properly
        tr = prog.result.getTrackResult(1)
        self.assertEquals(tr.accurip, False)
        self.assertEquals(tr.ARDBMaxConfidence, 0)
        self.assertEquals(tr.ARDBCRC, 0)
        self.assertEquals(tr.ARDBCRC, 0)

        tr = prog.result.getTrackResult(2)
        self.assertEquals(tr.accurip, True)
        self.assertEquals(tr.ARDBMaxConfidence, 2)
        self.assertEquals(tr.ARDBCRC, checksums[2 - 1])

        tr = prog.result.getTrackResult(10)
        self.assertEquals(tr.accurip, False)
        self.assertEquals(tr.ARDBMaxConfidence, 2)
        # we know track 10 was ripped wrong
        self.assertNotEquals(tr.ARDBCRC, checksums[10 - 1])

        res = prog.getAccurateRipResults()
        self.assertEquals(res[1 - 1],
            "Track  1: rip NOT accurate (not found)             "
            "[620b0797], DB [notfound]")
        self.assertEquals(res[2 - 1],
            "Track  2: rip accurate     (max confidence      2) "
            "[af8c44c5], DB [af8c44c5]")
        self.assertEquals(res[10 - 1],
            "Track 10: rip NOT accurate (max confidence      2) "
            "[16457a5a], DB [eb6e55b4]")


class HTOATestCase(unittest.TestCase):

    def setUp(self):
        path = os.path.join(os.path.dirname(__file__),
            'silentalarm.result.pickle')
        self._tracks = pickle.load(open(path, 'rb'))

    def testGetAccurateRipResults(self):
        prog = program.Program()
        prog.result = result.RipResult()
        prog.result.tracks = self._tracks

        prog.getAccurateRipResults()


class PathTestCase(unittest.TestCase):

    def testStandardTemplateEmpty(self):
        prog = program.Program()

        path = prog.getPath(u'/tmp', cd.DEFAULT_DISC_TEMPLATE, 'mbdiscid', 0)
        self.assertEquals(path,
            u'/tmp/Unknown Artist - mbdiscid/Unknown Artist - mbdiscid')

    def testStandardTemplateFilled(self):
        prog = program.Program()
        md = musicbrainzngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'
        prog.metadata = md

        path = prog.getPath(u'/tmp', cd.DEFAULT_DISC_TEMPLATE, 'mbdiscid', 0)
        self.assertEquals(path,
            u'/tmp/Jeff Buckley - Grace/Jeff Buckley - Grace')

    def testIssue66TemplateFilled(self):
        prog = program.Program()
        md = musicbrainzngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.title = 'Grace'
        prog.metadata = md

        path = prog.getPath(u'/tmp', u'%A/%d', 'mbdiscid', 0)
        self.assertEquals(path,
            u'/tmp/Jeff Buckley/Grace')
