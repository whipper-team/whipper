GOOD=/home/thomas/gst/git/gst-plugins-good/gst/audioparsers
MORI=/home/thomas/dev/own/morituri

cd $GOOD
make

GST_PLUGIN_PATH=$GOOD gst-inspect flacparse | grep ersion:

cd $MORI
GST_PLUGIN_PATH=$GOOD ./flacparse-testcase $MORI/morituri/test/track.flac
