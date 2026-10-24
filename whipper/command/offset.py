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
import math
import os
import tempfile
import logging
from whipper.command.basecommand import BaseCommand
from whipper.common import accurip, common, config, drive
from whipper.common import drive_offsets, offsetfind
from whipper.common import task as ctask
from whipper.program import arc, cdrdao, cdparanoia, utils
from whipper.extern.task import task

logger = logging.getLogger(__name__)

# see http://www.accuraterip.com/driveoffsets.htm
# and misc/offsets.py
OFFSETS = ("+6, +667, +48, +102, +30, +12, +103, +618, +96, +738, "
           "+594, +98, -472, +733, +696, +116, +120, +691, +685, "
           "+99, +702, +97, +600, +676, +690, +1292, +686, +697, "
           "-24, +704, +572, +1182, +688, -491, +91, +145, +689, "
           "+86, +355, +708, +79, +564, -496, +679, -1164, 0, "
           "+1160, -436, +684, +694, +1194, +94, +106, +681, "
           "+678, +117, +692, +943, +92, +680, +682, +1268, +1279, "
           "+1473, -54, +1263, -582, +674, +687, +1272, +1508, "
           "-489, +740, +675, +534, +122, +974, +976, +1303, "
           "+111, +108, +1130, +975, +87, +739, +732, -589, -495, "
           "-494, -12, +961, +935, +699, +668, +234, +1776, +138, "
           "+1364, +1336, +1262, +1161, +1127")


def _positive_seconds(value):
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError('must be positive, finite seconds')
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError('must be positive, finite seconds')
    return seconds


class Find(BaseCommand):
    summary = "find drive read offset"
    description = """Find drive's read offset by ripping tracks from a
CD in the AccurateRip database."""
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    device_option = True

    def add_arguments(self):
        self.parser.add_argument(
            '-o', '--offsets',
            action="store", dest="offsets", default=None,
            help="probe only these offsets, in order (comma-separated; "
                 "colon-separated ranges); otherwise detect automatically"
        )

        self.parser.add_argument(
            '--no-prioritize-known', action='store_true',
            help='do not prioritize configured or published model offsets')
        self.parser.add_argument(
            '--no-frame450', action='store_true',
            help='skip the short AccurateRip checksum window')
        self.parser.add_argument(
            '--read-timeout', type=_positive_seconds, metavar='SECONDS',
            default=offsetfind.DEFAULT_READ_TIMEOUT,
            help='maximum seconds for each offset window or confirmation read')
        self.parser.add_argument(
            '--read-idle-timeout', type=_positive_seconds, metavar='SECONDS',
            default=offsetfind.DEFAULT_IDLE_TIMEOUT,
            help='maximum seconds without forward read/write progress during '
                 'offset detection')

    def handle_arguments(self):
        self._explicit_offsets = self.options.offsets is not None
        self._offsets = []
        blocks = (self.options.offsets if self._explicit_offsets
                  else OFFSETS).split(',')
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

        if self.options.drive_auto_close is True:
            utils.load_device(device)
        utils.unmount_device(device)

        configured = None
        known = []
        if not self._explicit_offsets:
            try:
                info = drive.getDeviceInfo(device)
            except OSError as error:
                logger.debug('drive identity unavailable: %s', error)
                info = None
            if info:
                known = drive_offsets.known_offsets_for(*info[:2])
                try:
                    configured = config.Config().getReadOffset(*info)
                except (KeyError, TypeError, ValueError):
                    pass
        offsets = drive_offsets.order_offsets(
            self._offsets, configured, known,
            prioritize=not (self._explicit_offsets or
                            self.options.no_prioritize_known))

        # first get the Table Of Contents of the CD
        t = cdrdao.ReadTOCTask(device, fast_toc=True)
        runner.run(t)
        table = t.toc.table

        if len(table.tracks) < 3:
            logger.error("whipper offset find needs a CD with at least 3 "
                         "tracks on it to do its job")
            return None

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

        # An explicit list remains an ordered probe request; automatic
        # candidate selection must not jump ahead or add other offsets.
        if not self.options.no_frame450 and not self._explicit_offsets:
            guess = configured if configured is not None else (
                known[0] if known else 0)
            fast = offsetfind.find_offsets(
                runner, table, device, responses, guess=guess,
                read_timeout=self.options.read_timeout,
                idle_timeout=self.options.read_idle_timeout)
            # Several pressings may match the short window. Prefer known
            # drive offsets among those matches before trying other shifts.
            fast = drive_offsets.order_offsets(
                fast, configured=configured if configured in fast else None,
                known=[candidate for candidate in known if candidate in fast],
                prioritize=not self.options.no_prioritize_known)
            offsets = drive_offsets.order_offsets(offsets, known=fast)

        for offset in offsets:
            logger.info('trying read offset %d...', offset)
            if self._confirm_offset(runner, table, responses, offset):
                self._foundOffset(device, offset)
                return 0

        logger.error('no matching offset found. '
                     'Consider trying again with a different disc')
        return None

    def _confirm_offset(self, runner, table, responses, offset):
        """Keep the existing confirmation threshold for every candidate."""
        # Skip the last track because some drives cannot overread lead-out.
        for track in range(1, len(table.tracks)):
            try:
                checksums = self._arcs(runner, table, track, offset)
            except task.TaskException as error:
                if isinstance(error.exception,
                              (common.MissingDependencyException,
                               cdparanoia.ReadCleanupError)):
                    raise
                logger.warning('cannot confirm track %d at offset %d: %s',
                               track, offset, error)
                return False
            if not any(checksum == response.checksums[track - 1]
                       for checksum in checksums for response in responses):
                logger.debug('track %d did not confirm offset %d',
                             track, offset)
                return False
        return True

    def _arcs(self, runner, table, track, offset):
        # rips the track with the given offset, return the arcs checksums
        logger.debug('ripping track %r with offset %d...', track, offset)

        fd, path = tempfile.mkstemp(
            suffix='.track%02d.offset%d.whipper.wav' % (
                track, offset))
        os.close(fd)

        try:
            t = cdparanoia.ReadTrackTask(
                path, table, table.getTrackStart(track),
                table.getTrackEnd(track), overread=False, offset=offset,
                device=self.options.device,
                read_timeout=self.options.read_timeout,
                idle_timeout=self.options.read_idle_timeout)
            t.description = 'Ripping track %d with read offset %d' % (
                track, offset)
            runner.run(t)
            v1, v2 = arc.accuraterip_checksum(path, track, len(table.tracks))
            return "%08x" % v1, "%08x" % v2
        finally:
            os.unlink(path)

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
