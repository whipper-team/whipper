CLEANFILES = *.py{c,o}

moapdir = $(PYTHONLIBDIR)/moap/configure

moap_PYTHON = \
	__init__.py \
	configure.py \
	installed.py

noinst_PYTHON = uninstalled.py

BUILT_SOURCES = installed.py uninstalled.py

TAGS_FILES = installed.py.in uninstalled.py.in

DISTCLEANFILES = installed.pyc installed.pyo uninstalled.pyc uninstalled.pyo

EXTRA_DIST = $(moap_PYTHON) installed.py.in uninstalled.py.in
