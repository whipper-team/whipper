EXTRA_DIST = morituri.rss2 morituri.ics $(man_MANS)
DISTCLEANFILES = $(man_MANS)

all-local: feeds reference

if HAVE_EPYDOC
reference: $(top_srcdir)/morituri/*.py feeds
	epydoc -o reference $(top_srcdir)/morituri
else
reference:
	@true
endif

# generate feeds
feeds: morituri.rss2 morituri.ics

# don't fail fatally if user does not have RDF
morituri.rss2: $(top_srcdir)/morituri.doap
	-moap doap -f $(top_srcdir)/morituri.doap rss > morituri.rss2

morituri.ics: $(top_srcdir)/morituri.doap
	-moap doap -f $(top_srcdir)/morituri.doap ical > morituri.ics

man_MANS = rip.1

rip.1: $(top_srcdir)/morituri/extern/python-command/scripts/help2man $(top_srcdir)/morituri
	PYTHONPATH=$(top_srcdir) python $(top_srcdir)/morituri/extern/python-command/scripts/help2man morituri.rip.main.Rip rip > rip.1

clean-local:
	@rm -rf reference
