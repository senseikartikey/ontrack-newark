const STAGES = [
  { label: "GTFS-RT + weather", detail: "NJ Transit RailData API, NWS" },
  { label: "Postgres", detail: "trip_updates, weather_hourly" },
  { label: "LightGBM", detail: "delay risk, precomputed" },
  { label: "FastAPI", detail: "cached endpoints" },
  { label: "Dashboard", detail: "this page" },
];

export default function PipelineDiagram() {
  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-stretch gap-0 min-w-[720px] font-mono text-xs">
        {STAGES.map((stage, i) => (
          <div key={stage.label} className="flex items-stretch">
            <div className="flex flex-col justify-center rounded-md border border-[var(--border)] bg-[var(--surface)] px-4 py-3 min-w-[140px]">
              <span className="text-[var(--text-primary)] font-semibold">{stage.label}</span>
              <span className="text-[var(--text-muted)] mt-1">{stage.detail}</span>
            </div>
            {i < STAGES.length - 1 && (
              <div className="flex items-center px-2 text-[var(--text-muted)]" aria-hidden>
                →
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
