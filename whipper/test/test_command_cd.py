# vi:si:et:sw=4:sts=4:ts=4:set fileencoding=utf-8
"""Tests for the track selection of whipper.command.cd (--tracks)"""

import unittest

from whipper.command.cd import format_track_selection, parse_track_selection


class ParseTrackSelectionTestCase(unittest.TestCase):

    def testSingleTrack(self):
        self.assertEqual(parse_track_selection('5'), [5])

    def testRange(self):
        self.assertEqual(parse_track_selection('3-7'), [3, 4, 5, 6, 7])

    def testListOfRanges(self):
        self.assertEqual(parse_track_selection('3-5,10-11'),
                         [3, 4, 5, 10, 11])

    def testMixedWithSpaces(self):
        self.assertEqual(parse_track_selection(' 2, 4 - 5 ,9'), [2, 4, 5, 9])

    def testOverlapsAndDuplicatesMerge(self):
        self.assertEqual(parse_track_selection('3-5,4-6,5,3'),
                         [3, 4, 5, 6])

    def testWithinTrackCount(self):
        self.assertEqual(parse_track_selection('24', 24), [24])

    def testRejected(self):
        for spec in ('0', '0-3', '7-3', '3-', '-3', 'a', '1,,2', '', '1-2-3',
                     '²'):
            with self.assertRaises(ValueError, msg=repr(spec)):
                parse_track_selection(spec)

    def testAboveTrackCount(self):
        with self.assertRaises(ValueError) as cm:
            parse_track_selection('20-25', 24)
        self.assertIn('only 24 tracks', str(cm.exception))

    def testNoTrackCountSkipsUpperBound(self):
        self.assertEqual(parse_track_selection('99'), [99])


class FormatTrackSelectionTestCase(unittest.TestCase):

    def testCompactsRanges(self):
        self.assertEqual(format_track_selection([3, 4, 5, 6, 7, 10]), '3-7,10')

    def testSingleTrack(self):
        self.assertEqual(format_track_selection([24]), '24')

    def testRoundTrip(self):
        spec = '1,3-5,10-13,20'
        self.assertEqual(
            format_track_selection(parse_track_selection(spec)), spec)
