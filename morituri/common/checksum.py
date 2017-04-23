# -*- Mode: Python; test-case-name: morituri.test.test_common_checksum -*-
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

import binascii
import wave


from morituri.extern.task import task as etask

from morituri.program.arc import accuraterip_checksum

import logging
logger = logging.getLogger(__name__)

# checksums are not CRC's. a CRC is a specific type of checksum.


class CRC32Task(etask.Task):
    # TODO: Support sampleStart, sampleLength later on (should be trivial, just
    # add change the read part in _crc32 to skip some samples and/or not
    # read too far)
    def __init__(self, path, sampleStart=0, sampleLength=-1):
        self.path = path

    def start(self, runner):
        etask.Task.start(self, runner)
        self.schedule(0.0, self._crc32)

    def _crc32(self):
        w = wave.open(self.path)
        d = w._data_chunk.read()

        self.checksum = binascii.crc32(d) & 0xffffffff
        self.stop()


class FastAccurateRipChecksumTask(etask.Task):
    description = 'Calculating (Fast) AccurateRip checksum'

    def __init__(self, path, trackNumber, trackCount, wave, v2=False):
        self.path = path
        self.trackNumber = trackNumber
        self.trackCount = trackCount
        self._wave = wave
        self._v2 = v2
        self.checksum = None

    def start(self, runner):
        etask.Task.start(self, runner)
        self.schedule(0.0, self._arc)

    def _arc(self):
        arc = accuraterip_checksum(self.path, self.trackNumber, self.trackCount,
                self._wave, self._v2)
        self.checksum = arc

        self.stop()
