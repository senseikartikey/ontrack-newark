"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  getStationTransfers,
  searchStations,
  type StationSearchResult,
  type StationTransfers,
} from "@/lib/api";
import ThemeToggle from "@/components/ThemeToggle";
import { colorForLine } from "@/lib/lineColors";

type PickerSlot = { stopId: string; label: string };

// Newark Penn Station and Newark Broad Street are a nice existing example --
// two well-known, geographically real stations -- used only to pre-populate the
// picker so the page isn't empty on first load. Nothing downstream is gated to
// these two anymore: GET /stations/{stop_id}/transfers now resolves any real
// static stop_id statewide (backend/routers/stations.py), and either picker
// below can be pointed at any station via GET /stations/static?q=.
const DEFAULT_SLOTS: [PickerSlot, PickerSlot] = [
  { stopId: "107", label: "Newark Penn Station" },
  { stopId: "106", label: "Newark Broad Street" },
];

// Debounce for the station search-as-you-type box, so a full keystroke's worth
// of typing doesn't fire a request per character against GET /stations/static.
const SEARCH_DEBOUNCE_MS = 250;

// Below this many characters, a search is more likely to return a noisy
// too-broad result set than something useful -- skip the request entirely.
const MIN_QUERY_LENGTH = 2;

// Refresh interval for re-fetching the static schedule. This is not "live" data --
// the schedule itself basically never changes minute to minute -- but re-fetching
// keeps each departure's minutes_until from drifting stale on a screen left open,
// same spirit as the board/trip views' polling, just on a longer cadence since
// there's no live delay signal here to chase.
const REFRESH_INTERVAL_MS = 60_000;

type StationState =
  | { status: "loading" }
  | { status: "error" }
  | { status: "ok"; data: StationTransfers };

function formatMinutesUntil(minutes: number): string {
  if (minutes < 1) return "due";
  if (minutes < 60) return `${Math.round(minutes)}m`;
  const hours = Math.floor(minutes / 60);
  const remainder = Math.round(minutes % 60);
  return remainder === 0 ? `${hours}h` : `${hours}h ${remainder}m`;
}

// The static `stops` table stores names in ALL CAPS (e.g. "NEWARK BROAD ST",
// "TRENTON TRANSIT CENTER") -- title-case them for display so search results
// and picked-station labels read consistently with the hand-written defaults
// above rather than shouting.
function formatStationName(raw: string): string {
  return raw
    .toLowerCase()
    .split(" ")
    .filter(Boolean)
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

function StationPicker({
  id,
  currentLabel,
  onSelect,
}: {
  id: string;
  currentLabel: string;
  onSelect: (slot: PickerSlot) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StationSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    // Below the threshold there's nothing to search for -- the dropdown itself
    // is gated on the same length check at render time, so stale `results`
    // simply won't be shown; no need to reset state synchronously here (that
    // pattern trips react-hooks/set-state-in-effect -- see frontend/CLAUDE.md's
    // note on version-specific breaking changes to check before writing code).
    if (trimmed.length < MIN_QUERY_LENGTH) {
      return;
    }
    let cancelled = false;
    const timer = setTimeout(() => {
      // All setState calls live inside this async callback (fired by the
      // debounce timer), not synchronously in the effect body itself.
      setSearching(true);
      setSearchError(false);
      searchStations(trimmed)
        .then((res) => {
          if (cancelled) return;
          setResults(res.stations);
          setSearching(false);
        })
        .catch(() => {
          if (cancelled) return;
          setSearchError(true);
          setSearching(false);
        });
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  function handleSelect(result: StationSearchResult) {
    onSelect({ stopId: result.stop_id, label: formatStationName(result.stop_name) });
    setQuery("");
    setResults([]);
    setOpen(false);
  }

  return (
    <div className="relative">
      <label
        htmlFor={id}
        className="font-mono text-[10px] tracking-wide uppercase text-[var(--text-muted)]"
      >
        Search a station
      </label>
      <input
        id={id}
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => {
          // Delayed so a click on a result below still registers before the
          // dropdown unmounts and the query resets.
          setTimeout(() => {
            setOpen(false);
            setQuery("");
            setResults([]);
          }, 150);
        }}
        placeholder={currentLabel}
        autoComplete="off"
        className="w-full mt-1 font-mono text-sm px-3 py-2 rounded-md border border-[var(--border)] bg-[var(--background)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
      />
      {open && query.trim().length >= MIN_QUERY_LENGTH && (
        <div className="absolute z-10 mt-1 w-full max-h-64 overflow-y-auto rounded-md border border-[var(--border)] bg-[var(--surface)] shadow-lg">
          {searching && (
            <p className="px-3 py-2 font-mono text-xs text-[var(--text-muted)]">searching…</p>
          )}
          {!searching && searchError && (
            <p className="px-3 py-2 font-mono text-xs text-[var(--status-warning)]">
              Search failed. Try again.
            </p>
          )}
          {!searching && !searchError && results.length === 0 && (
            <p className="px-3 py-2 font-mono text-xs text-[var(--text-muted)]">
              No stations match &quot;{query.trim()}&quot;.
            </p>
          )}
          {!searching &&
            !searchError &&
            results.map((r) => (
              <button
                key={r.stop_id}
                type="button"
                onClick={() => handleSelect(r)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-[var(--border)]/40 transition-colors"
              >
                {formatStationName(r.stop_name)}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}

export default function HubPage() {
  const [slots, setSlots] = useState<[PickerSlot, PickerSlot]>(DEFAULT_SLOTS);
  const [stationStates, setStationStates] = useState<Record<string, StationState>>(
    () => Object.fromEntries(DEFAULT_SLOTS.map((s) => [s.stopId, { status: "loading" }])),
  );

  useEffect(() => {
    let cancelled = false;

    function load() {
      slots.forEach(({ stopId }) => {
        getStationTransfers(stopId)
          .then((data) => {
            if (cancelled) return;
            setStationStates((prev) => ({ ...prev, [stopId]: { status: "ok", data } }));
          })
          .catch(() => {
            if (cancelled) return;
            setStationStates((prev) => ({ ...prev, [stopId]: { status: "error" } }));
          });
      });
    }

    load();
    const interval = setInterval(load, REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [slots]);

  function handleSelect(index: 0 | 1, picked: PickerSlot) {
    setStationStates((prev) => ({
      ...prev,
      [picked.stopId]: prev[picked.stopId] ?? { status: "loading" },
    }));
    setSlots((prev) => {
      const next: [PickerSlot, PickerSlot] = [...prev];
      next[index] = picked;
      return next;
    });
  }

  const comparingSameStation = slots[0].stopId === slots[1].stopId;
  const allLoaded = slots.every((s) => stationStates[s.stopId]?.status === "ok");
  const allErrored = slots.every((s) => stationStates[s.stopId]?.status === "error");

  // Real observation, computed from whichever two stations are actually
  // selected right now -- not a fact baked in about any specific pair of
  // stations, so it stays honest as the picker changes.
  const overlap = useMemo(() => {
    if (comparingSameStation) return null;
    const stationsOk = slots.map((s) => stationStates[s.stopId]).filter(
      (s): s is { status: "ok"; data: StationTransfers } => s?.status === "ok",
    );
    if (stationsOk.length !== 2) return null;
    const [a, b] = stationsOk.map((s) => new Set(s.data.lines.map((l) => l.line)));
    const shared = [...a].filter((line) => b.has(line));
    return shared;
  }, [stationStates, slots, comparingSameStation]);

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
              <span className="text-[var(--text-primary)] border-b border-[var(--accent)] pb-0.5">
                Transfers
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

      <main className="max-w-5xl mx-auto px-6 py-10 w-full flex-1">
        <div className="mb-8">
          <h1 className="font-display font-bold text-2xl tracking-tight">
            Compare transfers at any two stations
          </h1>
          <p className="text-[var(--text-secondary)] text-sm mt-1 max-w-2xl">
            Search any NJ Transit rail station statewide to see which lines call
            there, and roughly when each one runs next — the transfer info NJ
            Transit&apos;s own app stopped showing up front.
          </p>
        </div>

        {allErrored && (
          <p className="font-mono text-sm text-[var(--status-warning)] mb-6">
            Can&apos;t reach the API right now. Set NEXT_PUBLIC_API_BASE_URL and make
            sure the backend is running (see /backend/README.md).
          </p>
        )}

        {comparingSameStation && (
          <p className="font-mono text-xs text-[var(--text-muted)] mb-6 max-w-2xl leading-relaxed">
            Both pickers are set to the same station — pick two different
            stations below to compare their scheduled lines.
          </p>
        )}

        {!comparingSameStation && allLoaded && overlap !== null && (
          <p className="font-mono text-xs text-[var(--text-muted)] mb-6 max-w-2xl leading-relaxed">
            {overlap.length === 0 ? (
              <>
                {slots[0].label} and {slots[1].label} share{" "}
                <span className="text-[var(--text-primary)]">zero</span> lines in
                common, computed from what&apos;s actually scheduled at each — not
                assumed. Moving between the lines below always means a physical
                transfer between the two stations, not a same-platform change.
              </>
            ) : (
              <>
                Shared lines between {slots[0].label} and {slots[1].label}:{" "}
                {overlap.join(", ")}.
              </>
            )}
          </p>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {slots.map((slot, index) => {
            const state = stationStates[slot.stopId];
            return (
              <section
                key={index}
                className="rounded-lg border border-[var(--border)] bg-[var(--surface)] overflow-hidden"
              >
                <div className="px-5 py-3 border-b border-[var(--border)] space-y-3">
                  <StationPicker
                    id={`station-picker-${index}`}
                    currentLabel={slot.label}
                    onSelect={(picked) => handleSelect(index as 0 | 1, picked)}
                  />
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <h2 className="font-display font-semibold">{slot.label}</h2>
                    <span className="font-mono text-[10px] tracking-wide uppercase px-2 py-0.5 rounded-full border border-[var(--border)] text-[var(--text-muted)]">
                      scheduled, not live
                    </span>
                  </div>
                  {state?.status === "ok" && (
                    <p className="font-mono text-xs text-[var(--text-muted)] leading-relaxed">
                      {state.data.note}
                    </p>
                  )}
                </div>

                {state?.status === "loading" && (
                  <p className="px-5 py-8 text-[var(--text-secondary)] font-mono text-sm">
                    loading…
                  </p>
                )}

                {state?.status === "error" && (
                  <p className="px-5 py-8 text-[var(--status-warning)] font-mono text-sm">
                    Couldn&apos;t load transfers for {slot.label}. Retrying every 60s.
                  </p>
                )}

                {state?.status === "ok" && state.data.lines.length === 0 && (
                  <p className="px-5 py-8 text-[var(--text-secondary)] text-sm max-w-md">
                    No scheduled lines found for this station in the static
                    timetable.
                  </p>
                )}

                {state?.status === "ok" && state.data.lines.length > 0 && (
                  <div>
                    {state.data.lines.map((line) => {
                      const color = colorForLine(line.line);
                      return (
                        <div
                          key={line.line}
                          className="px-5 py-4 border-t border-[var(--border)] first:border-t-0"
                        >
                          <div className="flex items-center gap-2 mb-2.5 flex-wrap">
                            <span
                              className="inline-flex items-center gap-1.5 font-mono text-xs font-semibold px-2.5 py-1 rounded-full"
                              style={{ background: `${color}22`, color }}
                            >
                              <span
                                className="inline-block w-1.5 h-1.5 rounded-full"
                                style={{ background: color }}
                              />
                              {line.line}
                            </span>
                            <span className="text-[var(--text-secondary)] text-sm">
                              {line.line_display_name}
                            </span>
                            <span className="font-mono text-xs text-[var(--text-muted)] ml-auto">
                              {line.distinct_scheduled_times} scheduled today
                            </span>
                          </div>

                          {line.next_departures.length === 0 ? (
                            <p className="text-[var(--text-secondary)] text-xs">
                              No upcoming scheduled departures found.
                            </p>
                          ) : (
                            <ul className="space-y-1">
                              {line.next_departures.map((dep, i) => (
                                <li
                                  key={`${dep.scheduled_time_of_day}-${dep.headsign}-${i}`}
                                  className="flex items-center gap-3 text-sm"
                                >
                                  <span className="font-mono text-xs text-[var(--text-secondary)] w-12 shrink-0">
                                    {dep.scheduled_time_of_day}
                                  </span>
                                  <span className="text-[var(--text-primary)] flex-1 truncate">
                                    {dep.headsign ?? "—"}
                                  </span>
                                  <span
                                    className="font-mono text-xs shrink-0"
                                    style={{
                                      color:
                                        dep.minutes_until <= 10
                                          ? "var(--status-warning)"
                                          : "var(--text-muted)",
                                    }}
                                  >
                                    in {formatMinutesUntil(dep.minutes_until)}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      </main>
    </div>
  );
}
