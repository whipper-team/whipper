/*
 ============================================================================
 Name        : accuraterip-checksum.c
 Authors     : Leo Bogert (http://leo.bogert.de), Andreas Oberritter
 License     : GPLv3
 Description : A Python C extension to compute the AccurateRip checksum of WAV or FLAC tracks.
               Implemented according to http://www.hydrogenaudio.org/forums/index.php?showtopic=97603
 ============================================================================
 */

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
#include <sndfile.h>
#include <Python.h>

static bool check_fileformat(const SF_INFO *sfinfo)
{
#ifdef DEBUG
	printf("Channels: %i\n", sfinfo->channels);
	printf("Format: %X\n", sfinfo->format);
	printf("Frames: %li\n", sfinfo->frames);
	printf("Samplerate: %i\n", sfinfo->samplerate);
	printf("Sections: %i\n", sfinfo->sections);
	printf("Seekable: %i\n", sfinfo->seekable);
#endif

	switch (sfinfo->format & SF_FORMAT_TYPEMASK) {
	case SF_FORMAT_WAV:
	case SF_FORMAT_FLAC:
		return (sfinfo->channels == 2) &&
		       (sfinfo->samplerate == 44100) &&
		       ((sfinfo->format & SF_FORMAT_SUBMASK) == SF_FORMAT_PCM_16);
	}

	return false;
}

static void *load_full_audiodata(SNDFILE *sndfile, const SF_INFO *sfinfo, size_t size)
{
	void *data = malloc(size);

	if(data == NULL)
		return NULL;

	if(sf_readf_short(sndfile, data, sfinfo->frames) !=  sfinfo->frames) {
		free(data);
		return NULL;
	}

	return data;
}

static void compute_checksums(const uint32_t *audio_data, size_t audio_data_size, size_t track_number, size_t total_tracks, uint32_t *v1, uint32_t *v2)
{
	uint32_t csum_hi = 0;
	uint32_t csum_lo = 0;
	uint32_t AR_CRCPosCheckFrom = 0;
	size_t Datauint32_tSize = audio_data_size / sizeof(uint32_t);
	uint32_t AR_CRCPosCheckTo = Datauint32_tSize;
	const size_t SectorBytes = 2352;		// each sector
	uint32_t MulBy = 1;
	size_t i;

	if (track_number == 1)			// first?
		AR_CRCPosCheckFrom += ((SectorBytes * 5) / sizeof(uint32_t));
	if (track_number == total_tracks)		// last?
		AR_CRCPosCheckTo -= ((SectorBytes * 5) / sizeof(uint32_t));

	for (i = 0; i < Datauint32_tSize; i++) {
		if (MulBy >= AR_CRCPosCheckFrom && MulBy <= AR_CRCPosCheckTo) {
			uint64_t product = (uint64_t)audio_data[i] * (uint64_t)MulBy;
			csum_hi += (uint32_t)(product >> 32);
			csum_lo += (uint32_t)(product);
		}
		MulBy++;
	}

	*v1 = csum_lo;
	*v2 = csum_lo + csum_hi;
}

static PyObject *accuraterip_compute(PyObject *self, PyObject *args)
{
	const char *filename;
	unsigned int track_number;
	unsigned int total_tracks;
	uint32_t v1, v2;
	void *audio_data;
	size_t size;
	SF_INFO sfinfo;
	SNDFILE *sndfile = NULL;

	if (!PyArg_ParseTuple(args, "sII", &filename, &track_number, &total_tracks))
		goto err;

	if (track_number < 1 || track_number > total_tracks) {
		fprintf(stderr, "Invalid track_number!\n");
		goto err;
	}

	if (total_tracks < 1 || total_tracks > 99) {
		fprintf(stderr, "Invalid total_tracks!\n");
		goto err;
	}

#ifdef DEBUG
	printf("Reading %s\n", filename);
#endif

	memset(&sfinfo, 0, sizeof(sfinfo));
	sndfile = sf_open(filename, SFM_READ, &sfinfo);
	if (sndfile == NULL) {
		fprintf(stderr, "sf_open failed! sf_error==%i\n", sf_error(NULL));
		goto err;
	}

	if (!check_fileformat(&sfinfo)) {
		fprintf(stderr, "check_fileformat failed!\n");
		goto err;
	}

	size = sfinfo.frames * sfinfo.channels * sizeof(uint16_t);
	audio_data = load_full_audiodata(sndfile, &sfinfo, size);
	if (audio_data == NULL) {
		fprintf(stderr, "load_full_audiodata failed!\n");
		goto err;
	}

	compute_checksums(audio_data, size, track_number, total_tracks, &v1, &v2);
	free(audio_data);
	sf_close(sndfile);

	return Py_BuildValue("II", v1, v2);

err:
	if (sndfile)
		sf_close(sndfile);
	return Py_BuildValue("OO", Py_None, Py_None);
}

static PyMethodDef accuraterip_methods[] = {
	{ "compute", accuraterip_compute, METH_VARARGS, "Compute AccurateRip v1 and v2 checksums" },
	{ NULL, NULL, 0, NULL },
};

PyMODINIT_FUNC initaccuraterip(void)
{
	Py_InitModule("accuraterip", accuraterip_methods);
}
