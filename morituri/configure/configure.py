# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

import os

from morituri.common import common

config_dict = {
    'revision': common.getRevision(),
    'version': '0.4.0',
}

for key, value in config_dict.items():
    dictionary = locals()
    dictionary[key] = value
