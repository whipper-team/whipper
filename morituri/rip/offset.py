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
import tempfile

import gobject
gobject.threads_init()

from morituri.common import logcommand, task, checksum
from morituri.image import image
from morituri.program import cdrdao, cdparanoia


class Find(logcommand.LogCommand):
    summary = "find drive read offset"
    description = """Find drive's read offset by ripping tracks from a
CD in the AccurateRip database."""

    def addOptions(self):
        # see http://www.accuraterip.com/driveoffsets.htm
        default = "0, 6, 12, 48, 91, 97, 102, 108, 120, " + \
            "564, 594, 667, 685, 691, 704, 738, 1194, 1292, 1336, 1776, -582"
        self.parser.add_option('-o', '--offsets',
            action="store", dest="offsets",
            help="list of offsets, comma-separated, "
                "colon-separated for ranges (defaults to %s)" % default,
            default=default)

    def handleOptions(self, options):
        self.options = options
        self._offsets = []
        blocks = options.offsets.split(',')
        for b in blocks:
            if ':' in b:
                a, b = b.split(':')
                self._offsets.extend(range(int(a), int(b) + 1))
            else:
                self._offsets.append(int(b))

        self.debug('Trying with offsets %r', self._offsets)

    def do(self, args):
        runner = task.SyncRunner()

        # first get the Table Of Contents of the CD
        t = cdrdao.ReadTOCTask()

        runner.run(t)
        table = t.table

        self.debug("CDDB disc id: %r", table.getCDDBDiscId())
        url = table.getAccurateRipURL()
        self.debug("AccurateRip URL: %s", url)

        # FIXME: download url as a task too
        responses = []
        import urllib2
        try:
            handle = urllib2.urlopen(url)
            data = handle.read()
            responses = accurip.getAccurateRipResponses(data)
        except urllib2.HTTPError, e:
            if e.code == 404:
                print 'Album not found in AccurateRip database.'
                return 1
            else:
                raise

        if responses:
            self.debug('%d AccurateRip reponses found.' % len(responses))

            if responses[0].cddbDiscId != table.getCDDBDiscId():
                self.warning("AccurateRip response discid different: %s",
                    responses[0].cddbDiscId)

        # now rip the first track at various offsets, calculating AccurateRip
        # CRC, and matching it against the retrieved ones
        
        def match(archecksum, track, responses):
            for i, r in enumerate(responses):
                if archecksum == r.checksums[track - 1]:
                    return archecksum, i

            return None, None

        for offset in self._offsets:
            print 'Trying read offset %d ...' % offset
            archecksum = self._arcs(runner, table, 1, offset)

            self.debug('AR checksum calculated: %s' % archecksum)

            c, i = match(archecksum, 1, responses)
            if c:
                count = 1
                self.debug('MATCHED against response %d' % i)
                print 'Offset of device is likely %d, confirming ...' % offset

                # now try and rip all other tracks as well
                for track in range(2, len(table.tracks) + 1):
                    archecksum = self._arcs(runner, table, track, offset)
                    c, i = match(archecksum, track, responses)
                    if c:
                        self.debug('MATCHED track %d against response %d' % (
                            track, i))
                        count += 1

                if count == len(table.tracks):
                    print
                    print 'Read offset of device is: %d.' % offset
                    return 0
                else:
                    print 'Only %d of %d tracks matched, continuing ...' % (
                        count, len(table.tracks))
                    
        print 'No matching offset found.'
        print 'Consider trying again with a different disc.'
                 
    def _arcs(self, runner, table, track, offset):
        # rips the track with the given offset, return the arcs checksum
        self.debug('Ripping track %r with offset %d ...', track, offset)

        fd, path = tempfile.mkstemp(
            suffix='.track%02d.offset%d.morituri.wav' % (
                track, offset))
        os.close(fd)

        t = cdparanoia.ReadTrackTask(path, table, table.getTrackStart(track),
            table.getTrackEnd(track), offset)
        t.description = 'Ripping track %d with read offset %d' % (
            track, offset)
        runner.run(t)

        t = checksum.AccurateRipChecksumTask(path, trackNumber=track,
            trackCount=len(table.tracks))
        runner.run(t)
        
        os.unlink(path)
        return "%08x" % t.checksum

class Offset(logcommand.LogCommand):
    summary = "handle drive offsets"

    subCommandClasses = [Find, ]


