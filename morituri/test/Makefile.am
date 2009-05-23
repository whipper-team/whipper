CLEANFILES = *.py{c,o}

EXTRA_DIST = \
	__init__.py \
	common.py \
	test_common_accurip.py \
	test_common_renamer.py \
	test_image_cue.py \
	test_image_image.py \
	test_image_table.py \
	test_image_toc.py \
	test_program_cdparanoia.py \
	test_program_cdrdao.py \
	bloc.cue \
	bloc.toc \
	breeders.cue \
	breeders.toc \
	capital.fast.toc \
	cure.cue \
	cure.toc \
	dBAR-011-0010e284-009228a3-9809ff0b.bin \
	kanye.cue \
	kings-separate.cue \
	kings-single.cue \
	ladyhawke.toc \
	track-separate.cue \
	track-single.cue \
	cdparanoia.progress \
	cdrdao.readtoc.progress \
	track.flac

# re-generation of test files when needed
regenerate: track.flac

%.regenerate:
	rm $*
	make $*


track.flac:
	gst-launch audiotestsrc num-buffers=10 samplesperbuffer=588 ! audioconvert ! audio/x-raw-int,channels=2,width=16,height=16,rate=44100 ! flacenc ! filesink location=track.flac

