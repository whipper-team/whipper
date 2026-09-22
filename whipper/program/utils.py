import os
import subprocess
import sys

import logging
logger = logging.getLogger(__name__)


def _freebsd_tray(device, action):
    """Use FreeBSD's native tray command, falling back to eject on failure."""
    periph = os.path.basename(os.path.realpath(device))
    try:
        subprocess.check_output(['camcontrol', action, periph],
                                stderr=subprocess.STDOUT)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        logger.warning('camcontrol %s failed for %s: %s', action, device, e)
        return False
    return True


def eject_device(device):
    """Eject the given device."""
    logger.debug("ejecting device %s", device)
    if sys.platform.startswith('freebsd') and _freebsd_tray(device, 'eject'):
        return
    try:
        # `eject device` prints nothing to stdout
        subprocess.check_output(['eject', device], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.warning("command '%s' returned with exit code '%d' (%s)",
                       ' '.join(e.cmd), e.returncode, e.output.rstrip())
    except FileNotFoundError:
        if not sys.platform.startswith('freebsd'):
            raise
        logger.warning('eject is unavailable; open the tray manually')


def load_device(device):
    """Load the given device."""
    logger.debug("loading (eject -t) device %s", device)
    if sys.platform.startswith('freebsd') and _freebsd_tray(device, 'load'):
        return
    try:
        # `eject -t device` prints nothing to stdout
        subprocess.check_output(['eject', '-t', device],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.warning("command '%s' returned with exit code '%d' (%s)",
                       ' '.join(e.cmd), e.returncode, e.output.rstrip())
    except FileNotFoundError:
        if not sys.platform.startswith('freebsd'):
            raise
        logger.warning('eject is unavailable; close the tray manually')


def unmount_device(device):
    """
    Unmount the given device if it is mounted.

    This usually happens with automounted data tracks.

    If the given device is a symlink, the target will be checked.
    """
    device = os.path.realpath(device)
    logger.debug('possibly unmount real path %r', device)
    if sys.platform.startswith('freebsd'):
        try:
            mounts = subprocess.check_output(['mount', '-p']).decode()
        except (OSError, subprocess.CalledProcessError) as e:
            logger.warning('cannot check mounts for %s: %s', device, e)
            return
        # mount -p uses fstab columns. Compare the complete device field,
        # so /dev/cd1 does not match /dev/cd10.
        mounted = any(line.split() and line.split()[0] == device
                      for line in mounts.splitlines())
    else:
        # Preserve the existing path on platforms other than FreeBSD.
        with open('/proc/mounts') as handle:
            mounted = device in handle.read()
    if mounted:
        print('Device %s is mounted, unmounting' % device)
        if sys.platform.startswith('freebsd'):
            try:
                subprocess.check_output(['umount', device],
                                        stderr=subprocess.STDOUT)
            except (OSError, subprocess.CalledProcessError) as e:
                logger.warning('cannot unmount %s: %s', device, e)
        else:
            os.system('umount %s' % device)
