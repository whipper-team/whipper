import logging
import os
import sys

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version('whipper')
except PackageNotFoundError:
    # not installed as package or is being run from source/git checkout
    from setuptools_scm import get_version
    __version__ = get_version()

level = logging.INFO
if 'WHIPPER_DEBUG' in os.environ:
    level = os.environ['WHIPPER_DEBUG'].upper()
if 'WHIPPER_LOGFILE' in os.environ:
    logging.basicConfig(filename=os.environ['WHIPPER_LOGFILE'],
                        filemode='w', level=level)
else:
    logging.basicConfig(stream=sys.stderr, level=level)
