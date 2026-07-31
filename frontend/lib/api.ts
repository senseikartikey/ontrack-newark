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
      predicted_delay_seconds: number;
      risk_level: "low" | "medium" | "high";
      sample_size: number;
      computed_at: string;
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
