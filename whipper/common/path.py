# -*- Mode: Python; test-case-name: whipper.test.test_common_path -*-
# vi:si:et:sw=4:sts=4:ts=4

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

import re


class PathFilter(object):
    """I filter path components for safe storage on file systems.

    :ivar slashes: whether to convert slashes to dashes.
    :vartype slashes:
    :ivar quotes: whether to normalize quotes.
    :vartype quotes:
    :ivar fat: whether to strip characters illegal on FAT filesystems.
    :vartype fat:
    :ivar special: whether to strip special characters.
    :vartype special:
    """

    def __init__(self, slashes=True, quotes=True, fat=True, special=False):
        self._slashes = slashes
        self._quotes = quotes
        self._fat = fat
        self._special = special

    def filter(self, path):
        if self._slashes:
            path = re.sub(r'[/\\]', '-', path, re.UNICODE)

        def separators(path):
            # replace separators with a space-hyphen or hyphen
            path = re.sub(r'[:]', ' -', path, re.UNICODE)
            path = re.sub(r'[\|]', '-', path, re.UNICODE)
            return path

        # change all fancy single/double quotes to normal quotes
        if self._quotes:
            path = re.sub(ur'[\xc2\xb4\u2018\u2019\u201b]', "'", path,
                          re.UNICODE)
            path = re.sub(ur'[\u201c\u201d\u201f]', '"', path, re.UNICODE)

        if self._special:
            path = separators(path)
            path = re.sub(r'[\*\?&!\'\"\$\(\)`{}\[\]<>]',
                          '_', path, re.UNICODE)

        if self._fat:
            path = separators(path)
            # : and | already gone, but leave them here for reference
            path = re.sub(r'[:\*\?"<>|"]', '_', path, re.UNICODE)

        return path
