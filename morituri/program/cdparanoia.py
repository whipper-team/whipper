# -*- Mode: Python; test-case-name: morituri.test.test_program_cdparanoia -*-
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
import subprocess

from morituri.common import task, log, common
from morituri.extern import asyncsub

_PROGRESS_RE = re.compile(r"""
    ^\#\#: (?P<code>.+)\s      # function code
    \[(?P<function>.*)\]\s@\s     # function name
    (?P<offset>\d+)        # offset
""", re.VERBOSE)

# from reading cdparanoia source code, it looks like offset is reported in
# number of single-channel samples, ie. 2 bytes per unit
class ProgressParser(object):
    read = 0

    def parse(self, line):
        """
        Parse a line.
        """
        m = _PROGRESS_RE.search(line)
        if m:
            code = int(m.group('code'))
            function = m.group('function')
            offset = int(m.group('offset'))
            if function == 'read':
                if offset % 1176 != 0:
                    print 'THOMAS: not a multiple of 2532', offset
                    print line
                else:
                    self.read = offset / 1176

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
        self._parser = ProgressParser()

        self._buffer = "" # accumulate characters
        self._errors = []

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
                
            self.stop()
            return
