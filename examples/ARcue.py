# -*- Mode: Python; test-case-name: morituri.test.test_header -*-
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

import sys
import optparse

import gobject
gobject.threads_init()
import gtk

from morituri.image import image
from morituri.common import task, crc

def gtkmain(taskk):
    progress = task.GtkProgressRunner()
    progress.connect('stop', lambda _: gtk.main_quit())

    window = gtk.Window()
    window.add(progress)
    window.show_all()

    progress.run(taskk)

    gtk.main()

def climain(taskk):
    runner = task.SyncRunner()

    runner.run(taskk)


def main(argv):
    parser = optparse.OptionParser()

    default = 'cli'
    parser.add_option('-r', '--runner',
        action="store", dest="runner",
        help="runner ('cli' or 'gtk', defaults to %s)" % default,
        default=default)

    options, args = parser.parse_args(argv[1:])

    path = 'test.cue'

    try:
        path = sys.argv[1]
    except IndexError:
        pass

    cueImage = image.Image(path)
    verifytask = image.ImageVerifyTask(cueImage)
    cuetask = image.AudioRipCRCTask(cueImage)

    if options.runner == 'cli':
        climain(verifytask)
        climain(cuetask)
    elif options.runner == 'gtk':
        gtkmain(verifytask)
        gtkmain(cuetask)

    for i, crc in enumerate(cuetask.crcs):
        print "Track %2d: %08x" % (i + 1, crc)

main(sys.argv)
