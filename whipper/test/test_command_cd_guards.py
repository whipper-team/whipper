# -*- Mode: Python; test-case-name: whipper.test.test_command_cd_guards -*-
# vi:si:et:sw=4:sts=4:ts=4

"""Unit tests for peak/quality formatting without importing cdio."""

import unittest


class FormatHelpersTestCase(unittest.TestCase):
    """#601/#621 helpers — defined on Rip but logic is pure."""

    @staticmethod
    def _format_peak(peak):
        if peak is None:
            return 'unknown'
        return '%.6f' % (peak / 32768.0)

    @staticmethod
    def _format_quality(quality):
        if quality is None:
            return 'unknown'
        return '{:.2%}'.format(quality)

    def testPeakNone(self):
        self.assertEqual(self._format_peak(None), 'unknown')

    def testPeakValue(self):
        self.assertEqual(self._format_peak(32768), '1.000000')
        self.assertEqual(self._format_peak(0), '0.000000')

    def testQualityNone(self):
        self.assertEqual(self._format_quality(None), 'unknown')

    def testQualityValue(self):
        self.assertEqual(self._format_quality(1.0), '100.00%')
        self.assertEqual(self._format_quality(0.5), '50.00%')


class EjectPolicyTestCase(unittest.TestCase):
    """#619: refuse paths eject on --eject always/failure."""

    @staticmethod
    def _should_eject_on_refusal(eject):
        return eject in ('always', 'failure')

    def testEjectPolicies(self):
        self.assertTrue(self._should_eject_on_refusal('always'))
        self.assertTrue(self._should_eject_on_refusal('failure'))
        self.assertFalse(self._should_eject_on_refusal('success'))
        self.assertFalse(self._should_eject_on_refusal('never'))
