# -*- Mode: Python; test-case-name: morituri.test.test_program_cdparanoia -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import unittest

from morituri.program import cdrdao

class FakeTask:
    def setProgress(self, value):
        pass

class ParseTestCase(unittest.TestCase):
    def setUp(self):
        path = os.path.join(os.path.dirname(__file__),
            'cdrdao.readtoc.progress')
        self._parser = cdrdao.OutputParser(FakeTask())

        self._handle = open(path)

    def testParse(self):
        for line in self._handle.readlines():
            self._parser.read(line)
        self.assertEquals(self._parser._starts,
            [0, 13864, 31921, 48332, 61733, 80961,
             100219, 116291, 136188, 157504, 175275])
