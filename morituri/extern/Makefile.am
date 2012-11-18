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

musicbrainzngsdir = $(PYTHONLIBDIR)/morituri/extern/musicbrainzngs

musicbrainzngs_PYTHON = \
	musicbrainzngs/__init__.py \
	musicbrainzngs/musicbrainz.py \
	musicbrainzngs/mbxml.py


EXTRA_DIST = log/test_log.py command/test_command.py command/help2man.py

musicbrainzngs/musicbrainz.py: all

python-musicbrainz-ngs:
	git clone https://github.com/thomasvs/python-musicbrainz-ngs.git

python-musicbrainz-ngs-check:
	if test ! -e $(top_srcdir)/morituri/extern/musicbrainzngs/musicbrainz.py; then echo cloning python-musicbrainz-ngs; make python-musicbrainz-ngs; fi

python-command:
	git clone https://github.com/thomasvs/python-command.git

python-command-check:
	if test ! -e $(top_srcdir)/morituri/extern/command/command.py; then echo cloning python-command; make python-command; fi

all: python-musicbrainz-ngs-check python-command-check
