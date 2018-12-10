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
from whipper.common import config, drive
from whipper.extern.task import task
from whipper.program import cdparanoia

import logging
logger = logging.getLogger(__name__)


class Analyze(BaseCommand):
    summary = "analyze caching behaviour of drive"
    description = """Determine whether cdparanoia can defeat the audio cache of the drive."""  # noqa: E501
    device_option = True

    def do(self):
        runner = task.SyncRunner()
        t = cdparanoia.AnalyzeTask(self.options.device)
        runner.run(t)

        if t.defeatsCache is None:
            logger.critical('cannot analyze the drive: is there a CD in it?')
            return
        if not t.defeatsCache:
            logger.info('cdparanoia cannot defeat the audio cache '
                        'on this drive')
        else:
            logger.info('cdparanoia can defeat the audio cache on this drive')

        info = drive.getDeviceInfo(self.options.device)
        if not info:
            logger.error('Drive caching behaviour not saved: '
                         'could not get device info')
            return

        logger.info('adding drive cache behaviour to configuration file')

        config.Config().setDefeatsCache(
            info[0], info[1], info[2], t.defeatsCache)


class List(BaseCommand):
    summary = "list drives"
    description = """list available CD-DA drives"""

    def do(self):
        paths = drive.getAllDevicePaths()
        self.config = config.Config()

        if not paths:
            logger.critical('No drives found. Create /dev/cdrom '
                            'if you have a CD drive, or install '
                            'pycdio for better detection')
            return

        try:
            import cdio as _  # noqa: F401 (TODO: fix it in a separate PR?)
        except ImportError:
            logger.error('install pycdio for vendor/model/release detection')
            return

        for path in paths:
            vendor, model, release = drive.getDeviceInfo(path)
            print("drive: %s, vendor: %s, model: %s, release: %s" % (
                  path, vendor, model, release))

            try:
                offset = self.config.getReadOffset(
                    vendor, model, release)
                print("       Configured read offset: %d" % offset)
            except KeyError:
                # Note spaces at the beginning for pretty terminal output
                logger.warning("no read offset found. "
                               "Run 'whipper offset find'")

            try:
                defeats = self.config.getDefeatsCache(
                    vendor, model, release)
                print("       Can defeat audio cache: %s" % defeats)
            except KeyError:
                logger.warning("unknown whether audio cache can be "
                               "defeated. Run 'whipper drive analyze'")


class Drive(BaseCommand):
    summary = "handle drives"
    description = """Drive utilities."""
    subcommands = {
        'analyze': Analyze,
        'list': List
    }
