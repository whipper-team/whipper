# -*- Mode: Python; test-case-name:morituri.test.test_program_cdrdao -*-
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
import signal
import subprocess
import tempfile

from morituri.common import log, common
from morituri.image import toc, table

from morituri.extern import asyncsub
from morituri.extern.task import task


class ProgramError(Exception):
    """
    The program had a fatal error.
    """

    def __init__(self, errorMessage):
        self.args = (errorMessage, )
        self.errorMessage = errorMessage

states = ['START', 'TRACK', 'LEADOUT', 'DONE']

_VERSION_RE = re.compile(r'^Cdrdao version (?P<version>.*) - \(C\)')

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

_POSITION_RE = re.compile(r"""
    ^(?P<hh>\d\d):       # HH
    (?P<mm>\d\d):        # MM
    (?P<ss>\d\d)         # SS
""", re.VERBOSE)

_ERROR_RE = re.compile(r"""^ERROR: (?P<error>.*)""")


class LineParser(object, log.Loggable):
    """
    Parse incoming bytes into lines
    Calls 'parse' on owner for each parsed line.
    """

    def __init__(self, owner):
        self._buffer = ""     # accumulate characters
        self._lines = []      # accumulate lines
        self._owner = owner

    def read(self, bytes):
        self.log('received %d bytes', len(bytes))
        self._buffer += bytes

        # parse buffer into lines if possible, and parse them
        if "\n" in self._buffer:
            self.log('buffer has newline, splitting')
            lines = self._buffer.split('\n')
            if lines[-1] != "\n":
                # last line didn't end yet
                self.log('last line still in progress')
                self._buffer = lines[-1]
                del lines[-1]
            else:
                self.log('last line finished, resetting buffer')
                self._buffer = ""

            for line in lines:
                self.log('Parsing %s', line)
                self._owner.parse(line)

            self._lines.extend(lines)


class OutputParser(object, log.Loggable):

    def __init__(self, taskk, session=None):
        self._buffer = ""     # accumulate characters
        self._lines = []      # accumulate lines
        self._state = 'START'
        self._frames = None   # number of frames
        self.track = 0        # which track are we analyzing?
        self._task = taskk
        self.tracks = 0      # count of tracks, relative to session
        self._session = session


        self.table = table.Table() # the index table for the TOC
        self.version = None # cdrdao version

    def read(self, bytes):
        self.log('received %d bytes in state %s', len(bytes), self._state)
        self._buffer += bytes

        # find counter in LEADOUT state; only when we read full toc
        self.log('state: %s, buffer bytes: %d', self._state, len(self._buffer))
        if self._buffer and self._state == 'LEADOUT':
            # split on lines that end in \r, which reset cursor to counter
            # start
            # this misses the first one, but that's ok:
            # length 03:40:71...\n00:01:00
            times = self._buffer.split('\r')
            # counter ends in \r, so the last one would be empty
            if not times[-1]:
                del times[-1]

            position = ""
            m = None
            while times and not m:
                position = times.pop()
                m = _POSITION_RE.search(position)

            # we need both a position reported and an Analyzing line
            # to have been parsed to report progress
            if m and self.track is not None:
                track = self.table.tracks[self.track - 1]
                frame = (track.getIndex(1).absolute or 0) \
                    + int(m.group('hh')) * 60 * common.FRAMES_PER_SECOND \
                    + int(m.group('mm')) * common.FRAMES_PER_SECOND \
                    + int(m.group('ss'))
                self.log('at frame %d of %d', frame, self._frames)
                self._task.setProgress(float(frame) / self._frames)

        # parse buffer into lines if possible, and parse them
        if "\n" in self._buffer:
            self.log('buffer has newline, splitting')
            lines = self._buffer.split('\n')
            if lines[-1] != "\n":
                # last line didn't end yet
                self.log('last line still in progress')
                self._buffer = lines[-1]
                del lines[-1]
            else:
                self.log('last line finished, resetting buffer')
                self._buffer = ""
            for line in lines:
                self.log('Parsing %s', line)
                m = _ERROR_RE.search(line)
                if m:
                    error = m.group('error')
                    self._task.errors.append(error)
                    self.debug('Found ERROR: output: %s', error)
                    self._task.exception = ProgramError(error)
                    self._task.abort()
                    return

            self._parse(lines)
            self._lines.extend(lines)

    def _parse(self, lines):
        for line in lines:
            #print 'parsing', len(line), line
            methodName = "_parse_" + self._state
            getattr(self, methodName)(line)

    def _parse_START(self, line):
        if line.startswith('Cdrdao version'):
            m = _VERSION_RE.search(line)
            self.version = m.group('version')

        if line.startswith('Track'):
            self.debug('Found possible track line')
            if line == "Track   Mode    Flags  Start                Length":
                self.debug('Found track line, moving to TRACK state')
                self._state = 'TRACK'
                return

        m = _ERROR_RE.search(line)
        if m:
            error = m.group('error')
            self._task.errors.append(error)

    def _parse_TRACK(self, line):
        if line.startswith('---'):
            return

        m = _TRACK_RE.search(line)
        if m:
            t = int(m.group('track'))
            self.tracks += 1
            track = table.Track(self.tracks, session=self._session)
            track.index(1, absolute=int(m.group('start')))
            self.table.tracks.append(track)
            self.debug('Found absolute track %d, session-relative %d', t,
                self.tracks)

        m = _LEADOUT_RE.search(line)
        if m:
            self.debug('Found leadout line, moving to LEADOUT state')
            self._state = 'LEADOUT'
            self._frames = int(m.group('start'))
            self.debug('Found absolute leadout at offset %r', self._frames)
            self.info('%d tracks found for this session', self.tracks)
            return

    def _parse_LEADOUT(self, line):
        m = _ANALYZING_RE.search(line)
        if m:
            self.debug('Found analyzing line')
            track = int(m.group('track'))
            self.description = 'Analyzing track %d...' % track
            self.track = track


# FIXME: handle errors


class CDRDAOTask(task.Task):
    """
    I am a task base class that runs CDRDAO.
    """

    logCategory = 'CDRDAOTask'
    description = "Reading TOC..."
    options = None

    def __init__(self):
        self.errors = []
        self.debug('creating CDRDAOTask')

    def start(self, runner):
        task.Task.start(self, runner)

        bufsize = 1024
        try:
            self._popen = asyncsub.Popen(["cdrdao", ] + self.options,
                bufsize=bufsize,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True)
        except OSError, e:
            import errno
            if e.errno == errno.ENOENT:
                raise common.MissingDependencyException('cdrdao')

            raise

        self.debug('Started cdrdao with pid %d and options %r',
            self._popen.pid, self.options)
        self.debug('command: cdrdao %s', ' '.join(self.options))

        self.schedule(1.0, self._read, runner)

    def _read(self, runner):
        try:
            ret = self._popen.recv()

            if ret:
                self.log("read from stdout: %s", ret)
                self.readbytesout(ret)

            ret = self._popen.recv_err()

            if ret:
                self.log("read from stderr: %s", ret)
                self.readbyteserr(ret)

            if self._popen.poll() is None and self.runner:
                # not finished yet
                self.schedule(1.0, self._read, runner)
                return

            self._done()
        except Exception, e:
            self.debug('exception during _read()')
            self.debug(log.getExceptionMessage(e))
            self.setException(e)
            self.stop()

    def _done(self):
            assert self._popen.returncode is not None, "No returncode"

            if self._popen.returncode >= 0:
                self.debug('Return code was %d', self._popen.returncode)
            else:
                self.debug('Terminated with signal %d',
                    -self._popen.returncode)

            self.setProgress(1.0)

            if self._popen.returncode != 0:
                if self.errors:
                    raise DeviceOpenException("\n".join(self.errors))
                else:
                    raise ProgramFailedException(self._popen.returncode)
            else:
                self.done()

            self.stop()
            return

    def abort(self):
        self.debug('Aborting, sending SIGTERM to %d', self._popen.pid)
        os.kill(self._popen.pid, signal.SIGTERM)
        # self.stop()

    def readbytesout(self, bytes):
        """
        Called when bytes have been read from stdout.
        """
        pass

    def readbyteserr(self, bytes):
        """
        Called when bytes have been read from stderr.
        """
        pass

    def done(self):
        """
        Called when cdrdao completed successfully.
        """
        raise NotImplementedError


class DiscInfoTask(CDRDAOTask):
    """
    I am a task that reads information about a disc.

    @ivar sessions: the number of sessions
    @type sessions: int
    """

    logCategory = 'DiscInfoTask'
    description = "Scanning disc..."
    table = None
    sessions = None

    def __init__(self, device=None):
        """
        @param device:  the device to rip from
        @type  device:  str
        """
        CDRDAOTask.__init__(self)

        self.options = ['disk-info', ]
        if device:
            self.options.extend(['--device', device, ])

        self.parser = LineParser(self)

    def readbytesout(self, bytes):
        self.parser.read(bytes)

    def readbyteserr(self, bytes):
        self.parser.read(bytes)

    def parse(self, line):
        # called by parser
        if line.startswith('Sessions'):
            self.sessions = int(line[line.find(':') + 1:])
            self.debug('Found %d sessions', self.sessions)
        m = _ERROR_RE.search(line)
        if m:
            error = m.group('error')
            self.errors.append(error)

    def done(self):
        pass


# Read stuff for one session


class ReadSessionTask(CDRDAOTask):
    """
    I am a task that reads things for one session.

    @ivar table: the index table
    @type table: L{table.Table}
    """

    logCategory = 'ReadSessionTask'
    description = "Reading session"
    table = None
    extraOptions = None

    def __init__(self, session=None, device=None):
        """
        @param session: the session to read
        @type  session: int
        @param device:  the device to rip from
        @type  device:  str
        """
        CDRDAOTask.__init__(self)
        self.parser = OutputParser(self)
        (fd, self._tocfilepath) = tempfile.mkstemp(
            suffix=u'.readtablesession.morituri')
        os.close(fd)
        os.unlink(self._tocfilepath)

        self.options = ['read-toc', ]
        if device:
            self.options.extend(['--device', device, ])
        if session:
            self.options.extend(['--session', str(session)])
            self.description = "%s of session %d..." % (
                self.description, session)
        if self.extraOptions:
            self.options.extend(self.extraOptions)

        self.options.extend([self._tocfilepath, ])

    def readbyteserr(self, bytes):
        self.parser.read(bytes)

        if self.parser.tracks > 0:
            self.setProgress(float(self.parser.track - 1) / self.parser.tracks)

    def done(self):
        # by merging the TOC info.
        self._tocfile = toc.TocFile(self._tocfilepath)
        self._tocfile.parse()
        os.unlink(self._tocfilepath)
        self.table = self._tocfile.table

        # we know the .toc file represents a single wav rip, so all offsets
        # are absolute since beginning of disc
        self.table.absolutize()
        # we unset relative since there is no real file backing this toc
        for t in self.table.tracks:
            for i in t.indexes.values():
                #i.absolute = i.relative
                i.relative = None

        # copy the leadout from the parser's table
        # FIXME: how do we get the length of the last audio track in the case
        # of a data track ?
        # self.table.leadout = self.parser.table.leadout

        # we should have parsed it from the initial output
        assert self.table.leadout is not None


class ReadTableSessionTask(ReadSessionTask):
    """
    I am a task that reads all indexes of a CD for a session.

    @ivar table: the index table
    @type table: L{table.Table}
    """

    logCategory = 'ReadTableSessionTask'
    description = "Scanning indexes"


class ReadTOCSessionTask(ReadSessionTask):
    """
    I am a task that reads the TOC of a CD, without pregaps.

    @ivar table: the index table that matches the TOC.
    @type table: L{table.Table}
    """

    logCategory = 'ReadTOCSessTask'
    description = "Reading TOC"
    extraOptions = ['--fast-toc', ]

    def done(self):
        ReadSessionTask.done(self)

        assert self.table.hasTOC(), "This Table Index should be a TOC"

# read all sessions


class ReadAllSessionsTask(task.MultiSeparateTask):
    """
    I am a base class for tasks that need to read all sessions.

    @ivar table: the index table
    @type table: L{table.Table}
    """

    logCategory = 'ReadAllSessionsTask'
    table = None
    _readClass = None

    def __init__(self, device=None):
        """
        @param device:  the device to rip from
        @type  device:  str
        """
        task.MultiSeparateTask.__init__(self)

        self._device = device

        self.debug('Starting ReadAllSessionsTask')
        self.tasks = [DiscInfoTask(device=device), ]

    def stopped(self, taskk):
        if not taskk.exception:
            # After first task, schedule additional ones
            if taskk == self.tasks[0]:
                for i in range(taskk.sessions):
                    self.tasks.append(self._readClass(session=i + 1,
                        device=self._device))

            if self._task == len(self.tasks):
                self.table = self.tasks[1].table
                if len(self.tasks) > 2:
                    for i, t in enumerate(self.tasks[2:]):
                        self.table.merge(t.table, i + 2)

                assert self.table.leadout is not None

        task.MultiSeparateTask.stopped(self, taskk)


class ReadTableTask(ReadAllSessionsTask):
    """
    I am a task that reads all indexes of a CD for all sessions.

    @ivar table: the index table
    @type table: L{table.Table}
    """

    logCategory = 'ReadTableTask'
    description = "Scanning indexes..."
    _readClass = ReadTableSessionTask


class ReadTOCTask(ReadAllSessionsTask):
    """
    I am a task that reads the TOC of a CD, without pregaps.

    @ivar table: the index table that matches the TOC.
    @type table: L{table.Table}
    """

    logCategory = 'ReadTOCTask'
    description = "Reading TOC..."
    _readClass = ReadTOCSessionTask


class DeviceOpenException(Exception):

    def __init__(self, msg):
        self.msg = msg
        self.args = (msg, )


class ProgramFailedException(Exception):

    def __init__(self, code):
        self.code = code
        self.args = (code, )
