CLEANFILES = *.py{c,o} command/*.py{c,o} log/*.py{c,o}

morituridir = $(PYTHONLIBDIR)/morituri/extern

morituri_PYTHON = \
	__init__.py \
	asyncsub.py

logdir = $(PYTHONLIBDIR)/morituri/extern/log

log_PYTHON = \
	log/__init__.py \
	log/log.py

commanddir = $(PYTHONLIBDIR)/morituri/extern/command

command_PYTHON = \
	command/__init__.py \
	command/command.py

taskdir = $(PYTHONLIBDIR)/morituri/extern/task

task_PYTHON = \
	task/__init__.py \
	task/task.py \
	task/taskgtk.py \
	task/gstreamer.py

EXTRA_DIST = log/test_log.py command/test_command.py command/help2man.py

python-musicbrainz-ngs:
	git clone https://github.com/thomasvs/python-musicbrainz-ngs.git

all: python-musicbrainz-ngs
