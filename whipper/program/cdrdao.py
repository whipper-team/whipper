import os
import re
import shutil
import tempfile
from subprocess import Popen, PIPE

from whipper.common.common import EjectError, truncate_filename
from whipper.image.toc import TocFile

import logging
logger = logging.getLogger(__name__)

CDRDAO = 'cdrdao'


def read_toc(device, fast_toc=False, toc_bpath=None, toc_fpath=None):
    """
    Return cdrdao-generated table of contents for 'device'.
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
    if toc_fpath is not None:
        t_comp = os.path.abspath(toc_fpath).split(os.sep)
        t_dirn = os.sep.join(t_comp[:-1])
        # If the output path doesn't exist, make it recursively
        if not os.path.isdir(t_dirn):
            os.makedirs(t_dirn)
        t_dst = truncate_filename(os.path.join(t_dirn, t_comp[-1] + '.toc'))
        shutil.copy(tocfile, os.path.join(t_dirn, t_dst))
    os.unlink(tocfile)
    return toc


def DetectCdr(device):
    """
    Return whether cdrdao detects a CD-R for 'device'.
    """
    cmd = [CDRDAO, 'disk-info', '-v1', '--device', device]
    logger.debug("executing %r", cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    if 'CD-R medium          : n/a' in p.stdout.read():
        return False
    else:
        return True


def version():
    """
    Return cdrdao version as a string.
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
    """
    stopgap morituri-insanity compatibility layer
    """
    return read_toc(device, fast_toc=True)


def ReadTableTask(device, toc_bpath=None, toc_fpath=None):
    """
    stopgap morituri-insanity compatibility layer
    """
    return read_toc(device, toc_bpath=toc_bpath, toc_fpath=toc_fpath)


def getCDRDAOVersion():
    """
    stopgap morituri-insanity compatibility layer
    """
    return version()
