# -*- Mode: Python; test-case-name: morituri.test.test_result_logger -*-
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

import time

from morituri.common import common
from morituri.configure import configure


class MorituriLogger(object):

    def log(self, ripResult, epoch=time.time()):
        lines = self.logRip(ripResult, epoch=epoch)
        return '\n'.join(lines)

    def logRip(self, ripResult, epoch):

        lines = []

        ### global

        lines.append("Logfile created by: morituri %s" % configure.version)
        # FIXME: when we localize this, see #49 to handle unicode properly.
        import locale
        old = locale.getlocale(locale.LC_TIME)
        locale.setlocale(locale.LC_TIME, 'C')
        date = time.strftime("%b %d %H:%M:%S", time.localtime(epoch))
        locale.setlocale(locale.LC_TIME, old)
        lines.append("Logfile created on: %s" % date)
        lines.append("")

        # album
        lines.append("Album: %s - %s" % (ripResult.artist, ripResult.title))
        lines.append("")

        # drive
        lines.append(
            "Drive: vendor %s, model %s" % (
                ripResult.vendor, ripResult.model))
        lines.append("")

        lines.append("Read offset correction: %d" %
            ripResult.offset)
        lines.append("")

        # toc
        lines.append("Table of Contents:")
        lines.append("")
        lines.append(
            "     Track |   Start           |  Length")
        lines.append(
            "     ------------------------------------------------")
        table = ripResult.table


        for t in table.tracks:
            start = t.getIndex(1).absolute
            length = table.getTrackLength(t.number)
            lines.append(
            "       %2d  | %6d - %s | %6d - %s" % (
                t.number,
                start, common.framesToMSF(start),
                length, common.framesToMSF(length)))

        lines.append("")
        lines.append("")

        ### per-track
        for t in ripResult.tracks:
            lines.extend(self.trackLog(t))
            lines.append('')

        return lines

    def trackLog(self, trackResult):

        lines = []

        lines.append('Track %2d' % trackResult.number)
        lines.append('')
        lines.append('  Filename %s' % trackResult.filename)
        lines.append('')
        if trackResult.pregap:
            lines.append('  Pre-gap: %s' % common.framesToMSF(
                trackResult.pregap))
            lines.append('')

        lines.append('  Peak level %.1f %%' % (trackResult.peak * 100.0))
        if trackResult.copycrc is not None:
            lines.append('  Copy CRC %08X' % trackResult.copycrc)
        if trackResult.testcrc is not None:
            lines.append('  Test CRC %08X' % trackResult.testcrc)
            if trackResult.testcrc == trackResult.copycrc:
                lines.append('  Copy OK')
            else:
                lines.append("  WARNING: CRCs don't match!")
        else:
            lines.append("  WARNING: no CRC check done")

        if trackResult.accurip:
            lines.append('  Accurately ripped (confidence %d) [%08X]' % (
                trackResult.ARDBConfidence, trackResult.ARCRC))
        else:
            if trackResult.ARDBCRC:
                lines.append('  Cannot be verified as accurate '
                    '[%08X], AccurateRip returned [%08X]' % (
                        trackResult.ARCRC, trackResult.ARDBCRC))
            else:
                lines.append('  Track not present in AccurateRip database')

        return lines
