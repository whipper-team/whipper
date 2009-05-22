# configure.ac needs to AM_CONDITIONAL HAVE_PYCHECKER

if HAVE_PYCHECKER
check-local-pychecker: pychecker
else
check-local-pychecker:
	echo "Pychecker not found, passing"
endif

# include this snippet for the pychecker stuff
# Makefile.am needs to define
# PYCHECKER_WHITELIST
# and
# PYCHECKER_BLACKLIST

pychecker_setup = `ls $(top_srcdir)/misc/setup.py 2> /dev/null`
pychecker_help = `ls $(top_srcdir)/misc/pycheckerhelp.py 2> /dev/null`
pychecker =					\
	pychecker -Q -F misc/pycheckerrc	\
	$(pychecker_setup)			\
	$(pychecker_help)

# during distcheck, we get executed from $(NAME)-$(VERSION)/_build, while
# our python sources are one level up.  Figure this out and set a OUR_PATH
# this uses Makefile syntax, so we need to protect it from automake
thisdir = $(shell basename `pwd`)
OUR_PATH = $(if $(subst _build,,$(thisdir)),$(shell pwd),$(shell pwd)/..)

pychecker_files = $(filter-out $(PYCHECKER_BLACKLIST),$(wildcard $(PYCHECKER_WHITELIST)))

# we redirect stderr so we don't get messages like
# warning: couldn't find real module for class SSL.Error (module name: SSL)
# which can't be turned off in pychecker
pycheckersplit:
	@echo running pychecker on each file ...
	@for file in $(pychecker_all_files)
	do \
		$(pychecker) $$file > /dev/null 2>&1			\
		if test $$? -ne 0; then 				\
			echo "Error on $$file";				\
			$(pychecker) $$file; break			\
		fi							\
	done

pychecker: 
	@echo running pychecker ...
	@$(pychecker) $(pychecker_files) 2>/dev/null || make pycheckerverbose

pycheckerverbose:
	@echo "running pychecker (verbose) ..."
	$(pychecker) --limit 1000 $(pychecker_files)
