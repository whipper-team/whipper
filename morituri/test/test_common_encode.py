# -*- Mode: Python; test-case-name: morituri.test.test_common_encode -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import tempfile

import gobject
gobject.threads_init()

import gst

from morituri.common import encode

from morituri.extern.task import task, gstreamer

from morituri.test import common


class PathTestCase(common.TestCase):

    def _testSuffix(self, suffix):
        # because of https://bugzilla.gnome.org/show_bug.cgi?id=688625
        # we first create the file with a 'normal' filename, then rename
        self.runner = task.SyncRunner(verbose=False)
        fd, path = tempfile.mkstemp()

        cmd = "gst-launch " \
            "audiotestsrc num-buffers=100 samplesperbuffer=1024 ! " \
            "audioconvert ! audio/x-raw-int,width=16,depth=16,channels =2 ! " \
            "wavenc ! " \
            "filesink location=\"%s\" > /dev/null 2>&1" % (
            gstreamer.quoteParse(path).encode('utf-8'), )
        self.debug('Running cmd %r' % cmd)
        os.system(cmd)
        self.failUnless(os.path.exists(path))
        os.close(fd)

        fd, newpath = tempfile.mkstemp(suffix=suffix)
        os.rename(path, newpath)

        encodetask = encode.EncodeTask(newpath, newpath + '.out',
            encode.WavProfile())
        self.runner.run(encodetask, verbose=False)
        os.close(fd)
        os.unlink(newpath)
        os.unlink(newpath + '.out')


class UnicodePathTestCase(PathTestCase, common.UnicodeTestMixin):

    def testUnicodePath(self):
        # this test makes sure we can checksum a unicode path
        self._testSuffix(u'.morituri.test_encode.B\xeate Noire')


class NormalPathTestCase(PathTestCase):

    def testSingleQuote(self):
        self._testSuffix(u".morituri.test_encode.Guns 'N Roses")

    def testDoubleQuote(self):
        self._testSuffix(u'.morituri.test_encode.12" edit')


class TagReadTestCase(common.TestCase):

    def testRead(self):
        path = os.path.join(os.path.dirname(__file__), u'track.flac')
        self.runner = task.SyncRunner(verbose=False)
        t = encode.TagReadTask(path)
        self.runner.run(t)
        self.failUnless(t.taglist)
        self.assertEquals(t.taglist['audio-codec'], 'FLAC')
        self.assertEquals(t.taglist['description'], 'audiotest wave')


class TagWriteTestCase(common.TestCase):

    def testWrite(self):
        fd, inpath = tempfile.mkstemp(suffix=u'.morituri.tagwrite.flac')

        # wave is pink-noise because a pure sine is encoded too efficiently
        # by flacenc and triggers not enough frames in parsing
        # FIXME: file a bug for this in GStreamer
        os.system('gst-launch '
            'audiotestsrc '
                'wave=pink-noise num-buffers=10 samplesperbuffer=588 ! '
            'audioconvert ! '
            'audio/x-raw-int,channels=2,width=16,height=16,rate=44100 ! '
            'flacenc ! filesink location=%s > /dev/null 2>&1' % inpath)
        os.close(fd)

        fd, outpath = tempfile.mkstemp(suffix=u'.morituri.tagwrite.flac')
        self.runner = task.SyncRunner(verbose=False)
        taglist = gst.TagList()
        taglist[gst.TAG_ARTIST] = 'Artist'
        taglist[gst.TAG_TITLE] = 'Title'

        t = encode.TagWriteTask(inpath, outpath, taglist)
        self.runner.run(t)

        t = encode.TagReadTask(outpath)
        self.runner.run(t)
        self.failUnless(t.taglist)
        self.assertEquals(t.taglist['audio-codec'], 'FLAC')
        self.assertEquals(t.taglist['description'], 'audiotest wave')
        self.assertEquals(t.taglist[gst.TAG_ARTIST], 'Artist')
        self.assertEquals(t.taglist[gst.TAG_TITLE], 'Title')

        os.unlink(inpath)
        os.unlink(outpath)


class SafeRetagTestCase(common.TestCase):

    def setUp(self):
        self._fd, self._path = tempfile.mkstemp(suffix=u'.morituri.retag.flac')

        os.system('gst-launch '
            'audiotestsrc '
                'num-buffers=40 samplesperbuffer=588 wave=pink-noise ! '
            'audioconvert ! '
            'audio/x-raw-int,channels=2,width=16,height=16,rate=44100 ! '
            'flacenc ! filesink location=%s > /dev/null 2>&1' % self._path)
        os.close(self._fd)
        self.runner = task.SyncRunner(verbose=False)

    def tearDown(self):
        os.unlink(self._path)

    def testNoChange(self):
        taglist = gst.TagList()
        taglist[gst.TAG_DESCRIPTION] = 'audiotest wave'
        taglist[gst.TAG_AUDIO_CODEC] = 'FLAC'

        t = encode.SafeRetagTask(self._path, taglist)
        self.runner.run(t)

    def testChange(self):
        taglist = gst.TagList()
        taglist[gst.TAG_DESCRIPTION] = 'audiotest retagged'
        taglist[gst.TAG_AUDIO_CODEC] = 'FLAC'
        taglist[gst.TAG_ARTIST] = 'Artist'

        t = encode.SafeRetagTask(self._path, taglist)
        self.runner.run(t)
