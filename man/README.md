The man pages in this directory can be generated using the `rst2man` command
line tool provided by the Python `docutils` project:

    rst2man whipper.rst whipper.1

Alternatively, you can also build all the man pages in this directory at the
same time by running (requires `make`):

    make

or this way (without make):

   for manpage in *.rst; do rst2man --exit-status=2 --report=1 --debug ${manpage} "${manpage%%.*}".1 ; done

The directory can be cleaned of generated man pages by running:

    make clean

or this way (without make):

    rm *.1
