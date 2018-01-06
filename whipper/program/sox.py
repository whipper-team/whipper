import os
from subprocess import Popen, PIPE

import logging
logger = logging.getLogger(__name__)

SOX = 'sox'


def peak_level(track_path):
    """Accept a path to a sox-decodable audio file.

    :param track_path: full path to audio track.
    :type track_path: str
    :returns: track peak level from sox ('maximum amplitude') or None on error.
    :rtype: float or None
    """
    if not os.path.exists(track_path):
        logger.warning("SoX peak detection failed: file not found")
        return None
    sox = Popen([SOX, track_path, "-n", "stat"], stderr=PIPE)
    out, err = sox.communicate()
    if sox.returncode:
        logger.warning("SoX peak detection failed: " + str(sox.returncode))
        return None
    # relevant captured line looks like:
    # Maximum amplitude: 0.123456
    return float(err.splitlines()[3].split()[2])
