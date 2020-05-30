# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of whipper.
#
# whipper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# whipper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with whipper.  If not, see <http://www.gnu.org/licenses/>.

from whipper.command.basecommand import BaseCommand
from whipper.common import accurip, config, program
from whipper.extern.task import task
from whipper.image import image
from whipper.result import result

import logging
logger = logging.getLogger(__name__)


class Verify(BaseCommand):
    summary = "verify image"
    description = """
Verifies the image from the given .cue files against the AccurateRip database.
"""

    def add_arguments(self):
        self.parser.add_argument('cuefile', nargs='+', action='store',
                                 help="cue file to load rip image from")

    def do(self):
        prog = program.Program(config.Config())
        runner = task.SyncRunner()

        for arg in self.options.cuefile:
            cueImage = image.Image(arg)
            cueImage.setup(runner)

            # FIXME: this feels like we're poking at internals.
            prog.cuePath = arg
            prog.result = result.RipResult()
            for track in cueImage.table.tracks:
                tr = result.TrackResult()
                tr.number = track.number
                prog.result.tracks.append(tr)

            verified = False
            try:
                verified = prog.verifyImage(runner, cueImage.table)
            except accurip.EntryNotFound:
                print('AccurateRip entry not found')
            accurip.print_report(prog.result)
            if not verified:
                raise SystemExit(1)


class Image(BaseCommand):
    summary = "handle images"
    description = """
Handle disc images. Disc images are described by a .cue file.
Disc images can be verified.
"""
    subcommands = {
        'verify': Verify,
    }
