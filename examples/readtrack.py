# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import re
import os
import subprocess
import tempfile

from morituri.common import task, log, common
from morituri.image import toc
from morituri.program import cdparanoia
from morituri.extern import asyncsub

states = ['START', 'TRACK', 'LEADOUT', 'DONE']

_ANALYZING_RE = re.compile(r'^Analyzing track (?P<track>\d+).*')
_TRACK_RE = re.compile(r"""
    ^(?P<track>[\d\s]{2})\s+ # Track
    \w+\s+                   # Mode
    \d\s+                    # Flags
    \d\d:\d\d:\d\d           # Start in HH:MM:FF
    \((?P<start>.+)\)\s+     # Start in frames
    \d\d:\d\d:\d\d           # Length in HH:MM:FF
    \(.+\)                   # Length in frames
""", re.VERBOSE)
_LEADOUT_RE = re.compile(r"""
    ^Leadout\s
    \w+\s+               # Mode
    \d\s+                # Flags
    \d\d:\d\d:\d\d       # Start in HH:MM:FF
    \((?P<start>.+)\)    # Start in frames
""", re.VERBOSE)

# FIXME: handle errors

class ReadTrackTask(task.Task):
    """
    I am a task that reads a track using cdparanoia.
    """

    description = "Reading Track..."


    def __init__(self, path, start, stop, offset=0):
        """
        Read the given track.

        @param path:   where to store the ripped track
        @type  path:   str
        @param start:  first frame to rip
        @type  start:  int
        @param stop:   last frame to rip (inclusive)
        @type  stop:   int
        @param offset: read offset, in samples
        @type  offset: int
        """
        self.path = path
        self._start = start
        self._stop = stop
        self._offset = offset
        self._parser = cdparanoia.ProgressParser()

        self._buffer = "" # accumulate characters

    def start(self, runner):
        task.Task.start(self, runner)

        bufsize = 1024
        argv = ["cdparanoia",
            "--sample-offset=%d" % self._offset,
            "--stderr-progress",
            "[%s]-[%s]" % (
                common.framesToHMSF(self._start),
                common.framesToHMSF(self._stop)), self.path]
        self.debug('Running %s' % (" ".join(argv), ))
        self._popen = asyncsub.Popen(argv,
            bufsize=bufsize,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True)

        self.runner.schedule(1.0, self._read, runner)

    def _read(self, runner):
        ret = self._popen.recv_err()
        if not ret:
            if self._popen.poll() is not None:
                self._done()
                return
            self.runner.schedule(0.01, self._read, runner)
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
                self._parser.parse(line)
            # FIXME: self._parser.read *will* go past self._stop,
            # and only indicates read frames, not written frames.
            # but we can't rely on anything else.
            num = float(self._parser.read) - self._start
            den = float(self._stop) - self._start
            progress = num / den
            if progress < 1.0:
                self.setProgress(progress)

        # 0 does not give us output before we complete, 1.0 gives us output
        # too late
        self.runner.schedule(0.01, self._read, runner)

    def _poll(self, runner):
        if self._popen.poll() is None:
            self.runner.schedule(1.0, self._poll, runner)
            return

        self._done()

    def _done(self):
            self.setProgress(1.0)
            if self._popen.returncode != 0:
                if self._errors:
                    print "\n".join(self._errors)
                else:
                    print 'ERROR: exit code %r' % self._popen.returncode
            else:
                print
                print 'done'
                
            self.stop()
            return

def main():
    log.init()
    runner = task.SyncRunner()
    t = ReadTrackTask('/tmp/track.wav', 1000, 3000, offset=0)
    runner.run(t)
    print 'runner done'


main()
