# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import shutil
import unittest
from unittest import mock

from tempfile import NamedTemporaryFile
from whipper.common import program, mbngs, config

# Keep in sync with whipper.command.cd.DEFAULT_DISC_TEMPLATE.
# Imported as a literal so this unit test does not need pycdio/cdio.
DEFAULT_DISC_TEMPLATE = '%r/%A - %d/%A - %d'


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

    def testIssue585UnknownDiscDiscNumberTemplate(self):
        """%N/%M must not KeyError when ripping without MusicBrainz data."""
        prog = program.Program(config.Config())
        path = prog.getPath('/tmp', '%A - %d/%N-%t %n',
                            'mbdiscid', None, 3)
        self.assertEqual(
            path,
            '/tmp/Unknown Artist - mbdiscid/1-03 Unknown Track 3')

    def testIssue585UnknownDiscDiscTotals(self):
        prog = program.Program(config.Config())
        path = prog.getPath('/tmp', '%M-%N', 'mbdiscid', None)
        self.assertEqual(path, '/tmp/1-1')

    def testIssue585MetadataWithoutDiscNumbers(self):
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Jeff Buckley'
        md.releaseTitle = 'Grace'
        # discNumber/discTotal remain None
        path = prog.getPath('/tmp', '%A/%M-%N', 'mbdiscid', md)
        self.assertEqual(path, '/tmp/Jeff Buckley/1-1')


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

    def testFetchFrontImageUsesGetImageFront(self):
        payload = b'\xff\xd8fakejpeg'
        with mock.patch.object(program.musicbrainzngs, 'get_image_front',
                               return_value=payload) as front:
            data = program.fetch_front_image('release-id', 500)
        self.assertEqual(data, payload)
        front.assert_called_once_with('release-id', 500)

    def testFetchFrontImageFallbackWithoutGetImageFront(self):
        """Issue #554: some musicbrainzngs builds lack get_image_front."""
        payload = b'\xff\xd8fallback'
        listing = {
            'images': [{
                'front': True,
                'image': 'https://coverartarchive.org/release/x/front',
                'thumbnails': {
                    '500': 'https://coverartarchive.org/release/x/front-500',
                },
            }]
        }

        class FakeResponse:
            def read(self):
                return payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with mock.patch.object(program.musicbrainzngs, 'get_image_front',
                               None), \
                mock.patch.object(program.musicbrainzngs, 'get_image_list',
                                  return_value=listing) as image_list, \
                mock.patch('urllib.request.urlopen',
                           return_value=FakeResponse()) as urlopen:
            data = program.fetch_front_image('release-id', 500)

        self.assertEqual(data, payload)
        image_list.assert_called_once_with('release-id')
        urlopen.assert_called_once()
        self.assertIn('front-500', urlopen.call_args[0][0])

    def testGetCoverArtWritesFile(self):
        import tempfile
        payload = self._mock_get_front_image(
            '76df3287-6cda-33eb-8e9a-044b5e15ffdd')
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(program, 'fetch_front_image',
                                   return_value=payload):
                out = program.Program.getCoverArt(tmp, 'release-id')
            self.assertIsNotNone(out)
            self.assertTrue(os.path.isfile(out))
            with open(out, 'rb') as f:
                self.assertEqual(f.read(), payload)
