# -*- Mode: Python; test-case-name: whipper.test.test_common_mbngs -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import json

import unittest

from whipper.common import mbngs


class MetadataTestCase(unittest.TestCase):

    # Generated with rip -R cd info
    def testMissingReleaseDate(self):
        # Using: The KLF - Space & Chill Out
        # https://musicbrainz.org/release/c56ff16e-1d81-47de-926f-ba22891bd2bd
        filename = 'whipper.release.c56ff16e-1d81-47de-926f-ba22891bd2bd.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "b.yqPuCBdsV5hrzDvYrw52iK_jE-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertFalse(metadata.release)

    def test2MeterSessies10(self):
        # various artists, multiple artists per track
        filename = 'whipper.release.a76714e0-32b1-4ed4-b28e-f86d99642193.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "f7XO36a7n1LCCskkCiulReWbwZA-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertEqual(metadata.artist, u'Various Artists')
        self.assertEqual(metadata.release, u'2001-10-15')
        self.assertEqual(metadata.mbidArtist,
                         u'89ad4ac3-39f7-470e-963a-56509c546377')

        self.assertEqual(len(metadata.tracks), 18)

        track16 = metadata.tracks[15]

        self.assertEqual(track16.artist, 'Tom Jones & Stereophonics')
        self.assertEqual(track16.mbidArtist,
                         u'57c6f649-6cde-48a7-8114-2a200247601a'
                         ';0bfba3d3-6a04-4779-bb0a-df07df5b0558')
        self.assertEqual(track16.sortName,
                         u'Jones, Tom & Stereophonics')

    def testBalladOfTheBrokenSeas(self):
        # various artists disc
        filename = 'whipper.release.e32ae79a-336e-4d33-945c-8c5e8206dbd3.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "xAq8L4ELMW14.6wI6tt7QAcxiDI-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertEqual(metadata.artist, u'Isobel Campbell & Mark Lanegan')
        self.assertEqual(metadata.sortName,
                         u'Campbell, Isobel & Lanegan, Mark')
        self.assertEqual(metadata.release, u'2006-01-30')
        self.assertEqual(metadata.mbidArtist,
                         u'd51f3a15-12a2-41a0-acfa-33b5eae71164;'
                         'a9126556-f555-4920-9617-6e013f8228a7')

        self.assertEqual(len(metadata.tracks), 12)

        track12 = metadata.tracks[11]

        self.assertEqual(track12.artist, u'Isobel Campbell & Mark Lanegan')
        self.assertEqual(track12.sortName,
                         u'Campbell, Isobel'
                         ' & Lanegan, Mark')
        self.assertEqual(track12.mbidArtist,
                         u'd51f3a15-12a2-41a0-acfa-33b5eae71164;'
                         'a9126556-f555-4920-9617-6e013f8228a7')

    def testMalaInCuba(self):
        # single artist disc, but with multiple artists tracks
        # see https://github.com/thomasvs/morituri/issues/19
        filename = 'whipper.release.61c6fd9b-18f8-4a45-963a-ba3c5d990cae.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "u0aKVpO.59JBy6eQRX2vYcoqQZ0-"

        metadata = mbngs._getMetadata({}, response['release'], discid)

        self.assertEqual(metadata.artist, u'Mala')
        self.assertEqual(metadata.sortName, u'Mala')
        self.assertEqual(metadata.release, u'2012-09-17')
        self.assertEqual(metadata.mbidArtist,
                         u'09f221eb-c97e-4da5-ac22-d7ab7c555bbb')

        self.assertEqual(len(metadata.tracks), 14)

        track6 = metadata.tracks[5]

        self.assertEqual(track6.artist, u'Mala feat. Dreiser & Sexto Sentido')
        self.assertEqual(track6.sortName,
                         u'Mala feat. Dreiser & Sexto Sentido')
        self.assertEqual(track6.mbidArtist,
                         u'09f221eb-c97e-4da5-ac22-d7ab7c555bbb'
                         ';ec07a209-55ff-4084-bc41-9d4d1764e075'
                         ';f626b92e-07b1-4a19-ad13-c09d690db66c')

    def testUnknownArtist(self):
        """
        check the received metadata for artists tagged with [unknown]
        and artists tagged with an alias in MusicBrainz

        see https://github.com/whipper-team/whipper/issues/155
        """
        # Using: CunninLynguists - Sloppy Seconds, Volume 1
        # https://musicbrainz.org/release/8478d4da-0cda-4e46-ae8c-1eeacfa5cf37
        filename = 'whipper.release.8478d4da-0cda-4e46-ae8c-1eeacfa5cf37.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "RhrwgVb0hZNkabQCw1dZIhdbMFg-"

        metadata = mbngs._getMetadata({}, response['release'], discid)
        self.assertEqual(metadata.artist, u'CunninLynguists')
        self.assertEqual(metadata.release, u'2003')
        self.assertEqual(metadata.mbidArtist,
                         u'69c4cc43-8163-41c5-ac81-30946d27bb69')

        self.assertEqual(len(metadata.tracks), 30)

        track8 = metadata.tracks[7]

        self.assertEqual(track8.artist, u'???')
        self.assertEqual(track8.sortName, u'[unknown]')
        self.assertEqual(track8.mbidArtist,
                         u'125ec42a-7229-4250-afc5-e057484327fe')

        track9 = metadata.tracks[8]

        self.assertEqual(track9.artist, u'CunninLynguists feat. Tonedeff')
        self.assertEqual(track9.sortName,
                         u'CunninLynguists feat. Tonedeff')
        self.assertEqual(track9.mbidArtist,
                         u'69c4cc43-8163-41c5-ac81-30946d27bb69'
                         ';b3869d83-9fb5-4eac-b5ca-2d155fcbee12')

    def testNenaAndKimWildSingle(self):
        """
        check the received metadata for artists that differ between
        named on release and named in recording
        """
        filename = 'whipper.release.f484a9fc-db21-4106-9408-bcd105c90047.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read())
        handle.close()
        discid = "X2c2IQ5vUy5x6Jh7Xi_DGHtA1X8-"

        metadata = mbngs._getMetadata({}, response['release'], discid)
        self.assertEqual(metadata.artist, u'Nena & Kim Wilde')
        self.assertEqual(metadata.release, u'2003-05-19')
        self.assertEqual(metadata.mbidArtist,
                         u'38bfaa7f-ee98-48cb-acd0-946d7aeecd76'
                         ';4b462375-c508-432a-8c88-ceeec38b16ae')

        self.assertEqual(len(metadata.tracks), 4)

        track1 = metadata.tracks[0]

        self.assertEqual(track1.artist, u'Nena & Kim Wilde')
        self.assertEqual(track1.sortName, u'Nena & Wilde, Kim')
        self.assertEqual(track1.mbidArtist,
                         u'38bfaa7f-ee98-48cb-acd0-946d7aeecd76'
                         ';4b462375-c508-432a-8c88-ceeec38b16ae')
        self.assertEqual(track1.mbid,
                         u'1cc96e78-28ed-3820-b0b6-614c35b121ac')
        self.assertEqual(track1.mbidRecording,
                         u'fde5622c-ce23-4ebb-975d-51d4a926f901')

        track2 = metadata.tracks[1]

        self.assertEqual(track2.artist, u'Nena & Kim Wilde')
        self.assertEqual(track2.sortName, u'Nena & Wilde, Kim')
        self.assertEqual(track2.mbidArtist,
                         u'38bfaa7f-ee98-48cb-acd0-946d7aeecd76'
                         ';4b462375-c508-432a-8c88-ceeec38b16ae')
        self.assertEqual(track2.mbid,
                         u'f16db4bf-9a34-3d5a-a975-c9375ab7a2ca')
        self.assertEqual(track2.mbidRecording,
                         u'5f19758e-7421-4c71-a599-9a9575d8e1b0')
