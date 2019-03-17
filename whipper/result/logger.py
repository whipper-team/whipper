import time
import hashlib

import whipper
import yaml

from whipper.common import common
from whipper.result import result


class WhipperLogger(result.Logger):

    _accuratelyRipped = 0
    _inARDatabase = 0
    _errors = False

    def log(self, ripResult, epoch=time.time()):
        """Returns big str: logfile joined text lines"""

        riplog = self.logRip(ripResult, epoch=epoch)
        return yaml.safe_dump(riplog)

    def logRip(self, ripResult, epoch):
        """Returns logfile lines list"""

        # Ripper version
        logger_name = "whipper %s (internal logger)" % whipper.__version__

        # Technical settings
        drive = "%s%s (revision %s)" % (
            ripResult.vendor, ripResult.model, ripResult.release)
        engine = "cdparanoia %s" % ripResult.cdparanoiaVersion

        # Can CD drive cache be defeated?
        cache_defeat = "Unknown"
        if ripResult.cdparanoiaDefeatsCache:
            cache_defeat = "Yes"
        elif ripResult.cdparanoiaDefeatsCache is not None:
            cache_defeat = "No"

        # Overread is currently unsupported by the official cdparanoia package
        # Only implemented in whipper (ripResult.overread)
        overread = "Yes" if ripResult.overread else "No"

        riplog = {
            "Log created by": logger_name,
            "Log creation date": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                               time.gmtime(epoch)).strip(),
            # Rip technical settings
            "Ripping phase information": {
                "Drive": drive,
                "Extraction engine": engine,
                "Defeat audio cache": cache_defeat,
                "Read offset correction": ripResult.offset,
                "Overread into lead-out": overread,
                # Fully works only using patched cdparanoia package
                # "Fill up missing offset samples with silence": "Yes"
                "Gap detection": "cdrdao %s" % ripResult.cdrdaoVersion,
                "CD-R detected": "Yes" if ripResult.isCdr else "No",
            },
            "CD metadata": {
                "Release": "%s - %s" % (ripResult.artist, ripResult.title),
                "CDDB Disc ID": ripResult.table.getCDDBDiscId(),
                "MusicBrainz Disc ID": ripResult.table.getMusicBrainzDiscId(),
                "MusicBrainz lookup url":
                    ripResult.table.getMusicBrainzSubmitURL(),
            },
            "TOC": {},
            "Tracks": {},
            "Conclusive status report": {
                "AccurateRip summary": "",
                "Health status": "",
                "EOF": "End of status report",
            },
        }

        # TOC section
        table = ripResult.table

        # Test for HTOA presence
        htoa = None
        try:
            htoa = table.tracks[0].getIndex(0)
        except KeyError:
            pass

        # If True, include HTOA line into log's TOC
        if htoa and htoa.path:
            htoastart = htoa.absolute
            htoaend = table.getTrackEnd(0)
            htoalength = table.tracks[0].getIndex(1).absolute - htoastart
            riplog["TOC"][0] = {
                "Start": common.framesToMSF(htoastart),
                "Length": common.framesToMSF(htoalength),
                "Start sector": htoastart,
                "End sector": htoaend,
            }

        # For every track include information in the TOC
        for t in table.tracks:
            start = t.getIndex(1).absolute
            length = table.getTrackLength(t.number)
            end = table.getTrackEnd(t.number)
            riplog["TOC"][t.number] = {
                "Start": common.framesToMSF(start),
                "Length": common.framesToMSF(length),
                "Start sector": start,
                "End sector": end,
            }

        # Tracks section
        duration = 0.0
        for t in ripResult.tracks:
            if not t.filename:
                continue
            track_log, ARDB_entry, ARDB_match = self.trackLog(t)
            self._inARDatabase += int(ARDB_entry)
            self._accuratelyRipped += int(ARDB_match)
            riplog["Tracks"].update(track_log)
            duration += t.testduration + t.copyduration

        # Status report
        if self._inARDatabase == 0:
            ar_summary = ("None of the tracks are present in the "
                          "AccurateRip database")
        else:
            nonHTOA = len(ripResult.tracks)
            if ripResult.tracks[0].number == 0:
                nonHTOA -= 1
            if self._accuratelyRipped == 0:
                ar_summary = ("No tracks could be verified as accurate "
                              "(you may have a different pressing from the "
                              "one(s) in the database)")
            elif self._accuratelyRipped < nonHTOA:
                accurateTracks = nonHTOA - self._accuratelyRipped
                ar_summary = ("Some tracks could not be verified as accurate "
                              "(%d/%d got no match)") % (
                                 accurateTracks, nonHTOA)
            else:
                ar_summary = "All tracks accurately ripped"
        riplog["Conclusive status report"]["AccurateRip summary"] = ar_summary

        if self._errors:
            riplog["Health status"] = "There were errors"
        else:
            riplog["Health status"] = "No errors occurred"

        # Log hash
        loghash = hashlib.sha256(yaml.safe_dump(riplog))
        riplog["SHA-256 hash"] = loghash.hexdigest().upper()
        return riplog

    def trackLog(self, trackResult):
        """Returns Tracks section lines: data picked from trackResult"""

        # Track number
        n = trackResult.number
        track_log = {n: {}}

        # Filename (including path) of ripped track
        track_log[n]["Filename"] = trackResult.filename

        # Pre-gap length
        pregap = trackResult.pregap
        if pregap:
            track_log[n]["Pre-gap length"] = common.framesToMSF(pregap)

        # Peak level
        track_log[n]["Peak level"] = "%.6f" % (trackResult.peak / 32768.0)

        # Pre-emphasis status
        # Only implemented in whipper (trackResult.pre_emphasis)
        pre_emphasis = "Yes" if trackResult.pre_emphasis else "No"
        track_log[n]["Pre-emphasis"] = pre_emphasis

        # Extraction speed
        if trackResult.copyspeed:
            track_log[n]["Extraction speed"] = "%.1f X" % (
                trackResult.copyspeed)

        # Extraction quality
        if trackResult.quality and trackResult.quality > 0.001:
            track_log[n]["Extraction quality"] = "%.2f %%" % (
                trackResult.quality * 100.0)

        # Ripper Test CRC
        if trackResult.testcrc is not None:
            track_log[n]["Test CRC"] = "%08X" % trackResult.testcrc

        # Ripper Copy CRC
        if trackResult.copycrc is not None:
            track_log[n]["Copy CRC"] = "%08X" % trackResult.copycrc

        # AccurateRip track status
        ARDB_entry = 0
        ARDB_match = 0
        for v in ("v1", "v2"):
            if trackResult.AR[v]["DBCRC"]:
                ar_log = {}
                ARDB_entry += 1
                if trackResult.AR[v]["CRC"] == trackResult.AR[v]["DBCRC"]:
                    ar_log["Result"] = "Found, exact match"
                    ARDB_match += 1
                else:
                    ar_log["Result"] = "Found, NO exact match"
                ar_log["Confidence"] = trackResult.AR[v]["DBConfidence"]
                ar_log["Local CRC"] = trackResult.AR[v]["CRC"].upper()
                ar_log["Remote CRC"] = trackResult.AR[v]["DBCRC"].upper()
                track_log[n]["AccurateRip %s" % v] = ar_log
            elif trackResult.number != 0:
                track_log[n]["AccurateRip %s" % v] = {
                    "Result": "Track not present in AccurateRip database",
                }

        # Check if Test & Copy CRCs are equal
        if trackResult.testcrc == trackResult.copycrc:
            track_log[n]["Status"] = "Copy OK"
        else:
            self._errors = True
            track_log[n]["Status"] = "Error, CRC mismatch"
        return track_log, bool(ARDB_entry), bool(ARDB_match)
