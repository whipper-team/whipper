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
            print('Please specify a MusicBrainz disc id.')
            return 3

        metadatas = musicbrainz(discId)

        print('%d releases' % len(metadatas))
        for i, md in enumerate(metadatas):
            print('- Release %d:' % (i + 1, ))
            print('    Artist: %s' % md.artist.encode('utf-8'))
            print('    Title:  %s' % md.title.encode('utf-8'))
            print('    Type:   %s' % md.releaseType.encode('utf-8'))  # noqa: E501
            print('    URL:    %s' % md.url)
            print('    Tracks: %d' % len(md.tracks))
            if md.catalogNumber:
                print('    Cat no: %s' % md.catalogNumber)
            if md.barcode:
                print('   Barcode: %s' % md.barcode)

                for j, track in enumerate(md.tracks):
                    print('      Track %2d: %s - %s' % (
                        j + 1, track.artist.encode('utf-8'),
                        track.title.encode('utf-8')
                    ))

        return None
