# -*- Mode: Python; test-case-name: morituri.test.test_program_sox -*-

import os

from morituri.program import sox
from morituri.test import common

class PeakLevelTestCase(common.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(__file__), 'track.flac')

    def testParse(self):
        self.assertEquals(0.800018, sox.peak_level(self.path))
