# -*- Mode: Python; test-case-name: whipper.test.test_common_mbngs -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2009, 2010, 2011 Thomas Vander Stichele

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

"""
Handles communication with the MusicBrainz server using NGS.
"""
from urllib.error import HTTPError

import whipper
import json
import musicbrainzngs

import logging
logger = logging.getLogger(__name__)
musicbrainzngs.set_useragent("whipper", whipper.__version__,
                             "https://github.com/whipper-team/whipper")


VA_ID = "89ad4ac3-39f7-470e-963a-56509c546377"  # Various Artists


class MusicBrainzException(Exception):

    def __init__(self, exc):
        self.args = (exc, )
        self.exception = exc


class NotFoundException(MusicBrainzException):

    def __str__(self):
        return "Disc not found in MusicBrainz"


class TrackMetadata:
    artist = None
    title = None
    duration = None  # in ms
    mbid = None
    sortName = None
    mbidArtist = None
    mbidRecording = None
    mbidWorks = []


class DiscMetadata:
    """
    :param artist:       artist(s) name
    :param sortName:     release artist sort name
    :param release:      earliest release date, in YYYY-MM-DD
    :type  release:      str
    :param title:        title of the disc (with disambiguation)
    :param releaseTitle: title of the release (without disambiguation)
    :type  tracks:       list of :any:`TrackMetadata`
    """
    artist = None
    sortName = None
    title = None
    various = False
    tracks = None
    release = None

    releaseTitle = None
    releaseType = None

    mbid = None
    mbidReleaseGroup = None
    mbidArtist = None
    url = None

    catalogNumber = None
    barcode = None

    def __init__(self):
        self.tracks = []


def _record(record, which, name, what):
    # optionally record to disc as a JSON serialization
    if record:
        import json
        filename = 'whipper.%s.%s.json' % (which, name)
        handle = open(filename, 'w')
        handle.write(json.dumps(what))
        handle.close()
        logger.info('wrote %s %s to %s', which, name, filename)

# credit is of the form [dict, str, dict, ... ]
# e.g. [
#   {'artist': {
#     'sort-name': 'Sukilove',
#     'id': '5f4af6cf-a1b8-4e51-a811-befed399a1c6',
#     'name': 'Sukilove'
#   }}, ' & ', {
#   'artist': {
#     'sort-name': 'Blackie and the Oohoos',
#     'id': '028a9dc7-f5ef-43c2-866b-08d69ffff363',
#     'name': 'Blackie & the Oohoos'}}]
# or
# [{'artist':
#    {'sort-name': 'Pixies',
#     'id': 'b6b2bb8d-54a9-491f-9607-7b546023b433', 'name': 'Pixies'}}]


class _Credit(list):
    """
    I am a representation of an artist-credit in MusicBrainz for a disc
    or track.
    """

    def joiner(self, attributeGetter, joinString=None):
        res = []

        for item in self:
            if isinstance(item, dict):
                res.append(attributeGetter(item))
            else:
                if not joinString:
                    res.append(item)
                else:
                    res.append(joinString)

        return "".join(res)

    def getSortName(self):
        return self.joiner(lambda i: i.get('artist').get('sort-name', None))

    def getName(self):
        return self.joiner(lambda i: i.get('name',
                                           i.get('artist').get('name', None)))

    def getIds(self):
        # split()'s the joined string so we get a proper list of MBIDs
        return self.joiner(lambda i: i.get('artist').get('id', None),
                           joinString=";").split(';')


def _getWorks(recording):
    """
    Get 'performance of' works out of a recording.

   :param recording: recording entity in MusicBrainz
   :type recording: dict
   :returns: list of works being a performance of a recording
   :rtype: list
    """
    works = []
    valid_type_id = 'a3005666-a872-32c3-ad06-98af558e99b0'  # "Performance"
    if 'work-relation-list' in recording:
        for work in recording['work-relation-list']:
            if work['type-id'] == valid_type_id:
                works.append(work['work'])
    return works


def _getComposers(works):
    """
    Get composer(s) from works' artist-relation-list.

    :param works: list of works being a performance of a recording
    :type works: list
    :returns: sorted list of composers (without duplicates)
    :rtype: list
    """
    composers = set()
    valid_type_id = 'd59d99ea-23d4-4a80-b066-edca32ee158f'  # "Composer"
    for work in works:
        if 'artist-relation-list' in work:
            for artist_relation in work['artist-relation-list']:
                if artist_relation['type-id'] == valid_type_id:
                    composerName = artist_relation['artist']['name']
                    composers.add(composerName)
    return sorted(composers)  # convert to list: mutagen doesn't support set


def _getPerformers(recording):
    """
    Get performer(s) from recordings' artist-relation-list.

    :param recording: recording entity in MusicBrainz
    :type recording: dict
    :returns: sorted list of performers' names (without duplicates)
    :rtype: list
    """
    performers = set()
    valid_type_id = {
        '59054b12-01ac-43ee-a618-285fd397e461',  # "Instruments"
        '0fdbe3c6-7700-4a31-ae54-b53f06ae1cfa',  # "Vocals"
        '628a9658-f54c-4142-b0c0-95f031b544da'   # "Performers"
    }
    if 'artist-relation-list' in recording:
        for artist_relation in recording['artist-relation-list']:
            if artist_relation['type-id'] in valid_type_id:
                performers.add(artist_relation['artist']['name'])
    return sorted(performers)  # convert to list: mutagen doesn't support set


def _getMetadata(release, discid=None, country=None):
    """
    :type  release: dict
    :param release: a release dict as returned in the value for key release
                    from get_release_by_id

    :rtype: DiscMetadata or None
    """
    logger.debug('getMetadata for release id %r', release['id'])
    if not release['id']:
        logger.warning('no id for release %r', release)
        return None

    assert release['id'], 'Release does not have an id'

    if 'country' in release and country and release['country'] != country:
        logger.warning('%r was not released in %r', release, country)
        return None

    discMD = DiscMetadata()

    if 'type' in release['release-group']:
        discMD.releaseType = release['release-group']['type']
    discCredit = _Credit(release['artist-credit'])

    # FIXME: is there a better way to check for VA ?
    discMD.various = False
    if discCredit[0]['artist']['id'] == VA_ID:
        discMD.various = True

    if len(discCredit) > 1:
        logger.debug('artist-credit more than 1: %r', discCredit)

    releaseArtistName = discCredit.getName()

    # getUniqueName gets disambiguating names like Muse (UK rock band)
    discMD.artist = releaseArtistName
    discMD.sortName = discCredit.getSortName()
    if 'date' not in release:
        logger.warning("release with ID '%s' (%s - %s) does not have a date",
                       release['id'], discMD.artist, release['title'])
    else:
        discMD.release = release['date']

    discMD.mbid = release['id']
    discMD.mbidReleaseGroup = release['release-group']['id']
    discMD.mbidArtist = discCredit.getIds()
    discMD.url = 'https://musicbrainz.org/release/' + release['id']

    discMD.barcode = release.get('barcode', None)
    lil = release.get('label-info-list', [{}])
    if lil:
        discMD.catalogNumber = lil[0].get('catalog-number')
    tainted = False
    duration = 0

    # only show discs from medium-list->disc-list with matching discid
    for medium in release['medium-list']:
        for disc in medium['disc-list']:
            if discid is None or disc['id'] == discid:
                title = release['title']
                discMD.releaseTitle = title
                if 'disambiguation' in release:
                    title += " (%s)" % release['disambiguation']
                count = len(release['medium-list'])
                if count > 1:
                    title += ' (Disc %d of %d)' % (
                        int(medium['position']), count)
                if 'title' in medium:
                    title += ": %s" % medium['title']
                discMD.title = title
                for t in medium['track-list']:
                    track = TrackMetadata()
                    trackCredit = _Credit(
                        t.get('artist-credit', t['recording']['artist-credit']
                              ))
                    recordingCredit = _Credit(t['recording']['artist-credit'])
                    works = _getWorks(t['recording'])
                    if len(trackCredit) > 1:
                        logger.debug('artist-credit more than 1: %r',
                                     trackCredit)

                    # FIXME: leftover comment, need an example
                    # various artists discs can have tracks with no artist
                    track.artist = trackCredit.getName()
                    track.sortName = trackCredit.getSortName()
                    track.mbidArtist = trackCredit.getIds()
                    track.recordingArtist = recordingCredit.getName()

                    track.title = t.get('title', t['recording']['title'])
                    track.mbid = t['id']
                    track.mbidRecording = t['recording']['id']
                    track.mbidWorks = sorted({work['id'] for work in works})
                    track.composers = _getComposers(works)
                    track.performers = _getPerformers(t['recording'])

                    # FIXME: unit of duration ?
                    track.duration = int(t['recording'].get('length', 0))
                    if not track.duration:
                        logger.warning('track %r (%r) does not have duration',
                                       track.title, track.mbid)
                        tainted = True
                    else:
                        duration += track.duration

                    discMD.tracks.append(track)

                if not tainted:
                    discMD.duration = duration
                else:
                    discMD.duration = 0

    return discMD


def getReleaseMetadata(release_id, discid=None, country=None, record=False):
    """
    Return a DiscMetadata object based on MusicBrainz Release ID and Disc ID.

    If the disc id is not specified, it will match with any disc that is on
    the release disc-list. Otherwise only returns metadata of one disc in
    release disc-list.

    :param release_id: MusicBrainz Release ID
    :type release_id: str
    :param discid: MusicBrainz Disc ID
    :type discid: str or None
    :param country: the country the release was issued in
    :type country: str or None
    :param record: whether to record to disc as a JSON serialization
    :type record: bool
    :returns: a DiscMetadata object based on MusicBrainz Release ID & Disc ID
    :rtype: `DiscMetadata`
    """
    # to get titles of recordings, we need to query the release with
    # artist-credits

    res = musicbrainzngs.get_release_by_id(
            release_id, includes=["artists", "artist-credits",
                                  "recordings", "discids",
                                  "labels", "recording-level-rels",
                                  "work-rels", "release-groups",
                                  "work-level-rels", "artist-rels"])
    _record(record, 'release', release_id, res)
    releaseDetail = res['release']
    formatted = json.dumps(releaseDetail, sort_keys=False, indent=4)
    logger.debug('release %s', formatted)
    return _getMetadata(releaseDetail, discid, country)


# see http://bugs.musicbrainz.org/browser/python-musicbrainz2/trunk/examples/
#     ripper.py


def musicbrainz(discid, country=None, record=False):
    """
    Based on a MusicBrainz disc id, get a list of DiscMetadata objects
    for the given disc id.

    Example disc id: Mj48G109whzEmAbPBoGvd4KyCS4-

    :type  discid: str

    :rtype: list of :any:`DiscMetadata`
    """
    logger.debug('looking up results for discid %r', discid)

    logging.getLogger("musicbrainzngs").setLevel(logging.WARNING)
    ret = []

    try:
        result = musicbrainzngs.get_releases_by_discid(
            discid, includes=["artists", "recordings", "release-groups"])
    except musicbrainzngs.ResponseError as e:
        if isinstance(e.cause, HTTPError):
            if e.cause.code == 404:
                raise NotFoundException(e)
            else:
                logger.debug('received bad response from the server')

        raise MusicBrainzException(e)

    # The result can either be a "disc" or a "cdstub"
    if result.get('disc'):
        logger.debug('found %d releases for discid %r',
                     len(result['disc']['release-list']), discid)
        _record(record, 'releases', discid, result)

        # Display the returned results to the user.

        for release in result['disc']['release-list']:
            formatted = json.dumps(release, sort_keys=False, indent=4)
            logger.debug('result %s: artist %r, title %r', formatted,
                         release['artist-credit-phrase'], release['title'])

            md = getReleaseMetadata(release['id'], discid, country, record)
            if md:
                logger.debug('duration %r', md.duration)
                ret.append(md)

        return ret
    elif result.get('cdstub'):
        logger.debug('query returned cdstub: ignored')
    return None
