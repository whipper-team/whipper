# -*- Mode: Python; test-case-name: whipper.test.test_common_checksum -*-
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

import binascii
import wave
import tempfile
import subprocess
import os


from whipper.extern.task import task as etask

import logging
logger = logging.getLogger(__name__)

# checksums are not CRC's. a CRC is a specific type of checksum.


class InvalidAudioError(Exception):
    """The file could not be decoded as complete CD audio."""


class CRC32Task(etask.Task):
    # TODO: Support sampleStart, sampleLength later on (should be trivial, just
    # add change the read part in _crc32 to skip some samples and/or not
    # read too far)
    def __init__(self, path, sampleStart=0, sampleLength=-1, is_wave=True):
        self.path = path
        self.is_wave = is_wave

    def start(self, runner):
        etask.Task.start(self, runner)
        self.schedule(0.0, self._crc32)

    def _crc32(self):
        tmpf = None
        try:
            path = self.path
            if not self.is_wave:
                fd, tmpf = tempfile.mkstemp()
                os.close(fd)
                subprocess.check_call(['flac', '-d', self.path, '-fo', tmpf])
                path = tmpf

            with wave.open(path) as w:
                if (w.getnchannels(), w.getsampwidth(), w.getframerate()) != (
                        2, 2, 44100):
                    raise InvalidAudioError('expected 16-bit stereo 44100 Hz')
                d = w._data_chunk.read()
                if len(d) != w.getnframes() * 4 or len(d) % 4:
                    raise InvalidAudioError('truncated PCM data')
                # Count decoded stereo samples, not compressed bytes or a
                # possibly stale WAV header's declared length.
                self.sampleCount = len(d) // 4
        # wave's chunk reader raises RuntimeError for an out-of-bounds seek
        # when a corrupt subchunk length exceeds its enclosing RIFF chunk.
        except (wave.Error, EOFError, RuntimeError,
                subprocess.CalledProcessError) as e:
            raise InvalidAudioError(str(e)) from e
        finally:
            if tmpf is not None:
                try:
                    os.remove(tmpf)
                except FileNotFoundError:
                    # flac removes its output when decoding fails.
                    pass

        self.checksum = binascii.crc32(d) & 0xffffffff
        self.stop()
