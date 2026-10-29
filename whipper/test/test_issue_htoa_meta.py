# -*- Mode: Python; test-case-name: whipper.test.test_issue_htoa_meta -*-
# vi:si:et:sw=4:sts=4:ts=4

"""Unit tests for #282/#346/#309/#485 HTOA skip, default device, tags."""

import argparse
import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

from whipper.command import cd
from whipper.common import config as config_mod
from whipper.common import mbngs
from whipper.common import program as program_mod
from whipper.common.path import PathFilter
from whipper.image import table
from whipper.result import result


class ConfigDefaultDeviceTestCase(unittest.TestCase):
    """#346: [main] device / command-section device sets default drive."""

    def testGetSetDefaultDevice(self):
        fd, path = tempfile.mkstemp(suffix='.whipperrc')
        os.close(fd)
        with open(path, 'w') as f:
            f.write('[main]\ndevice = /dev/sr1\n')
        self.addCleanup(lambda p=path: os.path.exists(p) and os.unlink(p))
        cfg = config_mod.Config(path)
        self.assertEqual(cfg.getDefaultDevice(), '/dev/sr1')

    def testSetDefaultDevice(self):
        fd, path = tempfile.mkstemp(suffix='.whipperrc')
        os.close(fd)
        with open(path, 'w') as f:
            f.write('')
        self.addCleanup(lambda p=path: os.path.exists(p) and os.unlink(p))
        cfg = config_mod.Config(path)
        cfg.setDefaultDevice('/dev/sr0')
        cfg2 = config_mod.Config(path)
        self.assertEqual(cfg2.getDefaultDevice(), '/dev/sr0')

    def testNoDefaultDevice(self):
        fd, path = tempfile.mkstemp(suffix='.whipperrc')
        os.close(fd)
        with open(path, 'w') as f:
            f.write('[whipper]\n')
        self.addCleanup(lambda p=path: os.path.exists(p) and os.unlink(p))
        cfg = config_mod.Config(path)
        self.assertIsNone(cfg.getDefaultDevice())


class GenreNamesTestCase(unittest.TestCase):
    """#309: extract genre names from MusicBrainz entities."""

    def testExtractGenres(self):
        entity = {'genre-list': [
            {'name': 'Rock', 'count': 5},
            {'name': 'Indie Rock', 'count': 2},
            {'name': 'Rock'},  # duplicate
            {'count': 1},  # missing name
        ]}
        self.assertEqual(mbngs._genre_names(entity),
                         ['Rock', 'Indie Rock'])

    def testEmptyGenres(self):
        self.assertEqual(mbngs._genre_names({}), [])
        self.assertEqual(mbngs._genre_names({'genre-list': []}), [])


class GetTagListTestCase(unittest.TestCase):
    """#485/#309: HTOA and genres tags."""

    def _program_with_meta(self):
        prog = program_mod.Program.__new__(program_mod.Program)
        md = mbngs.DiscMetadata()
        md.artist = 'Mates of State'
        md.sortName = 'Mates of State'
        md.title = 'Bring It Back'
        md.mbid = 'release-mbid'
        md.mbidReleaseGroup = 'rg-mbid'
        md.mbidArtist = ['artist-mbid']
        md.release = '2006-03-07'
        md.discNumber = 1
        md.discTotal = 1
        md.genres = ['Indie Pop', 'Indie Rock']
        track = mbngs.TrackMetadata()
        track.artist = 'Mates of State'
        track.title = 'Think Long'
        track.mbid = 'track-mbid'
        track.mbidRecording = 'rec-mbid'
        track.mbidArtist = ['artist-mbid']
        track.mbidWorks = []
        track.composers = []
        track.performers = []
        md.tracks.append(track)
        prog.metadata = md
        return prog

    def testHtoaGetsAlbumMbidsAndDiscid(self):
        """#485: track 0 must include MusicBrainz IDs like other tracks."""
        prog = self._program_with_meta()
        tags = prog.getTagList(0, 'discid123')
        self.assertEqual(tags['MUSICBRAINZ_DISCID'], 'discid123')
        self.assertEqual(tags['MUSICBRAINZ_ALBUMID'], 'release-mbid')
        self.assertEqual(tags['MUSICBRAINZ_RELEASEGROUPID'], 'rg-mbid')
        self.assertEqual(tags['MUSICBRAINZ_ALBUMARTISTID'], ['artist-mbid'])
        self.assertEqual(tags['TITLE'], 'Hidden Track One Audio')
        self.assertEqual(tags['TRACKNUMBER'], '0')
        # no track-level recording id on HTOA
        self.assertNotIn('MUSICBRAINZ_TRACKID', tags)
        self.assertNotIn('MUSICBRAINZ_RELEASETRACKID', tags)
        self.assertEqual(tags['GENRE'], ['Indie Pop', 'Indie Rock'])

    def testHtoaUsesMbhTitleWhenPresent(self):
        prog = self._program_with_meta()
        prog.metadata.htoaTitle = 'How Hard'
        tags = prog.getTagList(0, 'discid123')
        self.assertEqual(tags['TITLE'], 'How Hard')

    def testParsedPregapTitleReachesTagsWithoutShiftingTracks(self):
        release_id = '410f99f8-a876-3416-bd8e-42233a00a477'
        filename = 'whipper.release.' + release_id + '.json'
        with open(os.path.join(os.path.dirname(__file__), filename)) as handle:
            release = json.load(handle)['release']
        medium = release['medium-list'][0]
        discid = medium['disc-list'][0]['id']
        for title in ('Hidden Prelude', None):
            with self.subTest(title=title):
                if title is not None:
                    medium['pregap'] = {'title': title, 'recording': {
                        'id': 'pregap-recording-id', 'title': title,
                    }}
                else:
                    medium.pop('pregap', None)
                prog = program_mod.Program.__new__(program_mod.Program)
                prog.metadata = mbngs._getMetadata(release, discid)

                tags = prog.getTagList(0, discid)
                self.assertEqual(tags['TITLE'],
                                 title or 'Hidden Track One Audio')
                self.assertEqual(tags['MUSICBRAINZ_DISCID'], discid)
                self.assertEqual(tags['MUSICBRAINZ_ALBUMID'], release_id)
                self.assertEqual(tags['MUSICBRAINZ_RELEASEGROUPID'],
                                 release['release-group']['id'])
                self.assertEqual(tags['TRACKNUMBER'], '0')
                self.assertNotIn('MUSICBRAINZ_TRACKID', tags)
                self.assertNotIn('MUSICBRAINZ_RELEASETRACKID', tags)
                self.assertNotIn('MUSICBRAINZ_ARTISTID', tags)

                normal_tags = prog.getTagList(1, discid)
                self.assertEqual(normal_tags['TITLE'], 'Fields of Joy')
                self.assertEqual(normal_tags['TRACKTOTAL'], '14')
                first = medium['track-list'][0]
                self.assertEqual(normal_tags['MUSICBRAINZ_RELEASETRACKID'],
                                 first['id'])
                self.assertEqual(normal_tags['MUSICBRAINZ_TRACKID'],
                                 first['recording']['id'])

    def testNormalTrackStillHasTrackMbids(self):
        prog = self._program_with_meta()
        tags = prog.getTagList(1, 'discid123')
        self.assertEqual(tags['MUSICBRAINZ_TRACKID'], 'rec-mbid')
        self.assertEqual(tags['MUSICBRAINZ_RELEASETRACKID'], 'track-mbid')
        self.assertEqual(tags['MUSICBRAINZ_ALBUMID'], 'release-mbid')
        self.assertEqual(tags['TITLE'], 'Think Long')
        self.assertEqual(tags['GENRE'], ['Indie Pop', 'Indie Rock'])

    def testUnknownDiscPreservesDiscid(self):
        prog = program_mod.Program.__new__(program_mod.Program)
        prog.metadata = None
        for number in (0, 1):
            with self.subTest(number=number):
                tags = prog.getTagList(number, 'discid123')
                self.assertEqual(tags['MUSICBRAINZ_DISCID'], 'discid123')
                self.assertEqual(tags['TITLE'], 'Unknown Track')
                self.assertEqual(tags['ARTIST'], 'Unknown Artist')
                self.assertEqual(tags['ALBUM'], 'Unknown Album')
                self.assertEqual(tags['TRACKNUMBER'], str(number))
                self.assertNotIn('MUSICBRAINZ_ALBUMID', tags)
                self.assertNotIn('MUSICBRAINZ_TRACKID', tags)
                self.assertNotIn('MUSICBRAINZ_RELEASETRACKID', tags)
                self.assertNotIn('GENRE', tags)

    def testUnknownDiscWithoutDiscid(self):
        prog = program_mod.Program.__new__(program_mod.Program)
        prog.metadata = None
        for number in (0, 1):
            for discid in (None, ''):
                with self.subTest(number=number, discid=discid):
                    tags = prog.getTagList(number, discid)
                    self.assertEqual(tags['TITLE'], 'Unknown Track')
                    self.assertEqual(tags['TRACKNUMBER'], str(number))
                    self.assertNotIn('MUSICBRAINZ_DISCID', tags)

    def testMissingGenresKeepOtherMetadata(self):
        for genres in (None, []):
            for number in (0, 1):
                with self.subTest(genres=genres, number=number):
                    prog = self._program_with_meta()
                    prog.metadata.genres = genres
                    tags = prog.getTagList(number, 'discid123')
                    self.assertNotIn('GENRE', tags)
                    self.assertEqual(tags['MUSICBRAINZ_DISCID'], 'discid123')
                    self.assertEqual(tags['MUSICBRAINZ_ALBUMID'],
                                     'release-mbid')
                    self.assertEqual(tags['TITLE'], 'Think Long' if number
                                     else 'Hidden Track One Audio')


class SkipHtoaOptionTestCase(unittest.TestCase):
    """#282: exercise the parsed option through ripping and cue output."""

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.outdir = directory.name
        self.cmd = cd.Rip.__new__(cd.Rip)
        self.cmd.parser = argparse.ArgumentParser()
        self.cmd.opts = SimpleNamespace(device='unused-device')
        # Argument registration normally queries the drive for its offset.
        with mock.patch.object(cd.drive, 'getDeviceInfo', return_value=None):
            self.cmd.add_arguments()
        self.cmd.device = 'unused-device'
        self.cmd.runner = mock.Mock(spec=[])
        self.cmd.logger = mock.Mock()
        self.cmd.skipped_tracks = []
        self.prog = program_mod.Program.__new__(program_mod.Program)
        self.prog._filter = PathFilter()
        self.prog.metadata = None
        self.prog.result = result.RipResult()
        self.cmd.program = self.prog
        self.prog.ripTrack = mock.Mock(side_effect=self._extract)
        self.prog.verifyTrack = mock.Mock(return_value=True)
        self.prog.verifyImage = mock.Mock()
        self.prog.writeLog = mock.Mock()
        self.prog.writeCue = mock.Mock(wraps=self.prog.writeCue)
        self.prog.write_m3u = mock.Mock(wraps=self.prog.write_m3u)
        self.cmd.mbdiscid = 'synthetic-disc'

    def _prepare(self, skip=True, htoa=True):
        args = ['--offset=0', '--output-directory', self.outdir,
                '--disc-template', 'album', '--track-template', '%t']
        if skip:
            args.append('--skip-htoa')
        self.cmd.options = self.cmd.parser.parse_args(args)
        toc = table.Table()
        first = table.Track(1)
        if htoa:
            first.index(0, absolute=0, path='disc.bin', relative=0, counter=0)
        first.index(1, absolute=150 if htoa else 0, path='disc.bin',
                    relative=150 if htoa else 0, counter=0)
        first.index(2, absolute=450, path='disc.bin', relative=450, counter=0)
        second = table.Track(2)
        second.index(0, absolute=900, path='disc.bin', relative=900, counter=0)
        second.index(1, absolute=1050, path='disc.bin', relative=1050,
                     counter=0)
        toc.tracks = [first, second]
        toc.leadout = 1800
        self.cmd.itable = self.prog.result.table = toc
        self.assertTrue(toc.hasTOC())
        return toc

    @staticmethod
    def _extract(runner, track_result, **kwargs):
        # Stand in for extracted audio without running an encoder or drive.
        with open(track_result.filename, 'wb') as handle:
            handle.write(b'synthetic audio')
        track_result.peak = 100
        track_result.testcrc = track_result.copycrc = 123

    def _run(self):
        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(cd.accurip, 'print_report'):
            return self.cmd.doCommand()

    def _read(self, suffix):
        with open(os.path.join(self.outdir, 'album' + suffix)) as handle:
            return handle.read()

    def _extracted(self):
        return [call.args[1].number
                for call in self.prog.ripTrack.call_args_list]

    def testSkipHtoaClearsOnlyHiddenIndexBeforeExtraction(self):
        toc = self._prepare()
        original = {id(index): vars(index).copy()
                    for track in toc.tracks for index in track.indexes.values()
                    if index is not toc.tracks[0].indexes[0]}

        def extract(runner, track_result, **kwargs):
            if track_result.number == 1:
                self.assertIsNone(toc.tracks[0].indexes[0].path)
                for track in toc.tracks:
                    for index in track.indexes.values():
                        if id(index) in original:
                            self.assertEqual(vars(index), original[id(index)])
            self._extract(runner, track_result, **kwargs)

        self.prog.ripTrack.side_effect = extract
        with mock.patch.object(toc, 'setFile', wraps=toc.setFile) as set_file:
            self._run()
        self.assertTrue(self.cmd.options.skip_htoa)
        self.assertEqual(set_file.call_args_list[0],
                         mock.call(1, 0, None, 150, 0))
        self.assertEqual(self._extracted(), [1, 2])
        hidden = toc.tracks[0].indexes[0]
        self.assertEqual((hidden.absolute, hidden.relative, hidden.counter),
                         (0, 0, 0))
        self.assertIsNone(hidden.path)

    def testDefaultStillExtractsHtoa(self):
        toc = self._prepare(skip=False)
        self.assertFalse(self.cmd.options.skip_htoa)
        self._run()
        self.assertEqual(self._extracted(), [0, 1, 2])
        hidden_path = os.path.join(self.outdir, '00.flac')
        self.assertEqual(toc.tracks[0].indexes[0].path, hidden_path)
        self.assertTrue(os.path.isfile(hidden_path))
        self.assertIn('FILE "00.flac" WAVE', self._read('.cue'))
        self.assertIn('00.flac', self._read('.m3u'))
        self.assertIsNotNone(self.prog.result.getTrackResult(0))

    def _assertNoHtoa(self, skip):
        toc = self._prepare(skip=skip, htoa=False)
        self._run()
        self.assertNotIn(0, toc.tracks[0].indexes)
        self.assertEqual(self._extracted(), [1, 2])
        self.assertEqual([t.number for t in self.prog.result.tracks], [1, 2])
        self.assertNotIn('00.flac', self._read('.cue'))
        self.assertNotIn('PREGAP', self._read('.cue'))
        self.assertEqual(toc.tracks[1].getPregap(), 150)

    def testNoHtoaWithSkipLeavesOrdinaryExtractionUnchanged(self):
        self._assertNoHtoa(skip=True)

    def testNoHtoaByDefaultLeavesOrdinaryExtractionUnchanged(self):
        self._assertNoHtoa(skip=False)

    def testIndexClearingFailureAbortsBeforeExtractionOrOutput(self):
        toc = self._prepare()
        failure = RuntimeError('cannot clear HTOA index')
        set_file = toc.setFile

        def fail_clear(track, index, path, length, counter=None):
            if (track, index, path) == (1, 0, None):
                raise failure
            return set_file(track, index, path, length, counter)

        with mock.patch.object(toc, 'setFile', side_effect=fail_clear):
            with self.assertRaises(RuntimeError) as raised:
                self._run()
        self.assertIs(raised.exception, failure)
        self.prog.ripTrack.assert_not_called()
        self.prog.writeCue.assert_not_called()
        self.prog.write_m3u.assert_not_called()
        self.prog.verifyImage.assert_not_called()
        self.prog.writeLog.assert_not_called()
        self.assertEqual(self.prog.result.tracks, [])
        self.assertEqual(os.listdir(self.outdir), [])

    def testSkippedOutputAndResultsReferenceOnlyExtractedAudio(self):
        toc = self._prepare()
        self._run()
        cue = self._read('.cue')
        # Keep physical pregaps and INDEX 02 while mapping numbered audio.
        self.assertIn('  TRACK 01 AUDIO\n    PREGAP 00:02:00\n'
                      '    INDEX 01 00:00:00\n    INDEX 02 00:04:00', cue)
        self.assertIn('  TRACK 02 AUDIO\n    INDEX 00 00:10:00\n'
                      'FILE "02.flac" WAVE\n    INDEX 01 00:00:00', cue)
        self.assertEqual([line for line in cue.splitlines()
                          if line.startswith('FILE ')],
                         ['FILE "01.flac" WAVE', 'FILE "02.flac" WAVE'])
        self.assertEqual([t.number for t in self.prog.result.tracks], [1, 2])
        self.assertIsNone(self.prog.result.getTrackResult(0))
        self.assertEqual([t.pregap for t in self.prog.result.tracks],
                         [150, 150])
        self.assertEqual([t.getIndex(1).absolute for t in toc.tracks],
                         [150, 1050])
        self.assertEqual(toc.tracks[0].getIndex(2).absolute, 450)
        playlist = self._read('.m3u')
        self.assertNotIn('00.flac', playlist)
        self.assertNotIn('disc.bin', cue)
        self.assertNotIn('TRACK 00', cue)
        self.assertEqual(sorted(os.listdir(self.outdir)),
                         ['01.flac', '02.flac', 'album.cue', 'album.m3u'])
        for track in self.prog.result.tracks:
            self.assertTrue(os.path.isfile(track.filename))
            self.assertIn(os.path.basename(track.filename), playlist)
        self.prog.writeLog.assert_called_once()


class BaseCommandDefaultDeviceFromConfigTestCase(unittest.TestCase):
    """#346: device default comes from config when present."""

    def testUsesConfigDevice(self):
        from whipper.command import basecommand as bc

        class Dummy(bc.BaseCommand):
            summary = 'dummy'
            description = 'dummy'
            device_option = True

        with mock.patch.object(config_mod.Config, 'get', create=True), \
                mock.patch('whipper.command.basecommand.config.Config') as C, \
                mock.patch('whipper.command.basecommand.drive.'
                           'getAllDevicePaths',
                           return_value=['/dev/sr0']), \
                mock.patch('os.path.exists', return_value=True), \
                mock.patch('os.path.realpath', side_effect=lambda p: p):
            C.return_value.get.side_effect = (
                lambda sec, opt: '/dev/sr7' if opt == 'device' else None)
            C.return_value.getDefaultDevice.return_value = '/dev/sr7'
            cmd = Dummy([], 'whipper dummy', None)
        self.assertEqual(cmd.options.device, '/dev/sr7')

    def testFallsBackToFirstDrive(self):
        from whipper.command import basecommand as bc

        class Dummy(bc.BaseCommand):
            summary = 'dummy'
            description = 'dummy'
            device_option = True

        with mock.patch('whipper.command.basecommand.config.Config') as C, \
                mock.patch('whipper.command.basecommand.drive.'
                           'getAllDevicePaths',
                           return_value=['/dev/sr2']), \
                mock.patch('os.path.exists', return_value=True), \
                mock.patch('os.path.realpath', side_effect=lambda p: p):
            C.return_value.get.return_value = None
            C.return_value.getDefaultDevice.return_value = None
            cmd = Dummy([], 'whipper dummy', None)
        self.assertEqual(cmd.options.device, '/dev/sr2')
