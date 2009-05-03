# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of morituri.
# 
# morituri is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# morituri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with morituri.  If not, see <http://www.gnu.org/licenses/>.


import re
import os
import subprocess
import tempfile

from morituri.common import task, log
from morituri.image import toc, table
from morituri.extern import asyncsub

states = ['START', 'TRACK', 'LEADOUT', 'DONE']

_ANALYZING_RE = re.compile(r'^Analyzing track (?P<track>\d+).*')
_TRACK_RE = re.compile(r"""
    ^(?P<track>[\d\s]{2})\s+ # Track
    (?P<mode>\w+)\s+         # Mode; AUDIO
    \d\s+                    # Flags
    \d\d:\d\d:\d\d           # Start in HH:MM:FF
    \((?P<start>.+)\)\s+     # Start in frames
    \d\d:\d\d:\d\d           # Length in HH:MM:FF
    \((?P<length>.+)\)       # Length in frames
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

    @ivar toc: the .toc object
    @type toc: L{toc.TOC}
    """

    description = "Reading TOC..."


    def __init__(self):
        self._buffer = "" # accumulate characters
        self._lines = [] # accumulate lines
        self._errors = [] # accumulate error lines
        self._lineIndex = 0 # where we are
        self._state = 'START'
        self._frames = None # number of frames
        self._starts = [] # start of each track, in frames
        self._track = None # which track are we analyzing?
        self._toc = None # path to temporary .toc file

        self.toc = None # result

    def start(self, runner):
        task.Task.start(self, runner)

        # FIXME: create a temporary file instead
        (fd, self._toc) = tempfile.mkstemp(suffix='.morituri')
        os.close(fd)
        os.unlink(self._toc)

        bufsize = 1024
        self._popen = asyncsub.Popen(["cdrdao", "read-toc", self._toc],
                  bufsize=bufsize,
                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, close_fds=True)

        self.runner.schedule(1.0, self._read, runner)

    def _read(self, runner):
        ret = self._popen.recv_err()
        self.log(ret)
        if not ret:
            # could be finished now
            self.runner.schedule(1.0, self._poll, runner)
            return

        self._buffer += ret

        # find counter in LEADOUT state
        if self._buffer and  self._state == 'LEADOUT':
            # split on lines that end in \r, which reset cursor to counter start
            # this misses the first one, but that's ok:
            # length 03:40:71...\n00:01:00
            times = self._buffer.split('\r')
            position = ""
            while times and len(position) != 8:
                position = times.pop()

            # we need both a position reported and an Analyzing line
            # to have been parsed to report progress
            if position and self._track is not None:
                frame = self._starts[self._track - 1]  or 0 \
                    + int(position[0:2]) * 60 * 75 \
                    + int(position[3:5]) * 75 \
                    + int(position[6:8])
                self.setProgress(float(frame) / self._frames)

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
                self.log('Parsing %s', line)
                if line.startswith('ERROR:'):
                    self._errors.append(line)

            self._parse(lines)
            self._lines.extend(lines)

        self.runner.schedule(1.0, self._read, runner)

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
                self.toc = toc.TOC(self._toc)
                self.toc.parse()
                os.unlink(self._toc)
                
            self.stop()
            return

    def _parse(self, lines):
        for line in lines:
            #print 'parsing', len(line), line
            methodName = "_parse_" + self._state
            getattr(self, methodName)(line)

    def _parse_START(self, line):
        if line.startswith('Track'):
            self.debug('Found possible track line')
        if line == "Track   Mode    Flags  Start                Length":
            self.debug('Found track line, moving to TRACK state')
            self._state = 'TRACK'

    def _parse_TRACK(self, line):
        if line.startswith('---'):
            return

        m = _TRACK_RE.search(line)
        if m:
            self._tracks = int(m.group('track'))
            self._starts.append(int(m.group('start')))
            self.debug('Found track %d', self._tracks)

        m = _LEADOUT_RE.search(line)
        if m:
            self.debug('Found leadout line, moving to LEADOUT state')
            self._state = 'LEADOUT'
            self._frames = int(m.group('start'))
            self.debug('Found leadout at offset %r', self._frames)
            self.info('%d tracks found', self._tracks)
            return


    def _parse_LEADOUT(self, line):
        m = _ANALYZING_RE.search(line)
        if m:
            self.debug('Found analyzing line')
            track = int(m.group('track'))
            self.description = 'Analyzing track %d...' % track
            self._track = track
            #self.setProgress(float(track - 1) / self._tracks)
            #print 'analyzing', track

class ReadTableTask(task.Task):
    """
    I am a task that reads the TOC of a CD, without pregaps.
    """

    description = "Reading TOC..."


    def __init__(self):
        self._buffer = "" # accumulate characters
        self._lines = [] # accumulate lines
        self._errors = [] # accumulate error lines
        self._lineIndex = 0 # where we are
        self._state = 'START'
        self._frames = None # number of frames
        self._starts = [] # start of each track, in frames
        self._track = None # which track are we analyzing?
        self._toc = None # path to temporary .toc file
        self._table = table.Table()

        self.toc = None # result

    def start(self, runner):
        task.Task.start(self, runner)

        # FIXME: create a temporary file instead
        (fd, self._toc) = tempfile.mkstemp(suffix='.morituri')
        os.close(fd)
        os.unlink(self._toc)

        bufsize = 1024
        self._popen = asyncsub.Popen(["cdrdao", "read-toc", "--fast-toc",
            self._toc],
                  bufsize=bufsize,
                  stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE, close_fds=True)

        self.runner.schedule(1.0, self._read, runner)

    def _read(self, runner):
        ret = self._popen.recv_err()
        self.log(ret)
        if not ret:
            # could be finished now
            self.runner.schedule(1.0, self._poll, runner)
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
                self.log('Parsing %s', line)
                if line.startswith('ERROR:'):
                    self._errors.append(line)

            self._parse(lines)
            self._lines.extend(lines)

        self.runner.schedule(1.0, self._read, runner)

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
                self.table = self._table
                os.unlink(self._toc)
                
            self.stop()
            return

    def _parse(self, lines):
        for line in lines:
            methodName = "_parse_" + self._state
            getattr(self, methodName)(line)

    def _parse_START(self, line):
        if line.startswith('Track'):
            self.debug('Found possible track line')
        if line == "Track   Mode    Flags  Start                Length":
            self.debug('Found track line, moving to TRACK state')
            self._state = 'TRACK'

    def _parse_TRACK(self, line):
        if line.startswith('---'):
            return

        m = _TRACK_RE.search(line)
        if m:
            self._tracks = int(m.group('track'))
            start = int(m.group('start'))
            self._starts.append(start)
            mode = m.group('mode')
            length = int(m.group('length'))
            self.debug('Found track %d', self._tracks)
            track = table.Track(self._tracks, start, start + length - 1,
                mode == "AUDIO") 
            self.debug('Track %d, start offset %d, length %d',
                self._tracks, start, length)
            self._table.tracks.append(track)
