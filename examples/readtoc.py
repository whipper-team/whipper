# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import re
import os
import subprocess

from morituri.common import task
from morituri.extern import asyncsub

states = ['START', 'TRACK', 'LEADOUT', 'DONE']

_ANALYZING_RE = re.compile(r'^Analyzing track (\d+).*')
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

class ReadTOCTask(task.Task):
    """
    I am a task that reads the TOC of a CD, including pregaps.
    """

    description = "Reading TOC..."


    def __init__(self):
        self._buffer = "" # accumulate characters
        self._lines = [] # accumulate lines
        self._lineIndex = 0 # where we are
        self._state = 'START'
        self._frames = None # number of frames
        self._starts = [] # start of each track, in frames
        self._track = None # which track are we analyzing?

    def start(self, runner):
        task.Task.start(self, runner)

        # FIXME: create a temporary file instead
        if os.path.exists('/tmp/toc'):
            os.unlink('/tmp/toc')

        bufsize = 1024
        self._popen = asyncsub.Popen(["cdrdao", "read-toc", "/tmp/toc"],
                  bufsize=bufsize,
                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, close_fds=True)

        self.runner.schedule(1.0, self._read, runner)

    def _read(self, runner):
        ret = self._popen.recv_err()
        if not ret:
            # FIXME: handle done
            self.setProgress(1.0)
            print
            print 'done'
            self.stop()
            return

        self._buffer += ret

        # find counter in LEADOUT state
        if self._buffer and  self._state == 'LEADOUT':
            times = self._buffer.split('\r')
            position = ""
            while len(position) != 8:
                position = times.pop()

            frame = self._starts[self._track - 1] \
                + int(position[0:2]) * 60 * 75 \
                + int(position[3:5]) * 75 \
                + int(position[6:8])
            self.setProgress(float(frame) / self._frames)

        if "\n" in self._buffer:
            lines = self._buffer.split('\n')
            if lines[-1] != "\n":
                # last line didn't end yet
                self._buffer = lines[-1]
                del lines[-1]
            else:
                self._buffer = ""
            self._parse(lines)
            self._lines.extend(lines)

        self.runner.schedule(1.0, self._read, runner)

    def _parse(self, lines):
        for line in lines:
            #print 'parsing', len(line), line
            methodName = "_parse_" + self._state
            getattr(self, methodName)(line)

    def _parse_START(self, line):
        if line == "Track   Mode    Flags  Start                Length":
            #print 'Found track line'
            self._state = 'TRACK'

    def _parse_TRACK(self, line):
        if line.startswith('---'):
            return

        m = _TRACK_RE.search(line)
        if m:
            self._tracks = int(m.group('track'))
            self._starts.append(int(m.group('start')))

        m = _LEADOUT_RE.search(line)
        if m:
            self._state = 'LEADOUT'
            self._frames = int(m.group('start'))
            return

        self._tracks = int(line[:2])
        #print '%d tracks found' % self._tracks

    def _parse_LEADOUT(self, line):
        m = _ANALYZING_RE.search(line)
        if m:
            track = int(m.expand('\\1'))
            self.description = 'Analyzing track %d...' % track
            self._track = track
            #self.setProgress(float(track - 1) / self._tracks)
            #print 'analyzing', track


def main():
    runner = task.SyncRunner()
    t = ReadTOCTask()
    runner.run(t)

main()
