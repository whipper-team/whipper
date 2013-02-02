# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# options and arguments shared between commands

DEFAULT_TRACK_TEMPLATE = u'%r/%A - %d/%t. %a - %n'
DEFAULT_DISC_TEMPLATE = u'%r/%A - %d/%A - %d'

TEMPLATE_DESCRIPTION = '''
Tracks are named according to the track template, filling in the variables
and adding the file extension.  Variables exclusive to the track template are:
 - %t: track number
 - %a: track artist
 - %n: track title
 - %s: track sort name

Disc files (.cue, .log, .m3u) are named according to the disc template,
filling in the variables and adding the file extension. Variables for both
disc and track template are:
 - %A: album artist
 - %S: album sort name
 - %d: disc title
 - %y: release year
 - %r: release type, lowercase
 - %R: Release type, normal case
 - %x: audio extension, lowercase
 - %X: audio extension, uppercase

'''

def addTemplate(self):
    # FIXME: get from config
    self.parser.add_option('', '--track-template',
        action="store", dest="track_template",
        help="template for track file naming (default %default)",
        default=DEFAULT_TRACK_TEMPLATE)
    self.parser.add_option('', '--disc-template',
        action="store", dest="disc_template",
        help="template for disc file naming (default %default)",
        default=DEFAULT_DISC_TEMPLATE)
