"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ApiError,
  getLines,
  getQuietCommute,
  getUpcomingStops,
  type QuietCommuteAssessment,
  type UpcomingStops,
} from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import { colorForLine } from "@/lib/lineColors";

// Raw GTFS "HH:MM:SS" string -- hours can exceed 24 for after-midnight service, so
// this is NOT a parseable ISO time on its own (see lib/api.ts's UpcomingStop docstring).
function formatScheduledTime(raw: string | null): string {
  if (!raw) return "—";
  const parts = raw.split(":");
  if (parts.length !== 3) return raw;
  const h = parseInt(parts[0], 10);
  const m = parseInt(parts[1], 10);
  if (Number.isNaN(h) || Number.isNaN(m)) return raw;
  const nextDay = h >= 24;
  const d = new Date();
  d.setHours(h % 24, m, 0, 0);
  const formatted = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  return nextDay ? `${formatted} (+1d)` : formatted;
}

function formatEstimatedArrival(raw: string | null): string {
  if (!raw) return "—";
  return new Date(raw).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDelay(seconds: number | null) {
  if (seconds === null) return { text: "unknown", color: "var(--text-muted)" };
  if (seconds <= 60) return { text: "on time", color: "var(--status-good)" };
  const minutes = Math.round(seconds / 60);
  if (seconds <= 300) return { text: `+${minutes} min`, color: "var(--status-warning)" };
  return { text: `+${minutes} min`, color: "var(--status-critical)" };
}

export default function TripCompanionPage() {
  const params = useParams<{ tripId: string }>();
  const tripId = decodeURIComponent(params.tripId ?? "");

  const [data, setData] = useState<UpcomingStops | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false);

  // Line code -> display name, so the page header can read like "Northeast
  // Corridor" instead of the raw line code. Same "fetch once on mount" pattern
  // as the dashboard's getLines() call; failure just leaves this empty and the
  // header below falls back to the raw code, which is still readable.
  const [lineDisplayNames, setLineDisplayNames] = useState<Record<string, string>>({});
  useEffect(() => {
    let cancelled = false;
    getLines()
      .then(({ lines }) => {
        if (cancelled) return;
        setLineDisplayNames(Object.fromEntries(lines.map((l) => [l.code, l.display_name])));
      })
      .catch(() => {
        // Non-critical -- header falls back to the raw line code.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Expand/collapse for the consolidated "why" technical detail below (match
  // quality + Quiet Commute reasoning) -- same interaction pattern as
  // DataConfidenceIndicator's anomaly-detail disclosure, reused deliberately
  // rather than inventing a second pattern on this page.
  const [detailsExpanded, setDetailsExpanded] = useState(false);

  // Quiet Commute lookup (docs/PRD-v2.md Phase 1) -- a best-effort rule-based
  // inference, fetched independently of the stop list. Fetched once (not on the
  // 30s poll interval below): it's derived from the trip's line/direction/scheduled
  // time, none of which change mid-trip, so re-polling it would just be a wasted
  // request. Any failure (404 for an unknown trip, or any other error) just leaves
  // this null and no badge renders -- same "don't show a separate error UI" handling
  // as the rest of this page for a trip that can't be found.
  const [quietCommute, setQuietCommute] = useState<QuietCommuteAssessment | null>(null);

  useEffect(() => {
    if (!tripId) return;
    let cancelled = false;

    function load() {
      getUpcomingStops(tripId)
        .then((result) => {
          if (cancelled) return;
          setData(result);
          setNotFound(false);
          setError(false);
        })
        .catch((err) => {
          if (cancelled) return;
          if (err instanceof ApiError && err.status === 404) {
            setNotFound(true);
            setError(false);
          } else {
            setError(true);
          }
        });
    }

    load();
    // Same 30s poll interval as the dashboard/board live views -- a mid-trip rider
    // watching this screen wants it to stay current without a manual refresh.
    const interval = setInterval(load, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [tripId]);

  useEffect(() => {
    if (!tripId) return;
    let cancelled = false;
    getQuietCommute(tripId)
      .then((result) => {
        if (!cancelled) setQuietCommute(result);
      })
      .catch(() => {
        if (!cancelled) setQuietCommute(null);
      });
    return () => {
      cancelled = true;
    };
  }, [tripId]);

  const lineColor = data ? colorForLine(data.line) : "var(--text-muted)";
  const nextStopIndex =
    data?.status === "ok" ? data.stops.findIndex((s) => s.passed === false) : -1;

  // Readable trip header ("Northeast Corridor · Westbound to Trenton") instead of
  // the raw internal trip_id, matching how the board/dashboard already present a
  // trip (line identity + direction). Destination is derived from this trip's own
  // final scheduled stop, since the API doesn't separately expose a headsign.
  const destination =
    data?.status === "ok" && data.stops.length > 0
      ? data.stops[data.stops.length - 1].station_name
      : null;
  const headerLine =
    data?.status === "ok" ? lineDisplayNames[data.line] ?? data.line : null;
  const headerLabel = headerLine
    ? [headerLine, data?.status === "ok" ? data.direction : null].filter(Boolean).join(" · ") +
      (destination ? ` to ${destination}` : "")
    : "Trip details";

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="font-display font-bold text-lg tracking-tight">
              OnTrack
            </Link>
            <nav className="flex items-center gap-4 font-mono text-xs">
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
                On this train
              </span>
              <Link
                href="/ny-penn"
                className="text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
              >
                NY Penn tracks
              </Link>
            </nav>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10 w-full flex-1">
        <div className="mb-8">
          <p className="font-mono text-xs text-[var(--text-muted)] mb-2">{headerLabel}</p>
          <h1 className="font-display font-bold text-2xl tracking-tight">
            Upcoming stops
          </h1>
          <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-xl">
            The ordered stop list for this train, so you can see what&apos;s coming
            next without hunting through NJ Transit&apos;s own app.
          </p>
        </div>

        {error && (
          <p className="font-mono text-sm text-[var(--status-warning)] mb-6">
            We can&apos;t reach live data right now. Please check back in a moment.
          </p>
        )}

        {!error && notFound && (
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-8">
            <p className="text-[var(--text-secondary)] text-sm max-w-md">
              No live data found for trip <code className="font-mono text-xs">{tripId}</code>.
              It may have already completed its run, not be currently active, or the
              trip ID may be wrong — this view only works for trips with at least one
              recent reading. Try selecting a trip from the{" "}
              <Link href="/dashboard" className="underline hover:text-[var(--text-primary)]">
                line dashboard
              </Link>
              {" "}or{" "}
              <Link href="/board" className="underline hover:text-[var(--text-primary)]">
                live board
              </Link>
              .
            </p>
          </div>
        )}

        {!error && !notFound && data === null && (
          <p className="font-mono text-sm text-[var(--text-secondary)] mb-8">loading…</p>
        )}

        {!error && !notFound && data?.status === "insufficient_data" && (
          <div className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-8">
            <p className="text-[var(--text-secondary)] text-sm max-w-md">{data.message}</p>
          </div>
        )}

        {!error && !notFound && data?.status === "ok" && (
          <>
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <span
                className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{ background: `${lineColor}22`, color: lineColor }}
              >
                <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: lineColor }} />
                {data.line}
              </span>
              {data.direction && (
                <span className="font-mono text-xs text-[var(--text-secondary)]">{data.direction}</span>
              )}
              {(() => {
                const delay = formatDelay(data.current_delay_seconds);
                return (
                  <span className="font-mono text-xs" style={{ color: delay.color }}>
                    current delay: {delay.text}
                  </span>
                );
              })()}
              {quietCommute && (
                <span
                  className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold px-2.5 py-1 rounded-full"
                  style={
                    quietCommute.likely_quiet_commute
                      ? { background: "var(--status-good)22", color: "var(--status-good)" }
                      : { color: "var(--text-muted)", border: "1px solid var(--border)" }
                  }
                >
                  <span
                    className="inline-block w-1.5 h-1.5 rounded-full"
                    style={{
                      background: quietCommute.likely_quiet_commute
                        ? "var(--status-good)"
                        : "var(--text-muted)",
                    }}
                  />
                  {quietCommute.likely_quiet_commute
                    ? "Likely Quiet Commute car"
                    : "Quiet Commute unlikely"}
                </span>
              )}
            </div>

            {/* Consolidated technical-detail disclosure: this page previously stacked
                the match-quality caveat and the Quiet Commute reasoning/disclaimer as
                two separate always-visible dense paragraphs. Both caveats are still
                fully present and honestly worded -- see backend/routers/trips.py's
                module docstring (live trip_id and static GTFS trip_id are unrelated ID
                spaces, so this is a closest-scheduled-departure match, not ground
                truth) and QUIET_COMMUTE_DISCLAIMER (a rule-of-thumb inference, not a
                guarantee) -- they're just collapsed by default behind one short line,
                reusing the same expand/collapse pattern as DataConfidenceIndicator's
                anomaly-detail list rather than a new UI pattern. */}
            <div className="font-mono text-xs mb-6 max-w-xl">
              <p className="text-[var(--text-muted)] leading-relaxed">
                Times shown are best-effort estimates, not live per-stop readings.{" "}
                <button
                  type="button"
                  onClick={() => setDetailsExpanded((e) => !e)}
                  aria-expanded={detailsExpanded}
                  className="text-[var(--accent)] hover:underline"
                >
                  why?{detailsExpanded ? " ▲" : " ▼"}
                </button>
              </p>

              {detailsExpanded && (
                <div className="mt-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 max-w-md">
                  <p className="text-[var(--text-secondary)] normal-case leading-relaxed mb-2">
                    Stops estimated from the closest scheduled trip in NJ Transit&apos;s
                    published timetable (~{data.match_time_gap_minutes} min match gap) — not a
                    guaranteed exact live match. Arrival times are the schedule plus this
                    trip&apos;s current known delay applied evenly to every remaining stop,
                    not a fresh per-stop live reading.
                  </p>
                  {quietCommute && (
                    <p className="text-[var(--text-secondary)] normal-case leading-relaxed">
                      {quietCommute.reasoning} {quietCommute.disclaimer}
                    </p>
                  )}
                </div>
              )}
            </div>

            <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
              <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
                <h2 className="font-display font-semibold">Stop sequence</h2>
                <span className="font-mono text-xs text-[var(--text-muted)]">
                  {data.stops.length} stop{data.stops.length === 1 ? "" : "s"} · refreshes every 30s
                </span>
              </div>

              <ol>
                {data.stops.map((stop, i) => {
                  const isNext = i === nextStopIndex;
                  const isPassed = stop.passed === true;
                  return (
                    <li
                      key={`${stop.stop_sequence}-${stop.stop_id}`}
                      className="px-5 py-3 border-t border-[var(--border)] first:border-t-0 flex items-center gap-4"
                      style={{ opacity: isPassed ? 0.45 : 1 }}
                    >
                      <span className="font-mono text-xs text-[var(--text-muted)] w-6 text-right shrink-0">
                        {stop.stop_sequence}
                      </span>
                      <span
                        className="inline-block w-2 h-2 rounded-full shrink-0"
                        style={{
                          background: isNext ? lineColor : isPassed ? "var(--text-muted)" : "var(--border)",
                        }}
                      />
                      <span
                        className="flex-1 text-sm"
                        style={{
                          color: isPassed ? "var(--text-muted)" : "var(--text-primary)",
                          textDecoration: isPassed ? "line-through" : "none",
                        }}
                      >
                        {stop.station_name ?? stop.stop_id}
                      </span>
                      {isNext && (
                        <span
                          className="font-mono text-xs font-semibold px-2 py-0.5 rounded-full"
                          style={{ background: `${lineColor}22`, color: lineColor }}
                        >
                          NEXT
                        </span>
                      )}
                      <span className="font-mono text-xs text-[var(--text-muted)] w-16 text-right shrink-0">
                        {formatScheduledTime(stop.scheduled_time)}
                      </span>
                      <span className="font-mono text-xs w-16 text-right shrink-0" style={{ color: isPassed ? "var(--text-muted)" : "var(--text-secondary)" }}>
                        {formatEstimatedArrival(stop.estimated_arrival)}
                      </span>
                    </li>
                  );
                })}
              </ol>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
