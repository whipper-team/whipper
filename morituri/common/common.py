# -*- Mode: Python; test-case-name: morituri.test.test_common_common -*-
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

def msfToFrames(msf):
    """
    Converts a string value in MM:SS:FF to frames

    @param msf:
    @type  msf: str

    @rtype int
    @returns number of frames
    """
    if not ':' in msf:
        return int(msf)

    m, s, f = msf.split(':')

    return 60 * 75 * int(m) + 75 * int(s) + int(f)

def framesToMSF(frames):
    f = frames % 75
    frames -= f
    s = (frames / 75) % 60
    frames -= s * 60
    m = frames / 75 / 60

    return "%02d:%02d:%02d" % (m, s, f)

def framesToHMSF(frames):
    # cdparanoia style
    f = frames % 75
    frames -= f
    s = (frames / 75) % 60
    frames -= s * 75
    m = (frames / 75 / 60) % 60
    frames -= m * 75 * 60
    h = frames / 75 / 60 / 60

    return "%02d:%02d:%02d.%02d" % (h, m, s, f)
