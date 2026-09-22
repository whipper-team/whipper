"""Platform regressions; these tests do not access an optical drive."""

import subprocess
import unittest
from unittest import mock

from whipper.common import drive
from whipper.program import cdrdao, utils


class DriveStatusTest(unittest.TestCase):
    def test_freebsd_does_not_open_device_or_call_linux_ioctl(self):
        with mock.patch.object(drive.sys, 'platform', 'freebsd15'), \
                mock.patch.object(drive.os, 'open') as opened, \
                mock.patch.object(drive, 'ioctl') as ioctl:
            self.assertEqual(drive.get_cdrom_drive_status('/dev/cd0'), 0)
        opened.assert_not_called()
        ioctl.assert_not_called()

    def test_linux_status_and_close_on_failure(self):
        with mock.patch.object(drive.sys, 'platform', 'linux'), \
                mock.patch.object(drive.os, 'open', return_value=42), \
                mock.patch.object(drive.os, 'close') as close, \
                mock.patch.object(drive, 'ioctl', return_value=4) as ioctl:
            self.assertEqual(drive.get_cdrom_drive_status('/dev/sr0'), 4)
            ioctl.assert_called_once_with(42, 0x5326)
            close.assert_called_once_with(42)
            ioctl.side_effect = OSError('no device')
            with self.assertRaises(OSError):
                drive.get_cdrom_drive_status('/dev/sr0')
            self.assertEqual(close.call_count, 2)


class TrayTest(unittest.TestCase):
    def test_freebsd_uses_native_commands(self):
        with mock.patch.object(utils.sys, 'platform', 'freebsd15'), \
                mock.patch.object(utils.os.path, 'realpath',
                                  return_value='/dev/cd12'), \
                mock.patch.object(utils.subprocess, 'check_output') as run:
            utils.load_device('/dev/cdrom')
            utils.eject_device('/dev/cdrom')
        self.assertEqual(run.call_args_list, [
            mock.call(['camcontrol', 'load', 'cd12'],
                      stderr=subprocess.STDOUT),
            mock.call(['camcontrol', 'eject', 'cd12'],
                      stderr=subprocess.STDOUT)])

    def test_freebsd_falls_back_when_camcontrol_fails(self):
        for failure in (FileNotFoundError(),
                        subprocess.CalledProcessError(1, ['camcontrol'])):
            with self.subTest(failure=type(failure).__name__), \
                    mock.patch.object(utils.sys, 'platform', 'freebsd15'), \
                    mock.patch.object(utils.subprocess, 'check_output',
                                      side_effect=[failure, b'']) as run:
                utils.load_device('/dev/cd0')
                self.assertEqual(run.call_args_list[-1], mock.call(
                    ['eject', '-t', '/dev/cd0'], stderr=subprocess.STDOUT))

    def test_missing_freebsd_helpers_warn(self):
        with mock.patch.object(utils.sys, 'platform', 'freebsd15'), \
                mock.patch.object(utils.subprocess, 'check_output',
                                  side_effect=FileNotFoundError()), \
                self.assertLogs(utils.logger, level='WARNING'):
            utils.load_device('/dev/cd0')
            utils.eject_device('/dev/cd0')

    def test_other_platforms_keep_eject_and_missing_binary_error(self):
        for platform in ('linux', 'darwin', 'openbsd7'):
            with self.subTest(platform=platform), \
                    mock.patch.object(utils.sys, 'platform', platform), \
                    mock.patch.object(utils.subprocess, 'check_output') as run:
                utils.load_device('/dev/sr0')
                run.assert_called_once_with(['eject', '-t', '/dev/sr0'],
                                            stderr=subprocess.STDOUT)
                run.side_effect = FileNotFoundError()
                with self.assertRaises(FileNotFoundError):
                    utils.eject_device('/dev/sr0')


class MountTest(unittest.TestCase):
    def test_freebsd_matches_complete_device_and_unmounts(self):
        for mounts, expected in ((b'/dev/cd10 /media cd9660 ro 0 0\n', 1),
                                 (b'/dev/cd1 /media cd9660 ro 0 0\n', 2)):
            with self.subTest(mounts=mounts), \
                    mock.patch.object(utils.sys, 'platform', 'freebsd15'), \
                    mock.patch.object(utils.os.path, 'realpath',
                                      return_value='/dev/cd1'), \
                    mock.patch.object(utils.subprocess, 'check_output',
                                      return_value=mounts) as run:
                utils.unmount_device('/dev/cdrom')
                self.assertEqual(run.call_count, expected)
                self.assertEqual(run.call_args_list[0],
                                 mock.call(['mount', '-p']))
                if expected == 2:
                    run.assert_called_with(['umount', '/dev/cd1'],
                                           stderr=subprocess.STDOUT)

    def test_freebsd_mount_and_unmount_failures_warn(self):
        for results in ([OSError('mount failed')],
                        [b'/dev/cd0 /media cd9660 ro 0 0\n',
                         subprocess.CalledProcessError(1, ['umount'])]):
            with mock.patch.object(utils.sys, 'platform', 'freebsd15'), \
                    mock.patch.object(utils.subprocess, 'check_output',
                                      side_effect=results), \
                    self.assertLogs(utils.logger, level='WARNING'):
                utils.unmount_device('/dev/cd0')

    def test_linux_keeps_proc_mounts(self):
        with mock.patch.object(utils.sys, 'platform', 'linux'), \
                mock.patch('builtins.open', mock.mock_open(
                    read_data='/dev/sr0 /media iso9660 ro 0 0\n')) as opened, \
                mock.patch.object(utils.os, 'system') as system, \
                mock.patch.object(utils.subprocess, 'check_output') as run:
            utils.unmount_device('/dev/sr0')
        opened.assert_called_once_with('/proc/mounts')
        system.assert_called_once_with('umount /dev/sr0')
        run.assert_not_called()


class CdrdaoTest(unittest.TestCase):
    def test_driver_is_freebsd_only(self):
        for platform in ('linux', 'freebsd15', 'darwin'):
            with self.subTest(platform=platform), \
                    mock.patch.object(cdrdao.sys, 'platform', platform):
                expected = ['cdrdao', 'read-toc', '--fast-toc']
                if platform == 'freebsd15':
                    expected += ['--driver', 'generic-mmc']
                expected += ['--device', '/dev/cd0', '/tmp/disc.toc']
                self.assertEqual(cdrdao.read_toc_command(
                    '/dev/cd0', True, '/tmp/disc.toc'), expected)
                with mock.patch.object(cdrdao, 'Popen') as popen:
                    popen.return_value.stdout.read.return_value = b''
                    cdrdao.DetectCdr('/dev/cd0')
                    command = popen.call_args[0][0]
                    self.assertEqual('--driver' in command,
                                     platform == 'freebsd15')

    def test_linux_and_freebsd_progress(self):
        for final in ('Leadout AUDIO 1 72:45:52(327427)',
                      'Reading of toc data finished successfully.'):
            parser = cdrdao.ProgressParser()
            parser.parse('Analyzing track 24 (AUDIO): start 68:34:30, '
                         'length 04:09:22')
            parser.parse('24 18697 308580 68:36:30')
            parser.parse(final)
            self.assertEqual(parser.tracks, 24)

    def test_usage_exit_codes_and_unrecognized_output(self):
        for code, output, expected in (
                (0, b'Cdrdao version 1.2.5 - test', '1.2.5'),
                (1, b'Cdrdao version 1.2.5 - test', '1.2.5'),
                (2, b'Cdrdao version 1.2.5 - test', None),
                (0, b'unrecognized output', None)):
            with mock.patch.object(cdrdao, 'Popen') as popen:
                popen.return_value.returncode = code
                popen.return_value.communicate.return_value = (b'', output)
                self.assertEqual(cdrdao.version(), expected)
