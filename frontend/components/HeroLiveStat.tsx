"use client";

import { useEffect, useState } from "react";
import { getStationBoard, getStations, type Departure, type StationBoard } from "@/lib/api";
import { colorForLine } from "@/lib/lineColors";

// How many of the currently-reporting stations to sample when picking a
// sensible default station to show first (the one with the most upcoming
// departures right now). Deliberately small and arbitrary -- this is "pick
// something reasonable to look at first," not a real ranking system (the
// visitor can always switch stations via the select below), and it keeps the
// number of API calls on page load bounded regardless of how many stations
// happen to be reporting statewide.
const CANDIDATE_SAMPLE_SIZE = 8;

// How many departures to show before truncating -- this lives in the hero
// next to the headline/CTA, it should stay compact, not become a second
// /board page.
const MAX_VISIBLE_DEPARTURES = 4;

type WidgetState =
  | { phase: "loading" }
  | { phase: "error" }
  | { phase: "empty" } // API reachable, but zero stations currently reporting
  | {
      phase: "ready";
      stations: string[];
      selected: string;
      board: StationBoard | null;
      boardError: boolean;
    };

function formatStatus(dep: Departure): { text: string; color: string } {
  if (dep.status === "unknown" || dep.delay_seconds === null) {
    return { text: "status unknown", color: "var(--paper-dim)" };
  }
  if (dep.status === "on_time") {
    return { text: "on time", color: "var(--status-good)" };
  }
  const minutes = Math.round(dep.delay_seconds / 60);
  const color = dep.delay_seconds <= 300 ? "var(--status-warning)" : "var(--status-critical)";
  return { text: `+${minutes} min`, color };
}

/**
 * Compact, real live departure board for one NJ Transit station, embedded
 * directly in the landing page hero -- a visitor can actually use this
 * without clicking anywhere else, not just read a summary stat.
 *
 * The station is NOT hardcoded (this project's rebrand was specifically
 * about not being Newark-centric): on mount, it samples a handful of the
 * live-reporting stations from GET /stations and defaults to whichever has
 * the most upcoming departures, then lets the visitor switch via the select
 * below. If nothing is currently reporting (a real possibility right now --
 * NJT's RailData quota has been exhausted during testing), this shows a
 * calm, honest empty state rather than breaking or rendering nothing.
 */
export default function HeroLiveStat() {
  const [state, setState] = useState<WidgetState>({ phase: "loading" });

  // Initial load: fetch the live-reporting station list, sample a handful of
  // them for departure counts, and default to the busiest one.
  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const { stations } = await getStations();
        if (cancelled) return;

        if (stations.length === 0) {
          setState({ phase: "empty" });
          return;
        }

        const sorted = [...stations].sort();
        const candidates = sorted.slice(0, CANDIDATE_SAMPLE_SIZE);
        const counts = await Promise.all(
          candidates.map((s) =>
            getStationBoard(s)
              .then((board) => board.departures.length)
              .catch(() => 0)
          )
        );

        let bestIndex = 0;
        counts.forEach((count, i) => {
          if (count > counts[bestIndex]) bestIndex = i;
        });

        if (!cancelled) {
          setState({
            phase: "ready",
            stations: sorted,
            selected: candidates[bestIndex],
            board: null,
            boardError: false,
          });
        }
      } catch {
        if (!cancelled) setState({ phase: "error" });
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, []);

  // Load (and then poll) the selected station's board -- fires immediately on
  // mount/selection-change, then every 30s, same cadence as /board.
  const selected = state.phase === "ready" ? state.selected : null;
  useEffect(() => {
    if (!selected) return;
    let cancelled = false;

    function load() {
      getStationBoard(selected!)
        .then((board) => {
          if (cancelled) return;
          setState((prev) => (prev.phase === "ready" ? { ...prev, board, boardError: false } : prev));
        })
        .catch(() => {
          if (cancelled) return;
          setState((prev) => (prev.phase === "ready" ? { ...prev, boardError: true } : prev));
        });
    }

    load();
    const interval = setInterval(load, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selected]);

  return (
    <div
      className="font-mono text-xs border w-full max-w-md text-left backdrop-blur-sm"
      style={{ borderColor: "var(--hairline)", background: "rgba(12,10,8,0.55)" }}
    >
      <div
        className="flex items-center justify-between gap-3 px-5 py-3 border-b"
        style={{ borderColor: "var(--hairline)" }}
      >
        <span className="tracking-[0.08em]" style={{ color: "var(--paper-dim)" }}>
          LIVE_BOARD.JSON
        </span>
        <span className="flex items-center gap-1.5" style={{ color: "var(--paper-dim)" }}>
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{
              background: state.phase === "ready" ? "var(--signal)" : "var(--paper-dim)",
            }}
          />
          {state.phase === "ready" ? "connected" : state.phase === "loading" ? "connecting" : "offline"}
        </span>
      </div>

      <div className="px-5 py-4">
        {state.phase === "loading" && <p style={{ color: "var(--paper-dim)" }}>reaching the API…</p>}

        {state.phase === "error" && (
          <p style={{ color: "var(--paper-dim)" }}>
            API not reachable from here yet — this board goes live once the backend is
            deployed and ingestion is running.
          </p>
        )}

        {state.phase === "empty" && (
          <p style={{ color: "var(--paper-dim)" }}>
            No stations are reporting live departures right now — a quiet window in the
            data, not a broken board. Check back shortly.
          </p>
        )}

        {state.phase === "ready" && (
          <>
            <div className="flex items-center gap-2 mb-3 flex-wrap">
              <label htmlFor="hero-station-select" className="sr-only">
                Station
              </label>
              <select
                id="hero-station-select"
                value={state.selected}
                onChange={(e) => {
                  const value = e.target.value;
                  setState((prev) =>
                    prev.phase === "ready"
                      ? { ...prev, selected: value, board: null, boardError: false }
                      : prev
                  );
                }}
                className="font-mono text-xs px-2 py-1 border bg-transparent max-w-[12rem]"
                style={{ borderColor: "var(--hairline)", color: "var(--paper)" }}
              >
                {state.stations.map((s) => (
                  <option key={s} value={s} style={{ color: "#000" }}>
                    {s}
                  </option>
                ))}
              </select>
              <span style={{ color: "var(--paper-faint)" }}>next 30 min</span>
            </div>

            {state.board === null && !state.boardError && (
              <p style={{ color: "var(--paper-dim)" }}>loading…</p>
            )}

            {state.boardError && state.board === null && (
              <p style={{ color: "var(--paper-dim)" }}>Couldn&apos;t load this board. Retrying…</p>
            )}

            {state.board !== null && state.board.departures.length === 0 && (
              <p style={{ color: "var(--paper-dim)" }}>
                No departures at {state.board.station} in the last 30 minutes — a quiet
                window, not a broken board.
              </p>
            )}

            {state.board !== null && state.board.departures.length > 0 && (
              <div className="space-y-2">
                {state.board.departures.slice(0, MAX_VISIBLE_DEPARTURES).map((dep) => {
                  const status = formatStatus(dep);
                  const color = colorForLine(dep.line);
                  return (
                    <div key={dep.trip_id} className="flex items-center justify-between gap-3">
                      <span className="flex items-center gap-1.5 min-w-0">
                        <span
                          className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
                          style={{ background: color }}
                        />
                        <span style={{ color }}>{dep.line}</span>
                        <span style={{ color: "var(--paper-dim)" }}>
                          {new Date(dep.scheduled_time).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                        {dep.track && (
                          <span
                            className="px-1 border flex-shrink-0"
                            style={{ borderColor: "var(--hairline)", color: "var(--paper-dim)" }}
                          >
                            trk {dep.track}
                          </span>
                        )}
                      </span>
                      <span style={{ color: status.color }} className="flex-shrink-0">
                        {status.text}
                      </span>
                    </div>
                  );
                })}
                {state.board.departures.length > MAX_VISIBLE_DEPARTURES && (
                  <a href="/board" className="block pt-1 hover:underline" style={{ color: "var(--signal)" }}>
                    view full board →
                  </a>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
