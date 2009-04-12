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

    def testAudioRipCRC(self):
        crctask = image.AudioRipCRCTask(self.image) 
        runner = task.SyncRunner()
        runner.run(crctask, verbose=False)

        self.assertEquals(len(crctask.crcs), 4)
        self.assertEquals(h(crctask.crcs[0]), '0x00000000')
        self.assertEquals(h(crctask.crcs[1]), '0x793fa868')
        self.assertEquals(h(crctask.crcs[2]), '0x8dd37c26')
        self.assertEquals(h(crctask.crcs[3]), '0x00000000')

class KingsSeparateTestCase(unittest.TestCase):
    def setUp(self):
        self.image = image.Image(os.path.join(os.path.dirname(__file__),
            'track-separate.cue'))

    def testAudioRipCRC(self):
        crctask = image.AudioRipCRCTask(self.image) 
        runner = task.SyncRunner()
        runner.run(crctask, verbose=False)

        self.assertEquals(len(crctask.crcs), 4)
        self.assertEquals(h(crctask.crcs[0]), '0xaf18681e')
        self.assertEquals(h(crctask.crcs[1]), '0xd63dc2d2')
        self.assertEquals(h(crctask.crcs[2]), '0xd63dc2d2')
        self.assertEquals(h(crctask.crcs[3]), '0x7271db39')

class AudioLengthTestCase(unittest.TestCase):
    def testLength(self):
        path = os.path.join(os.path.dirname(__file__), 'track.flac')
        t = image.AudioLengthTask(path)
        runner = task.SyncRunner()
        runner.run(t, verbose=False)
        self.assertEquals(t.length, 5880)
        


