# -*- Mode: Python; test-case-name: morituri.test.test_common_musicbrainz -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009, 2010, 2011 Thomas Vander Stichele

# This file is part of morituri.
#
# morituri is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# morituri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with morituri.  If not, see <http://www.gnu.org/licenses/>.

"""
Handles communication with the musicbrainz server.
"""

import urlparse

from morituri.common import log


class MusicBrainzException(Exception):

    def __init__(self, exc):
        self.args = (exc, )
        self.exception = exc


class TrackMetadata(object):

    artist = None
    title = None
    duration = None # in ms
    mbid = None
    sortName = None
    mbidArtist = None


class DiscMetadata(object):
    """
    @param release: earliest release date, in YYYY-MM-DD
    @type  release: unicode
    """
    artist = None
    sortName = None
    title = None
    various = False
    tracks = None
    release = None

    mbid = None
    mbidArtist = None

    def __init__(self):
        self.tracks = []


def _getMetadata(release):
    """
    @type  release: L{musicbrainz2.model.Release}

    @rtype: L{DiscMetadata} or None
    """
    log.debug('program', 'getMetadata for release id %r',
        release.getId())
    if not release.getId():
        log.warning('program', 'No id for release %r', release)
        return None

    assert release.id, 'Release does not have an id'

    metadata = DiscMetadata()

    isSingleArtist = release.isSingleArtistRelease()
    metadata.various = not isSingleArtist
    metadata.title = release.title
    # getUniqueName gets disambiguating names like Muse (UK rock band)
    metadata.artist = release.artist.name
    metadata.sortName = release.artist.sortName
    metadata.release = release.getEarliestReleaseDate()

    metadata.mbid = urlparse.urlparse(release.id)[2].split("/")[-1]
    metadata.mbidArtist = urlparse.urlparse(release.artist.id)[2].split("/")[-1]
    metadata.url = release.getId()

    tainted = False
    duration = 0

    for t in release.tracks:
        track = TrackMetadata()

        if isSingleArtist or t.artist == None:
            track.artist = metadata.artist
            track.sortName = metadata.sortName
            track.mbidArtist = metadata.mbidArtist
        else:
            # various artists discs can have tracks with no artist
            track.artist = t.artist and t.artist.name or release.artist.name
            track.sortName = t.artist.sortName
            track.mbidArtist = urlparse.urlparse(t.artist.id)[2].split("/")[-1]

        track.title = t.title
        track.mbid = urlparse.urlparse(t.id)[2].split("/")[-1]

        track.duration = t.duration
        if not track.duration:
            log.warning('getMetadata',
                'track %r (%r) does not have duration' % (
                    track.title, track.mbid))
            tainted = True
        else:
            duration += t.duration

        metadata.tracks.append(track)

    if not tainted:
        metadata.duration = duration
    else:
        metadata.duration = 0

    return metadata


# see http://bugs.musicbrainz.org/browser/python-musicbrainz2/trunk/examples/ripper.py


def musicbrainz(discid):
    """
    Based on a MusicBrainz disc id, get a list of DiscMetadata objects
    for the given disc id.

    Example disc id: Mj48G109whzEmAbPBoGvd4KyCS4-

    @type  discid: str

    @rtype: list of L{DiscMetadata}
    """
    log.debug('musicbrainz', 'looking up results for discid %r', discid)
    #import musicbrainz2.disc as mbdisc
    import musicbrainz2.webservice as mbws

    results = []

    # Setup a Query object.
    service = mbws.WebService()
    query = mbws.Query(service)


    # Query for all discs matching the given DiscID.
    # FIXME: let mbws.WebServiceError go through for now
    try:
        rfilter = mbws.ReleaseFilter(discId=discid)
        results = query.getReleases(rfilter)
    except mbws.WebServiceError, e:
        raise MusicBrainzException(e)

    # No disc matching this DiscID has been found.
    if len(results) == 0:
        return None

    log.debug('musicbrainz', 'found %d results for discid %r', len(results),
        discid)

    # Display the returned results to the user.
    ret = []

    for result in results:
        release = result.release
        log.debug('program', 'result %r: artist %r, title %r' % (
            release, release.artist.getName(), release.title))
        # The returned release object only contains title and artist, but no
        # tracks.  Query the web service once again to get all data we need.
        try:
            inc = mbws.ReleaseIncludes(artist=True, tracks=True,
                releaseEvents=True, discs=True)
            # Arid - Under the Cold Street Lights has getId() None
            if release.getId():
                release = query.getReleaseById(release.getId(), inc)
        except mbws.WebServiceError, e:
            raise MusicBrainzException(e)

        md = _getMetadata(release)
        if md:
            log.debug('program', 'duration %r', md.duration)
            ret.append(md)


    return ret
