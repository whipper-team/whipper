import os
import logging
from subprocess import Popen, PIPE

SOX = 'sox'

def peak_level(track_path):
	if not os.path.exists(track_path):
		logging.warning("SoX peak detection failed: file not found")
		return None
	sox = Popen([SOX, track_path, "-n", "stat"], stderr=PIPE)
	out, err = sox.communicate()
	if sox.returncode:
		logging.warning("SoX peak detection failed: " + s.returncode)
		return None
	return float(err.split('\n')[3].split()[2])	# Maximum amplitude: 0.123456
