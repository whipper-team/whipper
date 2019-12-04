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

import argparse
import os
import tempfile
import logging
from whipper.command.basecommand import BaseCommand
from whipper.common import accurip, common, config, drive
from whipper.common import task as ctask
from whipper.program import arc, cdrdao, cdparanoia, utils
from whipper.extern.task import task

logger = logging.getLogger(__name__)

# see http://www.accuraterip.com/driveoffsets.htm
# and misc/offsets.py
OFFSETS = ("+6, +667, +48, +102, +12, +30, +103, +618, +96, +594, "
           "+738, +98, -472, +116, +733, +696, +120, +691, +685, "
           "+99, +97, +600, +676, +690, +1292, +702, +686, -24, "
           "+704, +697, +572, +1182, +688, +91, -491, +145, +689, "
           "+564, +708, +86, +355, +79, -496, +679, -1164, 0, "
           "+1160, -436, +694, +684, +94, +1194, +106, +681, "
           "+117, +692, +943, +92, +680, +678, +682, +1268, +1279, "
           "+1473, -582, -54, +674, +687, +1272, +1263, +1508, "
           "+675, +534, +740, +122, -489, +974, +976, +1303, "
           "+108, +1130, +111, +739, +732, -589, -495, -494, "
           "+975, +961, +935, +87, +668, +234, +1776, +138, +1364, "
           "+1336, +1262, +1127")


class Find(BaseCommand):
    summary = "find drive read offset"
    description = """Find drive's read offset by ripping tracks from a
CD in the AccurateRip database."""
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    device_option = True

    def add_arguments(self):
        self.parser.add_argument(
            '-o', '--offsets',
            action="store", dest="offsets", default=OFFSETS,
            help="list of offsets, comma-separated, colon-separated for ranges"
        )

    def handle_arguments(self):
        self._offsets = []
        blocks = self.options.offsets.split(',')
        for b in blocks:
            if ':' in b:
                a, b = b.split(':')
                self._offsets.extend(list(range(int(a), int(b) + 1)))
            else:
                self._offsets.append(int(b))

        logger.debug('trying with offsets %r', self._offsets)

    def do(self):
        runner = ctask.SyncRunner()

        device = self.options.device

        # if necessary, load and unmount
        logger.info('checking device %s', device)

        utils.load_device(device)
        utils.unmount_device(device)

        # first get the Table Of Contents of the CD
        t = cdrdao.ReadTOCTask(device)
        runner.run(t)
        table = t.toc.table

        logger.debug("CDDB disc id: %r", table.getCDDBDiscId())
        try:
            responses = accurip.get_db_entry(table.accuraterip_path())
        except accurip.EntryNotFound:
            logger.warning("AccurateRip entry not found: drive offset "
                           "can't be determined, try again with another disc")
            return None

        if responses:
            logger.debug('%d AccurateRip responses found.', len(responses))
            if responses[0].cddbDiscId != table.getCDDBDiscId():
                logger.warning("AccurateRip response discid different: %s",
                               responses[0].cddbDiscId)

        # now rip the first track at various offsets, calculating AccurateRip
        # CRC, and matching it against the retrieved ones

        # archecksums is a tuple of accuraterip checksums: (v1, v2)
        def match(archecksums, track, responses):
            for i, r in enumerate(responses):
                for checksum in archecksums:
                    if checksum == r.checksums[track - 1]:
                        return checksum, i

            return None, None

        for offset in self._offsets:
            logger.info('trying read offset %d...', offset)
            try:
                archecksums = self._arcs(runner, table, 1, offset)
            except task.TaskException as e:

                # let MissingDependency fall through
                if isinstance(e.exception, common.MissingDependencyException):
                    raise e

                if isinstance(e.exception, cdparanoia.FileSizeError):
                    logger.warning('cannot rip with offset %d...', offset)
                    continue

                logger.warning("unknown task exception for offset %d: %s",
                               offset, e)
                logger.warning('cannot rip with offset %d...', offset)
                continue

            logger.debug('AR checksums calculated: %s', archecksums)

            c, i = match(archecksums, 1, responses)
            if c:
                count = 1
                logger.debug('matched against response %d', i)
                logger.info('offset of device is likely %d, confirming...',
                            offset)

                # now try and rip all other tracks as well, except for the
                # last one (to avoid readers that can't do overread
                for track in range(2, (len(table.tracks) + 1) - 1):
                    try:
                        archecksums = self._arcs(runner, table, track, offset)
                    except task.TaskException as e:
                        if isinstance(e.exception, cdparanoia.FileSizeError):
                            logger.warning('cannot rip with offset %d...',
                                           offset)
                            continue

                    c, i = match(archecksums, track, responses)
                    if c:
                        logger.debug('matched track %d against response %d',
                                     track, i)
                        count += 1

                if count == len(table.tracks) - 1:
                    self._foundOffset(device, offset)
                    return 0
                else:
                    logger.warning('only %d of %d tracks matched, '
                                   'continuing...', count,
                                   len(table.tracks))

        logger.error('no matching offset found. '
                     'Consider trying again with a different disc')

        return None

    def _arcs(self, runner, table, track, offset):
        # rips the track with the given offset, return the arcs checksums
        logger.debug('ripping track %r with offset %d...', track, offset)

        fd, path = tempfile.mkstemp(
            suffix='.track%02d.offset%d.whipper.wav' % (
                track, offset))
        os.close(fd)

        t = cdparanoia.ReadTrackTask(path, table,
                                     table.getTrackStart(
                                         track), table.getTrackEnd(track),
                                     overread=False, offset=offset,
                                     device=self.options.device)
        t.description = 'Ripping track %d with read offset %d' % (
            track, offset)
        runner.run(t)

        v1, v2 = arc.accuraterip_checksum(path, track, len(table.tracks))

        os.unlink(path)
        return "%08x" % v1, "%08x" % v2

    @staticmethod
    def _foundOffset(device, offset):
        print('\nRead offset of device is: %d.' % offset)

        info = drive.getDeviceInfo(device)
        if not info:
            logger.error('offset not saved: '
                         'could not get device info (requires pycdio)')
            return

        logger.info('adding read offset to configuration file')

        config.Config().setReadOffset(info[0], info[1], info[2],
                                      offset)


class Offset(BaseCommand):
    summary = "handle drive offsets"
    description = """
Drive offset detection utility.
"""
    subcommands = {
        'find': Find,
    }
