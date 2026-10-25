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
    #   https://web.archive.org/web/20200331130804/http://www.freedb.org/freedb/misc/c60af50d
    #   https://web.archive.org/web/20200331130829/http://www.freedb.org/freedb/jazz/c60af50d
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


class SaneTOCAndMusicBrainzTestCase(tcommon.TestCase):
    """Issue #583: corrupt / over-long TOCs must not crash in libdiscid."""

    def _table_with_offsets(self, offsets, leadout):
        t = table.Table()
        for i, offset in enumerate(offsets):
            track = table.Track(i + 1, audio=True)
            track.index(1, absolute=offset)
            t.tracks.append(track)
        t.leadout = leadout
        return t

    def test_sane_normal_toc(self):
        t = self._table_with_offsets([0, 150, 300], 450)
        self.assertEqual(t.hasSaneTOC(), (True, None))

    def test_insane_non_monotonic(self):
        t = self._table_with_offsets([0, 300, 200], 400)
        ok, reason = t.hasSaneTOC()
        self.assertFalse(ok)
        self.assertIn('before previous', reason)
        self.assertIsNone(t.getMusicBrainzDiscId())

    def test_insane_disc_too_long(self):
        # leadout beyond libdiscid's ~90 minute limit
        t = self._table_with_offsets([0, 100, 200], table.MAX_CD_SECTORS + 10)
        ok, reason = t.hasSaneTOC()
        self.assertFalse(ok)
        self.assertIn('exceeds', reason)
        self.assertIsNone(t.getMusicBrainzDiscId())

    def test_incomplete_toc(self):
        t = table.Table()
        track = table.Track(1, audio=True)
        t.tracks.append(track)
        ok, reason = t.hasSaneTOC()
        self.assertFalse(ok)

    def test_cue_records_accuraterip_path(self):
        # Issue #677: cue must carry the rip-time AccurateRip entry
        t = self._table_with_offsets([0, 2000], 5000)
        for i, track in enumerate(t.tracks):
            track.index(1, absolute=track.getIndex(1).absolute,
                        path='track%02d.flac' % (i + 1),
                        relative=0, counter=i + 1)
        cue_text = t.cue()
        self.assertIn('REM ACCURATERIP_PATH ', cue_text)
        self.assertIn(t.accuraterip_path(), cue_text)
