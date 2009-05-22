dnl initialize autoconf
dnl when going to/from release please remove/add the nano (fourth number)
dnl releases only do Wall, cvs and prerelease does Werror too
AC_INIT(morituri, 0.0.0.1,
   http://thomas.apestaart.org/thomas/trac/newticket?component=morituri,
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
AS_PATH_PYTHON(2.3)

dnl check for where to install our python stuff
dnl PYTHONLIBDIR=`$PYTHON -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"`
PYVER=[`$PYTHON -c "import sys ; print sys.version[:3]"`]
PYTHONLIBDIR=\${libdir}/python$PYVER/site-packages
AC_MSG_NOTICE(Installing python code in $PYTHONLIBDIR)
AC_SUBST(PYTHONLIBDIR)

dnl check for epydoc
AC_CHECK_PROG(EPYDOC, epydoc, yes, no)
AM_CONDITIONAL(HAVE_EPYDOC, test "x$EPYDOC" = "xyes")

dnl check for pychecker
AC_CHECK_PROG(PYCHECKER, pychecker, yes, no)
AM_CONDITIONAL(HAVE_PYCHECKER, test "x$PYCHECKER" = "xyes")

dnl output stuff
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
morituri/test/Makefile
doc/Makefile
misc/Makefile
morituri.spec
)
