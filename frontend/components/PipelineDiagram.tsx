const STAGES = [
  { id: "01", label: "GTFS-RT + weather", detail: "NJ Transit RailData API, NWS" },
  { id: "02", label: "Postgres", detail: "trip_updates, weather_hourly" },
  { id: "03", label: "LightGBM", detail: "delay risk, precomputed" },
  { id: "04", label: "FastAPI", detail: "cached endpoints" },
  { id: "05", label: "Dashboard", detail: "this page" },
];

export default function PipelineDiagram() {
  return (
    <div className="border-t" style={{ borderColor: "var(--hairline)" }}>
      {STAGES.map((stage) => (
        <div
          key={stage.id}
          className="flex items-baseline justify-between py-3 border-b font-mono text-xs"
          style={{ borderColor: "var(--hairline)" }}
        >
          <div className="flex items-baseline gap-4">
            <span style={{ color: "var(--signal)" }}>{stage.id}</span>
            <span style={{ color: "var(--paper)" }}>{stage.label}</span>
          </div>
          <span style={{ color: "var(--paper-dim)" }}>{stage.detail}</span>
        </div>
      ))}
    </div>
  );
}
