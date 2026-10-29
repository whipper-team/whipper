# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import argparse
import os

from whipper.common import config, drive

import logging
logger = logging.getLogger(__name__)

# Q: What about argparse.add_subparsers(), you ask?
# A: Unfortunately add_subparsers() does not support specifying the
# formatter_class of subparsers, nor does it support epilogs, so
# it does not quite fit our use case.

# Q: Why not subclass ArgumentParser and extend/replace the relevant
# methods?
# A: If this can be done in a simpler fashion than this current
# implementation, by all means submit a patch.

# Q: Why not argparse.parse_known_args()?
# A: The prefix matching prevents passing '-h' (and possibly other
# options) to the child command.


class BaseCommand:
    """
    Register and handle whipper command arguments with ArgumentParser.

    Register arguments by overriding ``add_arguments()`` and modifying
    ``self.parser``. Option defaults are read from the dot-separated
    ``prog_name`` section of the config file (e.g., ``whipper cd rip``
    options are read from ``[whipper.cd.rip]``). Runs
    ``argparse.parse_args()`` then calls ``handle_arguments()``.

    Provides ``self.epilog()`` formatting command for argparse.

    Overriding ``formatter_class`` sets the argparse formatter class.

    If the ``subcommands`` dictionary is set, ``__init__`` searches the
    arguments for ``subcommands.keys()`` and instantiates the class
    implementing the subcommand as self.cmd, passing all non-understood
    arguments, the current options namespace, and the full command path
    name.

    :cvar device_option: if set to True adds ``-d`` / ``--device``
                         option to current command
    :cvar no_add_help: if set to True removes ``-h`` ``--help``
                       option from current command
    """

    device_option = False
    no_add_help = False  # for rip.main.Whipper
    formatter_class = argparse.RawDescriptionHelpFormatter

    def __init__(self, argv, prog_name, opts):
        self.opts = opts  # for Rip.add_arguments()
        self.prog_name = prog_name

        self.init_parser()
        self.add_arguments()

        config_section = prog_name.replace(' ', '.')
        defaults = {}
        for action in self.parser._actions:
            val = None
            if isinstance(action, argparse._StoreAction):
                val = config.Config().get(config_section, action.dest)
            elif isinstance(action, (argparse._StoreTrueAction,
                                     argparse._StoreFalseAction)):
                val = config.Config().getboolean(config_section, action.dest)
            if val is not None:
                defaults[action.dest] = val
        self.parser.set_defaults(**defaults)

        if hasattr(self, 'subcommands'):
            self.parser.add_argument('remainder',
                                     nargs=argparse.REMAINDER,
                                     help=argparse.SUPPRESS)

        if self.device_option:
            # pick the first drive as default; config may override (#346)
            drives = drive.getAllDevicePaths()
            config_device = None
            try:
                cfg = config.Config()
                config_device = cfg.get(config_section, 'device')
                if not config_device:
                    # global default: [main] device / helper (#346)
                    config_device = cfg.getDefaultDevice()
            except Exception as e:
                logger.debug('could not read default device from config: %r',
                             e)
            if config_device:
                default_device = config_device
                logger.debug('default device from config: %r', default_device)
            elif drives:
                default_device = drives[0]
            else:
                msg = 'No CD-DA drives found!'
                logger.critical(msg)
                raise IOError(msg)
            self.parser.add_argument('-d', '--device',
                                     action="store",
                                     dest="device",
                                     default=default_device,
                                     help="CD-DA device (default: first "
                                          "drive, or [main] device / "
                                          "command-section device in the "
                                          "config file)")

        self.options = self.parser.parse_args(argv, namespace=opts)

        if self.device_option:
            if self.options.device:
                self.options.device = os.path.realpath(self.options.device)
                if not os.path.exists(self.options.device):
                    msg = 'CD-DA device %s not found!' % self.options.device
                    logger.critical(msg)
                    raise IOError(msg)
            else:
                msg = 'No CD-DA drives found!'
                logger.critical(msg)
                raise IOError(msg)

        self.handle_arguments()

        if hasattr(self, 'subcommands'):
            if not self.options.remainder:
                self.parser.print_help()
                raise SystemExit()
            if not self.options.remainder[0] in self.subcommands:
                logger.critical("incorrect subcommand: %s",
                                self.options.remainder[0])
                raise SystemExit(1)
            self.cmd = self.subcommands[self.options.remainder[0]](
                self.options.remainder[1:],
                prog_name + " " + self.options.remainder[0],
                self.options
            )

    def init_parser(self):
        kw = {
            'prog': self.prog_name,
            'description': self.description,
            'formatter_class': self.formatter_class,
        }
        if hasattr(self, 'subcommands'):
            kw['epilog'] = self.epilog()
        if self.no_add_help:
            kw['add_help'] = False
        self.parser = argparse.ArgumentParser(**kw)

    def add_arguments(self):
        pass

    def handle_arguments(self):
        pass

    def do(self):
        return self.cmd.do()

    def epilog(self):
        s = "commands:\n"
        for com in sorted(self.subcommands.keys()):
            s += "  %s %s\n" % (com.ljust(8), self.subcommands[com].summary)
        return s
