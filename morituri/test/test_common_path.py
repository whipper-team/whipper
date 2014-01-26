# -*- Mode: Python; test-case-name: morituri.test.test_common_path -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.common import path

from morituri.test import common


class FilterTestCase(common.TestCase):

    def setUp(self):
        self._filter = path.PathFilter(special=True)

    def testSlash(self):
        part = u'A Charm/A Blade'
        self.assertEquals(self._filter.filter(part), u'A Charm-A Blade')

    def testFat(self):
        part = u'A Word: F**k you?'
        self.assertEquals(self._filter.filter(part), u'A Word - F__k you_')

    def testSpecial(self):
        part = u'<<< $&*!\' "()`{}[]spaceship>>>'
        self.assertEquals(self._filter.filter(part),
               u'___ _____ ________spaceship___')

    def testGreatest(self):
        part = u'Greatest Ever! Soul: The Definitive Collection'
        self.assertEquals(self._filter.filter(part),
               u'Greatest Ever_ Soul - The Definitive Collection')
