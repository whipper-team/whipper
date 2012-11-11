# -*- Mode: Python; test-case-name: morituri.test.test_common_drive -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.test import common
from morituri.common import drive


class ListifyTestCase(common.TestCase):

    def testString(self):
        string = '/dev/sr0'
        self.assertEquals(drive._listify(string), [string, ])

    def testList(self):
        lst = ['/dev/scd0', '/dev/sr0']
        self.assertEquals(drive._listify(lst), lst)
