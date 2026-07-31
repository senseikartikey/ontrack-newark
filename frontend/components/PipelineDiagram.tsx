const STAGES = [
  { label: "GTFS-RT + weather", detail: "NJ Transit RailData API, NWS", accent: "#3987e5" },
  { label: "Postgres", detail: "trip_updates, weather_hourly", accent: "#199e70" },
  { label: "LightGBM", detail: "delay risk, precomputed", accent: "#d55181" },
  { label: "FastAPI", detail: "cached endpoints", accent: "#9085e9" },
  { label: "Dashboard", detail: "this page", accent: "#c98500" },
];

export default function PipelineDiagram() {
  return (
    <div className="w-full overflow-x-auto">
      <div className="flex items-stretch gap-0 min-w-[720px] font-mono text-xs">
        {STAGES.map((stage, i) => (
          <div key={stage.label} className="flex items-stretch">
            <div
              className="flex flex-col justify-center rounded-xl border border-white/10 bg-[var(--ink-raised)] px-4 py-3 min-w-[140px] transition-transform hover:-translate-y-0.5"
              style={{ borderTop: `2px solid ${stage.accent}` }}
            >
              <span className="text-white font-semibold">{stage.label}</span>
              <span className="text-white/50 mt-1">{stage.detail}</span>
            </div>
            {i < STAGES.length - 1 && (
              <div className="flex items-center px-2 text-white/30" aria-hidden>
                →
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
