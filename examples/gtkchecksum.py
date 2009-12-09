# -*- Mode: Python -*-
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

import gobject
gobject.threads_init()

import gtk

from morituri.common import task, checksum, taskgtk

def main(path, start, end):
    progress = taskgtk.GtkProgressRunner()
    progress.connect('stop', lambda _: gtk.main_quit())

    window = gtk.Window()
    window.add(progress)
    window.show_all()

    checksumtask = checksum.CRC32Task(path, start, end)
    progress.run(checksumtask)

    gtk.main()

    print "CRC: %08X" % checksumtask.checksum

path = 'test.flac'

start = 0
end = -1
try:
    path = unicode(sys.argv[1])
    start = int(sys.argv[2])
    end = int(sys.argv[3])
except IndexError:
    pass

main(path, start, end)
