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

log_init_func = logging.basicConfig
if 'WHIPPER_COLOR_LOG' in os.environ:
    import coloredlogs
    def init_coloredlogs(**kwargs):
        # coloredlogs comes with its own log format, we don't want to use that
        coloredlogs.install(fmt=logging.BASIC_FORMAT, **kwargs)
    log_init_func = init_coloredlogs

if 'WHIPPER_LOGFILE' in os.environ:
    log_init_func(filename=os.environ['WHIPPER_LOGFILE'],
                  filemode='w', level=level)
else:
    log_init_func(stream=sys.stderr, level=level)
