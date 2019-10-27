# -*- Mode: Python; test-case-name: whipper.test.test_image_cue -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile
import unittest

import whipper

from whipper.image import table, cue

from whipper.test import common


class KingsSingleTestCase(unittest.TestCase):

    def setUp(self):
        self.cue = cue.CueFile(os.path.join(os.path.dirname(__file__),
                                            u'kings-single.cue'))
        self.cue.parse()
        self.assertEqual(len(self.cue.table.tracks), 11)

    def testGetTrackLength(self):
        t = self.cue.table.tracks[0]
        self.assertEqual(self.cue.getTrackLength(t), 17811)
        # last track has unknown length
        t = self.cue.table.tracks[-1]
        self.assertEqual(self.cue.getTrackLength(t), -1)


class KingsSeparateTestCase(unittest.TestCase):

    def setUp(self):
        self.cue = cue.CueFile(os.path.join(os.path.dirname(__file__),
                                            u'kings-separate.cue'))
        self.cue.parse()
        self.assertEqual(len(self.cue.table.tracks), 11)

    def testGetTrackLength(self):
        # all tracks have unknown length
        t = self.cue.table.tracks[0]
        self.assertEqual(self.cue.getTrackLength(t), -1)
        t = self.cue.table.tracks[-1]
        self.assertEqual(self.cue.getTrackLength(t), -1)


class KanyeMixedTestCase(unittest.TestCase):

    def setUp(self):
        self.cue = cue.CueFile(os.path.join(os.path.dirname(__file__),
                                            u'kanye.cue'))
        self.cue.parse()
        self.assertEqual(len(self.cue.table.tracks), 13)

    def testGetTrackLength(self):
        t = self.cue.table.tracks[0]
        self.assertEqual(self.cue.getTrackLength(t), -1)


class WriteCueFileTestCase(unittest.TestCase):

    @staticmethod
    def testWrite():
        fd, path = tempfile.mkstemp(suffix=u'.whipper.test.cue')
        os.close(fd)

        it = table.Table()

        t = table.Track(1)
        t.index(1, absolute=0, path=u'track01.wav', relative=0, counter=1)
        it.tracks.append(t)

        t = table.Track(2)
        t.index(0, absolute=1000, path=u'track01.wav',
                relative=1000, counter=1)
        t.index(1, absolute=2000, path=u'track02.wav', relative=0, counter=2)
        it.tracks.append(t)
        it.absolutize()
        it.leadout = 3000

        common.diffStrings(u"""REM DISCID 0C002802
REM COMMENT "whipper %s"
FILE "track01.wav" WAVE
  TRACK 01 AUDIO
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    INDEX 00 00:13:25
FILE "track02.wav" WAVE
    INDEX 01 00:00:00
""" % whipper.__version__, it.cue())
        os.unlink(path)
