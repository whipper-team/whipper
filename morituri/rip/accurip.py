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

from morituri.common import logcommand, accurip


class Show(logcommand.LogCommand):

    summary = "show accuraterip data"

    def do(self, args):

        try:
            url = args[0]
        except IndexError:
            self.stdout.write('Please specify an accuraterip URL.\n')
            return 3

        cache = accurip.AccuCache()
        responses = cache.retrieve(url)

        count = responses[0].trackCount

        self.stdout.write("Found %d responses for %d tracks\n\n" % (
            len(responses), count))

        for (i, r) in enumerate(responses):
            if r.trackCount != count:
                self.stdout.write(
                    "Warning: response %d has %d tracks instead of %d\n" % (
                        i, r.trackCount, count))


        # checksum and confidence by track
        for track in range(count):
            self.stdout.write("Track %d:\n" % (track + 1))
            checksums = {}

            for (i, r) in enumerate(responses):
                if r.trackCount != count:
                    continue

                assert len(r.checksums) == r.trackCount
                assert len(r.confidences) == r.trackCount

                entry = {}
                entry["confidence"] = r.confidences[track]
                entry["response"] = i + 1
                checksum = r.checksums[track]
                if checksum in checksums:
                    checksums[checksum].append(entry)
                else:
                    checksums[checksum] = [entry, ]

            # now sort track results in checksum by highest confidence
            sortedChecksums = []
            for checksum, entries in checksums.items():
                highest = max(d['confidence'] for d in entries)
                sortedChecksums.append((highest, checksum))

            sortedChecksums.sort()
            sortedChecksums.reverse()

            for highest, checksum in sortedChecksums:
                self.stdout.write("  %d result(s) for checksum %s: %s\n" % (
                    len(checksums[checksum]), checksum,
                    str(checksums[checksum])))


class AccuRip(logcommand.LogCommand):
    description = "Handle AccurateRip information."

    subCommandClasses = [Show, ]
