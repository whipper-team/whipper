"""Destination filesystem tests; NAME_MAX values are simulated, not mounted."""

import os
import tempfile
import unittest
import unicodedata
from unittest import mock

from whipper.common import common, config, mbngs, program, renamer


class DestinationNameMaxTestCase(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = os.path.realpath(self.temp.name)
        self.destination = os.path.join(self.root, 'destination')
        os.mkdir(self.destination)
        self.prog = program.Program(config.Config())

    def pathconf(self, limit):
        def lookup(directory, key):
            self.assertEqual(key, 'PC_NAME_MAX')
            self.assertTrue(os.path.isdir(directory), directory)
            directory = os.path.realpath(directory)
            if (directory == self.destination or
                    directory.startswith(self.destination + os.sep)):
                return limit
            # The working directory's filesystem deliberately differs.
            return 255 if limit == 128 else 128
        return mock.patch.object(common.os, 'pathconf', side_effect=lookup)

    def metadata(self, title):
        md = mbngs.DiscMetadata()
        md.artist = md.sortName = 'Artist'
        md.releaseTitle = md.title = title
        return md

    def testMissingOutputDirectories(self):
        for limit in (128, 255):
            for relative in (False, True):
                for title in ('a' * 400, '界' * 150, 'e\u0301' * 200):
                    with self.subTest(limit=limit, relative=relative,
                                      title=title[:3]):
                        outdir = os.path.join(self.destination, 'missing',
                                              'nested')
                        if relative:
                            outdir = os.path.relpath(outdir)
                        md = self.metadata(title)
                        with self.pathconf(limit) as lookup:
                            result = self.prog.getPath(
                                outdir, '%d/%D', 'discid', md)
                        normalized = unicodedata.normalize('NFC', title)
                        expected_dir = normalized.encode('utf-8')[:limit]
                        expected_dir = expected_dir.decode('utf-8', 'ignore')
                        expected_file = normalized.encode('utf-8')[:limit - 8]
                        expected_file = expected_file.decode('utf-8', 'ignore')
                        self.assertEqual(result, os.path.join(
                            outdir, expected_dir, expected_file))
                        self.assertTrue(lookup.called)
                        for extension in ('.flac', '.log', '.cue', '.toc'):
                            self.assertLessEqual(len(os.path.basename(
                                result + extension).encode('utf-8')), limit)
                        self.assertFalse(os.path.exists(os.path.join(
                            self.destination, 'missing')))

    def testExistingNestedDestination(self):
        album = os.path.join(self.destination, 'album')
        os.mkdir(album)
        with self.pathconf(128) as lookup:
            result = self.prog.getPath(
                self.destination, 'album/%d', 'discid',
                self.metadata('a' * 400))
        self.assertEqual(result, os.path.join(album, 'a' * 120))
        self.assertEqual(lookup.call_args_list[-1],
                         mock.call(album, 'PC_NAME_MAX'))

    def testComponentsRetainFullDestination(self):
        for limit in (128, 255):
            for relative in (False, True):
                with self.subTest(limit=limit, relative=relative):
                    path = os.path.join(self.destination, 'missing',
                                        '界' * 150, 'a' * 400)
                    if relative:
                        path = os.path.relpath(path)
                    with self.pathconf(limit):
                        result = common.truncate_path_components(path)
                    expected = os.path.join(
                        self.destination, 'missing', '界' * (limit // 3),
                        'a' * (limit - common.EXTENSION_RESERVE))
                    if relative:
                        expected = os.path.relpath(expected)
                    self.assertEqual(result, expected)

    def testTruncatedParentDeterminesChildFilesystem(self):
        # The emitted directory already exists and represents another mount.
        truncated_parent = os.path.join(self.destination, 'a' * 128)
        os.mkdir(truncated_parent)

        def lookup(directory, key):
            self.assertTrue(os.path.isdir(directory))
            return 255 if directory == truncated_parent else 128

        with mock.patch.object(common.os, 'pathconf', side_effect=lookup):
            path = os.path.join(self.destination, 'a' * 400, 'b' * 400)
            self.assertEqual(common.truncate_path_components(path),
                             os.path.join(truncated_parent, 'b' * 247))
            self.assertEqual(self.prog.getPath(
                self.destination, '%d/' + 'b' * 400, 'discid',
                self.metadata('a' * 400)),
                os.path.join(truncated_parent, 'b' * 247))

    def testFilenamePreservesExtensionAtDestination(self):
        for limit in (128, 255):
            with self.subTest(limit=limit), self.pathconf(limit):
                result = common.truncate_filename(os.path.join(
                    self.destination, 'missing', '界' * 150 + '.flac'))
                self.assertEqual(result, os.path.join(
                    self.destination, 'missing',
                    '界' * ((limit - 5) // 3) + '.flac'))

    def testNumberedTracksStayDistinctAndExistingAudioIsPreserved(self):
        for limit in (128, 255):
            with self.subTest(limit=limit), self.pathconf(limit):
                md = self.metadata('a' * 400)
                md.tracks = [mock.Mock(artist='Artist', sortName='Artist',
                                       title='a' * 400) for _ in range(2)]
                paths = [self.prog.getPath(
                    self.destination, '%t. %d', 'discid', md, number) + '.flac'
                         for number in (1, 2)]
                self.assertNotEqual(paths[0], paths[1])
                with open(paths[0], 'wb') as audio:
                    audio.write(b'existing audio')
                self.assertEqual(self.prog.getPath(
                    self.destination, '%t. %d', 'discid', md, 1) + '.flac',
                    paths[0])
                with open(paths[1], 'wb') as audio:
                    audio.write(b'other audio')
                # Retain the existing renamer's collision refusal.
                with self.assertRaises(AssertionError):
                    renamer.RenameFile(paths[1], paths[0]).verify()
                with open(paths[0], 'rb') as audio:
                    self.assertEqual(audio.read(), b'existing audio')

    def testTemplateSpellingPreserved(self):
        for outdir in ('.', '', self.destination):
            for template in ('%A/%d', './%A/../%d', '/%A//%d/', ''):
                with self.subTest(outdir=outdir, template=template):
                    expanded = template.strip('/').replace('%A', 'Artist')
                    expanded = expanded.replace('%d', 'Album')
                    parts = [p for p in expanded.split('/') if p]
                    expected = os.path.join(*parts) if parts else ''
                    if outdir != '.':
                        expected = os.path.join(outdir, expected)
                    self.assertEqual(self.prog.getPath(
                        outdir, template, 'discid', self.metadata('Album')),
                        expected)
