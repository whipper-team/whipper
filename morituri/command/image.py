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

import os
import sys

from morituri.command.basecommand import BaseCommand
from morituri.common import accurip, config, program
from morituri.common import encode
from morituri.extern.task import task
from morituri.image import image
from morituri.result import result

import logging
logger = logging.getLogger(__name__)


class Retag(BaseCommand):
    summary = "retag image files"
    description = """
Retags the image from the given .cue files with tags obtained from MusicBrainz.
"""

    def add_arguments(self):
        self.parser.add_argument('cuefile', nargs='+', action='store',
                                 help="cue file to load rip image from")
        self.parser.add_argument(
            '-R', '--release-id',
            action="store", dest="release_id",
            help="MusicBrainz release id to match to (if there are multiple)"
        )
        self.parser.add_argument(
            '-p', '--prompt',
            action="store_true", dest="prompt",
            help="Prompt if there are multiple matching releases"
        )
        self.parser.add_argument(
            '-c', '--country',
            action="store", dest="country",
            help="Filter releases by country"
        )

    def do(self):

        prog = program.Program(config.Config(), stdout=sys.stdout)
        runner = task.SyncRunner()

        for arg in self.options.cuefile:
            sys.stdout.write('Retagging image %r\n' % arg)
            arg = arg.decode('utf-8')
            cueImage = image.Image(arg)
            cueImage.setup(runner)

            mbdiscid = cueImage.table.getMusicBrainzDiscId()
            sys.stdout.write('MusicBrainz disc id is %s\n' % mbdiscid)

            sys.stdout.write("MusicBrainz lookup URL %s\n" %
                cueImage.table.getMusicBrainzSubmitURL())
            prog.metadata = prog.getMusicBrainz(cueImage.table, mbdiscid,
                release=self.options.release_id,
                country=self.options.country,
                prompt=self.options.prompt)

            if not prog.metadata:
                print 'Not in MusicBrainz database, skipping'
                continue

            prog.metadata.discid = mbdiscid

            # FIXME: this feels like we're poking at internals.
            prog.cuePath = arg
            prog.result = result.RipResult()
            for track in cueImage.table.tracks:
                path = cueImage.getRealPath(track.indexes[1].path)

                taglist = prog.getTagList(track.number)
                logger.debug(
                    'possibly retagging %r from cue path %r with taglist %r',
                    path, arg, taglist)
                t = encode.SafeRetagTask(path, taglist)
                runner.run(t)
                path = os.path.basename(path)
                if t.changed:
                    print 'Retagged %s' % path
                else:
                    print '%s already tagged correctly' % path
            print


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
        cache = accurip.AccuCache()

        for arg in self.options.cuefile:
            arg = arg.decode('utf-8')
            cueImage = image.Image(arg)
            cueImage.setup(runner)

            url = cueImage.table.getAccurateRipURL()
            responses = cache.retrieve(url)

            # FIXME: this feels like we're poking at internals.
            prog.cuePath = arg
            prog.result = result.RipResult()
            for track in cueImage.table.tracks:
                tr = result.TrackResult()
                tr.number = track.number
                prog.result.tracks.append(tr)

            prog.verifyImage(runner, responses)

            print "\n".join(prog.getAccurateRipResults()) + "\n"


class Image(BaseCommand):
    summary = "handle images"
    description = """
Handle disc images.  Disc images are described by a .cue file.
Disc images can be encoded to another format (for example, to make a
compressed encoding), retagged and verified.
"""
    subcommands = {
        'verify': Verify,
        'retag': Retag
    }
