import os
from subprocess import Popen, PIPE

import logging
logger = logging.getLogger(__name__)

SOX = 'sox'


def peak_level(track_path):
    """Accept a path to a sox-decodable audio file.

    :param track_path: full path to audio track.
    :type track_path: str
    :returns: track peak absolute value from sox or None on error.
    :rtype: int or None
    """
    if not os.path.exists(track_path):
        logger.warning("SoX peak detection failed: file not found")
        return None
    sox = Popen([SOX, track_path, "-n", "stats", "-b", "16"], stderr=PIPE)
    out, err = sox.communicate()
    if sox.returncode:
        logger.warning("SoX peak detection failed: " + str(sox.returncode))
        return None
    # relevant captured lines looks like this:
    # Min level     -26215
    # Max level      26215
    min_level = int(err.splitlines()[2].split()[2])
    max_level = int(err.splitlines()[3].split()[2])
    return max(abs(min_level), abs(max_level))
