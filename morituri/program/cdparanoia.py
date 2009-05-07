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

import os
import re
import stat
import shutil
import subprocess
import tempfile

from morituri.common import task, log, common, checksum
from morituri.extern import asyncsub

class FileSizeError(Exception):
    """
    The given path does not have the expected size.
    """
    def __init__(self, path):
        self.args = (path, )
        self.path = path

class ReturnCodeError(Exception):
    """
    The program had a non-zero return code.
    """
    def __init__(self, returncode):
        self.args = (returncode, )
        self.returncode = returncode

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

    description = "Reading Track"


    def __init__(self, path, table, start, stop, offset=0):
        """
        Read the given track.

        @param path:   where to store the ripped track
        @type  path:   str
        @param table:  table of contents of CD
        @type  table:  L{table.IndexTable}
        @param start:  first frame to rip
        @type  start:  int
        @param stop:   last frame to rip (inclusive)
        @type  stop:   int
        @param offset: read offset, in samples
        @type  offset: int
        """
        self.path = path
        self._table = table
        self._start = start
        self._stop = stop
        self._offset = offset
        self._parser = ProgressParser()

        self._buffer = "" # accumulate characters
        self._errors = []

    def start(self, runner):
        task.Task.start(self, runner)

        # find on which track the range starts and stops
        startTrack = 1
        startOffset = 0
        stopTrack = 1
        stopOffset = self._stop

        for i, t in enumerate(self._table.tracks):
            if self._table.getTrackStart(i + 1) <= self._start:
                startTrack = i + 1
                startOffset = self._start - self._table.getTrackStart(i + 1)
            if self._table.getTrackEnd(i + 1) <= self._stop:
                stopTrack = i + 1
                stopOffset = self._stop - self._table.getTrackStart(i + 1)

        self.debug('Ripping from %d to %d (inclusive)', self._start, self._stop)
        self.debug('Starting at track %d, offset %d', startTrack, startOffset)
        self.debug('Stopping at track %d, offset %d', stopTrack, stopOffset)

        bufsize = 1024
        argv = ["cdparanoia",
            "--sample-offset=%d" % self._offset,
            "--stderr-progress",
            "%d[%s]-%d[%s]" % (
                startTrack, common.framesToHMSF(startOffset),
                stopTrack, common.framesToHMSF(stopOffset)),
            self.path]
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

        # check if the length matches
        size = os.stat(self.path)[stat.ST_SIZE]
        # wav header is 44 bytes
        offsetLength = self._stop - self._start + 1
        expected = offsetLength * checksum.BYTES_PER_FRAME + 44
        if size != expected:
            # FIXME: handle errors better
            self.warning('file size %d did not match expected size %d',
                size, expected)
            if (size - expected) % checksum.BYTES_PER_FRAME == 0:
                print 'ERROR: %d frames difference' % (
                    (size - expected) / checksum.BYTES_PER_FRAME)

            self.exception = FileSizeError(self.path)

        if not self.exception and self._popen.returncode != 0:
            if self._errors:
                print "\n".join(self._errors)
            else:
                self.warning('exit code %r', self._popen.returncode)
                self.exception = ReturnCodeError(self._popen.returncode)
            
        self.stop()
        return

class ReadVerifyTrackTask(task.MultiSeparateTask):
    """
    I am a task that reads and verifies a track using cdparanoia.

    @ivar path:     the path where the file is to be stored.
    @ivar checksum: the checksum of the track.
    """

    def __init__(self, path, table, start, stop, offset=0):
        """
        @param path:   where to store the ripped track
        @type  path:   str
        @param table:  table of contents of CD
        @type  table:  L{table.Table}
        @param start:  first frame to rip
        @type  start:  int
        @param stop:   last frame to rip (inclusive)
        @type  stop:   int
        @param offset: read offset, in samples
        @type  offset: int
        """

        self.path = path

        # FIXME: choose a dir on the same disk/dir as the final path
        fd, tmppath = tempfile.mkstemp(suffix='.morituri.wav')
        os.close(fd)
        self._tmppath = tmppath

        self.tasks = []
        self.tasks.append(
            ReadTrackTask(tmppath, table, start, stop, offset))
        self.tasks.append(
            checksum.CRC32Task(tmppath))
        t = ReadTrackTask(tmppath, table, start, stop, offset)
        t.description = 'Verifying track...'
        self.tasks.append(
            ReadTrackTask(tmppath, table, start, stop, offset))
        self.tasks.append(
            checksum.CRC32Task(tmppath))

        self.checksum = None

    def stop(self):
        if not self.exception:
            c1 = self.tasks[1].checksum
            c2 = self.tasks[3].checksum
            if c1 == c2:
                self.info('Checksums match, %08x' % c1)
                try:
                    shutil.move(self._tmppath, self.path)
                    self.checksum = checksum
                except Exception, e:
                    self._exception = e
            else:
                print 'ERROR: read and verify failed'
                self.checksum = None

        task.MultiSeparateTask.stop(self)
