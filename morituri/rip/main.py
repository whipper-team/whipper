# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import argparse
import os
import sys
import pkg_resources
import musicbrainzngs

from morituri.common import logcommand, common, config, directory
from morituri.configure import configure
from morituri.extern.command import command
from morituri.extern.task import task
from morituri.rip import cd, offset, drive, image, accurip, debug

import logging
logger = logging.getLogger(__name__)

def main():
    # set user agent
    musicbrainzngs.set_useragent("morituri", configure.version,
        'https://thomas.apestaart.org/morituri/trac')
    # register plugins with pkg_resources
    distributions, _ = pkg_resources.working_set.find_plugins(
        pkg_resources.Environment([directory.data_path('plugins')])
    )
    map(pkg_resources.working_set.add, distributions)
    try:
        ret = Whipper(sys.argv[1:], os.path.basename(sys.argv[0])).do()
    except SystemError, e:
        sys.stderr.write('rip: error: %s\n' % e.args)
        return 255
    except ImportError, e:
        raise ImportError(e)
    except task.TaskException, e:
        if isinstance(e.exception, ImportError):
            raise ImportError(e.exception)
        elif isinstance(e.exception, common.MissingDependencyException):
            sys.stderr.write('rip: error: missing dependency "%s"\n' %
                             e.exception.dependency)
            return 255

        if isinstance(e.exception, common.EmptyError):
            logger.debug("EmptyError: %r", log.getExceptionMessage(e.exception))
            sys.stderr.write('rip: error: Could not create encoded file.\n')
            return 255

        # in python3 we can instead do `raise e.exception` as that would show
        # the exception's original context
        sys.stderr.write(e.exceptionMessage)
        return 255
    except command.CommandError, e:
        sys.stderr.write('rip: error: %s\n' % e.output)
        return e.status
    return ret if ret else 0

class Whipper(logcommand.Lager):
    description = """whipper is a CD ripping utility focusing on accuracy over speed.

whipper gives you a tree of subcommands to work with.
You can get help on subcommands by using the -h option to the subcommand.
"""
    subcommands = {
        'accurip': accurip.AccuRip,
        'cd':      cd.CD,
        'debug':   debug.Debug,
        'drive':   drive.Drive,
        'offset':  offset.Offset,
        'image':   image.Image
    }

    def __init__(self, argv, prog):
        parser = argparse.ArgumentParser(
            prog=prog,
            add_help=False,
            description=self.description,
            epilog=self.epilog(),
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        parser.add_argument('-R', '--record',
                            action='store_true', dest='record',
                            help="record API requests for playback")
        parser.add_argument('-v', '--version',
                            action="store_true", dest="version",
                            help="show version information")
        parser.add_argument('-h', '--help',
                            action="store_true", dest="help",
                            help="show this help message and exit")
        parser.add_argument('remainder', nargs=argparse.REMAINDER,
                            help=argparse.SUPPRESS)
        opts = parser.parse_args(argv)
        if opts.help or not opts.remainder:
            parser.print_help()
            sys.exit(0)
        if opts.version:
            print "whipper %s" % configure.version
            sys.exit(0)
        if not opts.remainder[0] in self.subcommands:
            sys.stderr.write("incorrect subcommand: %s" % opts.remainder[0])
            sys.exit(1)
        self.cmd = self.subcommands[opts.remainder[0]](
            opts.remainder[1:], prog + " " + opts.remainder[0], opts
        )
