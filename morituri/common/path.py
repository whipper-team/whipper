# -*- Mode: Python; test-case-name: morituri.test.test_common_path -*-
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


class PathFilter(object):
    """
    I filter path components for safe storage on file systems.
    """

    def __init__(self, slashes=True, quotes=True, fat=True, special=False):
        """
        @param slashes: whether to convert slashes to dashes
        @param quotes:  whether to normalize quotes
        @param fat:     whether to strip characters illegal on FAT filesystems
        @param special: whether to strip special characters
        """
        self._slashes = slashes
        self._quotes = quotes
        self._fat = fat
        self._special = special

    def filter(self, path):
        if self._slashes:
            path = re.sub(r'[/\\]', '-', path, re.UNICODE)

        if self._quotes:
            path = re.sub(ur'[\u2019]', "'", path, re.UNICODE)

        if self._special:
            # replace separators with a hyphen
            path = re.sub(r'[:\|]', '-', path, re.UNICODE)
            path = re.sub(r'[\*\?&!\'\"\$\(\)`{}\[\]<>]', '_', path, re.UNICODE)

        if self._fat:
            path = re.sub(r'[:\*\?"<>|"]', '_', path, re.UNICODE)

        return path
