"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getPredictedTracks,
  type PredictedTrackDeparture,
  type PredictedTracks,
} from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";

// New York Penn Station is the only station this page is built for -- see
// backend/routers/stations.py's PREDICTED_TRACKS_DISCLAIMER: NY Penn is
// Amtrak-dispatched and has zero official early track visibility (unlike the 17
// NJT-operated stations enriched on /board), which is exactly why a
// historical-pattern prediction is the only thing worth showing here at all.
// Hardcoded rather than a station picker -- GET /stations/{code}/predicted-tracks
// technically accepts any station_code, but this feature is deliberately
// NY-Penn-only per project scope, not a statewide tool.
const STATION_CODE = "NY";
const STATION_LABEL = "New York Penn Station";

// Not a per-second live feed -- this is an upcoming-schedule list enriched with a
// precomputed prediction, so a slower poll than the 30s live board/dashboard views
// is appropriate. Matches /hub's own cadence for the same reason.
const REFRESH_INTERVAL_MS = 60_000;

// Color-coded confidence directly on the track number, black/plain for anything
// that isn't a real prediction -- the proven nypenn.live/Clever Commute pattern
// (confirmed against a real screenshot this session), built from this project's
// existing status tokens rather than a bespoke palette. "insufficient_data" is
// deliberately absent here: it never reaches this map (see TrackCell below).
const CONFIDENCE_COLOR: Record<"high" | "medium" | "low", string> = {
  high: "var(--status-good)",
  medium: "var(--status-warning)",
  low: "var(--status-critical)",
};

const CONFIDENCE_LABEL: Record<"high" | "medium" | "low", string> = {
  high: "high confidence",
  medium: "medium confidence",
  low: "low confidence",
};

function formatScheduledTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Isolated so a future "confirmed" track source (see lib/api.ts's
// PredictedTrackDeparture docstring -- the current API has no way to distinguish
// a real confirmed track from a predicted one) can add a third branch here --
// unmarked, no asterisk, plain text color, matching nypenn.live's own convention
// for official data -- without reworking the two branches below.
function TrackCell({ dep }: { dep: PredictedTrackDeparture }) {
  // Honest empty state: no TrackPrediction row exists for this train yet. No
  // placeholder track number is ever shown here -- "insufficient_data" means
  // "we don't know," not "no track."
  if (dep.confidence === "insufficient_data" || dep.predicted_track === null) {
    return (
      <span className="font-mono text-xs text-[var(--text-muted)]">no prediction yet</span>
    );
  }

  const color = CONFIDENCE_COLOR[dep.confidence];
  const sharePct =
    dep.top_track_share !== null ? Math.round(dep.top_track_share * 100) : null;
  const title =
    sharePct !== null
      ? `Predicted from ${dep.sample_size} past departures of this train -- it used track ${dep.predicted_track} ${sharePct}% of the time.`
      : `Predicted from ${dep.sample_size} past departures of this train.`;

  return (
    <span className="inline-flex items-center gap-2" title={title}>
      <span
        className="inline-flex items-center font-mono text-sm font-bold px-2 py-0.5 rounded border"
        style={{ borderColor: color, color }}
      >
        {dep.predicted_track}
        {/* Marker distinguishing a predicted track from a confirmed one --
            same "*" convention nypenn.live itself uses. */}
        <span aria-hidden="true" className="ml-0.5">
          *
        </span>
      </span>
      <span
        className="font-mono text-[10px] uppercase tracking-wide whitespace-nowrap"
        style={{ color }}
      >
        {CONFIDENCE_LABEL[dep.confidence]}
      </span>
    </span>
  );
}

export default function NyPennPage() {
  const [data, setData] = useState<PredictedTracks | null>(null);
  const [error, setError] = useState(false);
  const [disclaimerExpanded, setDisclaimerExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    function load() {
      getPredictedTracks(STATION_CODE)
        .then((result) => {
          if (!cancelled) {
            setData(result);
            setError(false);
          }
        })
        .catch(() => {
          if (!cancelled) setError(true);
        });
    }

    load();
    const interval = setInterval(load, REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="font-display font-bold text-lg tracking-tight">
              OnTrack
            </Link>
            <nav className="flex flex-wrap items-center gap-4 font-mono text-xs">
              <Link
                href="/dashboard"
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                Line dashboard
              </Link>
              <Link
                href="/board"
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                Live board
              </Link>
              <Link
                href="/hub"
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                Transfers
              </Link>
              <span className="text-[var(--text-primary)] border-b border-[var(--accent)] pb-0.5">
                NY Penn tracks
              </span>
            </nav>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 w-full flex-1">
        <div className="mb-6">
          <h1 className="font-display font-bold text-2xl tracking-tight">
            {STATION_LABEL} — predicted tracks
          </h1>
          <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-xl">
            NY Penn is Amtrak-dispatched, so neither NJ Transit nor Amtrak publish
            early track assignments there. This estimates a likely track from each
            train&apos;s own history — the same approach third-party tools like
            Clever Commute and nypenn.live use, never an official source.
          </p>
        </div>

        {error && (
          <p className="font-mono text-sm text-[var(--status-warning)] mb-6">
            We can&apos;t reach live data right now. Please check back in a moment.
          </p>
        )}

        {/* Disclaimer -- one clear line up front, full backend-authored text
            available on demand. Same expand/collapse convention as the trip
            companion page's "why?" toggle, reused deliberately rather than
            inventing a new disclosure pattern. */}
        {!error && (
          <div className="mb-8 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 max-w-2xl">
            <p className="font-mono text-xs text-[var(--text-secondary)] leading-relaxed">
              <span className="text-[var(--status-warning)] font-semibold">
                Best-effort estimate, not an official source.
              </span>{" "}
              <button
                type="button"
                onClick={() => setDisclaimerExpanded((e) => !e)}
                aria-expanded={disclaimerExpanded}
                className="text-[var(--accent)] hover:underline"
              >
                full disclaimer{disclaimerExpanded ? " ▲" : " ▼"}
              </button>
            </p>
            {disclaimerExpanded && data && (
              <p className="mt-2 text-[var(--text-secondary)] text-xs normal-case leading-relaxed">
                {data.disclaimer}
              </p>
            )}
          </div>
        )}

        {!error && data === null && (
          <p className="font-mono text-sm text-[var(--text-secondary)] mb-8">loading…</p>
        )}

        {!error && data !== null && (
          <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between flex-wrap gap-2">
              <h2 className="font-display font-semibold">Upcoming departures</h2>
              <span className="font-mono text-xs text-[var(--text-muted)]">
                next {data.window_hours}h · refreshes every {REFRESH_INTERVAL_MS / 1000}s
              </span>
            </div>

            {data.departures.length === 0 && (
              <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
                Nothing on file for {STATION_LABEL} in the next {data.window_hours}{" "}
                hours yet. This view depends on NJ Transit&apos;s train-schedule data
                having been polled ahead of time — check back soon.
              </p>
            )}

            {data.departures.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--text-muted)] font-mono text-xs">
                      <th className="px-5 py-2 font-normal">Train</th>
                      <th className="px-5 py-2 font-normal">Line</th>
                      <th className="px-5 py-2 font-normal">Destination</th>
                      <th className="px-5 py-2 font-normal">Scheduled</th>
                      <th className="px-5 py-2 font-normal">Track</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.departures.map((dep) => (
                      <tr
                        key={`${dep.train_id}-${dep.scheduled_time}`}
                        className="border-t border-[var(--border)]"
                      >
                        <td className="px-5 py-2 font-mono text-xs">{dep.train_id}</td>
                        {/* dep.line is NJT RailData's own free-text field, a
                            different identifier space than this app's line codes
                            (see lib/api.ts) -- shown as plain text, never colored
                            via colorForLine (it wouldn't match anything real). */}
                        <td className="px-5 py-2 text-[var(--text-secondary)]">
                          {dep.line ?? "—"}
                        </td>
                        <td className="px-5 py-2 text-[var(--text-secondary)]">
                          {dep.destination ?? "—"}
                        </td>
                        <td className="px-5 py-2 font-mono text-xs text-[var(--text-secondary)]">
                          {formatScheduledTime(dep.scheduled_time)}
                        </td>
                        <td className="px-5 py-2">
                          <TrackCell dep={dep} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
