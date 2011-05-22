# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import sys

from morituri.common import log, logcommand, common, task
from morituri.rip import cd, offset, drive, image, accurip

def main(argv):
    c = Rip()
    try:
        ret = c.parse(argv)
    except SystemError, e:
        sys.stderr.write('rip: error: %s\n' % e.args)
        return 255
    except ImportError, e:
        # FIXME: decide how to handle
        raise
        # deps.handleImportError(e)
        # ret = -1
    except task.TaskException, e:
        if isinstance(e.exception, common.MissingDependencyException):
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
        raise

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
        cd.CD, drive.Drive, offset.Offset, image.Image, ]

    def addOptions(self):
        # FIXME: is this the right place ?
        log.init()
        from morituri.configure import configure
        log.debug("morituri", "This is morituri version %s (%s)",
            configure.version, configure.revision)

        self.parser.add_option('-v', '--version',
                          action="store_true", dest="version",
                          help="show version information")

    def handleOptions(self, options):
        if options.version:
            from morituri.configure import configure
            print "rip %s" % configure.version
            sys.exit(0)

    def parse(self, argv):
        log.debug("morituri", "rip %s" % " ".join(argv))
        logcommand.LogCommand.parse(self, argv)
