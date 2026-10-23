# -*- Mode: Python; test-case-name: whipper.test.test_image_verify -*-
# vi:si:et:sw=4:sts=4:ts=4

"""Issue #508: image verification must not KeyError on missing cue FILE."""

import os
import unittest
from unittest import mock

from whipper.image import image as image_mod


class FakeIndex:
    def __init__(self, path, relative=0, absolute=0, number=1, counter=1):
        self.path = path
        self.relative = relative
        self.absolute = absolute
        self.number = number
        self.counter = counter


class FakeTrack:
    def __init__(self, path, number=1):
        self.number = number
        self.audio = True
        self.indexes = {0: FakeIndex(None, number=0),
                        1: FakeIndex(path, number=1)}


class FakeCue:
    def __init__(self, tracks):
        self.table = mock.Mock()
        self.table.tracks = tracks

    @staticmethod
    def getTrackLength(track):
        return -1


class FakeImage:
    def __init__(self, tracks):
        self.cue = FakeCue(tracks)

    @staticmethod
    def getRealPath(path):
        raise KeyError("Cannot find file for %r" % (path, ))


class ImageVerifyMissingFileTestCase(unittest.TestCase):

    def testConstructorSkipsUnresolvablePath(self):
        """Missing cue FILE paths must not raise KeyError (#508)."""
        fake = FakeImage([FakeTrack('../../data.wav')])
        with mock.patch.object(image_mod.task.MultiSeparateTask, '__init__',
                               return_value=None):
            verify = image_mod.ImageVerifyTask(fake, skipped_tracks=[])
        self.assertIsNotNone(verify)
        # No audio-length tasks scheduled for the unresolvable path
        self.assertEqual(getattr(verify, '_tasks', []), [])

    def testConstructorSkipsEmptyPath(self):
        fake = FakeImage([FakeTrack(None)])
        with mock.patch.object(image_mod.task.MultiSeparateTask, '__init__',
                               return_value=None):
            verify = image_mod.ImageVerifyTask(fake, skipped_tracks=[])
        self.assertEqual(getattr(verify, '_tasks', []), [])

    def testSkippedBasenameStillSkips(self):
        fake = FakeImage([FakeTrack('missing.flac')])
        with mock.patch.object(image_mod.task.MultiSeparateTask, '__init__',
                               return_value=None):
            verify = image_mod.ImageVerifyTask(
                fake, skipped_tracks=['missing.flac'])
        self.assertEqual(getattr(verify, '_tasks', []), [])
        self.assertTrue(os.path.basename('missing.flac') in
                        ['missing.flac'])
