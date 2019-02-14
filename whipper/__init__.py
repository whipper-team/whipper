import logging
import os
import sys

from pkg_resources import (get_distribution,
                           DistributionNotFound, RequirementParseError)
try:
    __version__ = get_distribution(__name__).version
except (DistributionNotFound, RequirementParseError):
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
