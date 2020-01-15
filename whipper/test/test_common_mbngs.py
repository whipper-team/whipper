# -*- Mode: Python; test-case-name: whipper.test.test_common_mbngs -*-
# vi:si:et:sw=4:sts=4:ts=4:set fileencoding=utf-8

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
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "b.yqPuCBdsV5hrzDvYrw52iK_jE-"

        metadata = mbngs._getMetadata(response['release'], discid)

        self.assertFalse(metadata.release)

    def testTrackTitle(self):
        """
        Check that the track title metadata is taken from MusicBrainz's track
        title (which may differ from the recording title, as in this case)
        see https://github.com/whipper-team/whipper/issues/192
        """
        # Using: The KLF - Space & Chill Out
        # https://musicbrainz.org/release/c56ff16e-1d81-47de-926f-ba22891bd2bd
        filename = 'whipper.release.c56ff16e-1d81-47de-926f-ba22891bd2bd.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "rb") as handle:
            response = json.loads(handle.read().decode('utf-8'))
        discid = "b.yqPuCBdsV5hrzDvYrw52iK_jE-"

        metadata = mbngs._getMetadata(response['release'], discid)
        track1 = metadata.tracks[0]
        self.assertEqual(track1.title, 'Brownsville Turnaround')

    def testComposersAndPerformers(self):
        """
        Test whether composers and performers are extracted properly.

        See: https://github.com/whipper-team/whipper/issues/191
        """
        # Using: Mama Said - Lenny Kravitz
        # https://musicbrainz.org/release/410f99f8-a876-3416-bd8e-42233a00a477
        filename = 'whipper.release.410f99f8-a876-3416-bd8e-42233a00a477.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, "rb") as handle:
            response = json.loads(handle.read().decode('utf-8'))

        metadata = mbngs._getMetadata(response['release'],
                                      discid='bIOeHwHT0aZJiENIYjAmoNxCPuA-')
        track1 = metadata.tracks[0]
        self.assertEqual(track1.composers,
                         ['Hal Fredericks', 'Michael Kamen'])
        self.assertEqual(track1.performers, ['Lenny Kravitz', 'Slash'])

    def test2MeterSessies10(self):
        # various artists, multiple artists per track
        filename = 'whipper.release.a76714e0-32b1-4ed4-b28e-f86d99642193.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "f7XO36a7n1LCCskkCiulReWbwZA-"

        metadata = mbngs._getMetadata(response['release'], discid)

        self.assertEqual(metadata.artist, 'Various Artists')
        self.assertEqual(metadata.release, '2001-10-15')
        self.assertEqual(metadata.mbidArtist,
                         ['89ad4ac3-39f7-470e-963a-56509c546377'])

        self.assertEqual(len(metadata.tracks), 18)

        track16 = metadata.tracks[15]

        self.assertEqual(track16.artist, 'Tom Jones & Stereophonics')
        self.assertEqual(track16.mbidArtist, [
            '57c6f649-6cde-48a7-8114-2a200247601a',
            '0bfba3d3-6a04-4779-bb0a-df07df5b0558',
        ])
        self.assertEqual(track16.sortName,
                         'Jones, Tom & Stereophonics')

    def testBalladOfTheBrokenSeas(self):
        # various artists disc
        filename = 'whipper.release.e32ae79a-336e-4d33-945c-8c5e8206dbd3.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "xAq8L4ELMW14.6wI6tt7QAcxiDI-"

        metadata = mbngs._getMetadata(response['release'], discid)

        self.assertEqual(metadata.artist, 'Isobel Campbell & Mark Lanegan')
        self.assertEqual(metadata.sortName,
                         'Campbell, Isobel & Lanegan, Mark')
        self.assertEqual(metadata.release, '2006-01-30')
        self.assertEqual(metadata.mbidArtist, [
            'd51f3a15-12a2-41a0-acfa-33b5eae71164',
            'a9126556-f555-4920-9617-6e013f8228a7',
        ])

        self.assertEqual(len(metadata.tracks), 12)

        track12 = metadata.tracks[11]

        self.assertEqual(track12.artist, 'Isobel Campbell & Mark Lanegan')
        self.assertEqual(track12.sortName,
                         'Campbell, Isobel'
                         ' & Lanegan, Mark')
        self.assertEqual(track12.mbidArtist, [
            'd51f3a15-12a2-41a0-acfa-33b5eae71164',
            'a9126556-f555-4920-9617-6e013f8228a7',
        ])

    def testMalaInCuba(self):
        # single artist disc, but with multiple artists tracks
        # see https://github.com/thomasvs/morituri/issues/19
        filename = 'whipper.release.61c6fd9b-18f8-4a45-963a-ba3c5d990cae.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "u0aKVpO.59JBy6eQRX2vYcoqQZ0-"

        metadata = mbngs._getMetadata(response['release'], discid)

        self.assertEqual(metadata.artist, 'Mala')
        self.assertEqual(metadata.sortName, 'Mala')
        self.assertEqual(metadata.release, '2012-09-17')
        self.assertEqual(metadata.mbidArtist,
                         ['09f221eb-c97e-4da5-ac22-d7ab7c555bbb'])

        self.assertEqual(len(metadata.tracks), 14)

        track6 = metadata.tracks[5]

        self.assertEqual(track6.artist, 'Mala feat. Dreiser & Sexto Sentido')
        self.assertEqual(track6.sortName,
                         'Mala feat. Dreiser & Sexto Sentido')
        self.assertEqual(track6.mbidArtist, [
            '09f221eb-c97e-4da5-ac22-d7ab7c555bbb',
            'ec07a209-55ff-4084-bc41-9d4d1764e075',
            'f626b92e-07b1-4a19-ad13-c09d690db66c',
        ])

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
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "RhrwgVb0hZNkabQCw1dZIhdbMFg-"

        metadata = mbngs._getMetadata(response['release'], discid)
        self.assertEqual(metadata.artist, 'CunninLynguists')
        self.assertEqual(metadata.release, '2003')
        self.assertEqual(metadata.mbidArtist,
                         ['69c4cc43-8163-41c5-ac81-30946d27bb69'])

        self.assertEqual(len(metadata.tracks), 30)

        track8 = metadata.tracks[7]

        self.assertEqual(track8.artist, '???')
        self.assertEqual(track8.sortName, '[unknown]')
        self.assertEqual(track8.mbidArtist,
                         ['125ec42a-7229-4250-afc5-e057484327fe'])

        track9 = metadata.tracks[8]

        self.assertEqual(track9.artist, 'CunninLynguists feat. Tonedeff')
        self.assertEqual(track9.sortName,
                         'CunninLynguists feat. Tonedeff')
        self.assertEqual(track9.mbidArtist, [
            '69c4cc43-8163-41c5-ac81-30946d27bb69',
            'b3869d83-9fb5-4eac-b5ca-2d155fcbee12'
        ])

    def testNenaAndKimWildSingle(self):
        """
        check the received metadata for artists that differ between
        named on release and named in recording
        """
        filename = 'whipper.release.f484a9fc-db21-4106-9408-bcd105c90047.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "X2c2IQ5vUy5x6Jh7Xi_DGHtA1X8-"

        metadata = mbngs._getMetadata(response['release'], discid)
        self.assertEqual(metadata.artist, 'Nena & Kim Wilde')
        self.assertEqual(metadata.release, '2003-05-19')
        self.assertEqual(metadata.mbidArtist, [
            '38bfaa7f-ee98-48cb-acd0-946d7aeecd76',
            '4b462375-c508-432a-8c88-ceeec38b16ae',
        ])

        self.assertEqual(len(metadata.tracks), 4)

        track1 = metadata.tracks[0]

        self.assertEqual(track1.artist, 'Nena & Kim Wilde')
        self.assertEqual(track1.sortName, 'Nena & Wilde, Kim')
        self.assertEqual(track1.mbidArtist, [
            '38bfaa7f-ee98-48cb-acd0-946d7aeecd76',
            '4b462375-c508-432a-8c88-ceeec38b16ae',
        ])
        self.assertEqual(track1.mbid,
                         '1cc96e78-28ed-3820-b0b6-614c35b121ac')
        self.assertEqual(track1.mbidRecording,
                         'fde5622c-ce23-4ebb-975d-51d4a926f901')

        track2 = metadata.tracks[1]

        self.assertEqual(track2.artist, 'Nena & Kim Wilde')
        self.assertEqual(track2.sortName, 'Nena & Wilde, Kim')
        self.assertEqual(track2.mbidArtist, [
            '38bfaa7f-ee98-48cb-acd0-946d7aeecd76',
            '4b462375-c508-432a-8c88-ceeec38b16ae',
        ])
        self.assertEqual(track2.mbid,
                         'f16db4bf-9a34-3d5a-a975-c9375ab7a2ca')
        self.assertEqual(track2.mbidRecording,
                         '5f19758e-7421-4c71-a599-9a9575d8e1b0')

    def testMissingReleaseGroupType(self):
        """Check that whipper doesn't break if there's no type."""
        # Using: Gustafsson, Österberg & Cowle - What's Up? 8 (disc 4)
        # https://musicbrainz.org/release/d8e6153a-2c47-4804-9d73-0aac1081c3b1
        filename = 'whipper.release.d8e6153a-2c47-4804-9d73-0aac1081c3b1.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "xu338_M8WukSRi0J.KTlDoflB8Y-"  # disc 4

        metadata = mbngs._getMetadata(response['release'], discid)
        self.assertEqual(metadata.releaseType, None)

    def testAllAvailableMetadata(self):
        """Check that all possible metadata gets assigned."""
        # Using: David Rovics - The Other Side
        # https://musicbrainz.org/release/6109ceed-7e21-490b-b5ad-3a66b4e4cfbb
        filename = 'whipper.release.6109ceed-7e21-490b-b5ad-3a66b4e4cfbb.json'
        path = os.path.join(os.path.dirname(__file__), filename)
        handle = open(path, "rb")
        response = json.loads(handle.read().decode('utf-8'))
        handle.close()
        discid = "cHW1Uutl_kyWNaLJsLmTGTe4rnE-"

        metadata = mbngs._getMetadata(response['release'], discid)
        self.assertEqual(metadata.artist, 'David Rovics')
        self.assertEqual(metadata.sortName, 'Rovics, David')
        self.assertFalse(metadata.various)
        self.assertIsInstance(metadata.tracks, list)
        self.assertEqual(metadata.release, '2015')
        self.assertEqual(metadata.releaseTitle, 'The Other Side')
        self.assertEqual(metadata.releaseType, 'Album')
        self.assertEqual(metadata.mbid,
                         '6109ceed-7e21-490b-b5ad-3a66b4e4cfbb')
        self.assertEqual(metadata.mbidReleaseGroup,
                         '99850b41-a06e-4fb8-992c-75c191a77803')
        self.assertEqual(metadata.mbidArtist,
                         ['4d56eb9f-13b3-4f05-9db7-50195378d49f'])
        self.assertEqual(metadata.url,
                         'https://musicbrainz.org/release'
                         '/6109ceed-7e21-490b-b5ad-3a66b4e4cfbb')
        self.assertEqual(metadata.catalogNumber, '[none]')
        self.assertEqual(metadata.barcode, '700261430249')

        self.assertEqual(len(metadata.tracks), 16)

        track1 = metadata.tracks[0]
        self.assertEqual(track1.artist, 'David Rovics')
        self.assertEqual(track1.title, 'Waiting for the Hurricane')
        self.assertEqual(track1.duration, 176320)
        self.assertEqual(track1.mbid,
                         '4116eea3-b9c2-452a-8d63-92f1e585b225')
        self.assertEqual(track1.sortName, 'Rovics, David')
        self.assertEqual(track1.mbidArtist,
                         ['4d56eb9f-13b3-4f05-9db7-50195378d49f'])
        self.assertEqual(track1.mbidRecording,
                         'b191794d-b7c6-4d6f-971e-0a543959b5ad')
        self.assertEqual(track1.mbidWorks,
                         ['90d5be68-0b29-45a3-ba01-c27ad78e3625'])
