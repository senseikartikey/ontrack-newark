"use client";

import { useEffect, useState } from "react";
import { getLines, getLiveStatus, type Line } from "@/lib/api";

type FetchState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ready"; lines: Line[]; activeTrips: number; delayedTrips: number };

export default function HeroLiveStat() {
  const [state, setState] = useState<FetchState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const { lines } = await getLines();
        const liveByLine = await Promise.all(lines.map((l) => getLiveStatus(l.code)));
        const allTrips = liveByLine.flatMap((l) => l.trips);
        const delayed = allTrips.filter((t) => (t.delay_seconds ?? 0) > 300).length;
        if (!cancelled) {
          setState({
            status: "ready",
            lines,
            activeTrips: allTrips.length,
            delayedTrips: delayed,
          });
        }
      } catch {
        if (!cancelled) setState({ status: "error" });
      }
    }

    load();
    const interval = setInterval(load, 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="font-mono text-sm rounded-lg border border-[var(--border)] bg-[var(--surface)] px-5 py-4 w-full max-w-sm">
      <div className="flex items-center justify-between text-[var(--text-muted)] text-xs mb-3">
        <span>live_status.json</span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{
              background:
                state.status === "ready" ? "var(--status-good)" : "var(--status-warning)",
            }}
          />
          {state.status === "ready" ? "connected" : state.status === "loading" ? "connecting" : "offline"}
        </span>
      </div>

      {state.status === "loading" && (
        <p className="text-[var(--text-secondary)]">reaching the API…</p>
      )}

      {state.status === "error" && (
        <p className="text-[var(--text-secondary)]">
          API not reachable from here yet — this panel goes live once the backend is
          deployed and ingestion is running.
        </p>
      )}

      {state.status === "ready" && state.activeTrips === 0 && (
        <p className="text-[var(--text-secondary)]">
          Connected to {state.lines.length} Newark-area lines. No active trips in the
          last 30 minutes — data collection is running, real numbers appear here once
          live trains are in the window.
        </p>
      )}

      {state.status === "ready" && state.activeTrips > 0 && (
        <div className="space-y-1 text-[var(--text-primary)]">
          <div>
            active_trips: <span className="text-[var(--accent)]">{state.activeTrips}</span>
          </div>
          <div>
            delayed_5min_plus:{" "}
            <span style={{ color: state.delayedTrips > 0 ? "var(--status-critical)" : "var(--status-good)" }}>
              {state.delayedTrips}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
