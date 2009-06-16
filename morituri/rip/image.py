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

from morituri.common import logcommand, task, checksum, accurip, program
from morituri.image import image, cue
from morituri.program import cdrdao, cdparanoia


class Verify(logcommand.LogCommand):
    summary = "verify image"

    def do(self, args):
        prog = program.Program()
        runner = task.SyncRunner()
        cache = accurip.AccuCache()

        for arg in args:
            cueImage = image.Image(arg)
            cueImage.setup(runner)

            url = cueImage.table.getAccurateRipURL()
            responses = cache.retrieve(url)

            return
            
            # FIXME: finish implementation
            prog.cuePath = arg
            prog.verifyImage(runner, responses) 

class Image(logcommand.LogCommand):
    summary = "handle images"

    subCommandClasses = [Verify, ]
