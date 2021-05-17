MAKEFLAGS += --silent

build:
	for manpage in *.rst; do rst2man --exit-status=2 --report=1 $${manpage} "$${manpage%%.*}".1 ; done

clean:
	rm *.1
