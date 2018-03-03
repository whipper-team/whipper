import sys

from whipper.command.basecommand import BaseCommand
from whipper.common.mbngs import musicbrainz

class MBLookup(BaseCommand):
    summary = "lookup MusicBrainz entry"
    description = """Look up a MusicBrainz disc id and output information.

You can get the MusicBrainz disc id with whipper cd info.

Example disc id: KnpGsLhvH.lPrNc1PBL21lb9Bg4-"""

    def add_arguments(self):
        self.parser.add_argument(
            'mbdiscid', action='store', help="MB disc id to look up"
        )


    def do(self):
        try:
            discId = unicode(self.options.mbdiscid)
        except IndexError:
            sys.stdout.write('Please specify a MusicBrainz disc id.\n')
            return 3

        metadatas = musicbrainz(discId)

        sys.stdout.write('%d releases\n' % len(metadatas))
        for i, md in enumerate(metadatas):
            sys.stdout.write('- Release %d:\n' % (i + 1, ))
            sys.stdout.write('    Artist: %s\n' % md.artist.encode('utf-8'))
            sys.stdout.write('    Title:  %s\n' % md.title.encode('utf-8'))
            sys.stdout.write('    Type:   %s\n' % md.releaseType.encode('utf-8'))  # noqa: E501
            sys.stdout.write('    URL: %s\n' % md.url)
            sys.stdout.write('    Tracks: %d\n' % len(md.tracks))
            if md.catalogNumber:
                sys.stdout.write('    Cat no: %s\n' % md.catalogNumber)
            if md.barcode:
                sys.stdout.write('   Barcode: %s\n' % md.barcode)

                for j, track in enumerate(md.tracks):
                    sys.stdout.write('      Track %2d: %s - %s\n' % (
                        j + 1, track.artist.encode('utf-8'),
                        track.title.encode('utf-8')))
