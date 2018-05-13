# Audio Tools, a module and set of tools for manipulating audio data
# Copyright (C) 2007-2016  Brian Langenberger

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA


import sys


def digit_sum(i):
    """returns the sum of all digits for the given integer"""

    return sum(map(int, str(i)))


class DiscID(object):
    def __init__(self, offsets, total_length, track_count, playable_length):
        """offsets is a list of track offsets, in CD frames
        total_length is the total length of the disc, in seconds
        track_count is the total number of tracks on the disc
        playable_length is the playable length of the disc, in seconds

        the first three items are for generating the hex disc ID itself
        while the last is for performing queries"""

        assert(len(offsets) == track_count)
        for o in offsets:
            assert(o >= 0)

        self.offsets = offsets
        self.total_length = total_length
        self.track_count = track_count
        self.playable_length = playable_length

    @classmethod
    def from_cddareader(cls, cddareader):
        """given a CDDAReader object, returns a DiscID for that object"""

        def offset(sector):
            # the HOWTO implies sectors should be lopped off, like:
            # t = ((cdtoc[tot_trks].min * 60) + cdtoc[tot_trks].sec) -
            #     ((cdtoc[0].min * 60) + cdtoc[0].sec);
            minutes = sector // 75 // 60
            seconds = sector // 75 % 60
            return minutes * 60 + seconds

        offsets = cddareader.track_offsets

        return cls(offsets=[(offsets[k] // 588) + 150 for k in
                            sorted(offsets.keys())],
                   total_length=(offset(cddareader.last_sector + 150 + 1) -
                                 offset(cddareader.first_sector + 150)),
                   track_count=len(offsets),
                   playable_length=(cddareader.last_sector + 150 + 1) // 75)

    @classmethod
    def from_tracks(cls, tracks):
        """given a sorted list of tracks,
        returns DiscID for those tracks as if they were a CD"""

        from audiotools import has_pre_gap_track

        if not has_pre_gap_track(tracks):
            offsets = [150]
            for track in tracks[0:-1]:
                offsets.append(offsets[-1] + track.cd_frames())

            #track_lengths = sum(t.cd_frames() for t in tracks) // 75
            total_length = sum(t.seconds_length() for t in tracks)

            return cls(offsets=offsets,
                       total_length=int(total_length),
                       track_count=len(tracks),
                       playable_length=int(total_length + 2))
        else:
            offsets = [150 + tracks[0].cd_frames()]
            for track in tracks[1:-1]:
                offsets.append(offsets[-1] + track.cd_frames())

            total_length = sum(t.seconds_length() for t in tracks[1:])

            return cls(
                offsets=offsets,
                total_length=int(total_length),
                track_count=len(tracks) - 1,
                playable_length=int(total_length + 2))

    @classmethod
    def from_sheet(cls, sheet, total_pcm_frames, sample_rate):
        """given a Sheet object
        length of the album in PCM frames
        and sample rate of the disc,
        returns a DiscID for that CD"""

        return cls(offsets=[int(t.index(1).offset() * 75 + 150)
                            for t in sheet],
                   total_length=((total_pcm_frames // sample_rate) -
                                 int(sheet.track(1).index(1).offset())),
                   track_count=len(sheet),
                   playable_length=((total_pcm_frames + (sample_rate * 2)) //
                                    sample_rate))

    def __repr__(self):
        return "DiscID({})".format(
            ", ".join(["{}={}".format(attr, getattr(self, attr))
                       for attr in ["offsets",
                                    "total_length",
                                    "track_count",
                                    "playable_length"]]))

    if sys.version_info[0] >= 3:
        def __str__(self):
            return self.__unicode__()
    else:
        def __str__(self):
            return self.__unicode__().encode('ascii')

    def __unicode__(self):
        return u"{:08X}".format(int(self))

    def __int__(self):
        digit_sum_ = sum([digit_sum(o // 75) for o in self.offsets])
        return (((digit_sum_ % 255) << 24) |
                ((self.total_length & 0xFFFF) << 8) |
                (self.track_count & 0xFF))


def perform_lookup(disc_id, freedb_server, freedb_port):
    """performs a web-based lookup using a DiscID
    on the given freedb_server string and freedb_int port

    iterates over a list of MetaData objects per successful match, like:
    [track1, track2, ...], [track1, track2, ...], ...

    may raise HTTPError if an error occurs querying the server
    or ValueError if the server returns invalid data
    """

    import re
    from time import sleep

    RESPONSE = re.compile(r'(\d{3}) (.+?)[\r\n]+')
    QUERY_RESULT = re.compile(r'(\S+) ([0-9a-fA-F]{8}) (.+)')
    FREEDB_LINE = re.compile(r'(\S+?)=(.+?)[\r\n]+')

    query = freedb_command(freedb_server,
                           freedb_port,
                           u"query",
                           *([disc_id.__unicode__(),
                              u"{:d}".format(disc_id.track_count)] +
                             [u"{:d}".format(o) for o in disc_id.offsets] +
                             [u"{:d}".format(disc_id.playable_length)]))

    line = next(query)
    response = RESPONSE.match(line)
    if response is None:
        raise ValueError("invalid response from server")
    else:
        # a list of (category, disc id, disc title) tuples
        matches = []
        code = int(response.group(1))
        if code == 200:
            # single exact match
            match = QUERY_RESULT.match(response.group(2))
            if match is not None:
                matches.append((match.group(1),
                                match.group(2),
                                match.group(3)))
            else:
                raise ValueError("invalid query result")
        elif (code == 211) or (code == 210):
            # multiple exact or inexact matches
            line = next(query)
            while not line.startswith(u"."):
                match = QUERY_RESULT.match(line)
                if match is not None:
                    matches.append((match.group(1),
                                    match.group(2),
                                    match.group(3)))
                else:
                    raise ValueError("invalid query result")
                line = next(query)
        elif code == 202:
            # no match found
            pass
        else:
            # some error has occurred
            raise ValueError(response.group(2))

    if len(matches) > 0:
        # for each result, query FreeDB for XMCD file data
        for (category, disc_id, title) in matches:
            sleep(1)  # add a slight delay to keep the server happy

            query = freedb_command(freedb_server,
                                   freedb_port,
                                   u"read",
                                   category,
                                   disc_id)

            response = RESPONSE.match(next(query))
            if response is not None:
                # FIXME - check response code here
                freedb = {}
                line = next(query)
                while not line.startswith(u"."):
                    if not line.startswith(u"#"):
                        entry = FREEDB_LINE.match(line)
                        if entry is not None:
                            if entry.group(1) in freedb:
                                freedb[entry.group(1)] += entry.group(2)
                            else:
                                freedb[entry.group(1)] = entry.group(2)
                    line = next(query)
                yield list(xmcd_metadata(freedb))
            else:
                raise ValueError("invalid response from server")


def freedb_command(freedb_server, freedb_port, cmd, *args):
    """given a freedb_server string, freedb_port int,
    command unicode string and argument unicode strings,
    yields a list of Unicode strings"""

    try:
        from urllib.request import urlopen
    except ImportError:
        from urllib2 import urlopen
    try:
        from urllib.parse import urlencode
    except ImportError:
        from urllib import urlencode
    from socket import getfqdn
    from audiotools import VERSION
    from sys import version_info

    PY3 = version_info[0] >= 3

    # some debug type checking
    assert(isinstance(cmd, str if PY3 else unicode))
    for arg in args:
        assert(isinstance(arg, str if PY3 else unicode))

    POST = []

    # generate query to post with arguments in specific order
    if len(args) > 0:
        POST.append((u"cmd", u"cddb {} {}".format(cmd, " ".join(args))))
    else:
        POST.append((u"cmd", u"cddb {}".format(cmd)))

    POST.append(
        (u"hello",
         u"user {} {} {}".format(
             getfqdn() if PY3 else getfqdn().decode("UTF-8", "replace"),
             u"audiotools",
             VERSION if PY3 else VERSION.decode("ascii"))))

    POST.append((u"proto", u"6"))

    # get Request object from post
    request = urlopen(
        "http://{}:{:d}/~cddb/cddb.cgi".format(freedb_server, freedb_port),
        urlencode(POST).encode("UTF-8") if (version_info[0] >= 3) else
        urlencode(POST))
    try:
        # yield lines of output
        line = request.readline()
        while len(line) > 0:
            yield line.decode("UTF-8", "replace")
            line = request.readline()
    finally:
        request.close()


def xmcd_metadata(freedb_file):
    """given a dict of KEY->value unicode strings,
    yields a MetaData object per track"""

    import re

    TTITLE = re.compile(r'TTITLE(\d+)')

    dtitle = freedb_file.get(u"DTITLE", u"")
    if u" / " in dtitle:
        (album_artist, album_name) = dtitle.split(u" / ", 1)
    else:
        album_artist = None
        album_name = dtitle

    year = freedb_file.get(u"DYEAR", None)

    ttitles = [(int(m.group(1)), value) for (m, value) in
               [(TTITLE.match(key), value) for (key, value) in
                freedb_file.items()] if m is not None]

    if len(ttitles) > 0:
        track_total = max([tracknum for (tracknum, ttitle) in ttitles]) + 1
    else:
        track_total = 0

    for (tracknum, ttitle) in sorted(ttitles, key=lambda t: t[0]):
        if u" / " in ttitle:
            (track_artist,
             track_name) = ttitle.split(u" / ", 1)
        else:
            track_artist = album_artist
            track_name = ttitle

        from audiotools import MetaData

        yield MetaData(
            track_name=track_name,
            track_number=tracknum + 1,
            track_total=track_total,
            album_name=album_name,
            artist_name=(track_artist if track_artist is not None else None),
            year=(year if year is not None else None))
