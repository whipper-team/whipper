# -*- Mode: Python; test-case-name: whipper.test.test_common_path -*-
# vi:si:et:sw=4:sts=4:ts=4

from whipper.common import path
from whipper.test import common


# TODO: Right now you're testing different strings for different functions.
# I think it'd make more sense to come up with a selection of strings to test
# and then test that set of strings for the entire matrix to make sure that
# they all behave correctly in all instances.
# <Freso 2018-11-04, GitHub comment>
class FilterTestCase(common.TestCase):
    def setUp(self):
        self._filter_none = path.PathFilter(dot=False, posix=False,
                                            vfat=False, whitespace=False,
                                            printable=False)
        self._filter_dot = path.PathFilter(dot=True, posix=False,
                                           vfat=False, whitespace=False,
                                           printable=False)
        self._filter_posix = path.PathFilter(dot=False, posix=True,
                                             vfat=False, whitespace=False,
                                             printable=False)
        self._filter_vfat = path.PathFilter(dot=False, posix=False,
                                            vfat=True, whitespace=False,
                                            printable=False)
        self._filter_whitespace = path.PathFilter(dot=False, posix=False,
                                                  vfat=False, whitespace=True,
                                                  printable=False)
        self._filter_printable = path.PathFilter(dot=False, posix=False,
                                                 vfat=False, whitespace=False,
                                                 printable=True)
        self._filter_all = path.PathFilter(dot=True, posix=True, vfat=True,
                                           whitespace=True, printable=True)

    def testNone(self):
        part = '<<< $&*!\' "()`{}[]spaceship>>>'
        self.assertEqual(self._filter_posix.filter(part), part)

    def testDot(self):
        part = '.弐'
        self.assertEqual(self._filter_dot.filter(part), '_弐')

    def testPosix(self):
        part = 'A Charm/A \x00Blade'
        self.assertEqual(self._filter_posix.filter(part), 'A Charm_A _Blade')

    def testVfat(self):
        part = 'A Word: F**k you?'
        self.assertEqual(self._filter_vfat.filter(part), 'A Word_ F__k you_')

    def testWhitespace(self):
        part = 'This is just a test!'
        self.assertEqual(self._filter_whitespace.filter(part),
                         'This_is_just_a_test!')

    def testPrintable(self):
        part = 'Supper’s Ready† 😽'
        self.assertEqual(self._filter_printable.filter(part),
                         'Supper_s Ready_ _')

    def testAll(self):
        part = 'Greatest Ever! Soul: The Definitive Collection'
        self.assertEqual(self._filter_all.filter(part),
                         'Greatest_Ever!_Soul__The_Definitive_Collection')
