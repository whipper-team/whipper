import os
import re
import tempfile
from subprocess import Popen, PIPE

from whipper.common.common import EjectError
from whipper.image.toc import TocFile

import logging
logger = logging.getLogger(__name__)

CDRDAO = 'cdrdao'


def read_toc(device, fast_toc=False):
    """Get the cd's toc using cdrdao and parse it.

    :param device: optical disk drive.
    :type device:
    :param fast_toc: enable cdrdao's fast-toc option? (Default value = False)
    :type fast_toc: bool
    :returns:
    :rtype: TocFile
    """
    # cdrdao MUST be passed a non-existing filename as its last argument
    # to write the TOC to; it does not support writing to stdout or
    # overwriting an existing file, nor does linux seem to support
    # locking a non-existant file. Thus, this race-condition introducing
    # hack is carried from morituri to whipper and will be removed when
    # cdrdao is fixed.
    fd, tocfile = tempfile.mkstemp(suffix=u'.cdrdao.read-toc.whipper')
    os.close(fd)
    os.unlink(tocfile)

    cmd = [CDRDAO, 'read-toc'] + (['--fast-toc'] if fast_toc else []) + [
        '--device', device, tocfile]
    # PIPE is the closest to >/dev/null we can get
    logger.debug("executing %r", cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    _, stderr = p.communicate()
    if p.returncode != 0:
        msg = 'cdrdao read-toc failed: return code is non-zero: ' + \
              str(p.returncode)
        logger.critical(msg)
        # Gracefully handle missing disc
        if "ERROR: Unit not ready, giving up." in stderr:
            raise EjectError(device, "no disc detected")
        raise IOError(msg)

    toc = TocFile(tocfile)
    toc.parse()
    os.unlink(tocfile)
    return toc


def DetectCdr(device):
    """Check if inserted disk is a CD-R.

    :param device: optical disk drive.
    :type device:
    :returns: False if inserted disk is not a CD-R, True otherwise.
    :rtype: bool
    """
    cmd = [CDRDAO, 'disk-info', '-v1', '--device', device]
    logger.debug("executing %r", cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    if 'CD-R medium          : n/a' in p.stdout.read():
        return False
    else:
        return True


def version():
    """Detect cdrdao's version.

    :returns:
    :rtype:
    """
    cdrdao = Popen(CDRDAO, stderr=PIPE)
    out, err = cdrdao.communicate()
    if cdrdao.returncode != 1:
        logger.warning("cdrdao version detection failed: "
                       "return code is " + str(cdrdao.returncode))
        return None
    m = re.compile(r'^Cdrdao version (?P<version>.*) - \(C\)').search(
        err.decode('utf-8'))
    if not m:
        logger.warning("cdrdao version detection failed: "
                       "could not find version")
        return None
    return m.group('version')


def ReadTOCTask(device):
    """Stopgap morituri-insanity compatibility layer.

    :param device: optical disk drive.
    :type device:
    :returns:
    :rtype: TocFile
    """
    return read_toc(device, fast_toc=True)


def ReadTableTask(device):
    """Stopgap morituri-insanity compatibility layer.

    :param device: optical disk drive.
    :type device:
    :returns:
    :rtype: TocFile
    """
    return read_toc(device)


def getCDRDAOVersion():
    """Stopgap morituri-insanity compatibility layer.

    :returns:
    :rtype:
    """
    return version()
