import os
import subprocess

import logging
logger = logging.getLogger(__name__)


def eject_device(device):
    """Eject the given device."""
    logger.debug("ejecting device %s", device)
    try:
        # `eject device` prints nothing to stdout
        subprocess.check_output(['eject', device], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.warning("command '%s' returned with exit code '%d' (%s)",
                       ' '.join(e.cmd), e.returncode, e.output.rstrip())


def load_device(device):
    """Load the given device."""
    logger.debug("loading (eject -t) device %s", device)
    try:
        # `eject -t device` prints nothing to stdout
        subprocess.check_output(['eject', '-t', device],
                                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.warning("command '%s' returned with exit code '%d' (%s)",
                       ' '.join(e.cmd), e.returncode, e.output.rstrip())


def unmount_device(device):
    """
    Unmount the given device if it is mounted.

    This usually happens with automounted data tracks.

    If the given device is a symlink, the target will be checked.
    """
    device = os.path.realpath(device)
    logger.debug('possibly unmount real path %r', device)
    proc = open('/proc/mounts').read()
    if device in proc:
        print('Device %s is mounted, unmounting' % device)
        os.system('umount %s' % device)
