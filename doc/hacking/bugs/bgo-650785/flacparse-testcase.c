/* gcc -Wall $(pkg-config --cflags --libs gstreamer-0.10) -g3 -ggdb3 -o flacparse-testcase ./flacparse-testcase.c */
#include <gst/gst.h>

static const char PIPELINE[] = "filesrc location=%s " \
                                "! decodebin ! audio/x-raw-int " \
                                "! appsink name=sink sync=False " \
                                          "emit-signals=True";

int main(int argc, char **argv)
{
    GstElement *pipeline;
    GstElement *sink;
    gchar *pipeline_str;
    GstStateChangeReturn state_change_status;
    gint64 duration;
    GstFormat query_format;
    gboolean query_success;

    gst_init(&argc, &argv);

    if (argc != 2) {
        g_print("Usage: %s filename\n", argv[0]);
        return 1;
    }

    pipeline_str = g_strdup_printf(PIPELINE, argv[1]);
    pipeline = gst_parse_launch(pipeline_str, NULL);
    if (pipeline == NULL) {
        g_print("Failed to create pipeline\n");
        g_print("%s\n", pipeline_str);
        return 2;
    }
    g_free(pipeline_str);

    gst_element_set_state(pipeline, GST_STATE_PAUSED);
    state_change_status = gst_element_get_state(pipeline, NULL, NULL,
                                                GST_CLOCK_TIME_NONE);
    if (state_change_status != GST_STATE_CHANGE_SUCCESS) {
        g_print("Failed to set pipeline to PAUSED\n");
        return 3;
    }

    sink = gst_bin_get_by_name(GST_BIN(pipeline), "sink");
    if (sink == NULL) {
        g_print("Couldn't find sink in pipeline\n");
        return 4;
    }

    query_format = GST_FORMAT_DEFAULT;
    query_success = gst_element_query_duration(sink, &query_format,
                                               &duration);
    if (query_success) {
        g_print("%s duration is %"G_GINT64_FORMAT"\n", argv[1], duration);
        return 0;
    } else {
        g_print("Couldn't get duration for %s\n", argv[1]);
        return 5;
    }

    gst_object_unref(GST_OBJECT(sink));
    gst_object_unref(GST_OBJECT(pipeline));

    return 6;
}
