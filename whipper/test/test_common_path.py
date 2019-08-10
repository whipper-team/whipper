# -*- Mode: Python; test-case-name: whipper.test.test_common_path -*-
# vi:si:et:sw=4:sts=4:ts=4

from whipper.common import path

from whipper.test import common


class FilterTestCase(common.TestCase):

    def setUp(self):
        self._filter = path.PathFilter(special=True)

    def testSlash(self):
        part = 'A Charm/A Blade'
        self.assertEqual(self._filter.filter(part), 'A Charm-A Blade')

    def testFat(self):
        part = 'A Word: F**k you?'
        self.assertEqual(self._filter.filter(part), 'A Word - F__k you_')

    def testSpecial(self):
        part = '<<< $&*!\' "()`{}[]spaceship>>>'
        self.assertEqual(self._filter.filter(part),
                         '___ _____ ________spaceship___')

    def testGreatest(self):
        part = 'Greatest Ever! Soul: The Definitive Collection'
        self.assertEqual(self._filter.filter(part),
                         'Greatest Ever_ Soul - The Definitive Collection')
