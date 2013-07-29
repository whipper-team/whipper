# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

'''
configure-time variables for installed or uninstalled operation

Code should run
    >>> from morituri.configure import configure

and then access the variables from the configure module.  For example:
    >>> print configure.version

@var  isinstalled: whether an installed version is being run
@type isinstalled: boolean

@var  version:     morituri version number
@type version:     string
'''

import os

# where am I on the disk ?
__thisdir = os.path.dirname(os.path.abspath(__file__))

if os.path.exists(os.path.join(__thisdir, 'uninstalled.py')):
    from morituri.configure import uninstalled
    config_dict = uninstalled.get()
else:
    from morituri.configure import installed
    config_dict = installed.get()

for key, value in config_dict.items():
    dictionary = locals()
    dictionary[key] = value
