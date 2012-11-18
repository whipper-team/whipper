# -*- Mode: Python; test-case-name: test_gstreamer -*-
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

import task

def quoteParse(path):
    """
    Quote a path for use in gst.parse_launch.
    """
    # Make sure double quotes and backslashes are escaped.  See
    # morituri.test.test_common_checksum.NormalPathTestCase

    return path.replace('\\', '\\\\').replace('"', '\\"')


class GstException(Exception):
    def __init__(self, gerror, debug):
        self.args = (gerror, debug, )
        self.gerror = gerror
        self.debug = debug

    def __repr__(self):
        return '<GstException: GError %r, debug %r>' % (
            self.gerror.message, self.debug)

class GstPipelineTask(task.Task):
    """
    I am a base class for tasks that use a GStreamer pipeline.

    I handle errors and raise them appropriately.

    @cvar gst:      the GStreamer module, so code does not have to import gst
                    as a module in code everywhere to avoid option stealing.
    @cvar playing:  whether the pipeline should be set to playing after
                    paused.  Some pipelines don't need to play for a task
                    to be done (for example, querying length)
    @type playing:  bool
    @type pipeline: L{gst.Pipeline}
    @type bus:      L{gst.Bus}
    """

    gst = None
    playing = True
    pipeline = None
    bus = None

    ### task.Task implementations
    def start(self, runner):
        import gst
        self.gst = gst

        task.Task.start(self, runner)

        self.getPipeline()

        self.bus = self.pipeline.get_bus()
        # FIXME: remove this
        self._bus = self.bus
        self.gst.debug('got bus %r' % self.bus)

        # a signal watch calls callbacks from an idle loop
        # self.bus.add_signal_watch()

        # sync emission triggers sync-message signals which calls callbacks
        # from the thread that signals, but happens immediately
        self.bus.enable_sync_message_emission()
        self.bus.connect('sync-message::eos', self.bus_eos_cb)
        self.bus.connect('sync-message::tag', self.bus_tag_cb)
        self.bus.connect('sync-message::error', self.bus_error_cb)

        self.parsed()

        self.debug('setting pipeline to PAUSED')
        self.pipeline.set_state(gst.STATE_PAUSED)
        self.debug('set pipeline to PAUSED')
        # FIXME: this can block
        ret = self.pipeline.get_state()
        self.debug('got pipeline to PAUSED: %r', ret)

        # GStreamer tasks could already be done in paused, and not
        # need playing.
        if self.exception:
            raise self.exception

        done = self.paused()

        if done:
            self.debug('paused() is done')
        else:
            self.debug('paused() wants more')
            self.play()

    def play(self):
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self._pipeline.set_state,
        #       gst.STATE_PLAYING)
        # would not work.
        def playLater():
            if self.exception:
                self.debug('playLater: exception was raised, not playing')
                self.stop()
                return False

            self.debug('setting pipeline to PLAYING')
            self.pipeline.set_state(self.gst.STATE_PLAYING)
            self.debug('set pipeline to PLAYING')
            return False

        if self.playing:
            self.debug('schedule playLater()')
            self.schedule(0, playLater)

    def stop(self):
        self.debug('stopping')


        # FIXME: in theory this should help clean up properly,
        # but in practice we can still get
        # python: /builddir/build/BUILD/Python-2.7/Python/pystate.c:595: PyGILState_Ensure: Assertion `autoInterpreterState' failed.

        self.pipeline.set_state(self.gst.STATE_READY)
        self.debug('set pipeline to READY')
        # FIXME: this can block
        ret = self.pipeline.get_state()
        self.debug('got pipeline to READY: %r', ret)

        self.debug('setting state to NULL')
        self.pipeline.set_state(self.gst.STATE_NULL)
        self.debug('set state to NULL')
        self.stopped()
        task.Task.stop(self)

    ### subclass optional implementations
    def getPipeline(self):
        desc = self.getPipelineDesc()

        self.debug('creating pipeline %r', desc)
        self.pipeline = self.gst.parse_launch(desc)

    def getPipelineDesc(self):
        """
        subclasses should implement this to provide a pipeline description.

        @rtype: str
        """
        raise NotImplementedError

    def parsed(self):
        """
        Called after parsing/getting the pipeline but before setting it to
        paused.
        """
        pass

    def paused(self):
        """
        Called after pipeline is paused.

        If this returns True, the task is done and
        should not continue going to PLAYING.
        """
        pass

    def stopped(self):
        """
        Called after pipeline is set back to NULL but before chaining up to
        stop()
        """
        pass

    def bus_eos_cb(self, bus, message):
        """
        Called synchronously (ie from messaging thread) on eos message.

        Override me to handle eos
        """
        pass

    def bus_tag_cb(self, bus, message):
        """
        Called synchronously (ie from messaging thread) on tag message.

        Override me to handle tags.
        """
        pass

    def bus_error_cb(self, bus, message):
        """
        Called synchronously (ie from messaging thread) on error message.
        """
        self.debug('bus_error_cb: bus %r, message %r' % (bus, message))
        if self.exception:
            self.debug('bus_error_cb: already got an exception, ignoring')
            return

        exc = GstException(*message.parse_error())
        self.setAndRaiseException(exc)
        self.debug('error, scheduling stop')
        self.schedule(0, self.stop)

    def query_length(self, element):
        """
        Query the length of the pipeline in samples, for progress updates.
        To be called from paused()
        """
        # get duration
        self.debug('query duration')
        try:
            duration, qformat = element.query_duration(self.gst.FORMAT_DEFAULT)
        except self.gst.QueryError, e:
            # Fall back to time; for example, oggdemux/vorbisdec only supports
            # TIME
            try:
                duration, qformat = element.query_duration(self.gst.FORMAT_TIME)
            except self.gst.QueryError, e:
                self.setException(e)
                # schedule it, otherwise runner can get set to None before
                # we're done starting
                self.schedule(0, self.stop)
                return

        # wavparse 0.10.14 returns in bytes
        if qformat == self.gst.FORMAT_BYTES:
            self.debug('query returned in BYTES format')
            duration /= 4

        if qformat == self.gst.FORMAT_TIME:
            rate = None
            self.debug('query returned in TIME format')
            # we need sample rate
            pads = list(element.pads())
            sink = element.get_by_name('sink')
            pads += list(sink.pads())

            for pad in pads:
                caps = pad.get_negotiated_caps()
                print caps[0].keys()
                if 'rate' in caps[0].keys():
                    rate = caps[0]['rate']
                    self.debug('Sample rate: %d Hz', rate)

            if not rate:
                raise KeyError(
                    'Cannot find sample rate, cannot convert to samples')

            duration = int(float(rate) * (float(duration) / self.gst.SECOND))

        self.debug('total duration: %r', duration)

        return duration


