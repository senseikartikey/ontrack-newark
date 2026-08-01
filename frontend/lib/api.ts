const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Line = { code: string; display_name: string };

export type LiveTrip = {
  trip_id: string;
  direction: string | null;
  stop_id: string;
  scheduled_time: string;
  delay_seconds: number | null;
};

export type LiveStatus = {
  line: string;
  as_of: string;
  trips: LiveTrip[];
};

export type PredictedRisk =
  | { line: string; status: "insufficient_data"; message: string }
  | {
      line: string;
      status: "ok";
      source: "statistical_baseline" | "ml_model";
      predicted_delay_seconds: number;
      risk_level: "low" | "medium" | "high";
      sample_size: number;
      computed_at: string;
      model_version?: string;
      mae_seconds?: number;
      baseline_mae_seconds?: number;
    };

export type Alert = {
  alert_id: string;
  line: string | null;
  header_text: string;
  url: string | null;
  active_from: string | null;
};

export type ScorecardWindow = { sample_size: number; on_time_pct: number | null };
export type Scorecard = {
  line: string;
  rolling_7_day: ScorecardWindow;
  rolling_30_day: ScorecardWindow;
};

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API request to ${path} failed with status ${res.status}`);
  }
  return res.json();
}

export function getLines(): Promise<{ lines: Line[] }> {
  return apiFetch("/lines");
}

export function getLiveStatus(lineCode: string): Promise<LiveStatus> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/live`);
}

export function getPredictedRisk(lineCode: string): Promise<PredictedRisk> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/predict`);
}

export function getScorecard(lineCode: string): Promise<Scorecard> {
  return apiFetch(`/lines/${encodeURIComponent(lineCode)}/scorecard`);
}

export function getAlerts(lineCode: string): Promise<{ alerts: Alert[] }> {
  return apiFetch(`/alerts?line=${encodeURIComponent(lineCode)}`);
}
