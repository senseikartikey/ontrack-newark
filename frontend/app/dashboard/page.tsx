"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getAlerts,
  getLines,
  getLiveStatus,
  getPredictedRisk,
  getScorecard,
  type Alert,
  type Line,
  type LiveTrip,
  type PredictedRisk,
  type Scorecard,
} from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import DataConfidenceIndicator from "@/components/DataConfidenceIndicator";
import { colorForLine } from "@/lib/lineColors";

function formatDelay(seconds: number | null) {
  if (seconds === null) return { text: "—", color: "var(--text-muted)" };
  if (seconds <= 60) return { text: "on time", color: "var(--status-good)" };
  const minutes = Math.round(seconds / 60);
  if (seconds <= 300) return { text: `+${minutes} min`, color: "var(--status-warning)" };
  return { text: `+${minutes} min`, color: "var(--status-critical)" };
}

const RISK_COLOR: Record<"low" | "medium" | "high", string> = {
  low: "var(--status-good)",
  medium: "var(--status-warning)",
  high: "var(--status-critical)",
};

export default function DashboardPage() {
  const [lines, setLines] = useState<Line[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [trips, setTrips] = useState<LiveTrip[] | null>(null);
  const [prediction, setPrediction] = useState<PredictedRisk | null>(null);
  const [scorecard, setScorecard] = useState<Scorecard | null>(null);
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    getLines()
      .then(({ lines }) => {
        setLines(lines);
        if (lines.length > 0) setSelected(lines[0].code);
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;

    function load() {
      getLiveStatus(selected!)
        .then((data) => {
          if (!cancelled) setTrips(data.trips);
        })
        .catch(() => {
          if (!cancelled) setError(true);
        });
    }

    load();
    const interval = setInterval(load, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selected]);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;

    getPredictedRisk(selected)
      .then((data) => {
        if (!cancelled) setPrediction(data);
      })
      .catch(() => {
        if (!cancelled) setPrediction(null);
      });

    return () => {
      cancelled = true;
    };
  }, [selected]);

  useEffect(() => {
    if (!selected) return;
    let cancelled = false;

    getScorecard(selected)
      .then((data) => {
        if (!cancelled) setScorecard(data);
      })
      .catch(() => {
        if (!cancelled) setScorecard(null);
      });

    getAlerts(selected)
      .then((data) => {
        if (!cancelled) setAlerts(data.alerts);
      })
      .catch(() => {
        if (!cancelled) setAlerts(null);
      });

    return () => {
      cancelled = true;
    };
  }, [selected]);

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="font-display font-bold text-lg tracking-tight">
              OnTrack
            </Link>
            <nav className="flex items-center gap-4 font-mono text-xs">
              <span className="text-[var(--text-primary)] border-b border-[var(--accent)] pb-0.5">
                Line dashboard
              </span>
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

      <main className="max-w-5xl mx-auto px-6 py-10 w-full flex-1">
        <div className="mb-8">
          <h1 className="font-display font-bold text-2xl tracking-tight">Delay risk &amp; reliability</h1>
          <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-xl">
            Pick a line to see what&apos;s running right now, how likely it is
            to run late (predicted before it happens, not just reported after),
            its on-time track record, and any active service alerts.
          </p>
        </div>

        {error && (
          <p className="font-mono text-sm text-[var(--status-warning)] mb-6">
            We can&apos;t reach live data right now. Please check back in a moment.
          </p>
        )}

        <div className="flex flex-wrap gap-2 mb-8">
          {lines.map((line) => {
            const color = colorForLine(line.code);
            const isSelected = selected === line.code;
            return (
              <button
                key={line.code}
                onClick={() => {
                  setSelected(line.code);
                  setTrips(null);
                  setScorecard(null);
                  setAlerts(null);
                }}
                className="font-mono text-xs px-3 py-1.5 rounded-full border flex items-center gap-1.5 transition-all hover:-translate-y-0.5"
                style={{
                  borderColor: isSelected ? color : "var(--border)",
                  background: isSelected ? color : "transparent",
                  color: isSelected ? "white" : "var(--text-secondary)",
                }}
              >
                <span
                  className="inline-block w-1.5 h-1.5 rounded-full"
                  style={{ background: isSelected ? "white" : color }}
                />
                {line.code} · {line.display_name}
              </button>
            );
          })}
        </div>

        <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          <div className="px-5 py-3 border-b border-[var(--border)] flex items-start justify-between flex-wrap gap-2">
            <h2 className="font-display font-semibold">Live status</h2>
            <div className="flex items-center gap-3">
              {/* Secondary trust signal (PRD-v2 Phase 1 data-confidence
                  indicator): honestly flags when NJ Transit's own feed looks
                  unreliable, without dominating the primary live-status panel. */}
              {selected && <DataConfidenceIndicator key={selected} lineCode={selected} />}
              <span className="font-mono text-xs text-[var(--text-muted)]">
                last 30 min · refreshes every 30s
              </span>
            </div>
          </div>

          {trips === null && !error && (
            <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
              loading…
            </p>
          )}

          {trips !== null && trips.length === 0 && (
            <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
              No trains currently reporting on this line. This usually just means a
              quiet window between departures — check back in a few minutes.
            </p>
          )}

          {trips !== null && trips.length > 0 && (
            <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-muted)] font-mono text-xs">
                  <th className="px-5 py-2 font-normal">Trip</th>
                  <th className="px-5 py-2 font-normal">Direction</th>
                  <th className="px-5 py-2 font-normal">Stop</th>
                  <th className="px-5 py-2 font-normal">Scheduled</th>
                  <th className="px-5 py-2 font-normal">Status</th>
                  <th className="px-5 py-2 font-normal"></th>
                </tr>
              </thead>
              <tbody>
                {trips.map((trip) => {
                  const delay = formatDelay(trip.delay_seconds);
                  return (
                    <tr key={trip.trip_id} className="border-t border-[var(--border)]">
                      <td className="px-5 py-2 font-mono text-xs">{trip.trip_id}</td>
                      <td className="px-5 py-2 text-[var(--text-secondary)]">
                        {trip.direction ?? "—"}
                      </td>
                      <td className="px-5 py-2 text-[var(--text-secondary)]">
                        {trip.stop_id}
                      </td>
                      <td className="px-5 py-2 text-[var(--text-secondary)]">
                        {new Date(trip.scheduled_time).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td className="px-5 py-2 font-mono" style={{ color: delay.color }}>
                        {delay.text}
                      </td>
                      <td className="px-5 py-2 text-right">
                        <Link
                          href={`/trips/${encodeURIComponent(trip.trip_id)}`}
                          className="font-mono text-xs text-[var(--accent)] hover:underline whitespace-nowrap"
                        >
                          on this train →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </div>
          )}
        </section>

        <section className="mt-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
            <h2 className="font-display font-semibold">Predicted delay risk</h2>
            <span className="font-mono text-xs text-[var(--text-muted)]">current hour</span>
          </div>

          {prediction === null && (
            <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
              loading…
            </p>
          )}

          {prediction?.status === "insufficient_data" && (
            <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
              Not enough delay history yet for this line at this hour to make a
              prediction. Check back once more trains have run.
            </p>
          )}

          {prediction?.status === "ok" && (
            <div className="px-5 py-5 flex items-center gap-4">
              <span
                className="font-mono text-xs font-semibold px-2.5 py-1 rounded-full"
                style={{
                  background: `${RISK_COLOR[prediction.risk_level]}22`,
                  color: RISK_COLOR[prediction.risk_level],
                }}
              >
                {prediction.risk_level.toUpperCase()} RISK
              </span>
              <span className="text-[var(--text-secondary)] text-sm">
                Historically ~{Math.round(prediction.predicted_delay_seconds / 60)} min
                delay for this line around this time, based on {prediction.sample_size}{" "}
                observed trips.{" "}
                {/* Subtle, non-primary affordance -- the model-version distinction
                    (v1 statistical baseline vs. v2 ML model) is real and documented,
                    but a rider doesn't need it forced on them as visible label text;
                    it's still available on hover for anyone curious. */}
                <span
                  className="font-mono text-xs text-[var(--text-muted)] cursor-help underline decoration-dotted underline-offset-2"
                  title={
                    prediction.source === "ml_model"
                      ? "Calculated by OnTrack's v2 machine-learning model, trained on observed delay history."
                      : "Calculated by OnTrack's v1 statistical baseline (typical delay for this line/hour), used until enough data exists to train the full model."
                  }
                >
                  how is this calculated?
                </span>
              </span>
            </div>
          )}
        </section>

        <div className="mt-6 grid md:grid-cols-2 gap-6">
          <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="px-5 py-3 border-b border-[var(--border)]">
              <h2 className="font-display font-semibold">Reliability scorecard</h2>
            </div>

            {scorecard === null && (
              <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
                loading…
              </p>
            )}

            {scorecard && (
              <div className="px-5 py-5 flex gap-8">
                <ScorecardStat label="Last 7 days" window={scorecard.rolling_7_day} />
                <ScorecardStat label="Last 30 days" window={scorecard.rolling_30_day} />
              </div>
            )}
          </section>

          <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="px-5 py-3 border-b border-[var(--border)]">
              <h2 className="font-display font-semibold">Service alerts</h2>
            </div>

            {alerts === null && (
              <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
                loading…
              </p>
            )}

            {alerts !== null && alerts.length === 0 && (
              <p className="px-5 py-8 text-[var(--text-secondary)] text-sm">
                No active alerts for this line right now.
              </p>
            )}

            {alerts !== null && alerts.length > 0 && (
              <ul className="divide-y divide-[var(--border)] max-h-72 overflow-y-auto">
                {alerts.map((alert) => (
                  <li key={alert.alert_id} className="px-5 py-3 text-sm text-[var(--text-secondary)]">
                    {alert.url ? (
                      <a
                        href={alert.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-[var(--text-primary)] transition-colors"
                      >
                        {alert.header_text}
                      </a>
                    ) : (
                      alert.header_text
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

function ScorecardStat({
  label,
  window,
}: {
  label: string;
  window: { sample_size: number; on_time_pct: number | null };
}) {
  return (
    <div>
      <p className="font-mono text-xs text-[var(--text-muted)] mb-1">{label}</p>
      {window.on_time_pct === null ? (
        <p className="text-[var(--text-secondary)] text-sm">no data yet</p>
      ) : (
        <>
          <p className="text-2xl font-display font-bold">{window.on_time_pct}%</p>
          <p className="font-mono text-xs text-[var(--text-muted)]">
            on time · {window.sample_size} trip{window.sample_size === 1 ? "" : "s"}
          </p>
        </>
      )}
    </div>
  );
}
