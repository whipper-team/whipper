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
        # FIXME: we should be testing splitting in byte blocks, not lines
        for line in self._handle.readlines():
            self._parser.read(line)

        for i, offset in enumerate(
            [0, 13864, 31921, 48332, 61733, 80961,
             100219, 116291, 136188, 157504, 175275]):
            track = self._parser.table.tracks[i]
            self.assertEquals(track.getIndex(1).absolute, offset)

        self.assertEquals(self._parser.version, '1.2.2')
