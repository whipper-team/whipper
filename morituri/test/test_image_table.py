# -*- Mode: Python; test-case-name: morituri.test.test_image_table -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.image import table

from morituri.test import common as tcommon


def h(i):
    return "0x%08x" % i

class TrackTestCase(tcommon.TestCase):
    def testRepr(self):
        track = table.Track(1)
        self.assertEquals(repr(track), "<Track 01>")

        track.index(1, 100)
        self.failUnless(repr(track.indexes[1]).startswith('<Index 01 '))

class LadyhawkeTestCase(tcommon.TestCase):
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
        self.assertEquals(self.table.tracks[0].getPregap(), 0)

    def testCDDB(self):
        self.assertEquals(self.table.getCDDBDiscId(), "c60af50d")

    def testMusicBrainz(self):
        # output from mb-submit-disc:
        # http://mm.musicbrainz.org/bare/cdlookup.html?toc=1+12+195856+150+15687+31841+51016+66616+81352+99559+116070+133243+149997+161710+177832&tracks=12&id=KnpGsLhvH.lPrNc1PBL21lb9Bg4-
        # however, not (yet) in musicbrainz database

        self.assertEquals(self.table.getMusicBrainzDiscId(),
            "KnpGsLhvH.lPrNc1PBL21lb9Bg4-")

    def testAccurateRip(self):
        self.assertEquals(self.table.getAccurateRipIds(), (
            "0013bd5a", "00b8d489"))
        self.assertEquals(self.table.getAccurateRipURL(),
        "http://www.accuraterip.com/accuraterip/a/5/d/dBAR-012-0013bd5a-00b8d489-c60af50d.bin")

    def testDuration(self):
        self.assertEquals(self.table.duration(), 2761413)


class MusicBrainzTestCase(tcommon.TestCase):
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

class PregapTestCase(tcommon.TestCase):

    def setUp(self):
        self.table = table.Table()

        for i in range(2):
            self.table.tracks.append(table.Track(i + 1, audio=True))

        offsets = [0, 15537]
        t = self.table.tracks
        for i, offset in enumerate(offsets):
            t[i].index(1, absolute=offset)
        t[1].index(0, offsets[1] - 200)

    def testPreGap(self):
        self.assertEquals(self.table.tracks[0].getPregap(), 0)
        self.assertEquals(self.table.tracks[1].getPregap(), 200)


