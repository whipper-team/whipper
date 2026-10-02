# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import shutil
import unittest
from unittest.mock import MagicMock, patch

import musicbrainzngs

from tempfile import NamedTemporaryFile
from whipper.common import program, mbngs, config
from whipper.command.cd import DEFAULT_DISC_TEMPLATE


class PathTestCase(unittest.TestCase):

    def testStandardTemplateEmpty(self):
        prog = program.Program(config.Config())

        path = prog.getPath('/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', None)
        self.assertEqual(path, ('/tmp/unknown/Unknown Artist - mbdiscid/'
                                'Unknown Artist - mbdiscid'))

    def testStandardTemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.releaseTitle = 'Grace'

        path = prog.getPath('/tmp', DEFAULT_DISC_TEMPLATE,
                            'mbdiscid', md, 0)
        self.assertEqual(path, ('/tmp/unknown/Jeff Buckley - Grace/'
                                'Jeff Buckley - Grace'))

    def testIssue66TemplateFilled(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.releaseTitle = 'Grace'

        path = prog.getPath('/tmp', '%A/%d', 'mbdiscid', md, 0)
        self.assertEqual(path,
                         '/tmp/Jeff Buckley/Grace')


# TODO: Test cover art embedding too.
class CoverArtTestCase(unittest.TestCase):

    @staticmethod
    def _mock_get_front_image(release_id):
        """
        Mock `musicbrainzngs.get_front_image` function.

        Reads a local cover art image and returns its binary data.

        :param release_id: a release id (self.program.metadata.mbid)
        :type  release_id: str
        :returns: the binary content of the local cover art image
        :rtype: bytes
        """
        filename = '%s.jpg' % release_id
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, 'rb') as f:
            return f.read()

    def _mock_getCoverArt(self, path, release_id):
        """
        Mock `common.program.getCoverArt` function.

        :param path: where to store the fetched image
        :type  path: str
        :param release_id: a release id (self.program.metadata.mbid)
        :type  release_id: str
        :returns: path to the downloaded cover art
        :rtype: str
        """
        cover_art_path = os.path.join(path, 'cover.jpg')

        data = self._mock_get_front_image(release_id)

        with NamedTemporaryFile(suffix='.cover.jpg', delete=False) as f:
            f.write(data)
        os.chmod(f.name, 0o644)
        shutil.move(f.name, cover_art_path)
        return cover_art_path

    def testCoverArtPath(self):
        """Test whether a fetched cover art is saved properly."""
        # Using: Dummy by Portishead
        # https://musicbrainz.org/release/76df3287-6cda-33eb-8e9a-044b5e15ffdd
        path = os.path.dirname(__file__)
        release_id = "76df3287-6cda-33eb-8e9a-044b5e15ffdd"
        coverArtPath = self._mock_getCoverArt(path, release_id)
        self.assertTrue(os.path.isfile(coverArtPath))


class MusicBrainzFallbackTestCase(unittest.TestCase):
    """Fall back to the requested release if the disc id is unknown."""

    RELEASE_ID = '94a934cd-eccd-4aff-a9f7-7a0e14192d80'
    DISCID = 'h7d9QcErIIaZ_VQsUxEdg4W9Vvc-'

    def setUp(self):
        self.program = program.Program(config.Config())
        self.ittoc = MagicMock()
        self.ittoc.duration.return_value = 4124520
        self.ittoc.getAudioTracks.return_value = 12

        self.metadata = mbngs.DiscMetadata()
        self.metadata.artist = 'Various Artists'
        self.metadata.releaseTitle = 'Ultra Dance 06 (Disc 2 of 2)'
        self.metadata.duration = 4124000
        self.metadata.mbid = self.RELEASE_ID
        self.metadata.url = ('https://musicbrainz.org/release/' +
                             self.RELEASE_ID)

    def _notFound(self, *args, **kwargs):
        raise mbngs.NotFoundException(Exception('404'))

    @patch('whipper.common.mbngs.getReleaseMetadataByToc')
    @patch('whipper.common.mbngs.musicbrainz')
    def testFallbackToRequestedRelease(self, musicbrainz, byToc):
        musicbrainz.side_effect = self._notFound
        byToc.return_value = self.metadata

        ret = self.program.getMusicBrainz(self.ittoc, self.DISCID,
                                          release=self.RELEASE_ID)

        self.assertIs(ret, self.metadata)
        byToc.assert_called_once_with(self.RELEASE_ID, 12, 4124520,
                                      discid=self.DISCID, country=None,
                                      record=False)

    @patch('whipper.common.mbngs.getReleaseMetadataByToc')
    @patch('whipper.common.mbngs.musicbrainz')
    def testNoFallbackWithoutRequestedRelease(self, musicbrainz, byToc):
        musicbrainz.side_effect = self._notFound

        ret = self.program.getMusicBrainz(self.ittoc, self.DISCID)

        self.assertIsNone(ret)
        byToc.assert_not_called()

    @patch('whipper.common.mbngs.getReleaseMetadataByToc')
    @patch('whipper.common.mbngs.musicbrainz')
    def testFallbackReleaseLookupFails(self, musicbrainz, byToc):
        musicbrainz.side_effect = self._notFound
        byToc.side_effect = musicbrainzngs.ResponseError()

        ret = self.program.getMusicBrainz(self.ittoc, self.DISCID,
                                          release=self.RELEASE_ID)

        self.assertIsNone(ret)

    @patch('whipper.common.mbngs.getReleaseMetadataByToc')
    @patch('whipper.common.mbngs.musicbrainz')
    def testNoFallbackWhenDiscIdKnown(self, musicbrainz, byToc):
        musicbrainz.return_value = [self.metadata]

        ret = self.program.getMusicBrainz(self.ittoc, self.DISCID,
                                          release=self.RELEASE_ID)

        self.assertIs(ret, self.metadata)
        byToc.assert_not_called()
