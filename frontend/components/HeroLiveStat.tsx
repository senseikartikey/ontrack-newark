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
    <div
      className="font-mono text-xs border px-5 py-4 w-full max-w-sm text-left backdrop-blur-sm"
      style={{ borderColor: "var(--hairline)", background: "rgba(12,10,8,0.55)" }}
    >
      <div
        className="flex items-center justify-between text-[0.6875rem] tracking-[0.08em] mb-3"
        style={{ color: "var(--paper-dim)" }}
      >
        <span>LIVE_STATUS.JSON</span>
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{
              background: state.status === "ready" ? "var(--signal)" : "var(--paper-dim)",
            }}
          />
          {state.status === "ready" ? "connected" : state.status === "loading" ? "connecting" : "offline"}
        </span>
      </div>

      {state.status === "loading" && <p style={{ color: "var(--paper-dim)" }}>reaching the API…</p>}

      {state.status === "error" && (
        <p style={{ color: "var(--paper-dim)" }}>
          API not reachable from here yet — this panel goes live once the backend is
          deployed and ingestion is running.
        </p>
      )}

      {state.status === "ready" && state.activeTrips === 0 && (
        <p style={{ color: "var(--paper-dim)" }}>
          Connected to {state.lines.length} Newark-area lines. No active trips in the
          last 30 minutes — data collection is running, real numbers appear here once
          live trains are in the window.
        </p>
      )}

      {state.status === "ready" && state.activeTrips > 0 && (
        <div className="space-y-1" style={{ color: "var(--paper)" }}>
          <div>
            active_trips: <span style={{ color: "var(--signal)" }}>{state.activeTrips}</span>
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
