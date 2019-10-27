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
from whipper.common.accurip import get_db_entry, ACCURATERIP_URL

import logging
logger = logging.getLogger(__name__)


class Show(BaseCommand):
    summary = "show accuraterip data"
    description = """
retrieves and display accuraterip data from the given URL
"""

    def add_arguments(self):
        self.parser.add_argument('url', action='store',
                                 help="accuraterip URL to load data from")

    def do(self):
        responses = get_db_entry(self.options.url.lstrip(ACCURATERIP_URL))

        count = responses[0].num_tracks

        logger.info("found %d responses for %d tracks", len(responses), count)

        for (i, r) in enumerate(responses):
            if r.num_tracks != count:
                logger.warning("response %d has %d tracks instead of %d",
                               i, r.num_tracks, count)

        # checksum and confidence by track
        for track in range(count):
            print("Track %d:" % (track + 1))
            checksums = {}

            for (i, r) in enumerate(responses):
                if r.num_tracks != count:
                    continue

                assert len(r.checksums) == r.num_tracks
                assert len(r.confidences) == r.num_tracks

                entry = {"confidence": r.confidences[track], "response": i + 1}
                checksum = r.checksums[track]
                if checksum in checksums:
                    checksums[checksum].append(entry)
                else:
                    checksums[checksum] = [entry, ]

            # now sort track results in checksum by highest confidence
            sortedChecksums = []
            for checksum, entries in list(checksums.items()):
                highest = max(d['confidence'] for d in entries)
                sortedChecksums.append((highest, checksum))

            sortedChecksums.sort()
            sortedChecksums.reverse()

            for highest, checksum in sortedChecksums:
                print("  %d result(s) for checksum %s: %s" % (
                      len(checksums[checksum]),
                      checksum, checksums[checksum]))


class AccuRip(BaseCommand):
    summary = "handle AccurateRip information"
    description = """
Handle AccurateRip information. Retrieves AccurateRip disc entries and
displays diagnostic information.
"""
    subcommands = {
        'show': Show
    }
