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
import errno
import re
import stat
import shutil
import subprocess
import tempfile

from morituri.common import log, common

from morituri.extern import asyncsub
from morituri.extern.task import task


class FileSizeError(Exception):

    message = None

    """
    The given path does not have the expected size.
    """

    def __init__(self, path, message):
        self.args = (path, message)
        self.path = path
        self.message = message


class ReturnCodeError(Exception):
    """
    The program had a non-zero return code.
    """

    def __init__(self, returncode):
        self.args = (returncode, )
        self.returncode = returncode


class ChecksumException(Exception):
    pass


_PROGRESS_RE = re.compile(r"""
    ^\#\#: (?P<code>.+)\s      # function code
    \[(?P<function>.*)\]\s@\s     # function name
    (?P<offset>\d+)        # offset
""", re.VERBOSE)

_ERROR_RE = re.compile("^scsi_read error:")

# from reading cdparanoia source code, it looks like offset is reported in
# number of single-channel samples, ie. 2 bytes per unit, and absolute


class ProgressParser(object):
    read = 0 # last [read] frame
    wrote = 0 # last [wrote] frame
    errors = 0 # count of number of scsi errors
    _nframes = None # number of frames read on each [read]
    _firstFrames = None # number of frames read on first [read]
    reads = 0 # total number of reads

    def __init__(self, start, stop):
        """
        @param start:  first frame to rip
        @type  start:  int
        @param stop:   last frame to rip (inclusive)
        @type  stop:   int
        """
        self.start = start
        self.stop = stop

        # FIXME: privatize
        self.read = start

        self._reads = {} # read count for each sector

    def parse(self, line):
        """
        Parse a line.
        """
        m = _PROGRESS_RE.search(line)
        if m:
            # code = int(m.group('code'))
            function = m.group('function')
            wordOffset = int(m.group('offset'))
            if function == 'read':
                self._parse_read(wordOffset)
            elif function == 'wrote':
                self._parse_wrote(wordOffset)

        m = _ERROR_RE.search(line)
        if m:
            self.errors += 1

    def _parse_read(self, wordOffset):
        if wordOffset % common.WORDS_PER_FRAME != 0:
            print 'THOMAS: not a multiple of %d: %d' % (
                common.WORDS_PER_FRAME, wordOffset)
            return

        frameOffset = wordOffset / common.WORDS_PER_FRAME

        # set nframes if not yet set
        if self._nframes is None and self.read != 0:
            self._nframes = frameOffset - self.read

        # set firstFrames if not yet set
        if self._firstFrames is None:
            self._firstFrames = frameOffset - self.start

        markStart = None
        markEnd = None

        # verify it either read nframes more or went back for verify
        if frameOffset > self.read:
            delta = frameOffset - self.read
            if self._nframes and delta != self._nframes:
                # print 'THOMAS: Read %d frames more, not %d' % (
                # delta, self._nframes)
                # my drive either reads 7 or 13 frames
                pass

            # update our read sectors hash
            markStart = self.read
            markEnd = frameOffset
        else:
            # went back to verify
            # we could use firstFrames as an estimate on how many frames this
            # read, but this lowers our track quality needlessly where
            # EAC still reports 100% track quality
            markStart = frameOffset # - self._firstFrames
            markEnd = frameOffset

        # FIXME: doing this is way too slow even for a testcase, so disable
        if False:
            for frame in range(markStart, markEnd):
                if not frame in self._reads.keys():
                    self._reads[frame] = 0
                self._reads[frame] += 1

        # cdparanoia reads quite a bit beyond the current track before it
        # goes back to verify; don't count those
        if markEnd > self.stop:
            markEnd = self.stop
        if markStart > self.stop:
            markStart = self.stop

        self.reads += markEnd - markStart

        # update our read pointer
        self.read = frameOffset

    def _parse_wrote(self, wordOffset):
        # cdparanoia outputs most [wrote] calls with one word less than a frame
        frameOffset = (wordOffset + 1) / common.WORDS_PER_FRAME
        self.wrote = frameOffset

    def getTrackQuality(self):
        """
        Each frame gets read twice.
        More than two reads for a frame reduce track quality.
        """
        frames = self.stop - self.start + 1
        reads = self.reads

        # don't go over a 100%; we know cdparanoia reads each frame at least
        # twice
        return min(frames * 2.0 / reads, 1.0)


# FIXME: handle errors


class ReadTrackTask(log.Loggable, task.Task):
    """
    I am a task that reads a track using cdparanoia.

    @ivar reads: how many reads were done to rip the track
    """

    description = "Reading track"
    quality = None # set at end of reading

    _MAXERROR = 100 # number of errors detected by parser

    def __init__(self, path, table, start, stop, offset=0, device=None,
        action="Reading", what="track"):
        """
        Read the given track.

        @param path:   where to store the ripped track
        @type  path:   unicode
        @param table:  table of contents of CD
        @type  table:  L{table.Table}
        @param start:  first frame to rip
        @type  start:  int
        @param stop:   last frame to rip (inclusive); >= start
        @type  stop:   int
        @param offset: read offset, in samples
        @type  offset: int
        @param device: the device to rip from
        @type  device: str
        @param action: a string representing the action; e.g. Read/Verify
        @type  action: str
        @param what:   a string representing what's being read; e.g. Track
        @type  what:   str
        """
        assert type(path) is unicode, "%r is not unicode" % path

        self.path = path
        self._table = table
        self._start = start
        self._stop = stop
        self._offset = offset
        self._parser = ProgressParser(start, stop)
        self._device = device

        self._buffer = "" # accumulate characters
        self._errors = []
        self.description = "%s %s" % (action, what)

    def start(self, runner):
        task.Task.start(self, runner)

        # find on which track the range starts and stops
        startTrack = 0
        startOffset = 0
        stopTrack = 0
        stopOffset = self._stop

        for i, t in enumerate(self._table.tracks):
            if self._table.getTrackStart(i + 1) <= self._start:
                startTrack = i + 1
                startOffset = self._start - self._table.getTrackStart(i + 1)
            if self._table.getTrackEnd(i + 1) <= self._stop:
                stopTrack = i + 1
                stopOffset = self._stop - self._table.getTrackStart(i + 1)

        self.debug('Ripping from %d to %d (inclusive)',
            self._start, self._stop)
        self.debug('Starting at track %d, offset %d',
            startTrack, startOffset)
        self.debug('Stopping at track %d, offset %d',
            stopTrack, stopOffset)

        bufsize = 1024
        argv = ["cdparanoia", "--stderr-progress",
            "--sample-offset=%d" % self._offset, ]
        if self._device:
            argv.extend(["--force-cdrom-device", self._device, ])
        argv.extend(["%d[%s]-%d[%s]" % (
                startTrack, common.framesToHMSF(startOffset),
                stopTrack, common.framesToHMSF(stopOffset)),
            self.path])
        self.debug('Running %s' % (" ".join(argv), ))
        try:
            self._popen = asyncsub.Popen(argv,
                bufsize=bufsize,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, close_fds=True)
        except OSError, e:
            import errno
            if e.errno == errno.ENOENT:
                raise common.MissingDependencyException('cdparanoia')

            raise

        self.schedule(1.0, self._read, runner)

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
                self._parser.parse(line)

            # fail if too many errors
            if self._parser.errors > self._MAXERROR:
                self.debug('%d errors, terminating', self._parser.errors)
                self._popen.terminate()

            num = self._parser.wrote - self._start + 1
            den = self._stop - self._start + 1
            assert den != 0, "stop %d should be >= start %d" % (
                self._stop, self._start)
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

        # check if the length matches
        size = os.stat(self.path)[stat.ST_SIZE]
        # wav header is 44 bytes
        offsetLength = self._stop - self._start + 1
        expected = offsetLength * common.BYTES_PER_FRAME + 44
        if size != expected:
            # FIXME: handle errors better
            self.warning('file size %d did not match expected size %d',
                size, expected)
            if (size - expected) % common.BYTES_PER_FRAME == 0:
                self.warning('%d frames difference' % (
                    (size - expected) / common.BYTES_PER_FRAME))
            else:
                self.warning('non-integral amount of frames difference')

            self.setAndRaiseException(FileSizeError(self.path,
                "File size %d did not match expected size %d" % (
                    size, expected)))

        if not self.exception and self._popen.returncode != 0:
            if self._errors:
                print "\n".join(self._errors)
            else:
                self.warning('exit code %r', self._popen.returncode)
                self.exception = ReturnCodeError(self._popen.returncode)

        self.quality = self._parser.getTrackQuality()

        self.stop()
        return


class ReadVerifyTrackTask(log.Loggable, task.MultiSeparateTask):
    """
    I am a task that reads and verifies a track using cdparanoia.

    The path where the file is stored can be changed if necessary, for
    example if the file name is too long.

    @ivar path:         the path where the file is to be stored.
    @ivar checksum:     the checksum of the track; set if they match.
    @ivar testchecksum: the test checksum of the track.
    @ivar copychecksum: the copy checksum of the track.
    @ivar peak:         the peak level of the track
    """

    checksum = None
    testchecksum = None
    copychecksum = None
    peak = None
    quality = None

    _tmpwavpath = None
    _tmppath = None

    def __init__(self, path, table, start, stop, offset=0, device=None,
                 profile=None, taglist=None, what="track"):
        """
        @param path:    where to store the ripped track
        @type  path:    str
        @param table:   table of contents of CD
        @type  table:   L{table.Table}
        @param start:   first frame to rip
        @type  start:   int
        @param stop:    last frame to rip (inclusive)
        @type  stop:    int
        @param offset:  read offset, in samples
        @type  offset:  int
        @param device:  the device to rip from
        @type  device:  str
        @param profile: the encoding profile
        @type  profile: L{encode.Profile}
        @param taglist: a list of tags
        @param taglist: L{gst.TagList}
        """
        task.MultiSeparateTask.__init__(self)

        self.debug('Creating read and verify task on %r', path)
        self.path = path

        if taglist:
            self.debug('read and verify with taglist %r', taglist)
        # FIXME: choose a dir on the same disk/dir as the final path
        fd, tmppath = tempfile.mkstemp(suffix='.morituri.wav')
        tmppath = unicode(tmppath)
        os.close(fd)
        self._tmpwavpath = tmppath

        # here to avoid import gst eating our options
        from morituri.common import checksum

        self.tasks = []
        self.tasks.append(
            ReadTrackTask(tmppath, table, start, stop,
                offset=offset, device=device, what=what))
        self.tasks.append(checksum.CRC32Task(tmppath))
        t = ReadTrackTask(tmppath, table, start, stop,
            offset=offset, device=device, action="Verifying", what=what)
        self.tasks.append(t)
        self.tasks.append(checksum.CRC32Task(tmppath))

        fd, tmpoutpath = tempfile.mkstemp(suffix='.morituri.%s' %
            profile.extension)
        tmpoutpath = unicode(tmpoutpath)
        os.close(fd)
        self._tmppath = tmpoutpath

        # here to avoid import gst eating our options
        from morituri.common import encode

        self.tasks.append(encode.EncodeTask(tmppath, tmpoutpath, profile,
            taglist=taglist, what=what))
        # make sure our encoding is accurate
        self.tasks.append(checksum.CRC32Task(tmpoutpath))

        self.checksum = None

        umask = os.umask(0)
        os.umask(umask)
        self.file_mode = 0666 - umask

    def stop(self):
        # FIXME: maybe this kind of try-wrapping to make sure
        # we chain up should be handled by a parent class function ?
        try:
            if not self.exception:
                self.quality = max(self.tasks[0].quality,
                    self.tasks[2].quality)
                self.peak = self.tasks[4].peak
                self.debug('peak: %r', self.peak)

                self.testchecksum = c1 = self.tasks[1].checksum
                self.copychecksum = c2 = self.tasks[3].checksum
                if c1 == c2:
                    self.info('Checksums match, %08x' % c1)
                    self.checksum = self.testchecksum
                else:
                    # FIXME: detect this before encoding
                    self.info('Checksums do not match, %08x %08x' % (
                        c1, c2))
                    self.exception = ChecksumException(
                        'read and verify failed: test checksum')

                if self.tasks[5].checksum != self.checksum:
                    self.exception = ChecksumException(
                        'Encoding failed, checksum does not match')

                # delete the unencoded file
                os.unlink(self._tmpwavpath)

                os.chmod(self._tmppath, self.file_mode)

                if not self.exception:
                    try:
                        self.debug('Moving to final path %r', self.path)
                        shutil.move(self._tmppath, self.path)
                    except IOError, e:
                        if e.errno == errno.ENAMETOOLONG:
                            self.path = common.shrinkPath(self.path)
                            shutil.move(self._tmppath, self.path)
                    except Exception, e:
                        self.debug('Exception while moving to final path %r: %r',
                            self.path, log.getExceptionMessage(e))
                        self.exception = e
                else:
                    os.unlink(self._tmppath)
            else:
                self.debug('stop: exception %r', self.exception)
        except Exception, e:
            print 'WARNING: unhandled exception %r' % (e, )

        task.MultiSeparateTask.stop(self)
