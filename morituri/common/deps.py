# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import urllib

from morituri.extern.deps import deps


class DepsHandler(deps.DepsHandler):

    def __init__(self, name='morituri'):
        deps.DepsHandler.__init__(self, name)

        self.add(GStPython())
        self.add(CDDB())
        self.add(SetupTools())
        self.add(PyCDIO())

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


class CDDB(deps.Dependency):
    module = 'CDDB'
    name = "python-CDDB"
    homepage = "http://cddb-py.sourceforge.net/"

    def Fedora_install(self, distro):
        return self.Fedora_yum('python-CDDB')

    def Ubuntu_install(self, distro):
        return self.Ubuntu_apt('python-cddb')


class SetupTools(deps.Dependency):
    module = 'pkg_resources'
    name = "python-setuptools"
    homepage = "http://pypi.python.org/pypi/setuptools"

    def Fedora_install(self, distro):
        return self.Fedora_yum('python-setuptools')


class PyCDIO(deps.Dependency):

    module = 'pycdio'
    name = "pycdio"
    homepage = "http://www.gnu.org/software/libcdio/"
    egg = 'pycdio'

    def Fedora_install(self, distro):
        return self.Fedora_yum('pycdio')

    def validate(self):
        version = self.version()
        if version == '0.18':
            return '''pycdio 0.18 does not work.
See http://savannah.gnu.org/bugs/?38185'''
