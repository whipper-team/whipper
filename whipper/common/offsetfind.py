"""Suggest offsets from track 1's frame-450 AccurateRip checksum.

This only proposes candidates. The command must confirm full-track checksums
before treating a candidate as a drive offset.
"""

# Format and checksum reference (Spoon, dBpoweramp Developers Corner):
# https://forum.dbpoweramp.com/forum/other-topics/developers-corner/20117-accuraterip-crc-calculation  # noqa: E501

import array
import logging
import os
import tempfile
import wave

from whipper.common import common
from whipper.extern.task import task
from whipper.program import cdparanoia

logger = logging.getLogger(__name__)
SECTOR_SAMPLES = 588
FRAME450 = 450 * SECTOR_SAMPLES
DEFAULT_SWEEP = 3000
DEFAULT_READ_TIMEOUT = 1800.0
DEFAULT_IDLE_TIMEOUT = 120.0


def offsetfind_crcs(pcm, start):
    """Return one-sector CRCs with local and track-position multipliers."""
    local = total = 0
    for i in range(SECTOR_SAMPLES):
        pos = (start + i) * 2
        sample = (pcm[pos] & 0xffff) | ((pcm[pos + 1] & 0xffff) << 16)
        local += (i + 1) * sample
        total += sample
    return local & 0xffffffff, (local + FRAME450 * total) & 0xffffffff


def match_offsets(pcm, sample_base, candidates, checksums):
    """Return all matching candidates in input order, within the PCM span."""
    targets = set(checksums)
    matches = []
    if not targets:
        return matches
    for offset in candidates:
        start = FRAME450 + offset - sample_base
        if start < 0 or start + SECTOR_SAMPLES > len(pcm) // 2:
            continue
        if targets.intersection(offsetfind_crcs(pcm, start)):
            matches.append(offset)
    return matches


def _read_pcm(path):
    with wave.open(path, 'rb') as handle:
        if (handle.getnchannels(), handle.getsampwidth(),
                handle.getframerate(), handle.getcomptype()) != (
                2, 2, 44100, 'NONE'):
            raise ValueError('offset detection requires CD-quality PCM')
        raw = handle.readframes(handle.getnframes())
        if len(raw) != handle.getnframes() * 4:
            raise ValueError('incomplete PCM window')
    # wave.readframes already converts 16-bit WAV data to native byte order.
    # array('h') uses native order too; do not swap again.
    pcm = array.array('h')
    pcm.frombytes(raw)
    return pcm


def read_window(runner, table, device, guess, sweep,
                read_timeout=DEFAULT_READ_TIMEOUT,
                idle_timeout=DEFAULT_IDLE_TIMEOUT):
    """Read one short span at zero correction, returning PCM and its origin."""
    first = max(0, (FRAME450 + guess - sweep) // SECTOR_SAMPLES - 2)
    last = (FRAME450 + guess + sweep + SECTOR_SAMPLES - 1) // \
        SECTOR_SAMPLES + 2
    track_start = table.getTrackStart(1)
    start = track_start + first
    stop = min(track_start + last, table.getTrackEnd(1))
    if stop < start or stop - track_start < 450:
        return None, None
    fd, path = tempfile.mkstemp(suffix='.offset-window.wav')
    os.close(fd)
    try:
        reader = cdparanoia.ReadTrackTask(
            path, table, start, stop, overread=False, offset=0, device=device,
            read_timeout=read_timeout, idle_timeout=idle_timeout)
        runner.run(reader)
        return _read_pcm(path), first * SECTOR_SAMPLES
    except task.TaskException as error:
        if isinstance(error.exception, (common.MissingDependencyException,
                                        cdparanoia.ReadCleanupError)):
            raise
        logger.warning('cannot read offset window: %s', error)
    except (OSError, EOFError, ValueError, wave.Error) as error:
        logger.warning('cannot read offset window: %s', error)
    finally:
        os.unlink(path)
    return None, None


def find_offsets(runner, table, device, responses, guess=0,
                 allowed_offsets=None, sweep=DEFAULT_SWEEP,
                 read_timeout=DEFAULT_READ_TIMEOUT,
                 idle_timeout=DEFAULT_IDLE_TIMEOUT):
    """Suggest candidates, leaving ordinary probing on unavailable data."""
    checksums = set()
    for response in responses:
        values = getattr(response, 'offsetfind_checksums', ())
        if not values:
            continue
        try:
            value = int(values[0], 16)
        except (TypeError, ValueError):
            continue
        if value:
            checksums.add(value)
    if not checksums:
        return []
    pcm, sample_base = read_window(
        runner, table, device, guess, sweep,
        read_timeout=read_timeout, idle_timeout=idle_timeout)
    if pcm is None:
        return []
    candidates = (range(guess - sweep, guess + sweep + 1)
                  if allowed_offsets is None else allowed_offsets)
    return match_offsets(pcm, sample_base, candidates, checksums)
