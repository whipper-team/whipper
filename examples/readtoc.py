# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import subprocess

from morituri.common import task
from morituri.extern import asyncsub

class ReadTOCTask(task.Task):
    """
    I am a task that reads the TOC of a CD, including pregaps.
    """

    description = "Reading TOC..."

    def start(self, runner):
        task.Task.start(self, runner)

        if os.path.exists('/tmp/toc'):
            os.unlink('/tmp/toc')

        bufsize = 1024
        self._popen = asyncsub.Popen(["cdrdao", "read-toc", "/tmp/toc"],
                  bufsize=bufsize,
                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, close_fds=True)

        self.runner.schedule(1.0, self._read, runner)

    def _read(self, runner):
        print self._popen.recv_err()
        self.runner.schedule(1.0, self._read, runner)


def main():
    runner = task.SyncRunner()
    t = ReadTOCTask()
    runner.run(t)

main()
