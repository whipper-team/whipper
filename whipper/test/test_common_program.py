# -*- Mode: Python; test-case-name: whipper.test.test_common_program -*-
# vi:si:et:sw=4:sts=4:ts=4


import os
import shutil
import unittest
from unittest import mock

from tempfile import NamedTemporaryFile
from whipper.common import program, mbngs, config

# Keep in sync with whipper.command.cd.DEFAULT_DISC_TEMPLATE.
# Literal avoids importing command.cd (requires pycdio).
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

    def testIssue453LongTitlesTruncated(self):
        """#453: extremely long release titles must not exceed NAME_MAX."""
        prog = program.Program(config.Config())
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Soulwax'
        # Path length that historically raised ENAMETOOLONG
        md.releaseTitle = (
            "Most of the remixes we've made for other people over the "
            "years except for the one for Einstürzende Neubauten because "
            "we lost it and a few we didn't think sounded good enough "
            "or just didn't fit in length-wise, but including some that "
            "are hard to find because either people forgot about them or "
            "just simply because they haven't been released yet"
        )
        md.title = md.releaseTitle
        path = prog.getPath('/tmp', '%A - %d/%A - %d',
                            'mbdiscid', md, 0)
        for part in path.split(os.sep):
            if part:
                self.assertLessEqual(len(part.encode('utf-8')), 255)
        self.assertTrue(path.startswith('/tmp/Soulwax'))
        # Adding extensions must stay within NAME_MAX too
        flac = path + '.flac'
        self.assertLessEqual(len(os.path.basename(flac).encode('utf-8')), 255)


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
