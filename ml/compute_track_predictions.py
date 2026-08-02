"""
Entrypoint: recompute per-train track predictions for New York Penn Station from
accumulated track_assignments history, and upsert into track_predictions. Intended
to run on a schedule (daily is plenty, same reasoning as compute_baseline.py -- the
underlying pattern for a given train_id shifts slowly) once devops-engineer-agent
wires it into /infra's GitHub Actions workflow (not done here -- see this repo's
CLAUDE.md: /ml doesn't edit /infra).

Methodology, styled after Clever Commute's own published approach (real third-party
NY Penn track-prediction tool, not guessed at): group historical observations by the
exact scheduled train_id (not just line/hour/day-of-week, which is far too coarse a
bucket for "which of ~20 physical tracks will this specific train use") and count how
often each track was actually used historically for that train. Reports three things
per train, matching Clever Commute's own displayed fields:
  - "Occurs" (this module's `sample_size`) -- the raw count of real, non-null
    observations behind the prediction.
  - "Historical %" / "Probability" (this module's `top_track_share`) -- the top
    track's share of that train's total observations.
  - A confidence tier (this module's `confidence`) -- see TRACK_MIN_SAMPLES_LOW/
    MEDIUM/HIGH and TRACK_SHARE_MEDIUM/HIGH in config.py for the exact thresholds.
Clever Commute doesn't publish an official confidence-tier cutoff, but does recommend
a ~60-day rolling window for best accuracy and states results get meaningfully more
reliable above roughly 20 observations -- this module doesn't yet filter to a rolling
window (there's no real NY Penn track data at all yet to reason about staleness with;
see below), so that's a deliberate fast-follow once real data exists, not an oversight.

CRITICAL DATA REALITY (2026-08-02, see ENGINEERING_LOG.md and
ingestion/models.py's TrackAssignment docstring): every real observation of
station_code == "NY" captured so far has track == NULL. NY Penn is Amtrak-dispatched,
not NJ Transit's own system, and neither NJT RailData's API nor NJT's own public
DepartureVision website has any early track visibility for it -- confirmed live,
twice, independently. It is genuinely unknown whether this ever changes closer to
departure; poll_track_assignments.py's ongoing logging is exactly what will answer
that over time. This module is written to work correctly either way:
  - A NULL track is "we don't know," never "the train used no track" -- the query
    below filters `track IS NOT NULL` before any grouping, so a NULL observation
    never gets counted as evidence for or against any track.
  - If real track values never start appearing for "NY", this module will run
    forever finding zero groups with any non-null observations and correctly,
    permanently write zero rows -- an honest "insufficient data" outcome, not a bug
    to route around and not something that needs fixing later. If they do start
    appearing, this module needs no changes to start producing real predictions
    once enough accumulate per train.

Safe to run repeatedly (recompute-and-replace via upsert on train_id), matching
compute_baseline.py's convention exactly.
"""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from config import (
    NY_PENN_STATION_CODE,
    TRACK_MIN_SAMPLES_HIGH,
    TRACK_MIN_SAMPLES_LOW,
    TRACK_MIN_SAMPLES_MEDIUM,
    TRACK_SHARE_HIGH,
    TRACK_SHARE_MEDIUM,
)
from db import get_session, init_db
from models import TrackAssignment, TrackPrediction


@dataclass
class _TrainHistory:
    track_counts: Counter = field(default_factory=Counter)

    @property
    def total(self) -> int:
        return sum(self.track_counts.values())


def _confidence_tier(sample_size: int, top_track_share: float) -> str | None:
    """Returns "high" / "medium" / "low", or None if sample_size doesn't even clear
    the lowest tier (in which case the caller must not write a row at all -- see
    module docstring's honesty convention)."""
    if sample_size >= TRACK_MIN_SAMPLES_HIGH and top_track_share >= TRACK_SHARE_HIGH:
        return "high"
    if sample_size >= TRACK_MIN_SAMPLES_MEDIUM and top_track_share >= TRACK_SHARE_MEDIUM:
        return "medium"
    if sample_size >= TRACK_MIN_SAMPLES_LOW:
        return "low"
    return None


def run(station_code: str = NY_PENN_STATION_CODE) -> dict:
    init_db()
    histories: dict[str, _TrainHistory] = defaultdict(_TrainHistory)

    with get_session() as session:
        rows = session.execute(
            select(TrackAssignment.train_id, TrackAssignment.track).where(
                TrackAssignment.station_code == station_code,
                TrackAssignment.track.is_not(None),
            )
        ).all()

        for train_id, track in rows:
            # Belt-and-suspenders against a stray empty string slipping through --
            # the SQL filter above already excludes real NULLs, but "" is a distinct
            # value from NULL in Postgres and would otherwise silently count as a
            # real track observation of nothing.
            if not track or not track.strip():
                continue
            histories[train_id].track_counts[track] += 1

        now = datetime.now(timezone.utc)
        written = 0
        skipped_low_sample = 0

        for train_id, history in histories.items():
            sample_size = history.total
            if sample_size < TRACK_MIN_SAMPLES_LOW:
                skipped_low_sample += 1
                continue

            top_track, top_count = history.track_counts.most_common(1)[0]
            top_track_share = top_count / sample_size

            confidence = _confidence_tier(sample_size, top_track_share)
            if confidence is None:
                skipped_low_sample += 1
                continue

            stmt = insert(TrackPrediction).values(
                train_id=train_id,
                station_code=station_code,
                predicted_track=top_track,
                confidence=confidence,
                sample_size=sample_size,
                top_track_share=top_track_share,
                computed_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["train_id"],
                set_={
                    "station_code": station_code,
                    "predicted_track": top_track,
                    "confidence": confidence,
                    "sample_size": sample_size,
                    "top_track_share": top_track_share,
                    "computed_at": now,
                },
            )
            session.execute(stmt)
            written += 1

    print(
        f"[compute_track_predictions] station={station_code}: wrote {written} "
        f"train predictions, skipped {skipped_low_sample} below the "
        f"{TRACK_MIN_SAMPLES_LOW}-observation minimum"
    )
    return {"written": written, "skipped_low_sample": skipped_low_sample}


if __name__ == "__main__":
    run()
