# -*- Mode: Python; test-case-name: morituri.test.test_common_path -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.common import path

from morituri.test import common


class FilterTestCase(common.TestCase):

    def setUp(self):
        self._filter = path.PathFilter()

    def testSlash(self):
        part = u'A Charm/A Blade'
        self.assertEquals(self._filter.filter(part), u'A Charm-A Blade')
