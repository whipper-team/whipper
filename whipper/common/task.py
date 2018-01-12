# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import signal
import subprocess

from whipper.extern import asyncsub
from whipper.extern.task import task

import logging
logger = logging.getLogger(__name__)


class SyncRunner(task.SyncRunner):
    pass


class LoggableTask(task.Task):
    pass


class LoggableMultiSeparateTask(task.MultiSeparateTask):
    pass


class PopenTask(task.Task):
    """I am a task that runs a command using Popen."""

    logCategory = 'PopenTask'
    bufsize = 1024
    command = None
    cwd = None

    def start(self, runner):
        task.Task.start(self, runner)

        try:
            self._popen = asyncsub.Popen(self.command,
                                         bufsize=self.bufsize,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         close_fds=True, cwd=self.cwd)
        except OSError as e:
            import errno
            if e.errno == errno.ENOENT:
                self.commandMissing()

            raise

        logger.debug('Started %r with pid %d', self.command,
                     self._popen.pid)

        self.schedule(1.0, self._read, runner)

    def _read(self, runner):
        try:
            read = False

            ret = self._popen.recv()

            if ret:
                logger.debug("read from stdout: %s", ret)
                self.readbytesout(ret)
                read = True

            ret = self._popen.recv_err()

            if ret:
                logger.debug("read from stderr: %s", ret)
                self.readbyteserr(ret)
                read = True

            # if we read anything, we might have more to read, so
            # reschedule immediately
            if read and self.runner:
                self.schedule(0.0, self._read, runner)
                return

            # if we didn't read anything, give the command more time to
            # produce output
            if self._popen.poll() is None and self.runner:
                # not finished yet
                self.schedule(1.0, self._read, runner)
                return

            self._done()
        except Exception as e:
            logger.debug('exception during _read(): %r', str(e))
            self.setException(e)
            self.stop()

    def _done(self):
        assert self._popen.returncode is not None, "No returncode"

        if self._popen.returncode >= 0:
            logger.debug('Return code was %d', self._popen.returncode)
        else:
            logger.debug('Terminated with signal %d',
                         -self._popen.returncode)

        self.setProgress(1.0)

        if self._popen.returncode != 0:
            self.failed()
        else:
            self.done()

        self.stop()
        return

    def abort(self):
        logger.debug('Aborting, sending SIGTERM to %d', self._popen.pid)
        os.kill(self._popen.pid, signal.SIGTERM)
        # self.stop()

    def readbytesout(self, bytes):
        """Call when bytes have been read from stdout.

        :param bytes:
        :type bytes:
        """
        pass

    def readbyteserr(self, bytes):
        """Call when bytes have been read from stderr.

        :param bytes:
        :type bytes:
        """
        pass

    def done(self):
        """Call when the command completed successfully."""
        pass

    def failed(self):
        """Call when the command failed."""
        pass

    def commandMissing(self):
        """Call when the command is missing."""
        pass
