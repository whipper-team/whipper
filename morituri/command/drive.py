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

import sys

from morituri.command.basecommand import BaseCommand
from morituri.common import config, drive
from morituri.extern.task import task
from morituri.program import cdparanoia

import logging
logger = logging.getLogger(__name__)

class Analyze(BaseCommand):
    summary = "analyze caching behaviour of drive"
    description = """Determine whether cdparanoia can defeat the audio cache of the drive."""
    device_option = True

    def do(self):
        runner = task.SyncRunner()
        t = cdparanoia.AnalyzeTask(self.options.device)
        runner.run(t)

        if t.defeatsCache is None:
            sys.stdout.write(
                'Cannot analyze the drive.  Is there a CD in it?\n')
            return
        if not t.defeatsCache:
            sys.stdout.write(
                'cdparanoia cannot defeat the audio cache on this drive.\n')
        else:
            sys.stdout.write(
                'cdparanoia can defeat the audio cache on this drive.\n')

        info = drive.getDeviceInfo(self.options.device)
        if not info:
            sys.stdout.write('Drive caching behaviour not saved: could not get device info (requires pycdio).\n')
            return

        sys.stdout.write(
            'Adding drive cache behaviour to configuration file.\n')

        config.Config().setDefeatsCache(info[0], info[1], info[2],
            t.defeatsCache)


class List(BaseCommand):
    summary = "list drives"
    description = """list available CD-DA drives"""

    def do(self):
        paths = drive.getAllDevicePaths()
        self.config = config.Config()

        if not paths:
            sys.stdout.write('No drives found.\n')
            sys.stdout.write('Create /dev/cdrom if you have a CD drive, \n')
            sys.stdout.write('or install pycdio for better detection.\n')

            return

        try:
            import cdio as _
        except ImportError:
            sys.stdout.write(
                'Install pycdio for vendor/model/release detection.\n')
            return

        for path in paths:
            vendor, model, release = drive.getDeviceInfo(path)
            sys.stdout.write(
                "drive: %s, vendor: %s, model: %s, release: %s\n" % (
                path, vendor, model, release))

            try:
                offset = self.config.getReadOffset(
                    vendor, model, release)
                sys.stdout.write(
                    "       Configured read offset: %d\n" % offset)
            except KeyError:
                sys.stdout.write(
                    "       No read offset found.  Run 'whipper offset find'\n")

            try:
                defeats = self.config.getDefeatsCache(
                    vendor, model, release)
                sys.stdout.write(
                    "       Can defeat audio cache: %s\n" % defeats)
            except KeyError:
                sys.stdout.write(
                    "       Unknown whether audio cache can be defeated. "
                    "Run 'whipper drive analyze'\n")


        if not paths:
            sys.stdout.write('No drives found.\n')


class Drive(BaseCommand):
    summary = "handle drives"
    description = """Drive utilities."""
    subcommands = {
        'analyze': Analyze,
        'list': List
    }
