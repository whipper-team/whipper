import sys
import os
import re
import shutil
import tempfile
from subprocess import Popen, PIPE

from whipper.common.common import truncate_filename
from whipper.image.toc import TocFile
from whipper.extern.task import task
from whipper.extern import asyncsub

import logging
logger = logging.getLogger(__name__)

CDRDAO = 'cdrdao'

class ReadTOCTask(task.Task):
    """
    Task that reads the TOC of the disc using cdrdao
    """
    description = "Reading TOC"
    toc = None
    
    def __init__(self, device, fast_toc=False, toc_path=None):
        """
        Read the TOC for 'device'.
        @device: path of device
        @type device: str
        @param fast_toc: use cdrdao fast-toc mode
        @type fast_toc: bool
        @param toc_path: Where to save the generated table of contents
        @type str
        """
        
        self.device = device
        self.fast_toc = fast_toc
        self.toc_path = toc_path
        
    def start(self, runner):
        task.Task.start(self, runner)

        cmd = [CDRDAO, 'read-toc'] + (['--fast-toc'] if fast_toc else []) + [
            '--device', device, tocfile]
        
        self._popen = asyncsub.Popen(cmd,
                                     bufsize=1024,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     close_fds=True)
        def _read(self, runner):
            ret = self._popen.recv_err()
            if not ret:
                if self._popen.poll() is not None:
                    self._done()
                    return
                self.schedule(0.01, self._read, runner)
                return
            self._buffer += ret
            
            # parse buffer into lines if possible, and parse them
            if "\n" in self._buffer:
                 lines = self._buffer.split('\n')
                if lines[-1] != "\n":
                    # last line didn't end yet
                    self._buffer = lines[-1]
                    del lines[-1]
                else:
                    self._buffer = ""

                for line in lines:
                    sys.stdout.write("%s\n" % line)

                progress = float(num) / float(den)
                if progress < 1.0:
                    self.setProgress(progress)
            
            # 0 does not give us output before we complete, 1.0 gives us output
            # too late
            self.schedule(0.01, self._read, runner)


    def _poll(self, runner):
        if self._popen.poll() is None:
            self.schedule(1.0, self._poll, runner)
            return

        self._done()


    def _done(self):
        self.setProgress(1.0)

        self.stop()
        return

def read_toc(device, fast_toc=False, toc_path=None):
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
    if toc_path is not None:
        t_comp = os.path.abspath(toc_path).split(os.sep)
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
                       "return code is %s", cdrdao.returncode)
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


def ReadTableTask(device, toc_path=None):
    """
    stopgap morituri-insanity compatibility layer
    """
    return read_toc(device, toc_path=toc_path)


def getCDRDAOVersion():
    """
    stopgap morituri-insanity compatibility layer
    """
    return version()
