# -*- Mode: Python; test-case-name: morituri.test.test_common_task -*-
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
import zlib

import gobject
import gst

class Task(object):
    description = 'I am doing something.'

    progress = 0.0
    increment = 0.01
    running = False

    _listeners = None

    def debug(self, *args, **kwargs):
        print args, kwargs
        sys.stdout.flush()
        pass

    def start(self):
        self.running = True
        self._notifyListeners('start')

    def stop(self):
        self.debug('stopping')
        self.running = False
        self._notifyListeners('stop')

    def setProgress(self, value):
        if value - self.progress > self.increment or value == 1.0:
            self.progress = value
            self._notifyListeners('progress', value)
            self.debug('notifying progress', value)
        
    def addListener(self, listener):
        if not self._listeners:
            self._listeners = []
        self._listeners.append(listener)

    def _notifyListeners(self, methodName, *args, **kwargs):
            if self._listeners:
                for l in self._listeners:
                    getattr(l, methodName)(*args, **kwargs)

class CRCTask(Task):
    # this object needs a main loop to stop
    description = 'Calculating CRC checksum...'

    def __init__(self, path, frameStart=0, frameEnd=-1):
        if not os.path.exists(path):
            raise IndexError, '%s does not exist' % path

        self._path = path
        self._frameStart = frameStart
        self._frameEnd = frameEnd
        self._crc = 0
        self._bytes = 0
        self._first = None
        self._last = None

        self.crc = None # result

    def start(self):
        Task.start(self)
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

        if self._frameEnd == -1:
            length, _ = sink.query_duration(gst.FORMAT_DEFAULT)
            self._frameEnd = length - 1
            self.debug('last frame is', self._frameEnd)

        self.debug('event')


        # the segment end only is respected since -good 0.10.14.1
        event = gst.event_new_seek(1.0, gst.FORMAT_DEFAULT,
            gst.SEEK_FLAG_FLUSH,
            gst.SEEK_TYPE_SET, self._frameStart,
            gst.SEEK_TYPE_SET, self._frameEnd + 1) # half-inclusive interval
        # FIXME: sending it with frameEnd set screws up the seek, we don't get everything
        result = sink.send_event(event)
        #self.debug('event sent')
        #self.debug(result)
        sink.connect('new-buffer', self._new_buffer_cb)
        sink.connect('eos', self._eos_cb)

        self.debug('setting to play')
        self._pipeline.set_state(gst.STATE_PLAYING)
        self.debug('set to play')

    def _new_buffer_cb(self, sink):
        buffer = sink.emit('pull-buffer')
        gst.debug('received new buffer at offset %r with length %r' % (
            buffer.offset, buffer.size))
        if self._first is None:
            self._first = buffer.offset
            self.debug('first sample is', self._first)
        self._last = buffer

        assert len(buffer) % 4 == 0, "buffer is not a multiple of 4 bytes"
        self._bytes += len(buffer)
        
        # update progress
        frame = self._first + self._bytes / 4
        progress = float((frame - self._frameStart)) / float((self._frameEnd - self._frameStart))
        self.setProgress(progress)

        self._crc = zlib.crc32(buffer, self._crc)

    def _eos_cb(self, sink):
        # get the last one; FIXME: why does this not get to us before ?
        #self._new_buffer_cb(sink)
        self.debug('setting state to NULL')
        gobject.timeout_add(0L, self.stop)

    def stop(self):
        self._pipeline.set_state(gst.STATE_NULL)
        self.debug('stopping')
        self._crc = self._crc % 2 ** 32
        last = self._last.offset + len(self._last) / 4 - 1
        self.debug("last sample:", last)
        self.debug("frame end:", self._frameEnd)
        self.debug("CRC: %08X" % self._crc)
        self.debug("bytes: %d" % self._bytes)
        if self._frameEnd != last:
            print 'ERROR: did not get all frames, %d missing' % (self._frameEnd - last)
        self.crc = self._crc
        Task.stop(self)

class SyncRunner:
    def __init__(self, task):
        self._task = task

    def run(self):
        self._loop = gobject.MainLoop()
        self._task.addListener(self)
        self._task.start()
        self._loop.run()

    def start(self):
        pass

    def progress(self, value):
        pass

    def stop(self):
        self._loop.quit()
