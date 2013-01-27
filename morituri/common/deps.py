# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import urllib

from morituri.extern.deps import deps


class DepsHandler(deps.DepsHandler):

    def __init__(self, name='morituri'):
        deps.DepsHandler.__init__(self, name)

        self.add(GStPython())

    def report(self, summary):
        reporter = os.environ.get('EMAIL_ADDRESS', None)
        get = "summary=%s" % urllib.quote(summary)
        if reporter:
            get += "&reporter=%s" % urllib.quote(reporter)
        return 'http://thomas.apestaart.org/morituri/trac/newticket?' + get


class GStPython(deps.Dependency):
    module = 'gst'
    name = "GStreamer Python bindings"
    homepage = "http://gstreamer.freedesktop.org"

    def Fedora_install(self, distro):
        return self.Fedora_yum('gstreamer-python')

    #def Ubuntu_install(self, distro):
    #    pass
