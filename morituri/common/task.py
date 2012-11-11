# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

from morituri.extern.log import log
from morituri.extern.task import task, gstreamer

# log.Loggable first to get logging


class SyncRunner(log.Loggable, task.SyncRunner):
    pass


class GstPipelineTask(log.Loggable, gstreamer.GstPipelineTask):
    pass
