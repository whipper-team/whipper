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

    def __init__(self, path, frameStart=0, frameLength=-1):
        """
        A frame is considered a set of samples for each channel;
        ie 16 bit stereo is 4 bytes per frame.
        If frameLength < 0 it is treated as 'unknown' and calculated.

        @type  path:       unicode
        @type  frameStart: int
        @param frameStart: the frame to start at
        """
        assert type(path) is unicode, "%r is not unicode" % path

        self.logName = "ChecksumTask 0x%x" % id(self)

        # use repr/%r because path can be unicode
        self.debug('Creating checksum task on %r from %d to %d',
            path, frameStart, frameLength)
        if not os.path.exists(path):
            raise IndexError('%r does not exist' % path)

        self._path = path
        self._frameStart = frameStart
        self._frameLength = frameLength
        self._frameEnd = None
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

    def paused(self):
        sink = self.pipeline.get_by_name('sink')

        if self._frameLength < 0:
            self.debug('query duration')
            try:
                length, qformat = sink.query_duration(gst.FORMAT_DEFAULT)
            except gst.QueryError, e:
                self.setException(e)
                return

            # wavparse 0.10.14 returns in bytes
            if qformat == gst.FORMAT_BYTES:
                self.debug('query returned in BYTES format')
                length /= 4
            self.debug('total length: %r', length)
            self._frameLength = length - self._frameStart
            self.debug('audio frame length is %r', self._frameLength)
        else:
            self.debug('frameLength known, is %d' % self._frameLength)
        self._frameEnd = self._frameStart + self._frameLength - 1

        self.debug('event')


        # the segment end only is respected since -good 0.10.14.1
        event = gst.event_new_seek(1.0, gst.FORMAT_DEFAULT,
            gst.SEEK_FLAG_FLUSH,
            gst.SEEK_TYPE_SET, self._frameStart,
            gst.SEEK_TYPE_SET, self._frameEnd + 1) # half-inclusive interval
        self.debug('CRCing %r from sector %d to sector %d' % (
            self._path,
            self._frameStart / common.SAMPLES_PER_FRAME,
            (self._frameEnd + 1) / common.SAMPLES_PER_FRAME))
        # FIXME: sending it with frameEnd set screws up the seek, we don't get
        # everything for flac; fixed in recent -good
        result = sink.send_event(event)
        self.debug('event sent, result %r', result)
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
            self.debug('not a single buffer gotten, setting exception EmptyError')
            self.setException(common.EmptyError('not a single buffer gotten'))
        else:
            self._checksum = self._checksum % 2 ** 32
            self.debug("last offset %r", self._last.offset)
            last = self._last.offset + len(self._last) / 4 - 1
            self.debug("last sample: %r", last)
            self.debug("frame end: %r", self._frameEnd)
            self.debug("frame length: %r", self._frameLength)
            self.debug("checksum: %08X", self._checksum)
            self.debug("bytes: %d", self._bytes)
            if self._frameEnd != last:
                print 'ERROR: did not get all frames, %d missing' % (
                    self._frameEnd - last)

        self.checksum = self._checksum

    ### subclass methods

    def do_checksum_buffer(self, buf, checksum):
        """
        Subclasses should implement this.
        """
        raise NotImplementedError

    ### private methods

    def _new_buffer_cb(self, sink):
        buf = sink.emit('pull-buffer')
        gst.log('received new buffer at offset %r with length %r' % (
            buf.offset, buf.size))
        if self._first is None:
            self._first = buf.offset
            self.debug('first sample is %r', self._first)
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
            frame = self._first + self._bytes / 4
            framesDone = frame - self._frameStart
            progress = float(framesDone) / float((self._frameLength))
            # marshall to the main thread
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

    def __init__(self, path, trackNumber, trackCount, frameStart=0,
            frameLength=-1):
        ChecksumTask.__init__(self, path, frameStart, frameLength)
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
            discFrameLength = self._frameLength / common.SAMPLES_PER_FRAME
            if self._discFrameCounter > discFrameLength - 5:
                self.debug('skipping frame %d', self._discFrameCounter)
                return checksum

        values = struct.unpack("<%dI" % (len(buf) / 4), buf)
        for i, value in enumerate(values):
            # self._bytes is updated after do_checksum_buffer
            checksum += (self._bytes / 4 + i + 1) * value
            checksum &= 0xFFFFFFFF
            # offset = self._bytes / 4 + i + 1
            # if offset % common.SAMPLES_PER_FRAME == 0:
            #   print 'frame %d, ends before %d, last value %08x, CRC %08x' % (
            #     offset / common.SAMPLES_PER_FRAME, offset, value, sum)

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
