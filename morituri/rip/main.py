# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import argparse
import os
import sys
import pkg_resources
import musicbrainzngs

from morituri.common import command, common, config, directory
from morituri.configure import configure
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
        ret = Whipper(sys.argv[1:], os.path.basename(sys.argv[0]), None).do()
    except SystemError, e:
        sys.stderr.write('whipper: error: %s\n' % e.args)
        return 255
    except ImportError, e:
        raise ImportError(e)
    except task.TaskException, e:
        if isinstance(e.exception, ImportError):
            raise ImportError(e.exception)
        elif isinstance(e.exception, common.MissingDependencyException):
            sys.stderr.write('whipper: error: missing dependency "%s"\n' %
                             e.exception.dependency)
            return 255

        if isinstance(e.exception, common.EmptyError):
            logger.debug("EmptyError: %r", log.getExceptionMessage(e.exception))
            sys.stderr.write('whipper: error: Could not create encoded file.\n')
            return 255

        # in python3 we can instead do `raise e.exception` as that would show
        # the exception's original context
        sys.stderr.write(e.exceptionMessage)
        return 255
    return ret if ret else 0

class Whipper(command.BaseCommand):
    description = """whipper is a CD ripping utility focusing on accuracy over speed.

whipper gives you a tree of subcommands to work with.
You can get help on subcommands by using the -h option to the subcommand.
"""
    no_add_help = True
    subcommands = {
        'accurip': accurip.AccuRip,
        'cd':      cd.CD,
        'debug':   debug.Debug,
        'drive':   drive.Drive,
        'offset':  offset.Offset,
        'image':   image.Image
    }

    def add_arguments(self):
        self.parser.add_argument('-R', '--record',
                            action='store_true', dest='record',
                            help="record API requests for playback")
        self.parser.add_argument('-v', '--version',
                            action="store_true", dest="version",
                            help="show version information")
        self.parser.add_argument('-h', '--help',
                            action="store_true", dest="help",
                            help="show this help message and exit")

    def handle_arguments(self):
        if self.options.help:
            self.parser.print_help()
            sys.exit(0)
        if self.options.version:
            print "whipper %s" % configure.version
            sys.exit(0)
