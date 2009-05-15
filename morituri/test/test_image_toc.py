# -*- Mode: Python; test-case-name: morituri.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.image import toc

from morituri.test import common

class CureTestCase(unittest.TestCase):
    def setUp(self):
        self.toc = toc.TocFile(os.path.join(os.path.dirname(__file__),
            'cure.toc'))
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
        self._assertAbsolute(1, 1, None)
        self._assertAbsolute(2, 0, None)
        self._assertAbsolute(2, 1, None)
        self._assertPath(1, 1, "data.wav")

        def dump():
            for t in self.toc.table.tracks:
                print t
                print t.indexes.values()

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
        self.assertEquals(cue, ref)

# Bloc Party - Silent Alarm has a Hidden Track One Audio
class BlocTestCase(unittest.TestCase):
    def setUp(self):
        self.toc = toc.TocFile(os.path.join(os.path.dirname(__file__),
            'bloc.toc'))
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

# The Breeders - Mountain Battles has CDText
class BreedersTestCase(unittest.TestCase):
    def setUp(self):
        self.toc = toc.TocFile(os.path.join(os.path.dirname(__file__),
            'breeders.toc'))
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
        self.failIf(self.toc.table.hasTOC())
        self.toc.table.absolutize()
        self.failUnless(self.toc.table.hasTOC())
        cue = self.toc.table.cue()
        ref = open(os.path.join(os.path.dirname(__file__),
            'breeders.cue')).read()
        self.assertEquals(cue, ref)
