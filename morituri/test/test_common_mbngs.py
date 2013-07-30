# -*- Mode: Python; test-case-name: morituri.test.test_common_mbngs -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import json

import unittest

from morituri.common import mbngs


class MetadataTestCase(unittest.TestCase):

    # Generated with rip -R cd info
    def testJeffEverybodySingle(self):
        path = os.path.join(os.path.dirname(__file__),
            'morituri.release.3451f29c-9bb8-4cc5-bfcc-bd50104b94f8.json')
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "wbjbST2jUHRZaB1inCyxxsL7Eqc-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.failIf(metadata.release)

    def test2MeterSessies10(self):
        # various artists, multiple artists per track
        path = os.path.join(os.path.dirname(__file__),
            'morituri.release.a76714e0-32b1-4ed4-b28e-f86d99642193.json')
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "f7XO36a7n1LCCskkCiulReWbwZA-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertEquals(metadata.artist, u'Various Artists')
        self.assertEquals(metadata.release, u'2001-10-15')
        self.assertEquals(metadata.mbidArtist,
            u'89ad4ac3-39f7-470e-963a-56509c546377')

        self.assertEquals(len(metadata.tracks), 18)

        track16 = metadata.tracks[15]

        self.assertEquals(track16.artist, 'Tom Jones & Stereophonics')
        # FIXME: this is the disc artist id, and it should be the combo
        #        of track artist id's
        self.assertEquals(track16.mbidArtist,
            u'89ad4ac3-39f7-470e-963a-56509c546377')

    def testBalladOfTheBrokenSeas(self):
        # various artists disc
        path = os.path.join(os.path.dirname(__file__),
            'morituri.release.e32ae79a-336e-4d33-945c-8c5e8206dbd3.json')
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "xAq8L4ELMW14.6wI6tt7QAcxiDI-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertEquals(metadata.artist, u'Isobel Campbell & Mark Lanegan')
        self.assertEquals(metadata.sortName,
            u'Campbell, Isobel & Lanegan, Mark')
        self.assertEquals(metadata.release, u'2006-01-30')
        self.assertEquals(metadata.mbidArtist,
            u'd51f3a15-12a2-41a0-acfa-33b5eae71164;'
            'a9126556-f555-4920-9617-6e013f8228a7')

        self.assertEquals(len(metadata.tracks), 12)

        track12 = metadata.tracks[11]

        self.assertEquals(track12.artist, u'Isobel Campbell & Mark Lanegan')
        # FIXME: this is only Isobel
        self.assertEquals(track12.mbidArtist,
            u'd51f3a15-12a2-41a0-acfa-33b5eae71164')
