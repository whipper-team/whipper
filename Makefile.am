# version first -- they are parsed LTR and later options depend on automake 1.8
AUTOMAKE_OPTIONS = 1.8 dist-bzip2 no-dist-gzip

ACLOCAL_AMFLAGS = -I m4

SUBDIRS = bin etc morituri doc m4 misc

EXTRA_DIST = HACKING morituri.spec morituri.doap RELEASE

check: pychecker check-python check-bash

check-python:
	trial morituri.test

check-bash:
	$(SHELL) $(top_srcdir)/morituri/test/test_bash_completion.sh $(top_builddir)/etc/bash_completion.d/morituri

_trial_temp/coverage: $(top_srcdir)/morituri/*.py $(top_srcdir)/morituri/*/*.py
	trial --coverage morituri.test

coverage: _trial_temp/coverage
	python misc/show-coverage.py `ls _trial_temp/coverage/morituri* | grep -v morituri.test | grep -v morituri.extern`

clean-local:
	@rm -rf _trial_temp

PYCHECKER_WHITELIST = \
	morituri/*.py \
	morituri/*/*.py

PYCHECKER_BLACKLIST = \
	morituri/extern/asyncsub.py

release: dist
	make $(PACKAGE)-$(VERSION).tar.bz2.md5

# generate md5 sum files
%.md5: %
	md5sum $< > $@

include $(top_srcdir)/m4/pychecker.mk
