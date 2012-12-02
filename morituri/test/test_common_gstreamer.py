# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.common import gstreamer

from morituri.test import common


class VersionTestCase(common.TestCase):

    def testGStreamer(self):
        version = gstreamer.gstreamerVersion()
        self.failUnless(version.startswith('0.'))

    def testGSTPython(self):
        version = gstreamer.gstPythonVersion()
        self.failUnless(version.startswith('0.'))

    def testFlacEnc(self):
        version = gstreamer.elementFactoryVersion('flacenc')
        self.failUnless(version.startswith('0.'))
