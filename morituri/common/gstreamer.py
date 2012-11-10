# -*- Mode: Python; test-case-name: morituri.test.test_common_gstreamer -*-
# vi:si:et:sw=4:sts=4:ts=4

# Morituri - for those about to RIP

# Copyright (C) 2009 Thomas Vander Stichele

# This file is part of morituri.
#
# morituri is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# morituri is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with morituri.  If not, see <http://www.gnu.org/licenses/>.

from morituri.common import log

# workaround for issue #64


def removeAudioParsers():
    log.debug('gstreamer', 'Removing buggy audioparsers plugin if needed')

    import gst
    registry = gst.registry_get_default()

    plugin = registry.find_plugin("audioparsersbad")
    if plugin:
        # always remove from bad
        log.debug('gstreamer', 'removing audioparsersbad plugin from registry')
        registry.remove_plugin(plugin)

    plugin = registry.find_plugin("audioparsers")
    if plugin:
        log.debug('gstreamer', 'Found audioparsers plugin from %s %s',
            plugin.get_source(), plugin.get_version())

        # was fixed after 0.10.30 and before 0.10.31
        if plugin.get_source() == 'gst-plugins-good' \
            and plugin.get_version() > '0.10.30.1':
            return

        registry.remove_plugin(plugin)
