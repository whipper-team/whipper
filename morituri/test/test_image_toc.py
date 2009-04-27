# -*- Mode: Python; test-case-name: morituri.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.image import toc

class CureTestCase(unittest.TestCase):
    def setUp(self):
        self.toc = toc.TOC(os.path.join(os.path.dirname(__file__),
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
        t = self.toc.tracks[1]
        (offset, file) = t.getIndex(0)
        self.assertEquals(offset, 28166)
        (offset, file) = t.getIndex(1)
        self.assertEquals(offset, 28245)
