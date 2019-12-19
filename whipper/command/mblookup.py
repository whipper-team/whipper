from whipper.command.basecommand import BaseCommand
from whipper.common.mbngs import musicbrainz, getReleaseMetadata

import re


class MBLookup(BaseCommand):
    summary = "lookup MusicBrainz entry"
    description = """Look up a MusicBrainz disc id and output information.

You can get the MusicBrainz disc id with whipper cd info.

Example disc id: KnpGsLhvH.lPrNc1PBL21lb9Bg4-"""

    def add_arguments(self):
        self.parser.add_argument(
            'mbid', action='store', help="MB disc id or release id to look up"
        )

    def _printMetadata(self, md):
        """
        Print out metadata received in a sensible way.

        :param md: MusicBrainz's metadata about the disc
        :type md: `DiscMetadata`
        """
        print('    Artist: %s' % md.artist.encode('utf-8'))
        print('    Title:  %s' % md.title.encode('utf-8'))
        print('    Type:   %s' % str(md.releaseType).encode('utf-8'))
        print('    URL:    %s' % md.url)
        print('    Tracks: %d' % len(md.tracks))
        if md.catalogNumber:
            print('    Cat no: %s' % md.catalogNumber)
        if md.barcode:
            print('    Barcode: %s' % md.barcode)

            for j, track in enumerate(md.tracks):
                print('      Track %2d: %s - %s' % (
                    j + 1, track.artist.encode('utf-8'),
                    track.title.encode('utf-8')
                ))

    def do(self):
        try:
            mbid = str(self.options.mbid.strip())
        except IndexError:
            print('Please specify a MusicBrainz disc id or release id.')
            return 3

        releaseIdMatch = re.match(
            r'^[\dA-Fa-f]{8}-(?:[\dA-Fa-f]{4}-){3}[\dA-Fa-f]{12}$',
            mbid
        )
        discIdMatch = re.match(
            r'^[\dA-Za-z._]{27}-$',
            mbid
        )

        # see https://musicbrainz.org/doc/MusicBrainz_Identifier
        if releaseIdMatch:
            md = getReleaseMetadata(releaseIdMatch.group(0))
            if md:
                self._printMetadata(md)
        elif discIdMatch:
            metadatas = musicbrainz(discIdMatch.group(0))

            print('%d releases' % len(metadatas))
            for i, md in enumerate(metadatas):
                print('- Release %d:' % (i + 1, ))
                self._printMetadata(md)
        return None
