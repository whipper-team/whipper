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
                                            'kings-single.cue'))
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
                                            'kings-separate.cue'))
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
                                            'kanye.cue'))
        self.cue.parse()
        self.assertEqual(len(self.cue.table.tracks), 13)

    def testGetTrackLength(self):
        t = self.cue.table.tracks[0]
        self.assertEqual(self.cue.getTrackLength(t), -1)


class WriteCueFileTestCase(unittest.TestCase):

    @staticmethod
    def testWrite():
        fd, path = tempfile.mkstemp(suffix='.whipper.test.cue')
        os.close(fd)

        it = table.Table()

        t = table.Track(1)
        t.index(1, absolute=0, path='track01.wav', relative=0, counter=1)
        it.tracks.append(t)

        t = table.Track(2)
        t.index(0, absolute=1000, path='track01.wav',
                relative=1000, counter=1)
        t.index(1, absolute=2000, path='track02.wav', relative=0, counter=2)
        it.tracks.append(t)
        it.absolutize()
        it.leadout = 3000

        common.diffStrings("""REM DISCID 0C002802
REM COMMENT "whipper %s"
REM ACCURATERIP_PATH 8/8/3/dBAR-002-00001388-000032c9-0c002802.bin
FILE "track01.wav" WAVE
  TRACK 01 AUDIO
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    INDEX 00 00:13:25
FILE "track02.wav" WAVE
    INDEX 01 00:00:00
""" % whipper.__version__, it.cue())
        os.unlink(path)


class ParsePregapAndARPathTestCase(unittest.TestCase):
    """PREGAP and REM ACCURATERIP_PATH must survive a cue round-trip (#677)."""

    def test_parse_bloc_pregap_cue(self):
        path = os.path.join(os.path.dirname(__file__), 'bloc.cue')
        c = cue.CueFile(path)
        c.parse()
        track1 = c.table.tracks[0]
        # PREGAP 03:22:70 == 15220 frames
        self.assertEqual(track1.pregap, 15220)
        self.assertEqual(track1.getPregap(), 15220)
        self.assertIn(0, track1.indexes)
        self.assertEqual(c.accuraterip_path,
                         'e/d/2/dBAR-013-001af2de-0105994e-ad0be00d.bin')

    def test_image_setup_uses_pregap_offset(self):
        # Without audio files, ImageVerifyTask cannot scan lengths; we only
        # check that _pregap_frames prefers the cue PREGAP directive.
        path = os.path.join(os.path.dirname(__file__), 'bloc.cue')
        c = cue.CueFile(path)
        c.parse()
        from whipper.image.image import Image
        # Image.__init__ parses the cue again
        img = Image(path)
        self.assertEqual(img._pregap_frames(img.cue.table.tracks[0]), 15220)
        self.assertEqual(img.accuraterip_path,
                         'e/d/2/dBAR-013-001af2de-0105994e-ad0be00d.bin')

    def test_write_and_parse_escaped_quotes(self):
        fd, path = tempfile.mkstemp(suffix='.whipper.test.cue')
        os.close(fd)
        it = table.Table()
        t = table.Track(1)
        t.index(1, absolute=0, path='12_ edit.flac', relative=0, counter=1)
        it.tracks.append(t)
        it.leadout = 100
        it.cdtext['TITLE'] = 'He said "hi"'
        with open(path, 'w') as f:
            f.write(it.cue())
        c = cue.CueFile(path)
        c.parse()
        self.assertEqual(c.table.tracks[0].getIndex(1).path, '12_ edit.flac')
        os.unlink(path)
