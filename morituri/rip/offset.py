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

from morituri.common import logcommand, accurip, drive, program
from morituri.program import cdrdao, cdparanoia

from morituri.extern.task import task

# see http://www.accuraterip.com/driveoffsets.htm
# and misc/offsets.py
OFFSETS = "+6, +48, +102, +667, +12, +30, +618, +594, +738, -472, " + \
          "+98, +116, +96, +733, +120, +691, +685, +97, +600, " + \
          "+690, +1292, +99, +676, +686, +1182, -24, +704, +572, " + \
          "+688, +91, +696, +103, -491, +689, +145, +708, +697, " + \
          "+564, +86, +679, +355, -496, -1164, +1160, +694, 0, " + \
          "-436, +79, +94, +684, +681, +106, +692, +943, +1194, " + \
          "+92, +117, +680, +682, +1268, +678, -582, +1473, +1279, " + \
          "-54, +1508, +740, +1272, +534, +976, +687, +675, +1303, " + \
          "+674, +1263, +108, +974, +122, +111, -489, +772, +732, " + \
          "-495, -494, +975, +935, +87, +668, +1776, +1364, +1336, " + \
          "+1127"


class Find(logcommand.LogCommand):
    summary = "find drive read offset"
    description = """Find drive's read offset by ripping tracks from a
CD in the AccurateRip database."""

    def addOptions(self):
        default = OFFSETS
        self.parser.add_option('-o', '--offsets',
            action="store", dest="offsets",
            help="list of offsets, comma-separated, "
                "colon-separated for ranges (defaults to %s)" % default,
            default=default)
        self.parser.add_option('-d', '--device',
            action="store", dest="device",
            help="CD-DA device")

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

        if not options.device:
            drives = drive.getAllDevicePaths()
            if not drives:
                self.error('No CD-DA drives found!')
                return 3

            # pick the first
            self.options.device = drives[0]

        # this can be a symlink to another device

    def do(self, args):
        prog = program.Program()
        runner = task.SyncRunner()

        device = self.options.device

        # if necessary, load and unmount
        self.stdout.write('Checking device %s\n' % device)

        prog.loadDevice(device)
        prog.unmountDevice(device)

        # first get the Table Of Contents of the CD
        t = cdrdao.ReadTOCTask(device=device)

        try:
            runner.run(t)
        except cdrdao.DeviceOpenException, e:
            self.error(e.msg)
            return 3

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
                self.stdout.write(
                    'Album not found in AccurateRip database.\n')
                return 1
            else:
                raise

        if responses:
            self.debug('%d AccurateRip responses found.' % len(responses))

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
            self.stdout.write('Trying read offset %d ...\n' % offset)
            try:
                archecksum = self._arcs(runner, table, 1, offset)
            except task.TaskException, e:
                if isinstance(e.exception, cdparanoia.FileSizeError):
                    self.stdout.write(
                        'WARNING: cannot rip with offset %d...\n' % offset)
                    continue
                self.warning("Unknown exception for offset %d: %r" % (
                    offset, e))
                self.stdout.write(
                    'WARNING: cannot rip with offset %d...\n' % offset)
                continue

            self.debug('AR checksum calculated: %s' % archecksum)

            c, i = match(archecksum, 1, responses)
            if c:
                count = 1
                self.debug('MATCHED against response %d' % i)
                self.stdout.write(
                    'Offset of device is likely %d, confirming ...\n' %
                        offset)

                # now try and rip all other tracks as well
                for track in range(2, len(table.tracks) + 1):
                    try:
                        archecksum = self._arcs(runner, table, track, offset)
                    except task.TaskException, e:
                        if isinstance(e.exception, cdparanoia.FileSizeError):
                            self.stdout.write(
                                'WARNING: cannot rip with offset %d...\n' %
                                offset)
                            continue

                    c, i = match(archecksum, track, responses)
                    if c:
                        self.debug('MATCHED track %d against response %d' % (
                            track, i))
                        count += 1

                if count == len(table.tracks):
                    self.stdout.write('\nRead offset of device is: %d.\n' %
                        offset)
                    return 0
                else:
                    self.stdout.write(
                        'Only %d of %d tracks matched, continuing ...\n' % (
                        count, len(table.tracks)))

        self.stdout.write('No matching offset found.\n')
        self.stdout.write('Consider trying again with a different disc.\n')

    def _arcs(self, runner, table, track, offset):
        # rips the track with the given offset, return the arcs checksum
        self.debug('Ripping track %r with offset %d ...', track, offset)

        fd, path = tempfile.mkstemp(
            suffix=u'.track%02d.offset%d.morituri.wav' % (
                track, offset))
        os.close(fd)

        t = cdparanoia.ReadTrackTask(path, table,
            table.getTrackStart(track), table.getTrackEnd(track),
            offset=offset, device=self.options.device)
        t.description = 'Ripping track %d with read offset %d' % (
            track, offset)
        runner.run(t)

        # here to avoid import gst eating our options
        from morituri.common import checksum

        t = checksum.AccurateRipChecksumTask(path, trackNumber=track,
            trackCount=len(table.tracks))
        runner.run(t)

        os.unlink(path)
        return "%08x" % t.checksum


class Offset(logcommand.LogCommand):
    summary = "handle drive offsets"

    subCommandClasses = [Find, ]
