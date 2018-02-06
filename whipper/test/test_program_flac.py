# -*- Mode: Python; test-case-name: whipper.test.test_program_flac -*-

from whipper.program import flac
from whipper.test import common


class VersionTestCase(common.TestCase):

    def testGetVersion(self):
        v = flac.getVersion()
        self.failUnless(v)
        # make sure it starts with a digit
        self.failUnless(int(v[0]))
