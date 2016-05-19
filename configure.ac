dnl initialize autoconf
dnl when going to/from release please remove/add the nano (fourth number)
dnl releases only do Wall, trunk and prerelease does Werror too
AC_INIT(morituri, 0.2.3.1,
   http://thomas.apestaart.org/morituri/trac/newticket,
   morituri)

dnl initialize automake
AM_INIT_AUTOMAKE

dnl define PACKAGE_VERSION_* variables
AS_VERSION

AS_NANO

dnl authors
AC_SUBST_FILE(AUTHORS)
AUTHORS=$srcdir/AUTHORS

dnl AM_MAINTAINER_MODE only provides the option to configure to enable it
AM_MAINTAINER_MODE

dnl Add parameters for aclocal
AC_SUBST(ACLOCAL_AMFLAGS, "-I m4")

dnl check for python
AM_PATH_PYTHON(2.3)

dnl check for where to install our python stuff
PYVER=[`$PYTHON -c "import sys ; print sys.version[:3]"`]

AC_ARG_WITH([pluginsdir],
	AS_HELP_STRING([--with-pluginsdir], [Set custom global plugin directory]),
	[],
	[with_pluginsdir=none])

dnl This is the best way of installing in an arch-independent location for now
AS_AC_EXPAND(PYTHONLIBDIR, "\${exec_prefix}/lib/python$PYVER/site-packages")

AC_MSG_NOTICE(Installing python code in $PYTHONLIBDIR)
AC_SUBST(PYTHONLIBDIR)

AS_IF([test "x$with_pluginsdir" != "xnone"], [AS_AC_EXPAND(PLUGINSDIR, "$with_pluginsdir")],
	  [test "x$with_pluginsdir" = "xnone"], [AS_AC_EXPAND(PLUGINSDIR, "\${libdir}/morituri/plugins")])
AC_MSG_NOTICE(Setting plugins directory to $PLUGINSDIR)

dnl get git revision for installed.py.in
AC_SUBST(REVISION, `$PYTHON -c 'from morituri.configure import configure; print configure.revision'`)
AC_MSG_NOTICE(Setting revision to $REVISION)

dnl check for epydoc
AC_CHECK_PROG(EPYDOC, epydoc, yes, no)
AM_CONDITIONAL(HAVE_EPYDOC, test "x$EPYDOC" = "xyes")

dnl check for pychecker
AC_CHECK_PROG(PYCHECKER, pychecker, yes, no)
AM_CONDITIONAL(HAVE_PYCHECKER, test "x$PYCHECKER" = "xyes")

dnl output stuff
AC_CONFIG_FILES([bin/rip], [chmod +x bin/rip])
AC_CONFIG_FILES([etc/bash_completion.d/bash-compgen],
                [chmod +x etc/bash_completion.d/bash-compgen])

AC_OUTPUT(
Makefile
bin/Makefile
etc/Makefile
etc/bash_completion.d/Makefile
m4/Makefile
morituri/Makefile
morituri/rip/Makefile
morituri/common/Makefile
morituri/configure/Makefile
morituri/configure/uninstalled.py
morituri/configure/installed.py
morituri/extern/Makefile
morituri/image/Makefile
morituri/program/Makefile
morituri/result/Makefile
morituri/test/Makefile
doc/Makefile
misc/Makefile
morituri.spec
)
