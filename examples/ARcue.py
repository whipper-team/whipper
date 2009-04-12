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

import gobject
gobject.threads_init()

from morituri.image import image
from morituri.common import task, crc

def main(path):
    cueImage = image.Image(path)

    runner = task.SyncRunner()
    cuetask = image.AudioRipCRCTask(cueImage)

    runner.run(cuetask)

    for i, crc in enumerate(cuetask.crcs):
        print "Track %2d: %08x" % (i, crc)

path = 'test.cue'

try:
    path = sys.argv[1]
except IndexError:
    pass

main(path)
