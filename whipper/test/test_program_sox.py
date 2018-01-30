# -*- Mode: Python; test-case-name: whipper.test.test_program_sox -*-

import os

from whipper.program import sox
from whipper.test import common


class PeakLevelTestCase(common.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__), 'track.flac')

    def testParse(self):
        self.assertEquals(26215, sox.peak_level(self.path))
