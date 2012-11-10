# -*- Mode: Python; test-case-name: morituri.test.test_common_encode -*-
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

import math
import os
import shutil
import tempfile

from morituri.common import common, log
from morituri.common import task as ctask

from morituri.extern.task import task, gstreamer


class Profile(object):
    name = None
    extension = None
    pipeline = None
    losless = None

    def test(self):
        """
        Test if this profile will work.
        Can check for elements, ...
        """
        pass


class FlacProfile(Profile):
    name = 'flac'
    extension = 'flac'
    pipeline = 'flacenc name=tagger quality=8'
    lossless = True

    # FIXME: we should do something better than just printing ERRORS

    def test(self):

        # here to avoid import gst eating our options
        import gst

        plugin = gst.registry_get_default().find_plugin('flac')
        if not plugin:
            print 'ERROR: cannot find flac plugin'
            return False

        versionTuple = tuple([int(x) for x in plugin.get_version().split('.')])
        if len(versionTuple) < 4:
            versionTuple = versionTuple + (0, )
        if versionTuple > (0, 10, 9, 0) and versionTuple <= (0, 10, 15, 0):
            print 'ERROR: flacenc between 0.10.9 and 0.10.15 has a bug'
            return False

        return True

# FIXME: ffenc_alac does not have merge_tags


class AlacProfile(Profile):
    name = 'alac'
    extension = 'alac'
    pipeline = 'ffenc_alac'
    lossless = True

# FIXME: wavenc does not have merge_tags


class WavProfile(Profile):
    name = 'wav'
    extension = 'wav'
    pipeline = 'wavenc'
    lossless = True


class WavpackProfile(Profile):
    name = 'wavpack'
    extension = 'wv'
    pipeline = 'wavpackenc bitrate=0 name=tagger'
    lossless = True


class MP3Profile(Profile):
    name = 'mp3'
    extension = 'mp3'
    pipeline = 'lame name=tagger quality=0 ! id3v2mux'
    lossless = False


class MP3VBRProfile(Profile):
    name = 'mp3vbr'
    extension = 'mp3'
    pipeline = 'lame name=tagger quality=0 vbr=new vbr-mean-bitrate=192 ! ' \
                'id3v2mux'
    lossless = False


class VorbisProfile(Profile):
    name = 'vorbis'
    extension = 'oga'
    pipeline = 'audioconvert ! vorbisenc name=tagger ! oggmux'
    lossless = False


PROFILES = {
    'wav': WavProfile,
    'flac': FlacProfile,
    'alac': AlacProfile,
    'wavpack': WavpackProfile,
}

LOSSY_PROFILES = {
    'mp3': MP3Profile,
    'mp3vbr': MP3VBRProfile,
    'vorbis': VorbisProfile,
}

ALL_PROFILES = PROFILES.copy()
ALL_PROFILES.update(LOSSY_PROFILES)


class EncodeTask(ctask.GstPipelineTask):
    """
    I am a task that encodes a .wav file.
    I set tags too.
    I also calculate the peak level of the track.

    @param peak: the peak volume, from 0.0 to 1.0.  This is the sqrt of the
                 peak power.
    @type  peak: float
    """

    logCategory = 'EncodeTask'

    description = 'Encoding'
    peak = None

    def __init__(self, inpath, outpath, profile, taglist=None, what="track"):
        """
        @param profile: encoding profile
        @type  profile: L{Profile}
        """
        assert type(inpath) is unicode, "inpath %r is not unicode" % inpath
        assert type(outpath) is unicode, \
            "outpath %r is not unicode" % outpath

        self._inpath = inpath
        self._outpath = outpath
        self._taglist = taglist

        self._level = None
        self._peakdB = None
        self._profile = profile

        self.description = "Encoding %s" % what
        self._profile.test()

    def getPipelineDesc(self):
        return '''
            filesrc location="%s" !
            decodebin name=decoder !
            audio/x-raw-int,width=16,depth=16,channels=2 !
            level name=level !
            %s ! identity name=identity !
            filesink location="%s" name=sink''' % (
                gstreamer.quoteParse(self._inpath).encode('utf-8'),
                self._profile.pipeline,
                gstreamer.quoteParse(self._outpath).encode('utf-8'))

    def parsed(self):
        tagger = self.pipeline.get_by_name('tagger')

        # set tags
        if tagger and self._taglist:
            # FIXME: under which conditions do we not have merge_tags ?
            # See for example comment saying wavenc did not have it.
            try:
                tagger.merge_tags(self._taglist, self.gst.TAG_MERGE_APPEND)
            except AttributeError, e:
                self.warning('Could not merge tags: %r',
                    log.getExceptionMessage(e))

    def paused(self):
        # get length
        identity = self.pipeline.get_by_name('identity')
        self.debug('query duration')
        try:
            length, qformat = identity.query_duration(self.gst.FORMAT_DEFAULT)
        except self.gst.QueryError, e:
            self.setException(e)
            self.stop()
            return


        # wavparse 0.10.14 returns in bytes
        if qformat == self.gst.FORMAT_BYTES:
            self.debug('query returned in BYTES format')
            length /= 4
        self.debug('total length: %r', length)
        self._length = length

        duration = None
        try:
            duration, qformat = identity.query_duration(self.gst.FORMAT_TIME)
        except self.gst.QueryError, e:
            self.debug('Could not query duration')
        self._duration = duration

        # set up level callbacks
        # FIXME: publicize bus and reuse it instead of regetting and adding ?
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()

        bus.connect('message::element', self._message_element_cb)
        self._level = self.pipeline.get_by_name('level')

        # set an interval that is smaller than the duration
        # FIXME: check level and make sure it emits level up to the last
        # sample, even if input is small
        interval = 1000000000L
        if interval < duration:
            interval = duration / 2
        self._level.set_property('interval', interval)
        # add a probe so we can track progress
        # we connect to level because this gives us offset in samples
        srcpad = self._level.get_static_pad('src')
        self.gst.debug('adding srcpad buffer probe to %r' % srcpad)
        ret = srcpad.add_buffer_probe(self._probe_handler)
        self.gst.debug('added srcpad buffer probe to %r: %r' % (srcpad, ret))

    def _probe_handler(self, pad, buffer):
        # update progress based on buffer offset (expected to be in samples)
        # versus length in samples
        # marshal to main thread
        self.schedule(0, self.setProgress,
            float(buffer.offset) / self._length)

        # don't drop the buffer
        return True

    def bus_eos_cb(self, bus, message):
        self.debug('eos, scheduling stop')
        self.schedule(0, self.stop)

    def _message_element_cb(self, bus, message):
        if message.src != self._level:
            return

        s = message.structure
        if s.get_name() != 'level':
            return


        if self._peakdB is None:
            self._peakdB = s['peak'][0]

        for p in s['peak']:
            if self._peakdB < p:
                self.log('higher peakdB found, now %r', self._peakdB)
                self._peakdB = p

        # FIXME: works around a bug on F-15 where buffer probes don't seem
        # to get triggered to update progress
        if self._duration is not None:
            self.schedule(0, self.setProgress,
                float(s['stream-time'] + s['duration']) / self._duration)

    def stopped(self):
        if self._peakdB is not None:
            self.debug('peakdB %r', self._peakdB)
            self.peak = math.sqrt(math.pow(10, self._peakdB / 10.0))
        else:
            self.warning('No peak found, something went wrong!')
            # workaround for when the file is too short to have volume ?
            # self.peak = 0.0


class TagReadTask(gstreamer.GstPipelineTask):
    """
    I am a task that reads tags.

    @ivar  taglist: the tag list read from the file.
    @type  taglist: L{gst.TagList}
    """

    logCategory = 'TagReadTask'

    description = 'Reading tags'

    taglist = None

    def __init__(self, path):
        """
        """
        assert type(path) is unicode, "path %r is not unicode" % path

        self._path = path

    def getPipelineDesc(self):
        return '''
            filesrc location="%s" !
            decodebin name=decoder !
            fakesink''' % (
                gstreamer.quoteParse(self._path).encode('utf-8'))

    def bus_eos_cb(self, bus, message):
        self.debug('eos, scheduling stop')
        self.schedule(0, self.stop)

    def bus_tag_cb(self, bus, message):
        taglist = message.parse_tag()
        self.taglist = taglist


class TagWriteTask(task.Task):
    """
    I am a task that retags an encoded file.
    """

    logCategory = 'TagWriteTask'

    description = 'Writing tags'

    def __init__(self, inpath, outpath, taglist=None):
        """
        """
        assert type(inpath) is unicode, "inpath %r is not unicode" % inpath
        assert type(outpath) is unicode, "outpath %r is not unicode" % outpath

        self._inpath = inpath
        self._outpath = outpath
        self._taglist = taglist

    def start(self, runner):
        task.Task.start(self, runner)

        # here to avoid import gst eating our options
        import gst

        self._pipeline = gst.parse_launch('''
            filesrc location="%s" !
            flactag name=tagger !
            filesink location="%s"''' % (
                gstreamer.quoteParse(self._inpath).encode('utf-8'),
                gstreamer.quoteParse(self._outpath).encode('utf-8')))

        # set tags
        tagger = self._pipeline.get_by_name('tagger')
        if self._taglist:
            tagger.merge_tags(self._taglist, gst.TAG_MERGE_APPEND)

        self.debug('pausing pipeline')
        self._pipeline.set_state(gst.STATE_PAUSED)
        self._pipeline.get_state()
        self.debug('paused pipeline')

        # add eos handling
        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', self._message_eos_cb)

        self.debug('scheduling setting to play')
        # since set_state returns non-False, adding it as timeout_add
        # will repeatedly call it, and block the main loop; so
        #   gobject.timeout_add(0L, self._pipeline.set_state,
        #       gst.STATE_PLAYING)
        # would not work.

        def play():
            self._pipeline.set_state(gst.STATE_PLAYING)
            return False
        self.schedule(0, play)

        #self._pipeline.set_state(gst.STATE_PLAYING)
        self.debug('scheduled setting to play')

    def _message_eos_cb(self, bus, message):
        self.debug('eos, scheduling stop')
        self.schedule(0, self.stop)

    def stop(self):
        # here to avoid import gst eating our options
        import gst

        self.debug('stopping')
        self.debug('setting state to NULL')
        self._pipeline.set_state(gst.STATE_NULL)
        self.debug('set state to NULL')
        task.Task.stop(self)


class SafeRetagTask(task.MultiSeparateTask):
    """
    I am a task that retags an encoded file safely in place.
    First of all, if the new tags are the same as the old ones, it doesn't
    do anything.
    If the tags are not the same, then the file gets retagged, but only
    if the decodes of the original and retagged file checksum the same.

    @ivar changed: True if the tags have changed (and hence an output file is
                   generated)
    """

    logCategory = 'SafeRetagTask'

    description = 'Retagging'

    changed = False

    def __init__(self, path, taglist=None):
        """
        """
        assert type(path) is unicode, "path %r is not unicode" % path

        task.MultiSeparateTask.__init__(self)

        self._path = path
        self._taglist = taglist.copy()

        self.tasks = [TagReadTask(path), ]

    def stopped(self, taskk):
        from morituri.common import checksum

        if not taskk.exception:
            # Check if the tags are different or not
            if taskk == self.tasks[0]:
                taglist = taskk.taglist.copy()
                if common.tagListEquals(taglist, self._taglist):
                    self.debug('tags are already fine: %r',
                        common.tagListToDict(taglist))
                else:
                    # need to retag
                    self.debug('tags need to be rewritten')
                    self.debug('Current tags: %r, new tags: %r',
                        common.tagListToDict(taglist),
                        common.tagListToDict(self._taglist))
                    assert common.tagListToDict(taglist) \
                        != common.tagListToDict(self._taglist)
                    self.tasks.append(checksum.CRC32Task(self._path))
                    self._fd, self._tmppath = tempfile.mkstemp(
                        dir=os.path.dirname(self._path), suffix=u'.morituri')
                    self.tasks.append(TagWriteTask(self._path,
                        self._tmppath, self._taglist))
                    self.tasks.append(checksum.CRC32Task(self._tmppath))
                    self.tasks.append(TagReadTask(self._tmppath))
            elif len(self.tasks) > 1 and taskk == self.tasks[4]:
                if common.tagListEquals(self.tasks[4].taglist, self._taglist):
                    self.debug('tags written successfully')
                    c1 = self.tasks[1].checksum
                    c2 = self.tasks[3].checksum
                    self.debug('comparing checksums %08x and %08x' % (c1, c2))
                    if c1 == c2:
                        # data is fine, so we can now move
                        # but first, copy original mode to our temporary file
                        shutil.copymode(self._path, self._tmppath)
                        self.debug('moving temporary file to %r' % self._path)
                        os.rename(self._tmppath, self._path)
                        self.changed = True
                    else:
                        # FIXME: don't raise TypeError
                        e = TypeError("Checksums failed")
                        self.setAndRaiseException(e)
                else:
                    self.debug('failed to update tags, only have %r',
                        common.tagListToDict(self.tasks[4].taglist))
                    os.unlink(self._tmppath)
                    e = TypeError("Tags not written")
                    self.setAndRaiseException(e)

        task.MultiSeparateTask.stopped(self, taskk)
