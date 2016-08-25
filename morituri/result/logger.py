import time
import hashlib

from morituri.common import common
from morituri.configure import configure
from morituri.result import result


class MorituriLogger(result.Logger):

    _accuratelyRipped = 0
    _inARDatabase = 0
    _errors = False

    def log(self, ripResult, epoch=time.time()):
        lines = self.logRip(ripResult, epoch=epoch)
        return "\n".join(lines)

    def logRip(self, ripResult, epoch):
        lines = []
        lines.append("Log created by: morituri %s" % configure.version)
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch)).strip()
        lines.append("Log creation date: %s" % date)
        lines.append("")

        lines.append("Ripping phase information:")
        lines.append("  Drive: %s%s (revision %s)" % (
            ripResult.vendor, ripResult.model, ripResult.release))
        defeat = "Unknown"
        if ripResult.cdparanoiaDefeatsCache is True:
            defeat = "Yes"
        elif ripResult.cdparanoiaDefeatsCache is False:
            defeat = "No"
        lines.append("  Defeat audio cache: %s" % defeat)
        lines.append("  Read offset correction: %+d" % ripResult.offset)
        # Currently unsupported by the official cdparanoia package
        over = "No"
        try:
            if ripResult.overread is True:
                over = "Yes"
        except NameError:
            pass
        lines.append("  Overread into lead-out: %s" % over)
        # Next one fully works only using the patched cdparanoia package
        # lines.append("Fill up missing offset samples with silence: Yes")
        lines.append("  Gap detection: cdrdao %s" % ripResult.cdrdaoVersion)
        lines.append("")

        lines.append("Encoding phase information:")
        lines.append("  Used output format: %s" % ripResult.profileName)
        lines.append("  GStreamer:")
        lines.append("    Pipeline: %s" % ripResult.profilePipeline)
        lines.append("    Version: %s" % ripResult.gstreamerVersion)
        lines.append("    Python version: %s" % ripResult.gstPythonVersion)
        lines.append("    Encoder plugin version: %s" %
                     ripResult.encoderVersion)
        lines.append("")

        lines.append("CD metadata:")
        lines.append("  Album: %s - %s" % (ripResult.artist, ripResult.title))
        lines.append("  CDDB Disc ID: %s" % ripResult. table.getCDDBDiscId())
        lines.append("  MusicBrainz Disc ID: %s" %
                     ripResult. table.getMusicBrainzDiscId())
        lines.append("  MusicBrainz lookup url: %s" %
                     ripResult. table.getMusicBrainzSubmitURL())
        lines.append("")

        lines.append("TOC:")
        table = ripResult.table
        htoa = None
        try:
            htoa = table.tracks[0].getIndex(0)
        except KeyError:
            pass
        if htoa and htoa.path:
            htoastart = htoa.absolute
            htoaend = table.getTrackEnd(0)
            htoalength = table.tracks[0].getIndex(1).absolute - htoastart
            lines.append("  00:")
            lines.append("    Start: %s" % common.framesToMSF(htoastart))
            lines.append("    Length: %s" % common.framesToMSF(htoalength))
            lines.append("    Start sector: %d" % htoastart)
            lines.append("    End sector: %d" % htoaend)
            lines.append("")
        for t in table.tracks:
            # FIXME: what happens to a track start over 60 minutes ?
            # Answer: tested empirically, everything seems OK
            start = t.getIndex(1).absolute
            length = table.getTrackLength(t.number)
            end = table.getTrackEnd(t.number)
            lines.append("  %02d:" % t.number)
            lines.append("    Start: %s" % common.framesToMSF(start))
            lines.append("    Length: %s" % common.framesToMSF(length))
            lines.append("    Start sector: %d" % start)
            lines.append("    End sector: %d" % end)
            lines.append("")

        lines.append("Tracks:")
        duration = 0.0
        for t in ripResult.tracks:
            if not t.filename:
                continue
            lines.extend(self.trackLog(t))
            lines.append("")
            duration += t.testduration + t.copyduration

        lines.append("Conclusive status report:")
        arHeading = "  AccurateRip summary:"
        if self._inARDatabase == 0:
            lines.append("%s None of the tracks are present in the "
                         "AccurateRip database" % arHeading)
        else:
            nonHTOA = len(ripResult.tracks)
            if ripResult.tracks[0].number == 0:
                nonHTOA -= 1
            if self._accuratelyRipped == 0:
                lines.append("%s No tracks could be verified as accurate "
                             "(you may have a different pressing from the "
                             "one(s) in the database)" % arHeading)
            elif self._accuratelyRipped < nonHTOA:
                accurateTracks = nonHTOA - self._accuratelyRipped
                lines.append("%s Some tracks could not be verified as "
                             "accurate (%d/%d got no match)" % (
                              arHeading, accurateTracks, nonHTOA))
            else:
                lines.append("%s All tracks accurately ripped" % arHeading)

        hsHeading = "  Health status:"
        if self._errors:
            lines.append("%s There were errors" % hsHeading)
        else:
            lines.append("%s No errors occurred" % hsHeading)
        lines.append("  EOF: End of status report")
        lines.append("")

        hasher = hashlib.sha256()
        hasher.update("\n".join(lines).encode("utf-8"))
        lines.append("SHA-256 hash: %s" % hasher.hexdigest().upper())
        lines.append("")
        return lines

    def trackLog(self, trackResult):
        lines = []
        lines.append("  %02d:" % trackResult.number)
        lines.append("    Filename: %s" % trackResult.filename)
        pregap = trackResult.pregap
        if pregap:
            lines.append("    Pre-gap length: %s" % common.framesToMSF(pregap))
        peak = trackResult.peak
        lines.append("    Peak level: %.6f %%" % peak)
        if trackResult.copyspeed:
            lines.append("    Extraction speed: %.1f X" % (
                trackResult.copyspeed))
        if trackResult.quality and trackResult.quality > 0.001:
            lines.append("    Track quality: %.2f %%" %
                         (trackResult.quality * 100.0, ))
        if trackResult.testcrc is not None:
            lines.append("    Test CRC: %08X" % trackResult.testcrc)
        if trackResult.copycrc is not None:
            lines.append("    Copy CRC: %08X" % trackResult.copycrc)
        if trackResult.accurip:
            lines.append("    AccurateRip V1:")
            self._inARDatabase += 1
            if trackResult.ARCRC == trackResult.ARDBCRC:
                lines.append("      Result: Found, exact match")
                self._accuratelyRipped += 1
            else:
                lines.append("      Result: Found, NO exact match")
            lines.append("      Confidence: %d" %
                         trackResult.ARDBConfidence)
            lines.append("      Local CRC: %08X" % trackResult.ARCRC)
            lines.append("      Remote CRC: %08X" % trackResult.ARDBCRC)
        elif trackResult.number != 0:
            lines.append("    AccurateRip V1:")
            lines.append("      Result: Track not present in "
                         "AccurateRip database")

        if trackResult.testcrc == trackResult.copycrc:
            lines.append("    Status: Copy OK")
        else:
            self._errors = True
            lines.append("    Status: Error, CRC mismatch")
        return lines
