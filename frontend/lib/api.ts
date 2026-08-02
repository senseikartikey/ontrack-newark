const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Line = { code: string; display_name: string };

export type LiveTrip = {
  trip_id: string;
  direction: string | null;
  stop_id: string;
  scheduled_time: string;
  delay_seconds: number | null;
};

export type LiveStatus = {
  line: string;
  as_of: string;
  trips: LiveTrip[];
};

export type PredictedRisk =
  | { line: string; status: "insufficient_data"; message: string }
  | {
      line: string;
      status: "ok";
      source: "statistical_baseline" | "ml_model";
      predicted_delay_seconds: number;
      risk_level: "low" | "medium" | "high";
      sample_size: number;
      computed_at: string;
      model_version?: string;
      mae_seconds?: number;
      baseline_mae_seconds?: number;
    };

export type Alert = {
  alert_id: string;
  line: string | null;
  header_text: string;
  url: string | null;
  active_from: string | null;
};

export type ScorecardWindow = { sample_size: number; on_time_pct: number | null };
export type Scorecard = {
  line: string;
  rolling_7_day: ScorecardWindow;
  rolling_30_day: ScorecardWindow;
};

export type Station = string;

// Track enrichment (backend/routers/stations.py, 2026-08-02): `track` is a
// best-effort match against NJT's own track_assignments data, only attempted
// for the 17 curated stations in config.TRACK_ASSIGNMENT_STATIONS, matched by
// nearest scheduled_time rather than a reliable train/trip ID (none exists --
// see that module's docstring). `track` is null in two genuinely different
// cases the UI should not conflate where avoidable:
//   - `track_match_type` absent/null entirely: no match was attempted or found
//     (station isn't one of the curated 17, or no track_assignments row was
//     close enough in time) -- the ordinary "we don't know" case.
//   - `track_match_type: "schedule_proximity"` present but `track` itself still
//     null: a plausible same-time TrackAssignment row was found (e.g. at New
//     York Penn Station, which NJT dispatches via Amtrak and has no early
//     track visibility for even in its own systems), so a match exists but
//     genuinely carries no track number.
// `track_match_time_gap_minutes` is how many minutes apart the matched
// TrackAssignment row's scheduled_time was from this departure's -- present
// only alongside a non-null `track_match_type`.
export type Departure = {
  trip_id: string;
  line: string;
  line_display_name: string;
  direction: string | null;
  scheduled_time: string;
  delay_seconds: number | null;
  status: "on_time" | "delayed" | "unknown";
  track: string | null;
  track_match_type: "schedule_proximity" | null;
  track_match_time_gap_minutes: number | null;
};

export type StationBoard = {
  station: string;
  as_of: string;
  departures: Departure[];
};

// Ordered upcoming-stop entry from GET /trips/{trip_id}/upcoming-stops. `scheduled_time`
// is a raw GTFS "HH:MM:SS" string (hours can exceed 24 for after-midnight service, so it's
// NOT a parseable ISO time on its own); `estimated_arrival` IS a full ISO datetime (the
// schedule combined with the trip's service-date midnight, offset by its current delay).
// `passed` is null when no usable scheduled time existed to compare against `as_of`.
export type UpcomingStop = {
  stop_sequence: number;
  stop_id: string;
  station_name: string | null;
  scheduled_time: string | null;
  estimated_arrival: string | null;
  passed: boolean | null;
};

// GET /trips/{trip_id}/upcoming-stops never fabricates an exact live join -- see
// backend/routers/trips.py's module docstring. `match_type` is currently always
// "schedule_proximity" (the live feed's trip_id and static GTFS's trip_id are
// unrelated ID spaces, empirically confirmed) and `match_time_gap_minutes` is how far
// off the matched static trip's own scheduled time is from the live trip's, so the UI
// can surface match quality honestly instead of implying a guaranteed-exact match.
export type UpcomingStops =
  | {
      trip_id: string;
      line: string;
      status: "insufficient_data";
      message: string;
    }
  | {
      trip_id: string;
      line: string;
      direction: string | null;
      status: "ok";
      match_type: "schedule_proximity";
      matched_static_trip_id: string;
      match_time_gap_minutes: number;
      current_delay_seconds: number | null;
      as_of: string;
      stops: UpcomingStop[];
    };

// Thrown by apiFetch instead of a plain Error so callers can branch on HTTP status --
// needed for GET /trips/{trip_id}/upcoming-stops, which uses a real 404 (not a
// status: "insufficient_data" body) to mean "this trip_id has no live data at all."
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new ApiError(res.status, `API request to ${path} failed with status ${res.status}`);
  }
  return res.json();
}

export function getLines(): Promise<{ lines: Line[] }> {
  return apiFetch("/lines");
}

export function getLiveStatus(lineCode: string): Promise<LiveStatus> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/live`);
}

export function getPredictedRisk(lineCode: string): Promise<PredictedRisk> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/predict`);
}

export function getScorecard(lineCode: string): Promise<Scorecard> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/scorecard`);
}

export function getAlerts(lineCode: string): Promise<{ alerts: Alert[] }> {
  return apiFetch(`/alerts?line=${encodeURIComponent(lineCode)}`);
}

export function getStations(): Promise<{ stations: Station[] }> {
  return apiFetch("/stations");
}

export function getStationBoard(stationName: string): Promise<StationBoard> {
  return apiFetch(`/stations/${encodeURIComponent(stationName)}/board`);
}

export function getUpcomingStops(tripId: string): Promise<UpcomingStops> {
  return apiFetch(`/trips/${encodeURIComponent(tripId)}/upcoming-stops`);
}

// One upcoming scheduled (static-timetable, not live) departure for a line at a
// Newark hub station, from GET /stations/{stop_id}/transfers.
export type TransferDeparture = {
  scheduled_time_of_day: string;
  headsign: string | null;
  minutes_until: number;
};

export type TransferLine = {
  line: string;
  line_display_name: string;
  distinct_scheduled_times: number;
  next_departures: TransferDeparture[];
};

// GET /stations/{stop_id}/transfers is built entirely from the static schedule
// (StopTime -> Trip -> Route), not the live feed -- `source` is always
// "static_schedule" and must be surfaced in the UI verbatim (see this project's
// honesty convention: never present a scheduled/approximate figure as live).
// `stop_id` is the static GTFS numeric stop_id (e.g. "107"), a different identifier
// space than /stations' live-feed station-name strings -- see
// backend/routers/stations.py's module docstring. As of the statewide widening
// (plan step 5, 2026-08-02) this works for ANY real static stop_id (231-row
// statewide `Stop` table), not just the original two Newark hubs -- existence is
// checked against that table directly, and a 404 means a genuinely unknown
// stop_id. Use `searchStations` below to resolve an arbitrary station name to its
// stop_id first.
export type StationTransfers = {
  stop_id: string;
  station_name: string;
  source: "static_schedule";
  note: string;
  as_of: string;
  lines: TransferLine[];
};

export function getStationTransfers(stopId: string): Promise<StationTransfers> {
  return apiFetch(`/stations/${encodeURIComponent(stopId)}/transfers`);
}

// GET /stations/static?q=<name> -- statewide, case-insensitive partial-match
// search over the static `Stop` table (231 rows, no line filter), capped at 20
// results server-side. This is the lookup that resolves an arbitrary station name
// to the numeric stop_id `getStationTransfers` needs, since that endpoint's
// identifier space has no other statewide discovery path (see
// backend/routers/stations.py's module docstring). An empty query or a query with
// zero matches both return 200 with an empty `stations` list -- never a 404, since
// there's nothing wrong with the request, the search just found nothing.
export type StationSearchResult = { stop_id: string; stop_name: string };

export type StationSearchResponse = {
  query: string;
  stations: StationSearchResult[];
};

export function searchStations(query: string): Promise<StationSearchResponse> {
  return apiFetch(`/stations/static?q=${encodeURIComponent(query)}`);
}

// GET /lines/{line}/data-confidence (docs/PRD-v2.md Phase 1's "data-confidence
// indicator" -- riders widely distrust NJ Transit's own live data, so this honestly
// flags when the underlying GTFS-RT feed itself looks unreliable, rather than
// synthesizing a vague trust score. See backend/routers/data_confidence.py's
// module docstring for the full rationale.
//
// `status` is one of three explicit states, and is deliberately NOT collapsed into
// a boolean "trustworthy y/n":
//   - "unknown": no recent live-feed activity for this line at all -- there isn't
//     enough current data to say anything about reliability. This is the expected,
//     non-alarming state during an ingestion outage (or between polls for a quiet
//     line) -- NOT the same claim as "the feed looks fine."
//   - "ok": recent polling exists and zero anomalies were recorded in the window.
//   - "issues_detected": recent polling exists and at least one anomaly was
//     recorded -- anomaly_counts/recent_anomalies give the specifics.
// All three states share the same field shape (no fields appear/disappear by
// status) -- this stays a flat type rather than a discriminated union, matching
// the actual response.
export type AnomalyType = "vanished_mid_route" | "stale_timestamp";

export type DataConfidenceAnomaly = {
  trip_id: string;
  anomaly_type: AnomalyType;
  detected_at: string;
  detail: string;
};

export type DataConfidence = {
  line: string;
  as_of: string;
  window_hours: number;
  last_poll_at: string | null;
  status: "unknown" | "ok" | "issues_detected";
  message: string;
  anomaly_counts: Record<AnomalyType, number>;
  total_anomalies: number;
  // Up to 5 most recent anomalies within the window -- only populated when
  // status is "issues_detected".
  recent_anomalies: DataConfidenceAnomaly[];
};

export function getDataConfidence(lineCode: string): Promise<DataConfidence> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/data-confidence`);
}

// GET /trips/{trip_id}/quiet-commute (docs/PRD-v2.md Phase 1's "Quiet Commute car
// lookup"). This is a rule-based best-effort inference from the trip's line +
// weekday peak-hour timing/direction -- NOT an official NJ Transit source, and NOT a
// lookup against a specific train's actual consist (no data source exists for that).
// `confidence` is always "best_effort" (no other value is currently returned) but is
// typed as a literal rather than widened to `string` so a caller can't accidentally
// treat this as a stronger claim than the backend makes. `disclaimer` must be
// surfaced in the UI verbatim per this project's honesty convention -- see
// backend/routers/trips.py's QUIET_COMMUTE_DISCLAIMER for the exact rider-facing text
// and the reasoning behind it. 404s under the same condition as /upcoming-stops (no
// live data at all for this trip_id).
export type QuietCommuteAssessment = {
  trip_id: string;
  line: string;
  direction: string | null;
  scheduled_time: string;
  likely_quiet_commute: boolean;
  confidence: "best_effort";
  reasoning: string;
  disclaimer: string;
};

export function getQuietCommute(tripId: string): Promise<QuietCommuteAssessment> {
  return apiFetch(`/trips/${encodeURIComponent(tripId)}/quiet-commute`);
}

// GET /stations/{station_code}/predicted-tracks (2026-08-02) -- historical-pattern
// track predictions for New York Penn Station, styled after third-party tools like
// Clever Commute / nypenn.live. `station_code` here is NJT RailData's own 2-character
// code (e.g. "NY" for New York Penn), a DIFFERENT identifier space than every other
// station type on this page (`Station`/live-feed name strings, or the static numeric
// `stop_id` StationTransfers uses) -- see backend/routers/stations.py's module
// docstring for the full station-identifier-space story.
//
// `confidence` is never fabricated: "insufficient_data" means no TrackPrediction row
// exists yet for that specific train_id (not "predicted no track") -- `predicted_track`
// is null in that case and the UI must not render a placeholder track number for it.
// "high" | "medium" | "low" are real predictions, each carrying `sample_size` (how many
// past departures the prediction is based on) and `top_track_share` (what fraction of
// those past departures used the predicted track) so a caller can show its own
// confidence detail rather than trusting the label alone.
//
// There is currently no way to distinguish a real *confirmed* official track from a
// predicted one in this response shape -- every non-null `predicted_track` here is
// necessarily a prediction, never official data (NY Penn is Amtrak-dispatched; neither
// NJT nor Amtrak publish early track assignments for it at all, confirmed empirically --
// see PredictedTracks.disclaimer). If a future backend change adds a real confirmed-track
// source, it will need a new field here (do not assume `predicted_track` alone could ever
// silently start meaning "confirmed").
export type TrackConfidence = "high" | "medium" | "low" | "insufficient_data";

export type PredictedTrackDeparture = {
  train_id: string;
  // NJT RailData's own free-text LINE field (e.g. "Northeast Corrdr") -- NOT this
  // codebase's own line codes ("NEC", "NJCL", etc.), so this must NOT be passed to
  // lib/lineColors' colorForLine (it would silently fail to match and fall back to
  // the "unknown line" gray for every real value). Displayed as plain text.
  line: string | null;
  destination: string | null;
  scheduled_time: string;
  predicted_track: string | null;
  confidence: TrackConfidence;
  sample_size: number;
  top_track_share: number | null;
};

export type PredictedTracks = {
  station_code: string;
  as_of: string;
  window_hours: number;
  // Full backend-authored disclaimer text -- must be surfaced somewhere in the UI
  // verbatim (this project's honesty convention, same as QUIET_COMMUTE_DISCLAIMER),
  // though not necessarily as the first thing a rider sees in full length.
  disclaimer: string;
  departures: PredictedTrackDeparture[];
};

export function getPredictedTracks(stationCode: string): Promise<PredictedTracks> {
  return apiFetch(`/stations/${encodeURIComponent(stationCode)}/predicted-tracks`);
}
