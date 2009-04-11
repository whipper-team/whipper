# -*- Mode: Python; test-case-name: morituri.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.image import cue

class KingsSingleTestCase(unittest.TestCase):
    def setUp(self):
        self.cue = cue.Cue(os.path.join(os.path.dirname(__file__),
            'kings-single.cue'))
        self.cue.parse()
        self.assertEquals(len(self.cue.tracks), 11)

    def testGetTrackLength(self):
        t = self.cue.tracks[0]
        self.assertEquals(self.cue.getTrackLength(t), 17811)
        # last track has unknown length
        t = self.cue.tracks[-1]
        self.assertEquals(self.cue.getTrackLength(t), -1)

class KingsSeparateTestCase(unittest.TestCase):
    def setUp(self):
        self.cue = cue.Cue(os.path.join(os.path.dirname(__file__),
            'kings-separate.cue'))
        self.cue.parse()
        self.assertEquals(len(self.cue.tracks), 11)

    def testGetTrackLength(self):
        # all tracks have unknown length
        t = self.cue.tracks[0]
        self.assertEquals(self.cue.getTrackLength(t), -1)
        t = self.cue.tracks[-1]
        self.assertEquals(self.cue.getTrackLength(t), -1)
