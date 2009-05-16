# -*- Mode: Python; test-case-name: morituri.test.test_image_table -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.image import table

def h(i):
    return "0x%08x" % i

class LadyhawkeTestCase(unittest.TestCase):
    # Ladyhawke - Ladyhawke - 0602517818866
    # contains 12 audio tracks and one data track
    # CDDB has been verified against freedb:
    #   http://www.freedb.org/freedb/misc/c60af50d
    #   http://www.freedb.org/freedb/jazz/c60af50d
    # AccurateRip URL has been verified against EAC's, using wireshark

    def setUp(self):
        self.table = table.Table()

        for i in range(12):
            self.table.tracks.append(table.Track(i + 1, audio=True))
        self.table.tracks.append(table.Track(13, audio=False))

        offsets = [0, 15537, 31691, 50866, 66466, 81202, 99409,
            115920, 133093, 149847, 161560, 177682, 207106]
        t = self.table.tracks
        for i, offset in enumerate(offsets):
            t[i].index(1, absolute=offset)

        self.failIf(self.table.hasTOC())

        self.table.leadout = 210385

        self.failUnless(self.table.hasTOC())

    def testCDDB(self):
        self.assertEquals(self.table.getCDDBDiscId(), "c60af50d")

    def testMusicBrainz(self):
        # track
        self.assertEquals(self.table.getMusicBrainzDiscId(),
            "qrJJkrLvXz5Nkvym3oZM4KI9U4A-")

    def testAccurateRip(self):
        self.assertEquals(self.table.getAccurateRipIds(), (
            "0013bd5a", "00b8d489"))

class MusicBrainzTestCase(unittest.TestCase):
    # example taken from http://musicbrainz.org/doc/DiscIDCalculation
    # disc is Ettella Diamant

    def setUp(self):
        self.table = table.Table()

        for i in range(6):
            self.table.tracks.append(table.Track(i + 1, audio=True))

        offsets = [0, 15213, 32164, 46442, 63264, 80339]
        t = self.table.tracks
        for i, offset in enumerate(offsets):
            t[i].index(1, absolute=offset)

        self.failIf(self.table.hasTOC())

        self.table.leadout = 95312

        self.failUnless(self.table.hasTOC())

    def testMusicBrainz(self):
        self.assertEquals(self.table.getMusicBrainzDiscId(),
            '49HHV7Eb8UKF3aQiNmu1GR8vKTY-')
