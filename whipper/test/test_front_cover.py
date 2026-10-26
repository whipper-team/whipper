"""Front-cover fallback selection and file-saving regressions."""

import os
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError

from whipper.common import program


class FrontCoverTestCase(unittest.TestCase):
    def setUp(self):
        self.api = mock.patch.object(program.musicbrainzngs,
                                     'get_image_front', None)
        self.api.start()
        self.addCleanup(self.api.stop)
        self.listing = mock.patch.object(program.musicbrainzngs,
                                         'get_image_list')
        self.image_list = self.listing.start()
        self.addCleanup(self.listing.stop)
        self.http = mock.patch('urllib.request.urlopen')
        self.urlopen = self.http.start()
        self.addCleanup(self.http.stop)
        self.payload = b'front-image-bytes'
        self.urlopen.return_value.__enter__.return_value.read.return_value = (
            self.payload)
        self.back = {'front': False, 'types': ['Back'],
                     'image': 'https://example.invalid/back.jpg'}
        self.front = {'front': True,
                      'image': 'https://example.invalid/front.jpg'}

    def assertNoCover(self, listing):
        self.image_list.return_value = listing
        with TemporaryDirectory() as directory:
            self.assertIsNone(program.Program.getCoverArt(
                directory, 'release'))
            self.assertEqual(os.listdir(directory), [])
        self.image_list.assert_called_once_with('release')
        self.urlopen.assert_not_called()

    def testFrontAfterOtherArtworkIsDownloadedAndSaved(self):
        self.image_list.return_value = {'images': [self.back, self.front]}
        with TemporaryDirectory() as directory:
            path = program.Program.getCoverArt(directory, 'release')
            self.assertEqual(path, os.path.join(directory, 'cover.jpg'))
            with open(path, 'rb') as image:
                self.assertEqual(image.read(), self.payload)
            self.assertEqual(os.listdir(directory), ['cover.jpg'])
        self.urlopen.assert_called_once_with(self.front['image'], timeout=30)

    def testBackOnlyDoesNotDownloadOrSave(self):
        self.assertNoCover({'images': [self.back]})

    def testUndesignatedArtworkDoesNotDownloadOrSave(self):
        self.assertNoCover({'images': [
            {'types': ['Booklet'],
             'image': 'https://example.invalid/book.jpg'},
            {'image': 'https://example.invalid/unknown.jpg'}]})

    def testEmptyOrMissingImagesDoNotDownloadOrSave(self):
        for listing in ({'images': []}, {'images': None}, {}, None):
            with self.subTest(listing=listing):
                self.image_list.reset_mock()
                self.assertNoCover(listing)

    def testFrontWithoutURLDoesNotDownloadOtherArtwork(self):
        for thumbnails in (None, {}, {'500': ''}):
            with self.subTest(thumbnails=thumbnails):
                self.image_list.reset_mock()
                self.assertNoCover({'images': [self.back, {
                    'front': True, 'thumbnails': thumbnails}]})

    def testThumbnailPreferenceAndOriginalURLFallback(self):
        urls = {'250': 'https://example.invalid/250.jpg',
                '500': 'https://example.invalid/500.jpg',
                'large': 'https://example.invalid/large.jpg'}
        for thumbnails, expected in (
                (urls, urls['250']),
                ({'500': urls['500'], 'large': urls['large']}, urls['500']),
                ({'large': urls['large']}, urls['large']),
                ({}, self.front['image']),
                ({'250': '', '500': None}, self.front['image'])):
            with self.subTest(thumbnails=thumbnails):
                self.urlopen.reset_mock()
                front = dict(self.front, thumbnails=thumbnails)
                self.image_list.return_value = {'images': [self.back, front]}
                self.assertEqual(program.fetch_front_image('release', 250),
                                 self.payload)
                self.urlopen.assert_called_once_with(expected, timeout=30)

    def testDownloadFailuresNeverSaveOtherArtwork(self):
        errors = (URLError('offline'), OSError('read failed'),
                  HTTPError(self.front['image'], 404, 'missing', None, None))
        for error in errors:
            for during_read in (False, True):
                with self.subTest(error=error, during_read=during_read):
                    self.urlopen.reset_mock(side_effect=True)
                    response = self.urlopen.return_value.__enter__.return_value
                    response.read.side_effect = error if during_read else None
                    if not during_read:
                        self.urlopen.side_effect = error
                    self.image_list.return_value = {
                        'images': [self.back, self.front]}
                    with TemporaryDirectory() as directory:
                        existing = os.path.join(directory, 'cover.jpg')
                        with open(existing, 'wb') as image:
                            image.write(b'existing-cover')
                        self.assertIsNone(program.Program.getCoverArt(
                            directory, 'release'))
                        with open(existing, 'rb') as image:
                            self.assertEqual(image.read(), b'existing-cover')
                        self.assertEqual(os.listdir(directory), ['cover.jpg'])
                        os.unlink(existing)
                        self.assertIsNone(program.Program.getCoverArt(
                            directory, 'release'))
                        self.assertEqual(os.listdir(directory), [])
                    self.assertEqual(self.urlopen.call_args_list, [
                        mock.call(self.front['image'], timeout=30)] * 2)
