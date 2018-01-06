# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys
import pkg_resources
import musicbrainzngs

import whipper

from whipper.command import cd, offset, drive, image, accurip, debug
from whipper.command.basecommand import BaseCommand
from whipper.common import common, directory, config
from whipper.extern.task import task
from whipper.program.utils import eject_device

import logging
logger = logging.getLogger(__name__)


def main():
    # set user agent
    musicbrainzngs.set_useragent("whipper", whipper.__version__,
                                 "https://github.com/JoeLametta/whipper")

    try:
        server = config.Config().get_musicbrainz_server()
    except KeyError, e:
        sys.stderr.write('whipper: %s\n' % e.message)
        sys.exit()

    musicbrainzngs.set_hostname(server)
    # register plugins with pkg_resources
    distributions, _ = pkg_resources.working_set.find_plugins(
        pkg_resources.Environment([directory.data_path('plugins')])
    )
    map(pkg_resources.working_set.add, distributions)
    try:
        cmd = Whipper(sys.argv[1:], os.path.basename(sys.argv[0]), None)
        ret = cmd.do()
    except SystemError as e:
        sys.stderr.write('whipper: error: %s\n' % e)
        if (type(e) is common.EjectError and
                cmd.options.eject in ('failure', 'always')):
            eject_device(e.device)
        return 255
    except RuntimeError as e:
        print(e)
        return 1
    except KeyboardInterrupt:
        return 2
    except ImportError as e:
        raise
    except task.TaskException as e:
        if isinstance(e.exception, ImportError):
            raise ImportError(e.exception)
        elif isinstance(e.exception, common.MissingDependencyException):
            sys.stderr.write('whipper: error: missing dependency "%s"\n' %
                             e.exception.dependency)
            return 255

        if isinstance(e.exception, common.EmptyError):
            logger.debug("EmptyError: %r", str(e.exception))
            sys.stderr.write('whipper: error: Could not create encoded file.\n')  # noqa: E501
            return 255

        # in python3 we can instead do `raise e.exception` as that would show
        # the exception's original context
        sys.stderr.write(e.exceptionMessage)
        return 255
    return ret if ret else 0


class Whipper(BaseCommand):
    description = """whipper is a CD ripping utility focusing on accuracy over speed.

whipper gives you a tree of subcommands to work with.
You can get help on subcommands by using the -h option to the subcommand.
"""
    no_add_help = True
    subcommands = {
        'accurip': accurip.AccuRip,
        'cd': cd.CD,
        'debug': debug.Debug,
        'drive': drive.Drive,
        'offset': offset.Offset,
        'image': image.Image
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
        self.parser.add_argument('-e', '--eject',
                                 action="store", dest="eject",
                                 default="always",
                                 choices=('never', 'failure',
                                          'success', 'always'),
                                 help="when to eject disc (default: always)")

    def handle_arguments(self):
        if self.options.help:
            self.parser.print_help()
            sys.exit(0)
        if self.options.version:
            print "whipper %s" % whipper.__version__
            sys.exit(0)
