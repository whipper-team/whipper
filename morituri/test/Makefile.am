CLEANFILES = *.py{c,o}

EXTRA_DIST = \
	__init__.py \
	common.py \
	test_common_accurip.py \
	test_common_cache.py \
	test_common_checksum.py \
	test_common_common.py \
	test_common_config.py \
	test_common_drive.py \
	test_common_encode.py \
	test_common_gstreamer.py \
	test_common_musicbrainzngs.py \
	test_common_program.py \
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
	capital.1.toc \
	capital.2.toc \
	cure.cue \
	cure.toc \
	jose.toc \
	dBAR-011-0010e284-009228a3-9809ff0b.bin \
	dBAR-020-002e5023-029d8e49-040eaa14.bin \
	release.08397059-86c1-463b-8ed0-cd596dbd174f.xml \
	release.93a6268c-ddf1-4898-bf93-fb862b1c5c5e.xml \
	release.c7d919f4-3ea0-4c4b-a230-b3605f069440.xml \
	morituri.release.3451f29c-9bb8-4cc5-bfcc-bd50104b94f8.json \
	kanye.cue \
	kings-separate.cue \
	kings-single.cue \
	ladyhawke.toc \
	track-separate.cue \
	track-single.cue \
	cdparanoia.progress \
	cdparanoia.progress.error \
	cdrdao.readtoc.progress \
	silentalarm.result.pickle \
	totbl.fast.toc \
	track.flac \
	cache/result/fe105a11.pickle \
	cdparanoia/MATSHITA.cdparanoia-A.log \
	cdparanoia/MATSHITA.cdparanoia-A.stderr \
	cdparanoia/PX-L890SA.cdparanoia-A.log \
	cdparanoia/PX-L890SA.cdparanoia-A.stderr


# re-generation of test files when needed
regenerate: track.flac

%.regenerate:
	rm $*
	make $*

track.flac:
	gst-launch audiotestsrc num-buffers=10 samplesperbuffer=588 ! audioconvert ! audio/x-raw-int,channels=2,width=16,height=16,rate=44100 ! flacenc ! filesink location=track.flac
