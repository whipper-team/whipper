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
from morituri.common import log, config
import argparse
import logging
import sys

class Lager():
    """
    Provides self.debug() logging facility for existing commands.
    Provides self.error() raising facility for existing commands.
    Provides self.epilog() formatting command for argparse.
    Provides self.config, self.stdout objects for children.

    __init__() registers a subcommand with .cmd that is executed
    by do(); this is because python does not allow returning values
    from __init__().
    """
    config = config.Config()
    stdout = sys.stdout

    def __init__(self, argv, prog=None):
        """
        Launch subcommands without any mid-level options.
        Override to include options.
        """
        parser = argparse.ArgumentParser(
            prog=prog,
            description=self.description,
            epilog=self.epilog(),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument('remainder', nargs=argparse.REMAINDER,
                            help=argparse.SUPPRESS)
        opt = parser.parse_args(argv)
        if not opt.remainder:
            parser.print_help()
            sys.exit(0)
        if not opt.remainder[0] in self.subcommands:
            sys.stderr.write("incorrect subcommand: %s" % opt.remainder[0])
            sys.exit(1)
        self.cmd = self.subcommands[opt.remainder[0]](
            opt.remainder[1:], prog=prog + " " + opt.remainder[0]
        )

    def do(self):
        return self.cmd.do()

    def debug(self, format, *args):
        # FIXME
        kwargs = {}
        pass

    def error(self, msg):
        # FIXME
        raise Exception(msg)

    def epilog(self):
        s = "commands:\n"
        for com in sorted(self.subcommands.keys()):
            s += "  %s %s\n" % (com.ljust(8), self.subcommands[com].summary)
        return s

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
