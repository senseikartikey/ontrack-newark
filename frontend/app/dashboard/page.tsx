"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getLines,
  getLiveStatus,
  getPredictedRisk,
  type Line,
  type LiveTrip,
  type PredictedRisk,
} from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
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

  return (
    <div className="flex-1 flex flex-col">
      <header className="border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-display font-bold text-lg tracking-tight">
            OnTrack Newark
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 w-full flex-1">
        {error && (
          <p className="font-mono text-sm text-[var(--status-warning)] mb-6">
            Can&apos;t reach the API right now. Set NEXT_PUBLIC_API_BASE_URL and make
            sure the backend is running (see /backend/README.md).
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
          <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
            <h2 className="font-display font-semibold">Live status</h2>
            <span className="font-mono text-xs text-[var(--text-muted)]">
              last 30 min · refreshes every 30s
            </span>
          </div>

          {trips === null && !error && (
            <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
              loading…
            </p>
          )}

          {trips !== null && trips.length === 0 && (
            <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
              No active trips reported in the last 30 minutes. Either it&apos;s a quiet
              window, or live ingestion hasn&apos;t started yet — see{" "}
              <code className="font-mono text-xs">/ingestion/README.md</code> for setup
              status.
            </p>
          )}

          {trips !== null && trips.length > 0 && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--text-muted)] font-mono text-xs">
                  <th className="px-5 py-2 font-normal">Trip</th>
                  <th className="px-5 py-2 font-normal">Direction</th>
                  <th className="px-5 py-2 font-normal">Stop</th>
                  <th className="px-5 py-2 font-normal">Scheduled</th>
                  <th className="px-5 py-2 font-normal">Status</th>
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
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>

        <section className="mt-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
          <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between">
            <h2 className="font-display font-semibold">Predicted delay risk</h2>
            <span className="font-mono text-xs text-[var(--text-muted)]">
              current hour · v1 statistical baseline
            </span>
          </div>

          {prediction === null && (
            <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
              loading…
            </p>
          )}

          {prediction?.status === "insufficient_data" && (
            <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
              Not enough historical data yet for this line at this hour/day. This
              baseline needs real accumulated delay history from `/ingestion` before
              it can predict anything — see <code className="font-mono text-xs">/ml/README.md</code>.
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
                observed trips.
              </span>
            </div>
          )}
        </section>

        <p className="mt-6 font-mono text-xs text-[var(--text-muted)]">
          Historical scorecards land once /ml&apos;s evaluation ships (Week 4) — see
          the project&apos;s ENGINEERING_LOG.md.
        </p>
      </main>
    </div>
  );
}
