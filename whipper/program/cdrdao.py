import os
import re
import tempfile
from subprocess import Popen, PIPE

from whipper.common import common
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


# Sample version string:
# Cdrdao version 1.2.3 - (C) Andreas Mueller <andreas@daneb.de>
_VERSION_RE = re.compile(
    r'^Cdrdao version (?P<major>.+)\.(?P<minor>.+)\.(?P<micro>.+) - \(C\)')


def getVersion():
    """Detect cdrdao's version.
      Cdrdao doesn't have a --version command - we call it with no parameters.

    :returns: Formatted cdrdao version string
    :rtype: string
    """
    getter = common.VersionGetter('cdrdao',
                                  [CDRDAO],
                                  _VERSION_RE,
                                  "%(major)s.%(minor)s.%(micro)s",
                                  stderr=True)

    return getter.get()


def getVersionWarnings():
    """Display any warnings based upon the detected cdrdao version number.

    :returns: Warning text specific to the detected CDRDAO version.
    :rtype: string
    """

    from pkg_resources import parse_version as V
    version = getVersion()
    if V(version) < V('1.2.3rc2'):
        return ('Warning: cdrdao older than 1.2.3 has a '
                'pre-gap length bug.\n'
                'See http://sourceforge.net/tracker/?func=detail&aid=604751&group_id=2171&atid=102171\n')  # noqa: E501
    else:
        return ''
