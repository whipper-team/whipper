# -*- Mode: Python; test-case-name: whipper.test.test_image_table -*-
# vi:si:et:sw=4:sts=4:ts=4

from os import environ
from shutil import rmtree
from tempfile import mkdtemp
from whipper.image import table
from whipper.common import config

from whipper.test import common as tcommon


def h(i):
    return "0x%08x" % i


class TrackTestCase(tcommon.TestCase):

    def testRepr(self):
        track = table.Track(1)
        self.assertEqual(repr(track), "<Track 01>")

        track.index(1, 100)
        self.assertTrue(repr(track.indexes[1]).startswith('<Index 01 '))


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

        self.assertFalse(self.table.hasTOC())

        self.table.leadout = 210385

        self.assertTrue(self.table.hasTOC())
        self.assertEqual(self.table.tracks[0].getPregap(), 0)

    def testCDDB(self):
        self.assertEqual(self.table.getCDDBDiscId(), "c60af50d")

    def testMusicBrainz(self):
        # output from mb-submit-disc:
        # https://musicbrainz.org/cdtoc/attach?toc=1+12+195856+150+
        # 15687+31841+51016+66616+81352+99559+116070+133243+149997+161710+
        # 177832&tracks=12&id=KnpGsLhvH.lPrNc1PBL21lb9Bg4-
        # however, not (yet) in MusicBrainz database

        # setup to test if MusicBrainz submit URL is hardcoded to use https
        env_original = environ.get('XDG_CONFIG_HOME')
        tmp_conf = mkdtemp(suffix='.config')
        # HACK: hijack env var to avoid overwriting user's whipper config file
        # This works because directory.config_path() builds the location where
        # whipper's conf will reside based on the value of env XDG_CONFIG_HOME
        environ['XDG_CONFIG_HOME'] = tmp_conf
        self.config = config.Config()
        self.config._parser.add_section('musicbrainz')
        self.config._parser.set('musicbrainz', 'server',
                                'http://musicbrainz.org')
        self.config.write()
        self.assertEqual(self.table.getMusicBrainzSubmitURL(),
                         "http://musicbrainz.org/cdtoc/attach?toc=1+12+1958"
                         "56+150+15687+31841+51016+66616+81352+99559+116070+13"
                         "3243+149997+161710+177832&tracks=12&id=KnpGsLhvH.lPr"
                         "Nc1PBL21lb9Bg4-")
        # HACK: continuation - restore original env value (if defined)
        if env_original is not None:
            environ['XDG_CONFIG_HOME'] = env_original
        else:
            environ.pop('XDG_CONFIG_HOME', None)
        self.assertEqual(self.table.getMusicBrainzDiscId(),
                         "KnpGsLhvH.lPrNc1PBL21lb9Bg4-")
        rmtree(tmp_conf)

    def testAccurateRip(self):
        self.assertEqual(self.table.accuraterip_ids(), (
            "0013bd5a", "00b8d489"))
        self.assertEqual(self.table.accuraterip_path(),
                         "a/5/d/dBAR-012-0013bd5a-00b8d489-c60af50d.bin")

    def testDuration(self):
        self.assertEqual(self.table.duration(), 2761413)


class MusicBrainzTestCase(tcommon.TestCase):
    # example taken from https://musicbrainz.org/doc/Disc_ID_Calculation
    # disc is Ettella Diamant

    def setUp(self):
        self.table = table.Table()

        for i in range(6):
            self.table.tracks.append(table.Track(i + 1, audio=True))

        offsets = [0, 15213, 32164, 46442, 63264, 80339]
        t = self.table.tracks
        for i, offset in enumerate(offsets):
            t[i].index(1, absolute=offset)

        self.assertFalse(self.table.hasTOC())

        self.table.leadout = 95312

        self.assertTrue(self.table.hasTOC())

    def testMusicBrainz(self):
        self.assertEqual(self.table.getMusicBrainzDiscId(),
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
        self.assertEqual(self.table.tracks[0].getPregap(), 0)
        self.assertEqual(self.table.tracks[1].getPregap(), 200)
