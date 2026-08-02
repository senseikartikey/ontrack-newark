"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { getStationBoard, getStations, type Departure, type StationBoard } from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import { colorForLine } from "@/lib/lineColors";

function formatBoardStatus(status: Departure["status"], seconds: number | null) {
  if (status === "unknown" || seconds === null) {
    return { text: "—", color: "var(--text-muted)" };
  }
  if (status === "on_time") {
    return { text: "on time", color: "var(--status-good)" };
  }
  const minutes = Math.round(seconds / 60);
  const color = seconds <= 300 ? "var(--status-warning)" : "var(--status-critical)";
  return { text: `+${minutes} min`, color };
}

export default function BoardPage() {
  const [stations, setStations] = useState<string[] | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [board, setBoard] = useState<StationBoard | null>(null);
  const [error, setError] = useState(false);
  const [boardError, setBoardError] = useState(false);

  // Station list -- fetched once, same "fetch once on mount" pattern as the
  // dashboard's getLines().
  useEffect(() => {
    getStations()
      .then(({ stations }) => {
        setStations(stations);
        if (stations.length > 0) {
          const hub = stations.find((s) => s.toLowerCase().includes("newark penn"));
          setSelected(hub ?? stations[0]);
        }
      })
      .catch(() => setError(true));
  }, []);

  // Board for the selected station -- polled every 30s, same interval as the
  // dashboard's live-status table.
  useEffect(() => {
    if (!selected) return;
    let cancelled = false;

    function load() {
      getStationBoard(selected!)
        .then((data) => {
          if (!cancelled) {
            setBoard(data);
            setBoardError(false);
          }
        })
        .catch(() => {
          if (!cancelled) setBoardError(true);
        });
    }

    load();
    const interval = setInterval(load, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selected]);

  const sortedStations = useMemo(() => (stations ? [...stations].sort() : []), [stations]);

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
              <span className="text-[var(--text-primary)] border-b border-[var(--accent)] pb-0.5">
                Live board
              </span>
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
          <h1 className="font-display font-bold text-2xl tracking-tight">Live station board</h1>
          <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-xl">
            Every upcoming departure across any NJ Transit rail line at one station,
            mixed together in one chronological list — the way a physical station
            board works, not filtered to a single line.
          </p>
        </div>

        {error && (
          <p className="font-mono text-sm text-[var(--status-warning)] mb-6">
            We can&apos;t reach live data right now. Please check back in a moment.
          </p>
        )}

        {!error && stations !== null && stations.length === 0 && (
          <p className="text-[var(--text-secondary)] text-sm max-w-md mb-8">
            No stations currently reporting traffic right now. This usually just
            means a quiet window — check back in a few minutes.
          </p>
        )}

        {!error && stations === null && (
          <p className="font-mono text-sm text-[var(--text-secondary)] mb-8">loading stations…</p>
        )}

        {stations !== null && stations.length > 0 && (
          <div className="flex flex-wrap items-center gap-3 mb-8">
            <label htmlFor="station-select" className="font-mono text-xs text-[var(--text-muted)]">
              STATION
            </label>
            <select
              id="station-select"
              value={selected ?? ""}
              onChange={(e) => {
                setSelected(e.target.value);
                setBoard(null);
              }}
              className="font-mono text-sm px-3 py-2 rounded-md border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)]"
            >
              {sortedStations.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
            <span className="font-mono text-xs text-[var(--text-muted)]">
              {stations.length} station{stations.length === 1 ? "" : "s"} currently reporting
            </span>
          </div>
        )}

        {selected && (
          <section className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden">
            <div className="px-5 py-3 border-b border-[var(--border)] flex items-center justify-between flex-wrap gap-2">
              <h2 className="font-display font-semibold">{board?.station ?? selected}</h2>
              <span className="font-mono text-xs text-[var(--text-muted)]">
                last 30 min · refreshes every 30s
              </span>
            </div>

            {boardError && (
              <p className="px-5 py-8 text-[var(--status-warning)] font-mono text-sm">
                Couldn&apos;t load the board for this station. Retrying every 30s.
              </p>
            )}

            {!boardError && board === null && (
              <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">loading…</p>
            )}

            {!boardError && board !== null && board.departures.length === 0 && (
              <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
                No departures reported at {board.station} in the last 30 minutes.
                This usually just means a quiet window — check back in a few
                minutes.
              </p>
            )}

            {!boardError && board !== null && board.departures.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-[var(--text-muted)] font-mono text-xs">
                      <th className="px-5 py-2 font-normal">Line</th>
                      <th className="px-5 py-2 font-normal">Direction</th>
                      <th className="px-5 py-2 font-normal">Scheduled</th>
                      <th className="px-5 py-2 font-normal">Track</th>
                      <th className="px-5 py-2 font-normal">Status</th>
                      <th className="px-5 py-2 font-normal"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {board.departures.map((dep) => {
                      const status = formatBoardStatus(dep.status, dep.delay_seconds);
                      const color = colorForLine(dep.line);
                      return (
                        <tr key={dep.trip_id} className="border-t border-[var(--border)]">
                          <td className="px-5 py-1.5">
                            <span className="inline-flex items-center gap-1.5 font-mono text-xs">
                              <span
                                className="inline-block w-1.5 h-1.5 rounded-full"
                                style={{ background: color }}
                              />
                              <span style={{ color }}>{dep.line}</span>
                              <span className="text-[var(--text-secondary)]">
                                {dep.line_display_name}
                              </span>
                            </span>
                          </td>
                          <td className="px-5 py-1.5 text-[var(--text-secondary)]">
                            {dep.direction ?? "—"}
                          </td>
                          <td className="px-5 py-1.5 font-mono text-xs text-[var(--text-secondary)]">
                            {new Date(dep.scheduled_time).toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td className="px-5 py-1.5">
                            {dep.track && (
                              <span
                                className="inline-flex items-center font-mono text-xs px-1.5 py-0.5 rounded border border-[var(--border)] text-[var(--text-primary)]"
                                title={
                                  dep.track_match_time_gap_minutes !== null
                                    ? `Best-effort match, ${dep.track_match_time_gap_minutes} min from scheduled time`
                                    : undefined
                                }
                              >
                                Track {dep.track}
                              </span>
                            )}
                          </td>
                          <td className="px-5 py-1.5 font-mono text-xs" style={{ color: status.color }}>
                            {status.text}
                          </td>
                          <td className="px-5 py-1.5 text-right">
                            <Link
                              href={`/trips/${encodeURIComponent(dep.trip_id)}`}
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
        )}
      </main>
    </div>
  );
}
