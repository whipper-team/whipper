completiondir = $(sysconfdir)/bash_completion.d
completion_DATA = rip

BUILT_SOURCES = rip
CLEANFILES = rip

EXTRA_DIST = bash-compgen

ENTRY = morituri.rip.main.Rip

rip: bash-compgen $(top_srcdir)/morituri $(top_srcdir)/morituri/*
	PYTHONPATH=$(top_srcdir):$$PYTHONPATH $(srcdir)/bash-compgen \
		$(completion_DATA) $(ENTRY) > $@
