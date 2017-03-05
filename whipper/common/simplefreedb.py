# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2017 Clément Bœsch <u@pkh.me>

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

import re
import socket
import getpass
import urllib
import whipper


class SimpleFreeDB:

    URL = 'http://freedb.freedb.org/~cddb/cddb.cgi'
    PROTO = 6

    def __init__(self):
        user = getpass.getuser()
        host = socket.gethostname()
        client = 'whipper'
        hello = '%s %s %s %s' % (user, host, client, whipper.__version__)
        self._hello = urllib.quote_plus(hello)
        self._slash_split_regex = re.compile(r'(?<!\\)/')

    def _cddb_cmd(self, cmd):
        cmd_arg = urllib.quote_plus('cddb ' + cmd)
        data_url = (self.URL, cmd_arg, self._hello, self.PROTO)
        url = '%s?cmd=%s&hello=%s&proto=%d' % data_url
        req = urllib.urlopen(url)
        return req.read().decode('utf-8')

    @staticmethod
    def _get_code(line):
        return int(line.split(None, 1)[0])

    def _split_dtitle(self, dtitle):
        # Note: we can not use a simple dtitle.split('/') here because the
        # slash could be escaped.
        artist, title = re.split(self._slash_split_regex, dtitle, maxsplit=1)
        return artist.rstrip(), title.lstrip()

    def _craft_match(self, category, discid_str, dtitle):
        artist, title = self._split_dtitle(dtitle)
        return {'category': category,
                'discid': int(discid_str, 16),
                'artist_title': dtitle,
                'artist': artist,
                'title': title}

    def query(self, discid, ntrks, offsets, nsecs):
        data_q = (discid, ntrks, ' '.join(str(x) for x in offsets), nsecs)
        cmd = 'query %08x %d %s %d' % data_q
        data = self._cddb_cmd(cmd)
        lines = data.splitlines()
        code = self._get_code(lines[0])
        matches = []
        if code == 200:
            line = lines[0]
            matches.append(self._craft_match(*line.split(None, 3)[1:]))
        elif code in (210, 211):
            for line in lines[1:]:
                if line == '.':
                    break
                matches.append(self._craft_match(*line.split(None, 2)))
        return matches

    def read(self, category, discid):
        cmd = 'read %s %08x' % (category, discid)
        data = self._cddb_cmd(cmd)
        lines = data.splitlines()
        code = self._get_code(lines[0])
        if code != 210:
            return None

        data = {}
        dtitle = ''
        tracks = {}

        for line in lines[1:]:
            if line == '.':
                break
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            if not value:
                continue
            if key == 'DTITLE':
                dtitle += value
            elif key == 'DYEAR':
                data['year'] = int(value)
            elif key == 'DGENRE':
                data['genre'] = value
            elif key.startswith('TTITLE'):
                n = int(key[6:])
                tracks[n] = tracks.get(n, '') + value

        try:
            artist, title = self._split_dtitle(dtitle)
        except:
            raise Exception('Unable to parse DTITLE "%s"' % dtitle)
        data['artist_title'] = dtitle
        data['artist'] = artist
        data['title'] = title

        data['tracks'] = [v for k, v in sorted(tracks.items())]

        return data


def main():
    test_queries = (
        # 200, 1 match
        (0xfd0ce112, 18, (150, 16732, 27750, 43075, 58800, 71690, 86442,
                          101030, 111812, 128367, 136967, 152115, 164812,
                          180337, 194072, 201690, 211652, 230517), 3299),
        # 211, inexact but 1 match
        (0xb70e170e, 14, (150, 20828, 36008, 53518, 71937, 90777, 109374,
                          128353, 150255, 172861, 192062, 216672, 235357,
                          253890), 3609),
    )
    import pprint
    fdb = SimpleFreeDB()
    dtitle_split_data = 'foo \\/ bar / bla / baz'
    dtitle_split_ref = ('foo \\/ bar', 'bla / baz')
    assert fdb._split_dtitle(dtitle_split_data) == dtitle_split_ref
    for i, query in enumerate(test_queries):
        for match in fdb.query(*query):
            pprint.pprint(fdb.read(match['category'], match['discid']))


if __name__ == '__main__':
    main()
