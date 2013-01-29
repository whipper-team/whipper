# -*- Mode: Python; test-case-name: morituri.test.test_image_toc -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import copy
import shutil
import tempfile

from morituri.image import toc

from morituri.test import common


class CureTestCase(common.TestCase):

    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__),
            u'cure.toc')
        self.toc = toc.TocFile(self.path)
        self.toc.parse()
        self.assertEquals(len(self.toc.table.tracks), 13)

    def testGetTrackLength(self):
        t = self.toc.table.tracks[0]
        # first track has known length because the .toc is a single file
        self.assertEquals(self.toc.getTrackLength(t), 28324)
        # last track has unknown length
        t = self.toc.table.tracks[-1]
        self.assertEquals(self.toc.getTrackLength(t), -1)

    def testIndexes(self):
        # track 2, index 0 is at 06:16:45 or 28245
        # track 2, index 1 is at 06:17:49 or 28324
        # FIXME: cdrdao seems to get length of FILE 1 frame too many,
        # and START value one frame less
        t = self.toc.table.tracks[1]
        self.assertEquals(t.getIndex(0).relative, 28245)
        self.assertEquals(t.getIndex(1).relative, 28324)

    def _getIndex(self, t, i):
        track = self.toc.table.tracks[t - 1]
        return track.getIndex(i)

    def _assertAbsolute(self, t, i, value):
        index = self._getIndex(t, i)
        self.assertEquals(index.absolute, value)

    def _assertPath(self, t, i, value):
        index = self._getIndex(t, i)
        self.assertEquals(index.path, value)

    def _assertRelative(self, t, i, value):
        index = self._getIndex(t, i)
        self.assertEquals(index.relative, value)

    def testSetFile(self):
        self._assertAbsolute(1, 1, 0)
        self._assertAbsolute(2, 0, 28245)
        self._assertAbsolute(2, 1, 28324)
        self._assertPath(1, 1, "data.wav")

        self.toc.table.absolutize()
        self.toc.table.clearFiles()

        self._assertAbsolute(1, 1, 0)
        self._assertAbsolute(2, 0, 28245)
        self._assertAbsolute(2, 1, 28324)
        self._assertAbsolute(3, 1, 46110)
        self._assertAbsolute(4, 1, 66767)
        self._assertPath(1, 1, None)
        self._assertRelative(1, 1, None)

        # adding the first track file with length 28324 to the table should
        # relativize from absolute 0 to absolute 28323, right before track 2,
        # index 1
        self.toc.table.setFile(1, 1, 'track01.wav', 28324)
        self._assertPath(1, 1, 'track01.wav')
        self._assertRelative(1, 1, 0)
        self._assertPath(2, 0, 'track01.wav')
        self._assertRelative(2, 0, 28245)

        self._assertPath(2, 1, None)
        self._assertRelative(2, 1, None)

    def testConvertCue(self):
        self.toc.table.absolutize()
        cue = self.toc.table.cue()
        ref = open(os.path.join(os.path.dirname(__file__), 'cure.cue')).read()
        common.diffStrings(cue, ref)

        # we verify it because it has failed in readdisc in the past
        self.assertEquals(self.toc.table.getAccurateRipURL(),
            'http://www.accuraterip.com/accuraterip/'
            '3/c/4/dBAR-013-0019d4c3-00fe8924-b90c650d.bin')

    def testGetRealPath(self):
        self.assertRaises(KeyError, self.toc.getRealPath, u'track01.wav')
        (fd, path) = tempfile.mkstemp(suffix=u'.morituri.test.wav')
        self.assertEquals(self.toc.getRealPath(path), path)

        winpath = path.replace('/', '\\')
        self.assertEquals(self.toc.getRealPath(winpath), path)
        os.close(fd)
        os.unlink(path)

# Bloc Party - Silent Alarm has a Hidden Track One Audio


class BlocTestCase(common.TestCase):

    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__),
            u'bloc.toc')
        self.toc = toc.TocFile(self.path)
        self.toc.parse()
        self.assertEquals(len(self.toc.table.tracks), 13)

    def testGetTrackLength(self):
        t = self.toc.table.tracks[0]
        # first track has known length because the .toc is a single file
        # the length is from Track 1, Index 1 to Track 2, Index 1, so
        # does not include the htoa
        self.assertEquals(self.toc.getTrackLength(t), 19649)
        # last track has unknown length
        t = self.toc.table.tracks[-1]
        self.assertEquals(self.toc.getTrackLength(t), -1)

    def testIndexes(self):
        t = self.toc.table.tracks[0]
        self.assertEquals(t.getIndex(0).relative, 0)
        self.assertEquals(t.getIndex(1).relative, 15220)

    # This disc has a pre-gap, so is a good test for .CUE writing

    def testConvertCue(self):
        #self.toc.table.absolutize()
        self.failUnless(self.toc.table.hasTOC())
        cue = self.toc.table.cue()
        ref = open(os.path.join(os.path.dirname(__file__),
            'bloc.cue')).read()
        self.assertEquals(cue, ref)

    def testCDDBId(self):
        self.toc.table.absolutize()
        # cd-discid output:
        # ad0be00d 13 15370 35019 51532 69190 84292 96826 112527 132448
        # 148595 168072 185539 203331 222103 3244

        self.assertEquals(self.toc.table.getCDDBDiscId(), 'ad0be00d')

    def testAccurateRip(self):
        # we verify it because it has failed in readdisc in the past
        self.toc.table.absolutize()
        self.assertEquals(self.toc.table.getAccurateRipURL(),
            'http://www.accuraterip.com/accuraterip/'
            'e/d/2/dBAR-013-001af2de-0105994e-ad0be00d.bin')

# The Breeders - Mountain Battles has CDText


class BreedersTestCase(common.TestCase):

    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__),
            u'breeders.toc')
        self.toc = toc.TocFile(self.path)
        self.toc.parse()
        self.assertEquals(len(self.toc.table.tracks), 13)

    def testCDText(self):
        cdt = self.toc.table.cdtext
        self.assertEquals(cdt['PERFORMER'], 'THE BREEDERS')
        self.assertEquals(cdt['TITLE'], 'MOUNTAIN BATTLES')

        t = self.toc.table.tracks[0]
        cdt = t.cdtext
        self.assertRaises(AttributeError, getattr, cdt, 'PERFORMER')
        self.assertEquals(cdt['TITLE'], 'OVERGLAZED')

    def testConvertCue(self):
        self.toc.table.absolutize()
        self.failUnless(self.toc.table.hasTOC())
        cue = self.toc.table.cue()
        ref = open(os.path.join(os.path.dirname(__file__),
            'breeders.cue')).read()
        self.assertEquals(cue, ref)

# Ladyhawke has a data track


class LadyhawkeTestCase(common.TestCase):

    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__),
            u'ladyhawke.toc')
        self.toc = toc.TocFile(self.path)
        self.toc.parse()
        self.assertEquals(len(self.toc.table.tracks), 13)
        #import code; code.interact(local=locals())
        self.failIf(self.toc.table.tracks[-1].audio)

    def testCDDBId(self):
        self.toc.table.absolutize()
        self.assertEquals(self.toc.table.getCDDBDiscId(), 'c60af50d')
        # output from cd-discid:
        # c60af50d 13 150 15687 31841 51016 66616 81352 99559 116070 133243
        # 149997 161710 177832 207256 2807

    def testMusicBrainz(self):
        self.assertEquals(self.toc.table.getMusicBrainzDiscId(),
            "KnpGsLhvH.lPrNc1PBL21lb9Bg4-")
        self.assertEquals(self.toc.table.getMusicBrainzSubmitURL(),
            "http://mm.musicbrainz.org/bare/cdlookup.html?toc="
            "1+12+195856+150+15687+31841+51016+66616+81352+99559+"
            "116070+133243+149997+161710+177832&"
            "tracks=12&id=KnpGsLhvH.lPrNc1PBL21lb9Bg4-")

    # FIXME: I don't trust this toc, but I can't find the CD anymore

    def testDuration(self):
        self.assertEquals(self.toc.table.duration(), 2761413)

    def testGetFrameLength(self):
        self.assertEquals(self.toc.table.getFrameLength(data=True), 210385)

    def testCue(self):
        self.failUnless(self.toc.table.canCue())
        data = self.toc.table.cue()
        lines = data.split("\n")
        self.assertEquals(lines[0], "REM DISCID C60AF50D")


class CapitalMergeTestCase(common.TestCase):

    def setUp(self):
        self.toc1 = toc.TocFile(os.path.join(os.path.dirname(__file__),
            u'capital.1.toc'))
        self.toc1.parse()
        self.assertEquals(len(self.toc1.table.tracks), 11)
        self.failUnless(self.toc1.table.tracks[-1].audio)

        self.toc2 = toc.TocFile(os.path.join(os.path.dirname(__file__),
            u'capital.2.toc'))
        self.toc2.parse()
        self.assertEquals(len(self.toc2.table.tracks), 1)
        self.failIf(self.toc2.table.tracks[-1].audio)

        self.table = copy.deepcopy(self.toc1.table)
        self.table.merge(self.toc2.table)

    def testCDDBId(self):
        self.table.absolutize()
        self.assertEquals(self.table.getCDDBDiscId(), 'b910140c')
        # output from cd-discid:
        # b910140c 12 24320 44855 64090 77885 88095 104020 118245 129255 141765
        # 164487 181780 209250 4440

    def testMusicBrainz(self):
        # URL to submit: http://mm.musicbrainz.org/bare/cdlookup.html?toc=1+11+
        # 197850+24320+44855+64090+77885+88095+104020+118245+129255+141765+
        # 164487+181780&tracks=11&id=MAj3xXf6QMy7G.BIFOyHyq4MySE-
        self.assertEquals(self.table.getMusicBrainzDiscId(),
            "MAj3xXf6QMy7G.BIFOyHyq4MySE-")

    def testDuration(self):
        # this matches track 11 end sector - track 1 start sector on
        # musicbrainz
        # compare to 3rd and 4th value in URL above
        self.assertEquals(self.table.getFrameLength(), 173530)
        self.assertEquals(self.table.duration(), 2313733)


class UnicodeTestCase(common.TestCase, common.UnicodeTestMixin):

    def setUp(self):
        # we copy the normal non-utf8 filename to a utf-8 filename
        # in this test because builds with LANG=C fail if we include
        # utf-8 filenames in the dist
        path = u'Jos\xe9Gonz\xe1lez.toc'
        self._performer = u'Jos\xe9 Gonz\xe1lez'
        source = os.path.join(os.path.dirname(__file__), 'jose.toc')
        (fd, self.dest) = tempfile.mkstemp(suffix=path)
        os.close(fd)
        shutil.copy(source, self.dest)
        self.toc = toc.TocFile(self.dest)
        self.toc.parse()
        self.assertEquals(len(self.toc.table.tracks), 10)

    def tearDown(self):
        os.unlink(self.dest)

    def testGetTrackLength(self):
        t = self.toc.table.tracks[0]
        # first track has known length because the .toc is a single file
        self.assertEquals(self.toc.getTrackLength(t), 12001)
        # last track has unknown length
        t = self.toc.table.tracks[-1]
        self.assertEquals(self.toc.getTrackLength(t), -1)

    def testGetTrackPerformer(self):
        t = self.toc.table.tracks[0]
        self.assertEquals(t.cdtext['PERFORMER'], self._performer)


# Interpol - Turn of the Bright Lights has same cddb disc id as
# Afghan Whigs - Gentlemen


class TOTBLTestCase(common.TestCase):

    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__),
            u'totbl.fast.toc')
        self.toc = toc.TocFile(self.path)
        self.toc.parse()
        self.assertEquals(len(self.toc.table.tracks), 11)

    def testCDDBId(self):
        self.toc.table.absolutize()
        self.assertEquals(self.toc.table.getCDDBDiscId(), '810b7b0b')
