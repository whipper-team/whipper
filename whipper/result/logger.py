import time
import hashlib
import re
from ruamel.yaml.comments import CommentedMap as OrderedDict

import whipper

from whipper.common import common
from whipper.common.yaml import YAML
from whipper.program.cdparanoia import classify_cdparanoia_events
from whipper.result import result


class WhipperLogger(result.Logger):

    _accuratelyRipped = 0
    _inARDatabase = 0
    _errors = False
    _skippedTracks = False
    _cdparanoiaSevere = False
    _cdparanoiaCorrections = False
    _cdparanoiaLossyNames = None
    _cdparanoiaCorrectionCount = 0
    _cdparanoiaSevereCount = 0

    def log(self, ripResult, epoch=time.time()):
        """Return logfile as string."""
        return self.logRip(ripResult, epoch)

    def _reset_counters(self):
        self._accuratelyRipped = 0
        self._inARDatabase = 0
        self._errors = False
        self._skippedTracks = False
        self._cdparanoiaSevere = False
        self._cdparanoiaCorrections = False
        self._cdparanoiaLossyNames = set()
        self._cdparanoiaCorrectionCount = 0
        self._cdparanoiaSevereCount = 0

    @staticmethod
    def _cdparanoia_health_label(severe, corrections, lossy_names):
        """
        Human-readable cdparanoia health for the status report (#294).

        * ``clean`` — no non-routine callbacks
        * ``corrections only`` — re-reads/patches; usually not lossy
        * ``severe recoverable errors`` — transport/cache errors that
          paranoia may have corrected (progress bar 'e')
        * ``definitely lossy (uncorrected/skipped): …`` — skip
          (progress bar 'V'); CRC match does not prove
          the audio is correct
        """
        if lossy_names:
            return "definitely lossy (uncorrected/skipped): %s" % (
                ', '.join(lossy_names),)
        if severe:
            return ("severe recoverable errors "
                    "(read/cache; recovery unverified; "
                    "verify against AccurateRip)")
        if corrections:
            return "corrections only"
        return "clean"

    def logRip(self, ripResult, epoch):
        """Return logfile as list of lines."""
        self._reset_counters()
        riplog = OrderedDict()

        # Ripper version
        riplog["Log created by"] = "whipper %s (internal logger)" % (
            whipper.__version__)

        # Rip date
        date = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch)).strip()
        riplog["Log creation date"] = date

        # Rip technical settings
        data = OrderedDict()

        data["Drive"] = "%s%s (revision %s)" % (
            ripResult.vendor, ripResult.model, ripResult.release)
        data["Extraction engine"] = "cdparanoia %s" % (
            ripResult.cdparanoiaVersion)
        data["Defeat audio cache"] = ripResult.cdparanoiaDefeatsCache
        data["Read offset correction"] = ripResult.offset

        # Currently unsupported by the official cdparanoia package
        # Only implemented in whipper (ripResult.overread)
        data["Overread into lead-out"] = True if ripResult.overread else False
        # Next one fully works only using the patched cdparanoia package
        # lines.append("Fill up missing offset samples with silence: true")
        data["Gap detection"] = "cdrdao %s" % ripResult.cdrdaoVersion

        data["CD-R detected"] = ripResult.isCdr
        riplog["Ripping phase information"] = data

        # CD metadata
        release = OrderedDict()
        release["Artist"] = ripResult.artist
        release["Title"] = ripResult.title
        data = OrderedDict()
        data["Release"] = release
        data["CDDB Disc ID"] = ripResult.table.getCDDBDiscId()
        data["MusicBrainz Disc ID"] = ripResult.table.getMusicBrainzDiscId()
        data["MusicBrainz lookup URL"] = (
            ripResult.table.getMusicBrainzSubmitURL())
        if ripResult.metadata:
            data["MusicBrainz Release URL"] = ripResult.metadata.url
        riplog["CD metadata"] = data

        # TOC section
        data = OrderedDict()
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
            track = OrderedDict()
            track["Start"] = common.framesToMSF(htoastart)
            track["Length"] = common.framesToMSF(htoalength)
            track["Start sector"] = htoastart
            track["End sector"] = htoaend
            data[0] = track

        # For every track include information in the TOC
        for t in table.tracks:
            start = t.getIndex(1).absolute
            length = table.getTrackLength(t.number)
            end = table.getTrackEnd(t.number)
            track = OrderedDict()
            track["Start"] = common.framesToMSF(start)
            track["Length"] = common.framesToMSF(length)
            track["Start sector"] = start
            track["End sector"] = end
            data[t.number] = track
        riplog["TOC"] = data

        # Tracks section
        data = OrderedDict()
        duration = 0.0
        for t in ripResult.tracks:
            if not t.filename:
                continue
            track_dict, ARDB_entry, ARDB_match = self.trackLog(t)
            self._inARDatabase += int(ARDB_entry)
            self._accuratelyRipped += int(ARDB_match)
            data[t.number] = track_dict
            duration += t.testduration + t.copyduration
        riplog["Tracks"] = data

        # Status report
        data = OrderedDict()
        if self._inARDatabase == 0:
            message = ("None of the tracks are present in the "
                       "AccurateRip database")
        else:
            nonHTOA = len(ripResult.tracks)
            if ripResult.tracks[0].number == 0:
                nonHTOA -= 1
            if self._accuratelyRipped == 0:
                message = ("No tracks could be verified as accurate "
                           "(you may have a different pressing from the "
                           "one(s) in the database)")
            elif self._accuratelyRipped < nonHTOA:
                accurateTracks = nonHTOA - self._accuratelyRipped
                message = ("Some tracks could not be verified as "
                           "accurate (%d/%d got no match)") % (
                        accurateTracks, nonHTOA)
            else:
                message = "All tracks accurately ripped"
        data["AccurateRip summary"] = message

        # Issue #294: make the cdparanoia-error health explicit so readers
        # can tell "CRCs match but sectors may be wrong" from a clean rip.
        data["cdparanoia health"] = self._cdparanoia_health_label(
            self._cdparanoiaSevereCount,
            self._cdparanoiaCorrectionCount,
            sorted(self._cdparanoiaLossyNames or []),
        )

        # Health status (issue #294), using libcdio-paranoia semantics:
        # - CRC mismatch always means errors.
        # - Definitely-lossy events (skip;
        #   progress bar 'V') can be wrong even when test and copy CRCs
        #   match, because both passes may agree on the same bad fill.
        #   Treat as errors.
        # - Potentially recoverable events (SCSI / transport / cache;
        #   progress bar 'e') still force "There were errors" so archival
        #   users notice; AccurateRip can confirm the result.
        # - Corrections-only rips usually recover; keep "No errors occurred"
        #   for compatibility. Event counts and suspicious positions remain
        #   on each track; see also "cdparanoia health" above.
        if self._errors or self._cdparanoiaSevere:
            message = "There were errors"
        elif self._skippedTracks:
            message = "Some tracks were not ripped (skipped)"
        else:
            message = "No errors occurred"
        data["Health status"] = message
        data["EOF"] = "End of status report"
        riplog["Conclusive status report"] = data

        yaml = YAML(
            typ="rt",
            pure=True
        )
        riplog = yaml.dump(
            riplog
        )
        # Add a newline after the "Log creation date" line
        riplog = re.sub(
            r'^(Log creation date: .*)$',
            "\\1\n",
            riplog,
            flags=re.MULTILINE
        )
        # Add a newline after a dictionary ends and returns to top-level
        riplog = re.sub(
            r"^(\s{2})([^\n]*)\n([A-Z][^\n]+)",
            "\\1\\2\n\n\\3",
            riplog,
            flags=re.MULTILINE
        )
        # Add a newline after a track closes
        riplog = re.sub(
            r"^(\s{4}[^\n]*)\n(\s{2}[0-9]+)",
            "\\1\n\n\\2",
            riplog,
            flags=re.MULTILINE
        )
        # Remove single quotes around the "Log creation date" value
        riplog = re.sub(
            r"^(Log creation date: )'(.*)'",
            "\\1\\2",
            riplog,
            flags=re.MULTILINE
        )

        # Log hash
        hasher = hashlib.sha256()
        hasher.update(riplog.encode("utf-8"))
        riplog += "\nSHA-256 hash: %s\n" % hasher.hexdigest().upper()
        return riplog

    def trackLog(self, trackResult):
        """Return Tracks section lines: data picked from trackResult."""
        track = OrderedDict()

        # Filename (including path) of ripped track
        track["Filename"] = trackResult.filename

        # Pre-gap length
        pregap = trackResult.pregap
        if pregap:
            track["Pre-gap length"] = common.framesToMSF(pregap)

        # Peak level
        peak = trackResult.peak / 32768.0
        track["Peak level"] = float("%.6f" % peak)

        # Pre-emphasis status
        # Only implemented in whipper (trackResult.pre_emphasis)
        track["Pre-emphasis"] = trackResult.pre_emphasis

        # Extraction speed
        if trackResult.copyspeed:
            track["Extraction speed"] = "%.1f X" % trackResult.copyspeed

        # Extraction quality
        if trackResult.quality and trackResult.quality > 0.001:
            track["Extraction quality"] = "%.2f %%" % (
                trackResult.quality * 100.0, )

        # Non-routine cdparanoia callbacks (issue #88 / #294 / #492)
        events = trackResult.cdparanoiaEvents or {}
        severe, corrections, lossy_names = classify_cdparanoia_events(events)
        # New results preserve per-pass, sector-aware accounting. Older saved
        # results only have raw counts, so retain the classifier lower bound.
        recorded_severe = getattr(trackResult, 'cdparanoiaSevereErrors', None)
        if recorded_severe is not None:
            severe = recorded_severe
        nonzero = OrderedDict()
        for name in sorted(events):
            if events[name]:
                nonzero[name] = events[name]
        if nonzero:
            track["cdparanoia events"] = nonzero
            self._cdparanoiaSevereCount += severe
            self._cdparanoiaCorrectionCount += corrections
            if severe:
                self._cdparanoiaSevere = True
                if self._cdparanoiaLossyNames is None:
                    self._cdparanoiaLossyNames = set()
                self._cdparanoiaLossyNames.update(lossy_names)
            if corrections:
                self._cdparanoiaCorrections = True

        # EAC-style suspicious positions
        positions = trackResult.suspiciousPositions or []
        if positions:
            track["Suspicious positions"] = [
                "%s - %s" % (common.framesToMSF(start),
                             common.framesToMSF(end))
                for start, end in positions
            ]

        # Ripper Test CRC
        if trackResult.testcrc is not None:
            track["Test CRC"] = "%08X" % trackResult.testcrc

        # Ripper Copy CRC
        if trackResult.copycrc is not None:
            track["Copy CRC"] = "%08X" % trackResult.copycrc

        # AccurateRip track status
        ARDB_entry = 0
        ARDB_match = 0
        for v in ("v1", "v2"):
            data = OrderedDict()
            if trackResult.AR[v]["DBCRC"]:
                ARDB_entry += 1
                if trackResult.AR[v]["CRC"] == trackResult.AR[v]["DBCRC"]:
                    data["Result"] = "Found, exact match"
                    ARDB_match += 1
                else:
                    data["Result"] = "Found, NO exact match"
                data["Confidence"] = trackResult.AR[v]["DBConfidence"]
                data["Local CRC"] = trackResult.AR[v]["CRC"].upper()
                data["Remote CRC"] = trackResult.AR[v]["DBCRC"].upper()
            elif trackResult.number != 0:
                data["Result"] = "Track not present in AccurateRip database"
            track["AccurateRip %s" % v] = data

        # Check if track has been skipped
        if trackResult.skipped:
            track["Status"] = "Track not ripped (skipped)"
            self._skippedTracks = True
        # Check if Test & Copy CRCs are equal
        elif trackResult.testcrc == trackResult.copycrc:
            if lossy_names:
                track["Status"] = (
                    "Copy OK (WARNING: uncorrected/skipped sectors: %s)" %
                    ', '.join(lossy_names))
            elif severe:
                track["Status"] = (
                    "Copy OK (cdparanoia reported severe recoverable "
                    "errors; recovery unverified)")
            else:
                track["Status"] = "Copy OK"
        else:
            self._errors = True
            track["Status"] = "Error, CRC mismatch"
        return track, bool(ARDB_entry), bool(ARDB_match)
