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

import argparse
import os

from morituri.extern.task import task
from morituri.common import command, drive
from morituri.program import cdparanoia

import logging
logger = logging.getLogger(__name__)

class Analyze(command.BaseCommand):
    summary = "analyze caching behaviour of drive"
    description = """Determine whether cdparanoia can defeat the audio cache of the drive."""
    device_option = True

    def do(self):
        runner = task.SyncRunner()
        t = cdparanoia.AnalyzeTask(self.options.device)
        runner.run(t)

        if t.defeatsCache is None:
            self.stdout.write(
                'Cannot analyze the drive.  Is there a CD in it?\n')
            return
        if not t.defeatsCache:
            self.stdout.write(
                'cdparanoia cannot defeat the audio cache on this drive.\n')
        else:
            self.stdout.write(
                'cdparanoia can defeat the audio cache on this drive.\n')

        info = drive.getDeviceInfo(self.options.device)
        if not info:
            self.stdout.write('Drive caching behaviour not saved: could not get device info (requires pycdio).\n')
            return

        self.stdout.write(
            'Adding drive cache behaviour to configuration file.\n')

        self.config.setDefeatsCache(info[0], info[1], info[2],
            t.defeatsCache)


class List(command.BaseCommand):
    summary = "list drives"
    description = """list available CD-DA drives"""

    def do(self):
        paths = drive.getAllDevicePaths()

        if not paths:
            self.stdout.write('No drives found.\n')
            self.stdout.write('Create /dev/cdrom if you have a CD drive, \n')
            self.stdout.write('or install pycdio for better detection.\n')

            return

        try:
            import cdio as _
        except ImportError:
            self.stdout.write(
                'Install pycdio for vendor/model/release detection.\n')
            return

        for path in paths:
            vendor, model, release = drive.getDeviceInfo(path)
            self.stdout.write(
                "drive: %s, vendor: %s, model: %s, release: %s\n" % (
                path, vendor, model, release))

            try:
                offset = self.config.getReadOffset(
                    vendor, model, release)
                self.stdout.write(
                    "       Configured read offset: %d\n" % offset)
            except KeyError:
                self.stdout.write(
                    "       No read offset found.  Run 'rip offset find'\n")

            try:
                defeats = self.config.getDefeatsCache(
                    vendor, model, release)
                self.stdout.write(
                    "       Can defeat audio cache: %s\n" % defeats)
            except KeyError:
                self.stdout.write(
                    "       Unknown whether audio cache can be defeated. "
                    "Run 'rip drive analyze'\n")


        if not paths:
            self.stdout.write('No drives found.\n')


class Drive(command.BaseCommand):
    summary = "handle drives"
    description = """Drive utilities."""
    subcommands = {
        'analyze': Analyze,
        'list': List
    }
