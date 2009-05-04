# -*- Mode: Python; test-case-name: morituri.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.image import toc

class CureTestCase(unittest.TestCase):
    def setUp(self):
        self.toc = toc.TocFile(os.path.join(os.path.dirname(__file__),
            'cure.toc'))
        self.toc.parse()
        self.assertEquals(len(self.toc.tracks), 13)

    def testGetTrackLength(self):
        t = self.toc.tracks[0]
        self.assertEquals(self.toc.getTrackLength(t), -1)
        # last track has unknown length
        t = self.toc.tracks[-1]
        self.assertEquals(self.toc.getTrackLength(t), -1)

    def testIndexes(self):
        # track 2, index 0 is at 06:16:45
        # FIXME: cdrdao seems to get length of FILE 1 frame too many,
        # and START value one frame less
        t = self.toc.tracks[1]
        (offset, file) = t.getIndex(0)
        self.assertEquals(offset, 28245)
        (offset, file) = t.getIndex(1)
        self.assertEquals(offset, 28324)

# Bloc Party - Silent Alarm has a Hidden Track One Audio
class BlocTestCase(unittest.TestCase):
    def setUp(self):
        self.toc = toc.TocFile(os.path.join(os.path.dirname(__file__),
            'bloc.toc'))
        self.toc.parse()
        self.assertEquals(len(self.toc.tracks), 13)

    def testGetTrackLength(self):
        t = self.toc.tracks[0]
        self.assertEquals(self.toc.getTrackLength(t), -1)
        # last track has unknown length
        t = self.toc.tracks[-1]
        self.assertEquals(self.toc.getTrackLength(t), -1)

    def testIndexes(self):
        t = self.toc.tracks[0]
        (offset, file) = t.getIndex(0)
        self.assertEquals(offset, 0)
        (offset, file) = t.getIndex(1)
        self.assertEquals(offset, 15220)
