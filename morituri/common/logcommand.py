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

"""
Logging Command.
"""

from morituri.extern.command import command
from morituri.common import log


class LogCommand(command.Command, log.Loggable):

    def __init__(self, parentCommand=None, **kwargs):
        command.Command.__init__(self, parentCommand, **kwargs)
        self.logCategory = self.name

    def parse(self, argv):
        cmd = self.getRootCommand()
        if hasattr(cmd, 'config'):
            config = cmd.config
            # find section name
            cmd = self
            section = []
            while cmd is not None:
                section.insert(0, cmd.name)
                cmd = cmd.parentCommand
            section = '.'.join(section)
            # get defaults from config
            defaults = {}
            for opt in self.parser.option_list:
                if opt.dest is None:
                    continue
                if 'string' == opt.type:
                    val = config.get(section, opt.dest)
                elif opt.action in ('store_false', 'store_true'):
                    val = config.getboolean(section, opt.dest)
                else:
                    val = None
                if val is not None:
                    defaults[opt.dest] = val
            self.parser.set_defaults(**defaults)
        command.Command.parse(self, argv)

    # command.Command has a fake debug method, so choose the right one

    def debug(self, format, *args):
        kwargs = {}
        log.Loggable.doLog(self, log.DEBUG, -2, format, *args, **kwargs)
