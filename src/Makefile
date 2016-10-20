# See LICENSE file for copyright and license details.

include config.mk

SRC = accuraterip-checksum.c
OBJ = ${SRC:.c=.o}

all: options accuraterip-checksum

options:
	@echo accuraterip-checksum build options:
	@echo "CFLAGS   = ${CFLAGS}"
	@echo "LDFLAGS  = ${LDFLAGS}"
	@echo "CC       = ${CC}"

.c.o:
	@echo CC $<
	@${CC} -c ${CFLAGS} $<

accuraterip-checksum: ${OBJ}
	@echo CC -o $@
	@${CC} -o $@ ${OBJ} ${LDFLAGS}

clean:
	@echo cleaning
	@rm -f accuraterip-checksum ${OBJ} accuraterip-checksum-${VERSION}.tar.gz

dist: clean
	@echo creating dist tarball
	@mkdir -p accuraterip-checksum-${VERSION}
	@cp -R Makefile README.md config.mk \
		${SRC} accuraterip-checksum-${VERSION}
	@tar -cf accuraterip-checksum-${VERSION}.tar accuraterip-checksum-${VERSION}
	@gzip accuraterip-checksum-${VERSION}.tar
	@rm -rf accuraterip-checksum-${VERSION}

install: all
	@echo installing executable file to ${DESTDIR}${PREFIX}/bin
	@mkdir -p ${DESTDIR}${PREFIX}/bin
	@cp -f accuraterip-checksum ${DESTDIR}${PREFIX}/bin
	@chmod 755 ${DESTDIR}${PREFIX}/bin/accuraterip-checksum

uninstall:
	@echo removing executable file from ${DESTDIR}${PREFIX}/bin
	@rm -f ${DESTDIR}${PREFIX}/bin/accuraterip-checksum

.PHONY: all options clean dist install uninstall
