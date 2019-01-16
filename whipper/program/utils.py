import os

import logging
logger = logging.getLogger(__name__)


def eject_device(device):
    """
    Eject the given device.
    """
    logger.debug("ejecting device %s", device)
    os.system('eject %s' % device)


def load_device(device):
    """
    Load the given device.
    """
    logger.debug("loading (eject -t) device %s", device)
    os.system('eject -t %s' % device)


def unmount_device(device):
    """
    Unmount the given device if it is mounted, as happens with automounted
    data tracks.

    If the given device is a symlink, the target will be checked.
    """
    device = os.path.realpath(device)
    logger.debug('possibly unmount real path %r', device)
    proc = open('/proc/mounts').read()
    if device in proc:
        print('Device %s is mounted, unmounting' % device)
        os.system('umount %s' % device)
