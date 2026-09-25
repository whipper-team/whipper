# vi:si:et:sw=4:sts=4:ts=4:set fileencoding=utf-8
"""Tests for whipper.command.basecommand"""

import unittest
from unittest import mock

from whipper.command.basecommand import BaseCommand


class DeviceCommand(BaseCommand):
    description = "test command"
    device_option = True


class DeviceOptionTestCase(unittest.TestCase):
    """A missing drive exits cleanly instead of raising a traceback."""

    @mock.patch('whipper.common.drive.getAllDevicePaths', return_value=[])
    def testNoDrivesFound(self, _):
        with self.assertLogs('whipper.command.basecommand', 'CRITICAL'):
            with self.assertRaises(SystemExit) as cm:
                DeviceCommand([], 'whipper test', None)
        self.assertEqual(cm.exception.code, 3)

    @mock.patch('whipper.common.drive.getAllDevicePaths',
                return_value=['/dev/sr0'])
    def testDeviceNotFound(self, _):
        with self.assertLogs('whipper.command.basecommand', 'CRITICAL'):
            with self.assertRaises(SystemExit) as cm:
                DeviceCommand(['-d', '/does/not/exist'], 'whipper test', None)
        self.assertEqual(cm.exception.code, 3)
