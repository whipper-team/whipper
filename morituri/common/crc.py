# -*- Mode: Python; test-case-name: morituri.test.test_common_crc -*-
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
import sys
import struct
import zlib

import gobject
import gst

from morituri.common import task

FRAMES_PER_DISC_FRAME = 588
SAMPLES_PER_DISC_FRAME = FRAMES_PER_DISC_FRAME * 4

class CRCTask(task.Task):
    # this object needs a main loop to stop
    description = 'Calculating CRC checksum...'

    def __init__(self, path, frameStart=0, frameLength=-1):
        """
        A frame is considered a set of samples for each channel;
        ie 16 bit stereo is 4 bytes per frame.
        If frameLength < 0 it is treated as 'unknown' and calculated.

        @type  frameStart: int
        @param frameStart: the frame to start at
        """
        if not os.path.exists(path):
            raise IndexError, '%s does not exist' % path

        self._path = path
        self._frameStart = frameStart
        self._frameLength = frameLength
        self._frameEnd = None
        self._crc = 0
        self._bytes = 0
        self._first = None
        self._last = None
        self._adapter = gst.Adapter()

        self.crc = None # result

    def start(self):
        task.Task.start(self)
        self._pipeline = gst.parse_launch('''
            filesrc location="%s" !
            decodebin ! audio/x-raw-int !
            appsink name=sink sync=False emit-signals=True''' % self._path)
        self.debug('pausing')
        self._pipeline.set_state(gst.STATE_PAUSED)
        self._pipeline.get_state()
        self.debug('paused')

        self.debug('query duration')
        sink = self._pipeline.get_by_name('sink')

        if self._frameLength < 0:
            length, format = sink.query_duration(gst.FORMAT_DEFAULT)
            # wavparse 0.10.14 returns in bytes
            if format == gst.FORMAT_BYTES:
                self.debug('query returned in BYTES format')
                length /= 4
            self.debug('total length', length)
            self._frameLength = length - self._frameStart
            self.debug('audio frame length is', self._frameLength)
        self._frameEnd = self._frameStart + self._frameLength - 1

        self.debug('event')


        # the segment end only is respected since -good 0.10.14.1
        event = gst.event_new_seek(1.0, gst.FORMAT_DEFAULT,
            gst.SEEK_FLAG_FLUSH,
            gst.SEEK_TYPE_SET, self._frameStart,
            gst.SEEK_TYPE_SET, self._frameEnd + 1) # half-inclusive interval
        # FIXME: sending it with frameEnd set screws up the seek, we don't get
        # everything for flac; fixed in recent -good
        result = sink.send_event(event)
        #self.debug('event sent')
        #self.debug(result)
        sink.connect('new-buffer', self._new_buffer_cb)
        sink.connect('eos', self._eos_cb)

        self.debug('scheduling setting to play')
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self._pipeline.set_state, gst.STATE_PLAYING)
        # would not work.

        def play():
            self._pipeline.set_state(gst.STATE_PLAYING)
            return False
        gobject.timeout_add(0L, play)

        #self._pipeline.set_state(gst.STATE_PLAYING)
        self.debug('scheduled setting to play')

    def _new_buffer_cb(self, sink):
        buffer = sink.emit('pull-buffer')
        gst.debug('received new buffer at offset %r with length %r' % (
            buffer.offset, buffer.size))
        if self._first is None:
            self._first = buffer.offset
            self.debug('first sample is', self._first)
        self._last = buffer

        assert len(buffer) % 4 == 0, "buffer is not a multiple of 4 bytes"
        
        # FIXME: gst-python 0.10.14.1 doesn't have adapter_peek/_take wrapped
        # see http://bugzilla.gnome.org/show_bug.cgi?id=576505
        self._adapter.push(buffer)

        while self._adapter.available() >= SAMPLES_PER_DISC_FRAME:
            # FIXME: in 0.10.14.1, take_buffer leaks a ref
            buffer = self._adapter.take_buffer(SAMPLES_PER_DISC_FRAME)

            self._crc = self.do_crc_buffer(buffer, self._crc)
            self._bytes += len(buffer)

            # update progress
            frame = self._first + self._bytes / 4
            framesDone = frame - self._frameStart
            progress = float(framesDone) / float((self._frameLength))
            # marshall to the main thread
            gobject.timeout_add(0L, self.setProgress, progress)


    def do_crc_buffer(self, buffer, crc):
        """
        Subclasses should implement this.
        """
        raise NotImplementedError

    def _eos_cb(self, sink):
        # get the last one; FIXME: why does this not get to us before ?
        #self._new_buffer_cb(sink)
        self.debug('eos, scheduling stop')
        gobject.timeout_add(0L, self.stop)

    def stop(self):
        self.debug('stopping')
        self.debug('setting state to NULL')
        self._pipeline.set_state(gst.STATE_NULL)

        if not self._last:
            # see http://bugzilla.gnome.org/show_bug.cgi?id=578612
            print 'ERROR: not a single buffer gotten'
            raise
        else:
            self._crc = self._crc % 2 ** 32
            last = self._last.offset + len(self._last) / 4 - 1
            self.debug("last sample:", last)
            self.debug("frame length:", self._frameLength)
            self.debug("CRC: %08X" % self._crc)
            self.debug("bytes: %d" % self._bytes)
            if self._frameEnd != last:
                print 'ERROR: did not get all frames, %d missing' % (
                    self._frameEnd - last)

        # publicize and stop
        self.crc = self._crc
        task.Task.stop(self)

class CRC32Task(CRCTask):
    """
    I do a simple CRC32 check.
    """
    def do_crc_buffer(self, buffer, crc):
        return zlib.crc32(buffer, crc)

class CRCAudioRipTask(CRCTask):
    def __init__(self, path, trackNumber, trackCount, frameStart=0, frameLength=-1):
        CRCTask.__init__(self, path, frameStart, frameLength)
        self._trackNumber = trackNumber
        self._trackCount = trackCount
        self._discFrameCounter = 0

    def do_crc_buffer(self, buffer, crc):
        self._discFrameCounter += 1

        # on first track ...
        if self._trackNumber == 1:
            # ... skip first 4 CD frames
            if self._discFrameCounter <= 4:
                self.debug('skipping frame %d' % self._discFrameCounter)
                return crc
            # ... on 5th frame, only use last value
            elif self._discFrameCounter == 5:
                values = struct.unpack("<I", buffer[-4:])
                crc += FRAMES_PER_DISC_FRAME * 5 * values[0]
                crc &= 0xFFFFFFFF
 
        # on last track, skip last 5 CD frames
        if self._trackNumber == self._trackCount:
            discFrameLength = self._frameLength / FRAMES_PER_DISC_FRAME
            if self._discFrameCounter > discFrameLength - 5:
                self.debug('skipping frame %d' % self._discFrameCounter)
                return crc

        values = struct.unpack("<%dI" % (len(buffer) / 4), buffer)
        for i, value in enumerate(values):
            crc += (self._bytes / 4 + i + 1) * value
            crc &= 0xFFFFFFFF
            offset = self._bytes / 4 + i + 1
            # if offset % FRAMES_PER_DISC_FRAME == 0:
            #    print 'THOMAS: frame %d, offset %d, value %d, CRC %d' % (
            #        offset / FRAMES_PER_DISC_FRAME, offset, value, crc)
        return crc
