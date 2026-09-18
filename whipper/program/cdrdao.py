import os
import re
import shutil
import tempfile
import subprocess
from subprocess import Popen, PIPE

from whipper.common.common import truncate_filename
from whipper.image.toc import TocFile
from whipper.extern.task import task
from whipper.extern import asyncsub

import logging
logger = logging.getLogger(__name__)

CDRDAO = 'cdrdao'

_TRACK_RE = re.compile(r"^Analyzing track (?P<track>[0-9]*) \(AUDIO\): start (?P<start>[0-9]*:[0-9]*:[0-9]*), length (?P<length>[0-9]*:[0-9]*:[0-9]*)")  # noqa: E501
_CRC_RE = re.compile(
    r"Found (?P<channels>[0-9]*) Q sub-channels with CRC errors")
_BEGIN_CDRDAO_RE = re.compile(r"-" * 60)
_LAST_TRACK_RE = re.compile(r"^[ ]?(?P<track>[0-9]*)")
_LEADOUT_RE = re.compile(
    r"^Leadout AUDIO\s*[0-9]\s*[0-9]*:[0-9]*:[0-9]*\([0-9]*\)")
_SUBCODE_EMPHASIS_LINE = ("Pre-emphasis flag of track differs from TOC - "
                          "toc file contains TOC setting.")
_SUBCODE_CHANNEL_LINE = (
    "2-/4-channel-audio  flag of track differs from TOC - "
    "toc file contains TOC setting.")
_SUBCODE_CHANNEL_RE = re.compile(
    r"2-/4-channel-audio\s+flag of track differs from TOC")
_CONTROL_MATCH_LINE = (
    "Control nibbles of track match CD-TOC settings.")


class ProgressParser:
    """
    Parse cdrdao read-toc diagnostics (issue #296).

    Records per-track whether subcode control nibbles matched the TOC.
    """

    tracks = 0
    currentTrack = 0
    oldline = ''  # for leadout/final track number detection

    def __init__(self):
        # track number -> True when subcode pre-emphasis differs from TOC
        self.preEmphasisMismatch = {}
        # track number -> True when control nibbles matched TOC
        self.controlMatch = {}
        # track number -> True when 2/4-channel flag differed from TOC
        self.channelMismatch = {}

    def parse(self, line):
        cdrdao_m = _BEGIN_CDRDAO_RE.match(line)

        if cdrdao_m:
            logger.debug("RE: Begin cdrdao toc-read")

        leadout_m = _LEADOUT_RE.match(line)

        if leadout_m:
            logger.debug("RE: Reached leadout")
            last_track_m = _LAST_TRACK_RE.match(self.oldline)
            if last_track_m:
                self.tracks = last_track_m.group('track')

        track_s = _TRACK_RE.search(line)
        if track_s:
            logger.debug("RE: Began reading track: %d",
                         int(track_s.group('track')))
            self.currentTrack = int(track_s.group('track'))

        crc_s = _CRC_RE.search(line)
        if crc_s:
            print("Track %d finished, "
                  "found %d Q sub-channels with CRC errors" %
                  (self.currentTrack, int(crc_s.group('channels'))))

        # Issue #296: subcode vs TOC control nibbles
        if _SUBCODE_EMPHASIS_LINE in line:
            logger.warning('track %d: %s',
                           self.currentTrack, _SUBCODE_EMPHASIS_LINE)
            if self.currentTrack:
                self.preEmphasisMismatch[self.currentTrack] = True

        if _SUBCODE_CHANNEL_LINE in line or _SUBCODE_CHANNEL_RE.search(line):
            logger.warning(
                'track %d: 2-/4-channel flag differs from TOC',
                self.currentTrack)
            if self.currentTrack:
                self.channelMismatch[self.currentTrack] = True

        if _CONTROL_MATCH_LINE in line:
            logger.debug('track %d: %s',
                         self.currentTrack, _CONTROL_MATCH_LINE)
            if self.currentTrack:
                self.controlMatch[self.currentTrack] = True

        self.oldline = line

    def subcodePreEmphasis(self, trackNumber, tocPreEmphasis):
        """
        Infer subcode pre-emphasis for a track from cdrdao diagnostics.

        :param trackNumber: 1-based track number
        :param tocPreEmphasis: TOC pre-emphasis (True/False/None)
        :returns: True/False when known, else None
        """
        if trackNumber in self.preEmphasisMismatch:
            # cdrdao writes the TOC value into the .toc; subcode differs
            if tocPreEmphasis is None:
                return None
            return not bool(tocPreEmphasis)
        if trackNumber in self.controlMatch:
            return bool(tocPreEmphasis) if tocPreEmphasis is not None else False
        return None


class ReadTOCTask(task.Task):
    """Task that reads the TOC of the disc using cdrdao."""

    description = "Reading TOC"
    toc = None

    def __init__(self, device, fast_toc=False, toc_path=None):
        """
        Read the TOC for ``device``.

        :param device: block device to read TOC from
        :type device: str
        :param fast_toc: whether to use fast-toc cdrdao mode
        :type fast_toc: bool
        :param toc_path: where to save TOC if wanted
        :type toc_path: str
        """
        self.device = device
        self.fast_toc = fast_toc
        self.toc_path = toc_path
        self._buffer = ""  # accumulate characters
        self._parser = ProgressParser()

        self.fd, self.tocfile = tempfile.mkstemp(
            suffix='.cdrdao.read-toc.whipper.task')

    def start(self, runner):
        task.Task.start(self, runner)
        os.close(self.fd)
        os.unlink(self.tocfile)

        cmd = ([CDRDAO, 'read-toc']
               + (['--fast-toc'] if self.fast_toc else [])
               + ['--device', self.device, self.tocfile])

        self._popen = asyncsub.Popen(cmd,
                                     bufsize=1024,
                                     stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     close_fds=True)

        self.schedule(0.01, self._read, runner)

    def _read(self, runner):
        ret = self._popen.recv_err()
        if not ret:
            if self._popen.poll() is not None:
                self._done()
                return
            self.schedule(0.01, self._read, runner)
            return
        self._buffer += ret.decode()

        # parse buffer into lines if possible, and parse them
        if "\n" in self._buffer:
            lines = self._buffer.split('\n')
            if lines[-1] != "\n":
                # last line didn't end yet
                self._buffer = lines[-1]
                del lines[-1]
            else:
                self._buffer = ""
            for line in lines:
                self._parser.parse(line)
                if (self._parser.currentTrack != 0 and
                        self._parser.tracks != 0):
                    progress = (float('%d' % self._parser.currentTrack) /
                                float(self._parser.tracks))
                    if progress < 1.0:
                        self.setProgress(progress)

        # 0 does not give us output before we complete, 1.0 gives us output
        # too late
        self.schedule(0.01, self._read, runner)

    def _poll(self, runner):
        if self._popen.poll() is None:
            self.schedule(1.0, self._poll, runner)
            return

        self._done()

    def _done(self):
        self.setProgress(1.0)
        self.toc = TocFile(self.tocfile)
        self.toc.parse()
        # Issue #296: attach subcode pre-emphasis diagnostics to the table
        self._applySubcodePreEmphasis(self.toc.table)
        if self.toc_path is not None:
            t_comp = os.path.abspath(self.toc_path).split(os.sep)
            t_dirn = os.sep.join(t_comp[:-1])
            # If the output path doesn't exist, make it recursively
            try:
                os.makedirs(t_dirn)
                logger.info("creating output directory %s", t_dirn)
            except FileExistsError as e:
                logger.debug(e)
            t_dst = truncate_filename(
                os.path.join(t_dirn, t_comp[-1] + '.toc'))
            shutil.copy(self.tocfile, os.path.join(t_dirn, t_dst))
        os.unlink(self.tocfile)
        self.stop()
        return

    def _applySubcodePreEmphasis(self, table):
        """
        Copy subcode pre-emphasis diagnostics onto table tracks (#296).

        TOC values stay authoritative for cue FLAGS (cdrdao writes TOC
        settings into the .toc). Subcode values are reported separately.
        """
        parser = self._parser
        for track in getattr(table, 'tracks', []) or []:
            number = getattr(track, 'number', None)
            if not number:
                continue
            toc_pe = getattr(track, 'pre_emphasis', None)
            if toc_pe is None:
                # explicit "NO PRE_EMPHASIS" was not seen; treat missing
                # PRE_EMPHASIS line as False when cdrdao reported match
                if number in parser.controlMatch:
                    toc_pe = False
                    track.pre_emphasis = False
            track.pre_emphasis_toc = toc_pe
            track.pre_emphasis_subcode = parser.subcodePreEmphasis(
                number, toc_pe)
            track.pre_emphasis_conflict = number in parser.preEmphasisMismatch
            if track.pre_emphasis_conflict:
                logger.warning(
                    'track %d: TOC pre-emphasis=%s but subcode=%s; '
                    'cue FLAGS will follow the TOC (cdrdao behaviour)',
                    number, toc_pe, track.pre_emphasis_subcode)


def DetectCdr(device):
    """Whether cdrdao detects a CD-R for ``device``."""
    cmd = [CDRDAO, 'disk-info', '-v1', '--device', device]
    logger.debug("executing %r", cmd)
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    return 'CD-R medium          : n/a' not in p.stdout.read().decode()


def version():
    """Return cdrdao version as a string."""
    cdrdao = Popen(CDRDAO, stderr=PIPE)
    _, err = cdrdao.communicate()
    if cdrdao.returncode != 1:
        logger.warning("cdrdao version detection failed: "
                       "return code is %s", cdrdao.returncode)
        return None
    m = re.compile(r'^Cdrdao version (?P<version>[^ ]*)').search(
        err.decode('utf-8'))
    if not m:
        logger.warning("cdrdao version detection failed: "
                       "could not find version")
        return None
    return m.group('version')
