# -*- Mode: Python; test-case-name: whipper.test.test_common_directory -*-
# vi:si:et:sw=4:sts=4:ts=4

from whipper.common import directory

from whipper.test import common


class DirectoryTestCase(common.TestCase):

    def testAll(self):
        path = directory.config_path()
        self.failUnless(path.startswith('/home'))

        path = directory.cache_path()
        self.failUnless(path.startswith('/home'))
