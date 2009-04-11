track.flac:
	gst-launch audiotestsrc num-buffers=10 samplesperbuffer=588 ! audioconvert ! audio/x-raw-int,channels=2,width=16,height=16,rate=44100 ! flacenc ! filesink location=track.flac
