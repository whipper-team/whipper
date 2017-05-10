# -*- Mode: Python; test-case-name: whipper.test.test_common_mbngs -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import json

import unittest

from whipper.common import mbngs


class MetadataTestCase(unittest.TestCase):

    # Generated with rip -R cd info
    def testJeffEverybodySingle(self):
        path = os.path.join(os.path.dirname(__file__),
                            'whipper.release.'
                            '3451f29c-9bb8-4cc5-bfcc-bd50104b94f8.json')
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "wbjbST2jUHRZaB1inCyxxsL7Eqc-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.failIf(metadata.release)

    def test2MeterSessies10(self):
        # various artists, multiple artists per track
        path = os.path.join(os.path.dirname(__file__),
                            'whipper.release.'
                            'a76714e0-32b1-4ed4-b28e-f86d99642193.json')
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
        self.assertEquals(track16.mbidArtist,
                          u'57c6f649-6cde-48a7-8114-2a200247601a'
                          ';0bfba3d3-6a04-4779-bb0a-df07df5b0558'
                          )
        self.assertEquals(track16.sortName,
                          u'Jones, Tom & Stereophonics')

    def testBalladOfTheBrokenSeas(self):
        # various artists disc
        path = os.path.join(os.path.dirname(__file__),
                            'whipper.release.'
                            'e32ae79a-336e-4d33-945c-8c5e8206dbd3.json')
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
        self.assertEquals(track12.sortName,
                          u'Campbell, Isobel'
                          ' & Lanegan, Mark'
                          )
        self.assertEquals(track12.mbidArtist,
                          u'd51f3a15-12a2-41a0-acfa-33b5eae71164;'
                          'a9126556-f555-4920-9617-6e013f8228a7')

    def testMalaInCuba(self):
        # single artist disc, but with multiple artists tracks
        # see https://github.com/thomasvs/morituri/issues/19
        path = os.path.join(os.path.dirname(__file__),
                            'whipper.release.'
                            '61c6fd9b-18f8-4a45-963a-ba3c5d990cae.json')
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "u0aKVpO.59JBy6eQRX2vYcoqQZ0-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertEquals(metadata.artist, u'Mala')
        self.assertEquals(metadata.sortName, u'Mala')
        self.assertEquals(metadata.release, u'2012-09-17')
        self.assertEquals(metadata.mbidArtist,
                          u'09f221eb-c97e-4da5-ac22-d7ab7c555bbb')

        self.assertEquals(len(metadata.tracks), 14)

        track6 = metadata.tracks[5]

        self.assertEquals(track6.artist, u'Mala feat. Dreiser & Sexto Sentido')
        self.assertEquals(track6.sortName,
                          u'Mala feat. Dreiser & Sexto Sentido')
        self.assertEquals(track6.mbidArtist,
                          u'09f221eb-c97e-4da5-ac22-d7ab7c555bbb'
                          ';ec07a209-55ff-4084-bc41-9d4d1764e075'
                          ';f626b92e-07b1-4a19-ad13-c09d690db66c'
                          )
