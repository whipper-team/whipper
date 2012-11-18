# version first -- they are parsed LTR and later options depend on automake 1.8
AUTOMAKE_OPTIONS = 1.8 dist-bzip2 no-dist-gzip

ACLOCAL_AMFLAGS = -I m4

SUBDIRS = morituri bin etc doc m4 misc

EXTRA_DIST = morituri.spec morituri.doap RELEASE README HACKING

SOURCES = $(top_srcdir)/morituri/*.py $(top_srcdir)/morituri/*/*.py

check: pychecker check-python

check-python:
	PYTHONPATH=$(PYTHONPATH):$(top_srcdir) trial morituri.test

_trial_temp/coverage: $(top_srcdir)/morituri/*.py $(top_srcdir)/morituri/*/*.py
	trial --coverage morituri.test

coverage: _trial_temp/coverage
	python misc/show-coverage.py `ls _trial_temp/coverage/morituri* | grep -v morituri.test | grep -v morituri.extern`

pep8:
	for file in $(SOURCES); do python misc/pep8.py --repeat $$file; done

clean-local:
	@rm -rf _trial_temp

PYCHECKER_WHITELIST = \
	morituri/*.py \
	morituri/*/*.py

PYCHECKER_BLACKLIST = \
	morituri/common/taskgtk.py \
	morituri/extern/asyncsub.py \
	morituri/extern/log/log.py

release: dist
	make $(PACKAGE)-$(VERSION).tar.bz2.md5

# generate md5 sum files
%.md5: %
	md5sum $< > $@

include $(top_srcdir)/m4/pychecker.mk
