# -*- Mode: Python; test-case-name: morituri.test.test_program_cdparanoia -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009 Thomas Vander Stichele

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

import re

_PROGRESS_RE = re.compile(r"""
    ^\#\#: (?P<code>.+)\s      # function code
    \[(?P<function>.*)\]\s@\s     # function name
    (?P<offset>\d+)        # offset
""", re.VERBOSE)

# from reading cdparanoia source code, it looks like offset is reported in
# number of single-channel samples, ie. 2 bytes per unit
class ProgressParser(object):
    read = 0

    def parse(self, line):
        """
        Parse a line.
        """
        m = _PROGRESS_RE.search(line)
        if m:
            code = int(m.group('code'))
            function = m.group('function')
            offset = int(m.group('offset'))
            if function == 'read':
                if offset % 1176 != 0:
                    print 'THOMAS: not a multiple of 2532', offset
                    print line
                else:
                    self.read = offset / 1176
