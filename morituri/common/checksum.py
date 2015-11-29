# -*- Mode: Python; test-case-name: morituri.test.test_common_checksum -*-
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
import struct
import zlib

import gst

from morituri.common import common
from morituri.common import gstreamer as cgstreamer
from morituri.common import log
from morituri.common import task

from morituri.extern.task import gstreamer

# checksums are not CRC's. a CRC is a specific type of checksum.


class ChecksumTask(log.Loggable, gstreamer.GstPipelineTask):
    """
    I am a task that calculates a checksum of the decoded audio data.

    @ivar checksum: the resulting checksum
    """

    logCategory = 'ChecksumTask'

    # this object needs a main loop to stop
    description = 'Calculating checksum'

    def __init__(self, path, sampleStart=0, sampleLength=-1):
        """
        A sample is considered a set of samples for each channel;
        ie 16 bit stereo is 4 bytes per sample.
        If sampleLength < 0 it is treated as 'unknown' and calculated.

        @type  path:       unicode
        @type  sampleStart: int
        @param sampleStart: the sample to start at
        """

        # sampleLength can be e.g. -588 when it is -1 * SAMPLES_PER_FRAME

        assert type(path) is unicode, "%r is not unicode" % path

        self.logName = "ChecksumTask 0x%x" % id(self)

        # use repr/%r because path can be unicode
        if sampleLength < 0:
            self.debug(
                'Creating checksum task on %r from sample %d until the end',
                path, sampleStart)
        else:
            self.debug(
                'Creating checksum task on %r from sample %d for %d samples',
                path, sampleStart, sampleLength)

        if not os.path.exists(path):
            raise IndexError('%r does not exist' % path)

        self._path = path
        self._sampleStart = sampleStart
        self._sampleLength = sampleLength
        self._sampleEnd = None
        self._checksum = 0
        self._bytes = 0 # number of bytes received
        self._first = None
        self._last = None
        self._adapter = gst.Adapter()

        self.checksum = None # result

        cgstreamer.removeAudioParsers()

    ### gstreamer.GstPipelineTask implementations

    def getPipelineDesc(self):
        return '''
            filesrc location="%s" !
            decodebin name=decode ! audio/x-raw-int !
            appsink name=sink sync=False emit-signals=True
            ''' % gstreamer.quoteParse(self._path).encode('utf-8')

    def _getSampleLength(self):
        # get length in samples of file
        sink = self.pipeline.get_by_name('sink')

        self.debug('query duration')
        try:
            length, qformat = sink.query_duration(gst.FORMAT_DEFAULT)
        except gst.QueryError, e:
            self.setException(e)
            return None

        # wavparse 0.10.14 returns in bytes
        if qformat == gst.FORMAT_BYTES:
            self.debug('query returned in BYTES format')
            length /= 4
        self.debug('total sample length of file: %r', length)

        return length


    def paused(self):
        sink = self.pipeline.get_by_name('sink')

        length = self._getSampleLength()
        if length is None:
            return

        if self._sampleLength < 0:
            self._sampleLength = length - self._sampleStart
            self.debug('sampleLength is queried as %d samples',
                self._sampleLength)
        else:
            self.debug('sampleLength is known, and is %d samples' %
                self._sampleLength)

        self._sampleEnd = self._sampleStart + self._sampleLength - 1
        self.debug('sampleEnd is sample %d' % self._sampleEnd)

        self.debug('event')


        if self._sampleStart == 0 and self._sampleEnd + 1 == length:
            self.debug('No need to seek, crcing full file')
        else:
            # the segment end only is respected since -good 0.10.14.1
            event = gst.event_new_seek(1.0, gst.FORMAT_DEFAULT,
                gst.SEEK_FLAG_FLUSH,
                gst.SEEK_TYPE_SET, self._sampleStart,
                gst.SEEK_TYPE_SET, self._sampleEnd + 1) # half-inclusive
            self.debug('CRCing %r from frame %d to frame %d (excluded)' % (
                self._path,
                self._sampleStart / common.SAMPLES_PER_FRAME,
                (self._sampleEnd + 1) / common.SAMPLES_PER_FRAME))
            # FIXME: sending it with sampleEnd set screws up the seek, we
            # don't get # everything for flac; fixed in recent -good
            result = sink.send_event(event)
            self.debug('event sent, result %r', result)
            if not result:
                self.error('Failed to select samples with GStreamer seek event')
        sink.connect('new-buffer', self._new_buffer_cb)
        sink.connect('eos', self._eos_cb)

        self.debug('scheduling setting to play')
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self.pipeline.set_state, gst.STATE_PLAYING)
        # would not work.

        def play():
            self.pipeline.set_state(gst.STATE_PLAYING)
            return False
        self.schedule(0, play)

        #self.pipeline.set_state(gst.STATE_PLAYING)
        self.debug('scheduled setting to play')

    def stopped(self):
        self.debug('stopped')
        if not self._last:
            # see http://bugzilla.gnome.org/show_bug.cgi?id=578612
            self.debug(
                'not a single buffer gotten, setting exception EmptyError')
            self.setException(common.EmptyError('not a single buffer gotten'))
            return
        else:
            self._checksum = self._checksum % 2 ** 32
            self.debug("last buffer's sample offset %r", self._last.offset)
            self.debug("last buffer's sample size %r", len(self._last) / 4)
            last = self._last.offset + len(self._last) / 4 - 1
            self.debug("last sample offset in buffer: %r", last)
            self.debug("requested sample end: %r", self._sampleEnd)
            self.debug("requested sample length: %r", self._sampleLength)
            self.debug("checksum: %08X", self._checksum)
            self.debug("bytes: %d", self._bytes)
            if self._sampleEnd != last:
                msg = 'did not get all samples, %d of %d missing' % (
                    self._sampleEnd - last, self._sampleEnd)
                self.warning(msg)
                self.setExceptionAndTraceback(common.MissingFrames(msg))
                return

        self.checksum = self._checksum

    ### subclass methods

    def do_checksum_buffer(self, buf, checksum):
        """
        Subclasses should implement this.

        @param buf:      a byte buffer containing two 16-bit samples per
                         channel.
        @type  buf:      C{str}
        @param checksum: the checksum so far, as returned by the
                         previous call.
        @type  checksum: C{int}
        """
        raise NotImplementedError

    ### private methods

    def _new_buffer_cb(self, sink):
        buf = sink.emit('pull-buffer')
        gst.log('received new buffer at offset %r with length %r' % (
            buf.offset, buf.size))
        if self._first is None:
            self._first = buf.offset
            self.debug('first sample is sample offset %r', self._first)
        self._last = buf

        assert len(buf) % 4 == 0, "buffer is not a multiple of 4 bytes"

        # FIXME: gst-python 0.10.14.1 doesn't have adapter_peek/_take wrapped
        # see http://bugzilla.gnome.org/show_bug.cgi?id=576505
        self._adapter.push(buf)

        while self._adapter.available() >= common.BYTES_PER_FRAME:
            # FIXME: in 0.10.14.1, take_buffer leaks a ref
            buf = self._adapter.take_buffer(common.BYTES_PER_FRAME)

            self._checksum = self.do_checksum_buffer(buf, self._checksum)
            self._bytes += len(buf)

            # update progress
            sample = self._first + self._bytes / 4
            samplesDone = sample - self._sampleStart
            progress = float(samplesDone) / float((self._sampleLength))
            # marshal to the main thread
            self.schedule(0, self.setProgress, progress)

    def _eos_cb(self, sink):
        # get the last one; FIXME: why does this not get to us before ?
        #self._new_buffer_cb(sink)
        self.debug('eos, scheduling stop')
        self.schedule(0, self.stop)


class CRC32Task(ChecksumTask):
    """
    I do a simple CRC32 check.
    """

    description = 'Calculating CRC'

    def do_checksum_buffer(self, buf, checksum):
        return zlib.crc32(buf, checksum)


class AccurateRipChecksumTask(ChecksumTask):
    """
    I implement the AccurateRip checksum.

    See http://www.accuraterip.com/
    """

    description = 'Calculating AccurateRip checksum'

    def __init__(self, path, trackNumber, trackCount, sampleStart=0,
            sampleLength=-1):
        ChecksumTask.__init__(self, path, sampleStart, sampleLength)
        self._trackNumber = trackNumber
        self._trackCount = trackCount
        self._discFrameCounter = 0 # 1-based

    def __repr__(self):
        return "<AccurateRipCheckSumTask of track %d in %r>" % (
            self._trackNumber, self._path)

    def do_checksum_buffer(self, buf, checksum):
        self._discFrameCounter += 1

        # on first track ...
        if self._trackNumber == 1:
            # ... skip first 4 CD frames
            if self._discFrameCounter <= 4:
                gst.debug('skipping frame %d' % self._discFrameCounter)
                return checksum
            # ... on 5th frame, only use last value
            elif self._discFrameCounter == 5:
                values = struct.unpack("<I", buf[-4:])
                checksum += common.SAMPLES_PER_FRAME * 5 * values[0]
                checksum &= 0xFFFFFFFF
                return checksum

        # on last track, skip last 5 CD frames
        if self._trackNumber == self._trackCount:
            discFrameLength = self._sampleLength / common.SAMPLES_PER_FRAME
            if self._discFrameCounter > discFrameLength - 5:
                self.debug('skipping frame %d', self._discFrameCounter)
                return checksum

        # self._bytes is updated after do_checksum_buffer
        factor = self._bytes / 4 + 1
        values = struct.unpack("<%dI" % (len(buf) / 4), buf)
        for value in values:
            checksum += factor * value
            factor += 1
            # offset = self._bytes / 4 + i + 1
            # if offset % common.SAMPLES_PER_FRAME == 0:
            #   print 'frame %d, ends before %d, last value %08x, CRC %08x' % (
            #     offset / common.SAMPLES_PER_FRAME, offset, value, sum)

        checksum &= 0xFFFFFFFF
        return checksum


class TRMTask(task.GstPipelineTask):
    """
    I calculate a MusicBrainz TRM fingerprint.

    @ivar trm: the resulting trm
    """

    trm = None
    description = 'Calculating fingerprint'

    def __init__(self, path):
        if not os.path.exists(path):
            raise IndexError('%s does not exist' % path)

        self.path = path
        self._trm = None
        self._bus = None

    def getPipelineDesc(self):
        return '''
            filesrc location="%s" !
            decodebin ! audioconvert ! audio/x-raw-int !
            trm name=trm !
            appsink name=sink sync=False emit-signals=True''' % self.path

    def parsed(self):
        sink = self.pipeline.get_by_name('sink')
        sink.connect('new-buffer', self._new_buffer_cb)

    def paused(self):
        gst.debug('query duration')

        self._length, qformat = self.pipeline.query_duration(gst.FORMAT_TIME)
        gst.debug('total length: %r' % self._length)
        gst.debug('scheduling setting to play')
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self.pipeline.set_state, gst.STATE_PLAYING)
        # would not work.


    # FIXME: can't move this to base class because it triggers too soon
    # in the case of checksum

    def bus_eos_cb(self, bus, message):
        gst.debug('eos, scheduling stop')
        self.schedule(0, self.stop)

    def bus_tag_cb(self, bus, message):
        taglist = message.parse_tag()
        if 'musicbrainz-trmid' in taglist.keys():
            self._trm = taglist['musicbrainz-trmid']

    def _new_buffer_cb(self, sink):
        # this is just for counting progress
        buf = sink.emit('pull-buffer')
        position = buf.timestamp
        if buf.duration != gst.CLOCK_TIME_NONE:
            position += buf.duration
        self.setProgress(float(position) / self._length)

    def stopped(self):
        self.trm = self._trm

class MaxSampleTask(ChecksumTask):
    """
    I check for the biggest sample value.
    """

    description = 'Finding highest sample value'

    def do_checksum_buffer(self, buf, checksum):
        values = struct.unpack("<%dh" % (len(buf) / 2), buf)
        absvalues = [abs(v) for v in values]
        m = max(absvalues)
        if checksum < m:
            checksum = m

        return checksum

