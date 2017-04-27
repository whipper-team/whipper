# -*- Mode: Python; test-case-name: whipper.test.test_program_cdparanoia -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

from whipper.program import cdrdao

from whipper.test import common

# TODO: Current test architecture makes testing cdrdao difficult. Revisit.

class VersionTestCase(common.TestCase):
    def testGetVersion(self):
        v = cdrdao.getCDRDAOVersion()
        self.failUnless(v)
        # make sure it starts with a digit
        self.failUnless(int(v[0]))
