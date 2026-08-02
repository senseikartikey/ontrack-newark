"use client";

import { useEffect, useState } from "react";
import { getDataConfidence, type AnomalyType, type DataConfidence } from "@/lib/api";

// Re-fetch cadence for this widget. Anomalies are written by /ingestion's
// reconcile_anomalies.py roughly once per poll cycle (every 5 min in production),
// and this indicator rolls those up over a 3h window (backend/routers/
// data_confidence.py's ANOMALY_WINDOW_HOURS) -- there's no benefit to polling as
// fast as the live-trips table (30s), but it should still update within a session
// without a manual page reload.
const REFRESH_INTERVAL_MS = 60_000;

const ANOMALY_LABELS: Record<AnomalyType, string> = {
  vanished_mid_route: "vanished mid-route",
  stale_timestamp: "stale timestamp",
};

type State = { status: "loading" } | { status: "error" } | { status: "ok"; data: DataConfidence };

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Small badge + optional expandable detail list, meant to sit as a secondary
// trust signal near the top of a line's dashboard section -- not a headline
// feature, but not buried either (see task brief: this is the project's
// differentiator against NJ Transit's own widely-distrusted live data).
//
// The caller renders this with `key={lineCode}` (see app/dashboard/page.tsx) so
// switching lines remounts the component and its state resets via the initial
// useState value -- deliberately not done with a synchronous setState() call at
// the top of the effect below, which react-hooks/set-state-in-effect flags as a
// cascading-render anti-pattern.
export default function DataConfidenceIndicator({ lineCode }: { lineCode: string }) {
  const [state, setState] = useState<State>({ status: "loading" });
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    function load() {
      getDataConfidence(lineCode)
        .then((data) => {
          if (!cancelled) setState({ status: "ok", data });
        })
        .catch(() => {
          if (!cancelled) setState({ status: "error" });
        });
    }

    load();
    const interval = setInterval(load, REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [lineCode]);

  if (state.status === "loading") {
    return (
      <span className="font-mono text-xs text-[var(--text-muted)]">
        checking feed…
      </span>
    );
  }

  // A failed fetch here is deliberately quiet -- the dashboard's main sections
  // already surface a loud "can't reach the API" banner when the backend is down,
  // so a second one for this secondary signal would just be noise.
  if (state.status === "error") {
    return (
      <span className="font-mono text-xs text-[var(--text-muted)]">
        feed confidence unavailable
      </span>
    );
  }

  const { data } = state;
  const badge = BADGE_BY_STATUS[data.status];
  const canExpand = data.status === "issues_detected" && data.recent_anomalies.length > 0;

  return (
    <div className="font-mono text-xs">
      <button
        type="button"
        onClick={() => canExpand && setExpanded((e) => !e)}
        aria-expanded={canExpand ? expanded : undefined}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border transition-colors"
        style={{
          borderColor: `${badge.color}55`,
          background: `${badge.color}18`,
          color: badge.color,
          cursor: canExpand ? "pointer" : "default",
        }}
        title={data.message}
      >
        <span className="inline-block w-1.5 h-1.5 rounded-full" style={{ background: badge.color }} />
        {badge.label}
        {canExpand && <span className="text-[var(--text-muted)]">{expanded ? " ▲" : " ▼"}</span>}
      </button>

      {expanded && data.status === "issues_detected" && (
        <div className="mt-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 max-w-md">
          <p className="text-[var(--text-secondary)] normal-case leading-relaxed mb-2">
            {data.message}
          </p>
          <ul className="space-y-1.5">
            {data.recent_anomalies.map((a, i) => (
              <li key={`${a.trip_id}-${a.detected_at}-${i}`} className="text-[var(--text-muted)] normal-case">
                <span className="text-[var(--text-secondary)]">{formatTime(a.detected_at)}</span>{" "}
                · trip <span className="text-[var(--text-secondary)]">{a.trip_id}</span> ·{" "}
                {ANOMALY_LABELS[a.anomaly_type] ?? a.anomaly_type}
                {a.detail ? <> — {a.detail}</> : null}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const BADGE_BY_STATUS: Record<DataConfidence["status"], { label: string; color: string }> = {
  // Neutral, not alarming -- this is currently production's real, honest steady
  // state (see task brief: an ongoing NJT-side feed outage), not an error.
  //
  // Plain-language rider-facing labels (2026-08-02 jargon pass) -- the underlying
  // three-state status/logic and the expandable anomaly detail below are unchanged,
  // only this display text. `title={data.message}` above still carries the fuller
  // technical wording on hover for anyone who wants it.
  unknown: { label: "live data currently unavailable", color: "var(--text-muted)" },
  ok: { label: "live data looks good", color: "var(--status-good)" },
  issues_detected: { label: "live data has had some hiccups", color: "var(--status-warning)" },
};
