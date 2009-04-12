# -*- Mode: Python; test-case-name: morituri.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

import gobject
gobject.threads_init()

from morituri.image import image
from morituri.common import task

def h(i):
    return "0x%08x" % i

class TrackSingleTestCase(unittest.TestCase):
    def setUp(self):
        self.image = image.Image(os.path.join(os.path.dirname(__file__),
            'track-single.cue'))
        self.runner = task.SyncRunner()
        self.image.setup(self.runner)

    def testAudioRipCRC(self):
        crctask = image.AudioRipCRCTask(self.image) 
        self.runner.run(crctask, verbose=False)

        self.assertEquals(len(crctask.crcs), 4)
        self.assertEquals(h(crctask.crcs[0]), '0x00000000')
        self.assertEquals(h(crctask.crcs[1]), '0x793fa868')
        self.assertEquals(h(crctask.crcs[2]), '0x8dd37c26')
        self.assertEquals(h(crctask.crcs[3]), '0x00000000')

    def testLength(self):
        tracks = self.image.cue.tracks
        self.assertEquals(self.image.getTrackLength(tracks[0]), 2)
        self.assertEquals(self.image.getTrackLength(tracks[1]), 2)
        self.assertEquals(self.image.getTrackLength(tracks[2]), 2)
        self.assertEquals(self.image.getTrackLength(tracks[3]), 4)

    def testCDDB(self):
        self.assertEquals(self.image.cddbDiscId(), "08000004")

class TracSeparateTestCase(unittest.TestCase):
    def setUp(self):
        self.image = image.Image(os.path.join(os.path.dirname(__file__),
            'track-separate.cue'))
        self.runner = task.SyncRunner()
        self.image.setup(self.runner)

    def testAudioRipCRC(self):
        crctask = image.AudioRipCRCTask(self.image) 
        self.runner.run(crctask, verbose=False)

        self.assertEquals(len(crctask.crcs), 4)
        self.assertEquals(h(crctask.crcs[0]), '0xaf18681e')
        self.assertEquals(h(crctask.crcs[1]), '0xd63dc2d2')
        self.assertEquals(h(crctask.crcs[2]), '0xd63dc2d2')
        self.assertEquals(h(crctask.crcs[3]), '0x7271db39')

    def testLength(self):
        tracks = self.image.cue.tracks
        self.assertEquals(self.image.getTrackLength(tracks[0]), 10)
        self.assertEquals(self.image.getTrackLength(tracks[1]), 10)
        self.assertEquals(self.image.getTrackLength(tracks[2]), 10)
        self.assertEquals(self.image.getTrackLength(tracks[3]), 10)

    def testCDDB(self):
        self.assertEquals(self.image.cddbDiscId(), "08000004")

class AudioLengthTestCase(unittest.TestCase):
    def testLength(self):
        path = os.path.join(os.path.dirname(__file__), 'track.flac')
        t = image.AudioLengthTask(path)
        runner = task.SyncRunner()
        runner.run(t, verbose=False)
        self.assertEquals(t.length, 5880)
        


