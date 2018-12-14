import logging
import os
import sys

__version__ = '0.7.3'

level = logging.INFO
if 'WHIPPER_DEBUG' in os.environ:
    level = os.environ['WHIPPER_DEBUG'].upper()
if 'WHIPPER_LOGFILE' in os.environ:
    logging.basicConfig(filename=os.environ['WHIPPER_LOGFILE'],
                        filemode='w', level=level)
else:
    logging.basicConfig(stream=sys.stderr, level=level)
