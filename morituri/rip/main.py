# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
import sys
import pkg_resources

from morituri.common import log, logcommand, common, config, directory
from morituri.configure import configure

from morituri.rip import cd, offset, drive, image, accurip, debug

from morituri.extern.command import command
from morituri.extern.task import task


def main(argv):
    # load plugins

    from morituri.configure import configure
    pluginsdir = configure.pluginsdir
    d = directory.Directory()
    homepluginsdir = d.getData('plugins')

    distributions, errors = pkg_resources.working_set.find_plugins(
        pkg_resources.Environment([pluginsdir, homepluginsdir]))
    if errors:
        log.warning('errors finding plugins: %r', errors)
    log.debug('mapping distributions %r', distributions)
    map(pkg_resources.working_set.add, distributions)

    # set user agent
    import musicbrainzngs
    musicbrainzngs.set_useragent("morituri", configure.version,
        'https://thomas.apestaart.org/morituri/trac')


    c = Rip()
    try:
        ret = c.parse(argv)
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
        # FIXME: move this exception
        from morituri.program import cdrdao
        if isinstance(e.exception, cdrdao.DeviceOpenException):
            sys.stderr.write("""rip: error: cannot read CD from drive.
cdrdao says:
%s
""" % e.exception.msg)
            return 255

        if isinstance(e.exception, common.EmptyError):
            log.debug('main',
                "EmptyError: %r", log.getExceptionMessage(e.exception))
            sys.stderr.write(
                'rip: error: Could not create encoded file.\n')
            return 255

        raise
    except command.CommandError, e:
        sys.stderr.write('rip: error: %s\n' % e.output)
        return e.status

    if ret is None:
        return 0

    return ret


class Rip(logcommand.LogCommand):
    usage = "%prog %command"
    description = """Rip rips CD's.

Rip gives you a tree of subcommands to work with.
You can get help on subcommands by using the -h option to the subcommand.
"""

    subCommandClasses = [accurip.AccuRip,
        cd.CD, debug.Debug, drive.Drive, offset.Offset, image.Image, ]

    def addOptions(self):
        # FIXME: is this the right place ?
        log.init()
        from morituri.configure import configure
        log.debug("morituri", "This is morituri version %s (%s)",
            configure.version, configure.revision)

        self.parser.add_option('-R', '--record',
                          action="store_true", dest="record",
                          help="record API requests for playback")
        self.parser.add_option('-v', '--version',
                          action="store_true", dest="version",
                          help="show version information")

    def handleOptions(self, options):
        if options.version:
            print "rip %s" % configure.version
            sys.exit(0)

        self.record = options.record

        self.config = config.Config()

    def parse(self, argv):
        log.debug("morituri", "rip %s" % " ".join(argv))
        logcommand.LogCommand.parse(self, argv)
