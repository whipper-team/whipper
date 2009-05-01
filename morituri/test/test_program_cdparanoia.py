# -*- Mode: Python; test-case-name: morituri.test.test_program_cdparanoia -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.program import cdparanoia

class ParseTestCase(unittest.TestCase):
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__),
            'cdparanoia.progress')
        self._parser = cdparanoia.ProgressParser()

        self._handle = open(path)

    def testParse(self):
        for line in self._handle.readlines():
            self._parser.parse(line)
