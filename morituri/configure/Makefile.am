CLEANFILES = *.py{c,o}

morituridir = $(PYTHONLIBDIR)/morituri/configure

morituri_PYTHON = \
	__init__.py \
	configure.py \
	installed.py

noinst_PYTHON = uninstalled.py

BUILT_SOURCES = installed.py uninstalled.py

TAGS_FILES = installed.py.in uninstalled.py.in

DISTCLEANFILES = installed.pyc installed.pyo uninstalled.pyc uninstalled.pyo

EXTRA_DIST = $(morituri_PYTHON) installed.py.in uninstalled.py.in
