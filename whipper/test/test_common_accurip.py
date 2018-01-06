# -*- Mode: Python; test-case-name: whipper.test.test_common_accurip -*-
# vi:si:et:sw=4:sts=4:ts=4

import sys
from StringIO import StringIO
from os import chmod, makedirs
from os.path import dirname, exists, join
from shutil import copy, rmtree
from tempfile import mkdtemp
from unittest import TestCase

from whipper.common import accurip
from whipper.common.accurip import (
    calculate_checksums, get_db_entry, print_report, verify_result,
    _split_responses, EntryNotFound
)
from whipper.result.result import RipResult, TrackResult


class TestAccurateRipResponse(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = 'c/1/2/dBAR-002-0000f21c-00027ef8-05021002.bin'
        cls.entry = _split_responses(
            open(join(dirname(__file__), cls.path[6:])).read()
        )
        cls.other_path = '4/8/2/dBAR-011-0010e284-009228a3-9809ff0b.bin'

    def setUp(self):
        self.cache_dir = mkdtemp(suffix='whipper_accurip_cache_test')
        accurip._CACHE_DIR = self.cache_dir

        def cleanup(cachedir):
            chmod(cachedir, 0755)
            rmtree(cachedir)
        self.addCleanup(cleanup, self.cache_dir)

    def test_uses_cache_dir(self):
        # copy normal entry into other entry's place
        makedirs(dirname(join(self.cache_dir, self.other_path)))
        copy(
            join(dirname(__file__), self.path[6:]),
            join(self.cache_dir, self.other_path)
        )
        # ask cache for other entry and assert cached entry equals normal entry
        self.assertEquals(self.entry, get_db_entry(self.other_path))

    def test_raises_entrynotfound_for_no_entry(self):
        with self.assertRaises(EntryNotFound):
            get_db_entry('definitely_a_404')

    def test_can_return_entry_without_saving(self):
        chmod(self.cache_dir, 0)
        self.assertEqual(get_db_entry(self.path), self.entry)
        chmod(self.cache_dir, 0755)
        self.assertFalse(exists(join(self.cache_dir, self.path)))

    def test_retrieves_and_saves_accuraterip_entry(self):
        # for path, entry in zip(self.paths[0], self.entries):
        self.assertFalse(exists(join(self.cache_dir, self.path)))
        self.assertEquals(get_db_entry(self.path), self.entry)
        self.assertTrue(exists(join(self.cache_dir, self.path)))

    def test_AccurateRipResponse_parses_correctly(self):
        responses = get_db_entry(self.path)
        self.assertEquals(len(responses), 2)

        self.assertEquals(responses[0].num_tracks, 2)
        self.assertEquals(responses[0].discId1, '0000f21c')
        self.assertEquals(responses[0].discId2, '00027ef8')
        self.assertEquals(responses[0].cddbDiscId, '05021002')
        self.assertEquals(responses[0].confidences[0], 12)
        self.assertEquals(responses[0].confidences[1], 20)
        self.assertEquals(responses[0].checksums[0], '284fc705')
        self.assertEquals(responses[0].checksums[1], '9cc1f32e')

        self.assertEquals(responses[1].num_tracks, 2)
        self.assertEquals(responses[1].discId1, '0000f21c')
        self.assertEquals(responses[1].discId2, '00027ef8')
        self.assertEquals(responses[1].cddbDiscId, '05021002')
        self.assertEquals(responses[1].confidences[0], 4)
        self.assertEquals(responses[1].confidences[1], 4)
        self.assertEquals(responses[1].checksums[0], 'dc77f9ab')
        self.assertEquals(responses[1].checksums[1], 'dd97d2c3')

# XXX: test arc.py


class TestCalculateChecksums(TestCase):
    def test_returns_none_for_bad_files(self):
        self.assertEquals(
            calculate_checksums(['/does/not/exist']),
            {'v1': [None], 'v2': [None]}
        )

    # TODO: test success when file exists


class TestVerifyResult(TestCase):
    @classmethod
    def setUpClass(cls):
        path = 'c/1/2/dBAR-002-0000f21c-00027ef8-05021002.bin'
        cls.responses = _split_responses(
            open(join(dirname(__file__), path[6:])).read()
        )
        cls.checksums = {
            'v1': ['284fc705', '9cc1f32e'],
            'v2': ['dc77f9ab', 'dd97d2c3'],
        }

    def setUp(self):
        self.result = RipResult()
        for n in range(1, 2 + 1):
            track = TrackResult()
            track.number = n
            self.result.tracks.append(track)

    def test_empty_result_returns_false(self):
        self.assertEquals(
            verify_result(RipResult(), self.responses, self.checksums),
            False
        )

    def test_empty_responses_returns_false(self):
        self.assertEquals(
            verify_result(self.result, [], self.checksums),
            False
        )

    # XXX: would this happen?
    def test_empty_checksums_returns_false(self):
        self.assertEquals(
            verify_result(self.result, self.responses, {}),
            False
        )

    def test_wrong_checksums_returns_false(self):
        self.assertEquals(
            verify_result(self.result, self.responses, {
                'v1': ['deadbeef', '89abcdef'],
                'v2': ['76543210', '01234567']
            }),
            False
        )

    def test_incomplete_checksums(self):
        self.assertEquals(
            verify_result(self.result, self.responses, {
                'v1': ['284fc705', '9cc1f32e'],
                'v2': [None, 'dd97d2c3'],
            }),
            True
        )
        self.assertEquals(
            verify_result(self.result, self.responses, {
                'v1': ['284fc705', None],
                'v2': ['dc77f9ab', 'dd97d2c3'],
            }),
            True
        )
        self.assertEquals(
            verify_result(self.result, self.responses, {
                'v1': ['284fc705', None],
                'v2': [None, 'dd97d2c3'],
            }),
            True
        )

    def test_matches_only_v1_or_v2_responses(self):
        self.assertEquals(
            verify_result(
                self.result, [self.responses[0]], self.checksums
            ),
            True
        )
        self.assertEquals(
            verify_result(
                self.result, [self.responses[1]], self.checksums
            ),
            True
        )

    def test_passes_with_htoa(self):
        htoa = TrackResult()
        htoa.number = 0
        self.result.tracks.append(htoa)
        self.assertEquals(
            verify_result(self.result, self.responses, self.checksums),
            True
        )

    def test_stores_accuraterip_results_on_result(self):
        self.assertEquals(
            verify_result(self.result, self.responses, self.checksums),
            True
        )
        self.assertEquals(self.result.tracks[0].AR, {
            'v1': {
                'CRC': '284fc705',
                'DBCRC': '284fc705',
                'DBConfidence': 12,
            },
            'v2': {
                'CRC': 'dc77f9ab',
                'DBCRC': 'dc77f9ab',
                'DBConfidence': 4,
            },
            'DBMaxConfidence': 12,
            'DBMaxConfidenceCRC': '284fc705',
        })
        self.assertEquals(self.result.tracks[1].AR, {
            'v1': {
                'CRC': '9cc1f32e',
                'DBCRC': '9cc1f32e',
                'DBConfidence': 20,
            },
            'v2': {
                'CRC': 'dd97d2c3',
                'DBCRC': 'dd97d2c3',
                'DBConfidence': 4,
            },
            'DBMaxConfidence': 20,
            'DBMaxConfidenceCRC': '9cc1f32e',
        })


class TestAccurateRipReport(TestCase):
    def setUp(self):
        sys.stdout = StringIO()
        self.result = RipResult()
        track = TrackResult()
        track.number = 1
        track.AR = {
            'v1': {
                'CRC': '284fc705',
                'DBCRC': '284fc705',
                'DBConfidence': 12,
            },
            'v2': {
                'CRC': 'dc77f9ab',
                'DBCRC': 'dc77f9ab',
                'DBConfidence': 4,
            },
            'DBMaxConfidence': 12,
            'DBMaxConfidenceCRC': '284fc705',
        }
        self.result.tracks.append(track)

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_report_no_result(self):
        track = TrackResult()
        track.number = 1
        self.result.tracks[0] = track
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  1: unknown          (error)\n'
        )

    def test_track_not_found(self):
        self.result.tracks[0].AR['DBMaxConfidence'] = None
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  1: rip NOT accurate (not found)            '
            ' v1 [284fc705], v2 [dc77f9ab], DB [notfound]\n'
        )

    def test_htoa_not_tracked(self):
        self.result.tracks[0].number = 0
        self.result.tracks[0].AR['v1']['CRC'] = None
        self.result.tracks[0].AR['v2']['CRC'] = None
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  0: unknown          (not tracked)\n'
        )

    def test_report_v1_only(self):
        self.result.tracks[0].AR['v2']['DBCRC'] = None
        self.result.tracks[0].AR['v2']['DBConfidence'] = None
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  1: rip accurate     (max confidence     12)'
            ' v1 [284fc705], v2 [dc77f9ab], DB [284fc705]\n'
        )

    def test_report_v2_only(self):
        self.result.tracks[0].AR['v1']['DBCRC'] = None
        self.result.tracks[0].AR['v1']['DBConfidence'] = None
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  1: rip accurate     (confidence   4 of  12)'
            ' v1 [284fc705], v2 [dc77f9ab], DB [dc77f9ab]\n'
        )

    def test_report_v1_and_v2_max_confidence(self):
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  1: rip accurate     (max confidence     12)'
            ' v1 [284fc705], v2 [dc77f9ab], DB [284fc705, dc77f9ab]\n'
        )

    def test_report_v1_and_v2(self):
        self.result.tracks[0].AR['DBMaxConfidence'] = 66
        print_report(self.result)
        self.assertEquals(
            sys.stdout.getvalue(),
            'track  1: rip accurate     (confidence  12 of  66)'
            ' v1 [284fc705], v2 [dc77f9ab], DB [284fc705, dc77f9ab]\n'
        )
