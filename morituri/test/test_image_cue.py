# -*- Mode: Python; test-case-name: morituri.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile
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

class KanyeMixedTestCase(unittest.TestCase):
    def setUp(self):
        self.cue = cue.Cue(os.path.join(os.path.dirname(__file__),
            'kanye.cue'))
        self.cue.parse()
        self.assertEquals(len(self.cue.tracks), 13)

    def testGetTrackLength(self):
        t = self.cue.tracks[0]
        self.assertEquals(self.cue.getTrackLength(t), -1)


class WriteCueTestCase(unittest.TestCase):
    def testWrite(self):
        fd, path = tempfile.mkstemp(suffix='morituri.test.cue')
        os.close(fd)
        c = cue.Cue(path)

        f = cue.File('track01.wav', 'AUDIO')
        t = cue.Track(1)
        t.index(1, 0, f)
        c.tracks.append(t)

        t = cue.Track(2)
        t.index(0, 1000, f)
        f = cue.File('track02.wav', 'AUDIO')
        t.index(1, 1100, f)
        c.tracks.append(t)

        print c.dump()

        
