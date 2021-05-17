# -*- Mode: Python; test-case-name: whipper.test.test_common_directory -*-
# vi:si:et:sw=4:sts=4:ts=4

from os.path import dirname, expanduser
from whipper.common import directory
from whipper.test import common


class DirectoryTestCase(common.TestCase):
    HOME = expanduser('~')
    HOME_PARENT = dirname(HOME)

    def testAll(self):
        path = directory.config_path()
        self.assertTrue(path.startswith(DirectoryTestCase.HOME_PARENT))
