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

# EAC by default saves .cue files one directory up from the rip directories,
# and only uses the title for the file name.
# Move the .cue file into the corresponding directory, and rename it

import os
import sys

from morituri.image import cue

def move(path):
    print 'reading', path
    cuefile = cue.CueFile(path)
    cuefile.parse()

    track = cuefile.tracks[0]
    idx, file = track.getIndex(1)
    destdir = os.path.dirname(cuefile.getRealPath(file.path))

    if os.path.exists(destdir):
        dirname = os.path.basename(destdir)
        destination = os.path.join(destdir, dirname + '.cue')
        print 'moving %s to %s' % (path, destination)
        os.rename(path, destination)

for path in sys.argv[1:]:
    move(path)
