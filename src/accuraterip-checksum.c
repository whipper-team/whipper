/*
 ============================================================================
 Name        : accuraterip-checksum.c
 Author      : Leo Bogert (http://leo.bogert.de)
 Git         : http://leo.bogert.de/accuraterip-checksum
 Version     : See global variable "version"
 Copyright   : GPL
 Description : A C99 commandline program to compute the AccurateRip checksum of singletrack WAV files.
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

const char *const version = "1.4";

bool check_fileformat(const SF_INFO* sfinfo) {
#ifdef DEBUG
	printf("Channels: %i\n", sfinfo->channels);
	printf("Format: %X\n", sfinfo->format);
	printf("Frames: %li\n", sfinfo->frames);
	printf("Samplerate: %i\n", sfinfo->samplerate);
	printf("Sections: %i\n", sfinfo->sections);
	printf("Seekable: %i\n", sfinfo->seekable);
#endif

	if(sfinfo->channels != 2) return false;
	if((sfinfo->format & SF_FORMAT_TYPEMASK & SF_FORMAT_WAV) != SF_FORMAT_WAV) return false;
	if((sfinfo->format & SF_FORMAT_SUBMASK & SF_FORMAT_PCM_16) != SF_FORMAT_PCM_16) return false;
	//if((sfinfo->format & SF_FORMAT_ENDMASK & SF_ENDIAN_LITTLE) != SF_ENDIAN_LITTLE) return false;
	if(sfinfo->samplerate != 44100) return false;

	return true;
}

size_t get_full_audiodata_size(const SF_INFO* sfinfo) {
	// 16bit = samplesize, 8 bit = bitcount in byte
	return sfinfo->frames * sfinfo->channels * (16 / 8);
}

uint32_t* load_full_audiodata(SNDFILE* sndfile, const SF_INFO* sfinfo) {
	uint32_t* data = (uint32_t*)malloc(get_full_audiodata_size(sfinfo));

	if(data == NULL)
		return NULL;

	if(sf_readf_short(sndfile, (short*)data, sfinfo->frames) !=  sfinfo->frames) {
		free(data);
		return NULL;
	}

	return data;
}

uint32_t compute_v1_checksum(const uint32_t* audio_data, const size_t audio_data_size, const int track_number, const int total_tracks) {
#define DWORD uint32_t

	const DWORD *pAudioData = audio_data;	// this should point entire track audio data
	int DataSize = 	audio_data_size;	// size of the data
	int TrackNumber = track_number;	// actual track number on disc, note that for the first & last track the first and last 5 sectors are skipped
	int AudioTrackCount = total_tracks;	// CD track count

	//---------AccurateRip CRC checks------------
	DWORD AR_CRC = 0, AR_CRCPosMulti = 1;
	DWORD AR_CRCPosCheckFrom = 0;
	DWORD AR_CRCPosCheckTo = DataSize / sizeof(DWORD);
#define SectorBytes 2352		// each sector
	if (TrackNumber == 1)			// first?
		AR_CRCPosCheckFrom+= ((SectorBytes * 5) / sizeof(DWORD));
	if (TrackNumber == AudioTrackCount)		// last?
		AR_CRCPosCheckTo-=((SectorBytes * 5) / sizeof(DWORD));


	int DataDWORDSize = DataSize / sizeof(DWORD);
	for (int i = 0; i < DataDWORDSize; i++)
	{
		if (AR_CRCPosMulti >= AR_CRCPosCheckFrom && AR_CRCPosMulti <= AR_CRCPosCheckTo)
			AR_CRC+=(AR_CRCPosMulti * pAudioData[i]);

		AR_CRCPosMulti++;
	}

	return AR_CRC;
}

uint32_t compute_v2_checksum(const uint32_t* audio_data, const size_t audio_data_size, const int track_number, const int total_tracks) {
#define DWORD uint32_t
#define __int64 uint64_t

	const DWORD *pAudioData = audio_data;	// this should point entire track audio data
	int DataSize = 	audio_data_size;	// size of the data
	int TrackNumber = track_number;	// actual track number on disc, note that for the first & last track the first and last 5 sectors are skipped
	int AudioTrackCount = total_tracks;	// CD track count

	//---------AccurateRip CRC checks------------
	DWORD AR_CRCPosCheckFrom = 0;
	DWORD AR_CRCPosCheckTo = DataSize / sizeof(DWORD);
#define SectorBytes 2352		// each sector
	if (TrackNumber == 1)			// first?
		AR_CRCPosCheckFrom+= ((SectorBytes * 5) / sizeof(DWORD));
	if (TrackNumber == AudioTrackCount)		// last?
		AR_CRCPosCheckTo-=((SectorBytes * 5) / sizeof(DWORD));

	int DataDWORDSize = DataSize / sizeof(DWORD);

    DWORD AC_CRCNEW = 0;
	DWORD MulBy = 1;
	for (int i = 0; i < DataDWORDSize; i++)
	{
		if (MulBy >= AR_CRCPosCheckFrom && MulBy <= AR_CRCPosCheckTo)
		{
			DWORD Value = pAudioData[i];

			uint64_t CalcCRCNEW = (uint64_t)Value * (uint64_t)MulBy;
			DWORD LOCalcCRCNEW = (DWORD)(CalcCRCNEW & (uint64_t)0xFFFFFFFF);
			DWORD HICalcCRCNEW = (DWORD)(CalcCRCNEW / (uint64_t)0x100000000);
			AC_CRCNEW+=HICalcCRCNEW;
			AC_CRCNEW+=LOCalcCRCNEW;
		}
        MulBy++;
	}

	return AC_CRCNEW;
}

void print_syntax_to_stderr() {
	fprintf(stderr, "Syntax: accuraterip-checksum [--version / --accuraterip-v1 / --accuraterip-v2 (default)] filename track_number total_tracks\n");
}

int main(int argc, const char** argv) {
	int arg_offset;
	bool use_v1;

	switch(argc) {
		case 2:
			if(strcmp(argv[1], "--version") != 0) {
				print_syntax_to_stderr();
				return EXIT_FAILURE;
			}
			printf("accuraterip-checksum version %s\n", version);
			return EXIT_SUCCESS;
		case 4:
			arg_offset = 0;
			use_v1 = false;
			break;
		case 5:
			arg_offset = 1;
			if(!strcmp(argv[1], "--accuraterip-v1")) {
				use_v1 = true;
			} else if(!strcmp(argv[1], "--accuraterip-v2")) {
				use_v1 = false;
			} else {
				print_syntax_to_stderr();
				return EXIT_FAILURE;
			}
			break;
		default:
			print_syntax_to_stderr();
			return EXIT_FAILURE;
	}

	const char* filename = argv[1 + arg_offset];
	const char* track_number_string = argv[2 + arg_offset];
	const char* total_tracks_string = argv[3 + arg_offset];

	const int track_number = atoi(track_number_string);
	const int total_tracks = atoi(total_tracks_string);

	if(track_number < 1 || track_number > total_tracks) {
		fprintf(stderr, "Invalid track_number!\n");
		return EXIT_FAILURE;
	}

	if(total_tracks < 1 || total_tracks > 99) {
		fprintf(stderr, "Invalid total_tracks!\n");
		return EXIT_FAILURE;
	}

#ifdef DEBUG
	printf("Reading %s\n", filename);
#endif

	SF_INFO sfinfo;
	sfinfo.channels = 0;
	sfinfo.format = 0;
	sfinfo.frames = 0;
	sfinfo.samplerate = 0;
	sfinfo.sections = 0;
	sfinfo.seekable = 0;

	SNDFILE* sndfile = sf_open(filename, SFM_READ, &sfinfo);

	if(sndfile == NULL) {
		fprintf(stderr, "sf_open failed! sf_error==%i\n", sf_error(NULL));
		return EXIT_FAILURE;
	}

	if(!check_fileformat(&sfinfo)) {
		fprintf(stderr, "check_fileformat failed!\n");
		sf_close(sndfile);
		return EXIT_FAILURE;
	}

	uint32_t* audio_data = load_full_audiodata(sndfile, &sfinfo);
	if(audio_data == NULL) {
		fprintf(stderr, "load_full_audiodata failed!\n");
		sf_close(sndfile);
		return EXIT_FAILURE;
	}

	const int checksum = use_v1 ?
			compute_v1_checksum(audio_data, get_full_audiodata_size(&sfinfo), track_number, total_tracks)
			: compute_v2_checksum(audio_data, get_full_audiodata_size(&sfinfo), track_number, total_tracks);

	printf("%08X\n", checksum);

	sf_close(sndfile);
	free(audio_data);

	return EXIT_SUCCESS;
}
