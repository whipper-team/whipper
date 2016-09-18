# -*- Mode: Python; test-case-name: morituri.test.test_common_directory -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.common import directory

from morituri.test import common


class DirectoryTestCase(common.TestCase):

    def testAll(self):
        d = directory.Directory()

        path = d.getConfig()
        self.failUnless(path.startswith('/home'))

        path = d.getCache()
        self.failUnless(path.startswith('/home'))
