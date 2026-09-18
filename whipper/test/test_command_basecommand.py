# -*- Mode: Python; test-case-name: whipper.test.test_command_basecommand -*-
# vi:si:et:sw=4:sts=4:ts=4

import unittest
from unittest import mock

from whipper.command.basecommand import BaseCommand


class _Leaf(BaseCommand):
    summary = "leaf"
    description = "leaf command"
    device_option = True


class _Parent(BaseCommand):
    summary = "parent"
    description = "parent command"
    device_option = True
    subcommands = {'leaf': _Leaf}


class HelpWithoutDriveTestCase(unittest.TestCase):
    """Issue #164: --help must work when no CD-DA drive is present."""

    def testHelpWithoutDrivesExitsZero(self):
        with mock.patch(
                'whipper.command.basecommand.drive.getAllDevicePaths',
                return_value=[]):
            with self.assertRaises(SystemExit) as ctx:
                _Leaf(['--help'], 'whipper leaf', None)
        self.assertEqual(ctx.exception.code, 0)

    def testShortHelpWithoutDrivesExitsZero(self):
        with mock.patch(
                'whipper.command.basecommand.drive.getAllDevicePaths',
                return_value=[]):
            with self.assertRaises(SystemExit) as ctx:
                _Leaf(['-h'], 'whipper leaf', None)
        self.assertEqual(ctx.exception.code, 0)

    def testSubcommandHelpWithoutDrivesExitsZero(self):
        with mock.patch(
                'whipper.command.basecommand.drive.getAllDevicePaths',
                return_value=[]):
            with self.assertRaises(SystemExit) as ctx:
                _Parent(['leaf', '--help'], 'whipper parent', None)
        self.assertEqual(ctx.exception.code, 0)

    def testRunWithoutDrivesStillFails(self):
        with mock.patch(
                'whipper.command.basecommand.drive.getAllDevicePaths',
                return_value=[]):
            with self.assertRaises(IOError) as ctx:
                _Leaf([], 'whipper leaf', None)
        self.assertIn('No CD-DA drives found', str(ctx.exception))

    def testDefaultDeviceUsedWhenDriveExists(self):
        with mock.patch(
                'whipper.command.basecommand.drive.getAllDevicePaths',
                return_value=['/dev/null']), \
                mock.patch('os.path.exists', return_value=True), \
                mock.patch('os.path.realpath', side_effect=lambda p: p):
            cmd = _Leaf([], 'whipper leaf', None)
        self.assertEqual(cmd.options.device, '/dev/null')

    def testMissingExplicitDeviceStillFails(self):
        with mock.patch(
                'whipper.command.basecommand.drive.getAllDevicePaths',
                return_value=['/dev/null']), \
                mock.patch('os.path.exists', return_value=False), \
                mock.patch('os.path.realpath', side_effect=lambda p: p):
            with self.assertRaises(IOError) as ctx:
                _Leaf(['-d', '/dev/missing'], 'whipper leaf', None)
        self.assertIn('not found', str(ctx.exception))
