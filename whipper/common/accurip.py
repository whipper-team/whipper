# -*- Mode: Python; test-case-name: whipper.test.test_common_accurip -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2017 Samantha Baldwin
# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of whipper.
#
# whipper is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# whipper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with whipper.  If not, see <http://www.gnu.org/licenses/>.

import requests
import struct
from errno import EEXIST
from os import makedirs
from os.path import dirname, exists, join

from whipper.common import directory
from whipper.program.arc import accuraterip_checksum

import logging
logger = logging.getLogger(__name__)


ACCURATERIP_URL = "http://www.accuraterip.com/accuraterip/"
_CACHE_DIR = join(directory.cache_path(), 'accurip')


class EntryNotFound(Exception):
    pass


class _AccurateRipResponse(object):
    """I represent an AccurateRip response with its metadata.

    An AccurateRip response contains a collection of metadata identifying a
    particular digital audio compact disc.

    For disc level metadata it contains the track count, two internal disc
    IDs, and the CDDB disc ID.

    A checksum and a confidence score is stored sequentially for each track in
    the disc index, which excludes any audio hidden in track pre-gaps (such as
    HTOA).

    The checksums and confidences arrays are indexed by relative track
    position, so track 1 will have array index 0, track 2 will have array
    index 1, and so forth. HTOA and other hidden tracks are not included.

    The response is stored as a packed binary structure.
    """

    def __init__(self, data):
        self.num_tracks = struct.unpack("B", data[0])[0]
        self.discId1 = "%08x" % struct.unpack("<L", data[1:5])[0]
        self.discId2 = "%08x" % struct.unpack("<L", data[5:9])[0]
        self.cddbDiscId = "%08x" % struct.unpack("<L", data[9:13])[0]

        self.confidences = []
        self.checksums = []
        pos = 13
        for _ in range(self.num_tracks):
            confidence = struct.unpack("B", data[pos])[0]
            checksum = "%08x" % struct.unpack("<L", data[pos + 1:pos + 5])[0]
            self.confidences.append(confidence)
            self.checksums.append(checksum)
            pos += 9

    def __eq__(self, other):
        return [
            self.num_tracks, self.discId1, self.discId2, self.cddbDiscId,
            self.confidences, self.checksums
        ] == [
            other.num_tracks, other.discId1, other.discId2, other.cddbDiscId,
            other.confidences, other.checksums
        ]


def _split_responses(raw_entry):
    responses = []
    while raw_entry:
        track_count = struct.unpack("B", raw_entry[0])[0]
        nbytes = 1 + 12 + track_count * (1 + 8)
        responses.append(_AccurateRipResponse(raw_entry[:nbytes]))
        raw_entry = raw_entry[nbytes:]
    return responses


def calculate_checksums(track_paths):
    """Calculate ARv1 and ARv2 checksums of the given tracks.

    Return ARv1 and ARv2 checksums as two arrays of character strings in a
    dictionary: {'v1': ['deadbeef', ...], 'v2': [...]}

    Return None instead of checksum string for unchecksummable tracks.

    HTOA checksums are not included in the database and are not calculated.

    :param track_paths:
    :type track_paths:
    """
    track_count = len(track_paths)
    v1_checksums = []
    v2_checksums = []
    logger.debug('checksumming %d tracks' % track_count)
    # This is done sequentially because it is very fast.
    for i, path in enumerate(track_paths):
        v1_sum = accuraterip_checksum(
            path, i + 1, track_count, wave=True, v2=False
        )
        if not v1_sum:
            logger.error(
                'could not calculate AccurateRip v1 checksum for track %d %r' %
                (i + 1, path)
            )
            v1_checksums.append(None)
        else:
            v1_checksums.append("%08x" % v1_sum)
        v2_sum = accuraterip_checksum(
            path, i + 1, track_count, wave=True, v2=True
        )
        if not v2_sum:
            logger.error(
                'could not calculate AccurateRip v2 checksum for track %d %r' %
                (i + 1, path)
            )
            v2_checksums.append(None)
        else:
            v2_checksums.append("%08x" % v2_sum)
    return {'v1': v1_checksums, 'v2': v2_checksums}


def _download_entry(path):
    url = ACCURATERIP_URL + path
    logger.debug('downloading AccurateRip entry from %s', url)
    try:
        resp = requests.get(url)
    except requests.exceptions.ConnectionError as e:
        logger.error('error retrieving AccurateRip entry: %r' % e)
        return None
    if not resp.ok:
        logger.error('error retrieving AccurateRip entry: %s %s %r' % (
            resp.status_code, resp.reason, resp
        ))
        return None
    return resp.content


def _save_entry(raw_entry, path):
    logger.debug('saving AccurateRip entry to %s', path)
    # XXX: os.makedirs(exist_ok=True) in py3
    try:
        makedirs(dirname(path))
    except OSError as e:
        if e.errno != EEXIST:
            logger.error('could not save entry to %s: %r' % (path, str(e)))
            return
    open(path, 'wb').write(raw_entry)


def get_db_entry(path):
    """Retrieve cached AccurateRip disc entry.

    (As array of _AccurateRipResponses).

    Downloads entry from accuraterip.com on cache fault.

    ``path`` is in the format of the output of table.accuraterip_path().

    :param path:
    :type path:
    """
    cached_path = join(_CACHE_DIR, path)
    if exists(cached_path):
        logger.debug('found accuraterip entry at %s', cached_path)
        raw_entry = open(cached_path, 'rb').read()
    else:
        raw_entry = _download_entry(path)
        if raw_entry:
            _save_entry(raw_entry, cached_path)
    if not raw_entry:
        logger.warning('entry not found in AccurateRip database')
        raise EntryNotFound
    return _split_responses(raw_entry)


def _assign_checksums_and_confidences(tracks, checksums, responses):
    for i, track in enumerate(tracks):
        for v in ('v1', 'v2'):
            track.AR[v]['CRC'] = checksums[v][i]
        track.AR['DBMaxConfidence'], track.AR['DBMaxConfidenceCRC'] = max(
            [(r.confidences[i], r.checksums[i]) for r in responses],
            key=lambda t: t[0]
        )


def _match_responses(tracks, responses):
    """Match and save track AccurateRip response checksums.

    The checksum are matched against all non-hidden tracks.

    Returns True if every track has a match for every entry for either
    AccurateRip version.

    :param tracks:
    :type tracks:
    :param responses:
    :type responses:
    """
    for r in responses:
        for i, track in enumerate(tracks):
            for v in ('v1', 'v2'):
                if track.AR[v]['CRC'] == r.checksums[i]:
                    if r.confidences[i] > track.AR[v]['DBConfidence']:
                        track.AR[v]['DBCRC'] = r.checksums[i]
                        track.AR[v]['DBConfidence'] = r.confidences[i]
                        logger.debug(
                            'track %d matched response %s in AccurateRip'
                            ' database: %s crc %s confidence %s' %
                            (i, r.cddbDiscId, v, track.AR[v]['DBCRC'],
                             track.AR[v]['DBConfidence'])
                        )
    return any((
        all([t.AR['v1']['DBCRC'] for t in tracks]),
        all([t.AR['v2']['DBCRC'] for t in tracks])
    ))


def verify_result(result, responses, checksums):
    """Verify track AccurateRip checksums against database responses.

    Stores track checksums and database values on result.

    :param result:
    :type result:
    :param responses:
    :type responses:
    :param checksums:
    :type checksums:
    """
    if not (result and responses and checksums):
        return False
    # exclude HTOA from AccurateRip verification
    # NOTE: if pre-gap hidden audio support is expanded to include
    # tracks other than HTOA, this is invalid.
    tracks = filter(lambda t: t.number != 0, result.tracks)
    if not tracks:
        return False
    _assign_checksums_and_confidences(tracks, checksums, responses)
    return _match_responses(tracks, responses)


def print_report(result):
    """Print AccurateRip verification results to stdout.

    :param result:
    :type result:
    """
    for i, track in enumerate(result.tracks):
        status = 'rip NOT accurate'
        conf = '(not found)'
        db = 'notfound'
        if track.AR['DBMaxConfidence'] is not None:
            db = track.AR['DBMaxConfidenceCRC']
            conf = '(max confidence    %3d)' % track.AR['DBMaxConfidence']
            if track.AR['v1']['DBCRC'] or track.AR['v2']['DBCRC']:
                status = 'rip accurate'
                db = ', '.join(filter(None, (
                    track.AR['v1']['DBCRC'],
                    track.AR['v2']['DBCRC']
                )))
            max_conf = max(
                [track.AR[v]['DBConfidence'] for v in ('v1', 'v2')]
            )
            if max_conf:
                if max_conf < track.AR['DBMaxConfidence']:
                    conf = '(confidence %3d of %3d)' % (
                        max_conf, track.AR['DBMaxConfidence']
                    )
        # htoa tracks (i == 0) do not have an ARCRC
        if track.number == 0:
            print('track  0: unknown          (not tracked)')
            continue
        if not (track.AR['v1']['CRC'] or track.AR['v2']['CRC']):
            logger.error(
                'no track AR CRC on non-HTOA track %d' % track.number
            )
            print('track %2d: unknown          (error)' % track.number)
        else:
            print('track %2d: %-16s %-23s v1 [%s], v2 [%s], DB [%s]' % (
                track.number, status, conf,
                track.AR['v1']['CRC'], track.AR['v2']['CRC'], db
            ))
