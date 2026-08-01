"""
Entrypoint: train the v2 LightGBM delay-risk model. Run on a schedule (daily,
after compute_baseline.py) via GitHub Actions.

Safe to run repeatedly on too little data -- it explicitly checks
MIN_TRAINING_ROWS and logs why it's skipping rather than fitting (and
potentially serving) an overfit model. Only writes to ml_predictions if the
model both clears that threshold AND beats the current statistical baseline's
MAE on a held-out, time-based test split (never a random split -- a trip's
repeated readings would otherwise leak between train and test).
"""
from datetime import datetime, timezone

import lightgbm as lgb
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from config import MIN_TRAINING_ROWS, TEST_HOLDOUT_FRACTION
from db import get_session, init_db
from features import FEATURE_COLUMNS, TARGET_COLUMN, build_training_frame
from models import DelayBaseline, MLPrediction

MODEL_VERSION = "lightgbm-v1"

CONTINUOUS_FEATURES = [
    "temperature_f",
    "wind_speed_mph",
    "precipitation_probability_pct",
    "active_alerts_for_line",
    "recent_avg_delay_same_line",
]


def _mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float))))


def _time_based_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split by scheduled_time, not randomly -- a trip's repeated GTFS-RT readings
    are correlated, so a random split would leak information between train/test."""
    df = df.sort_values("scheduled_time")
    split_idx = int(len(df) * (1 - TEST_HOLDOUT_FRACTION))
    return df.iloc[:split_idx], df.iloc[split_idx:]


def run() -> dict:
    init_db()

    with get_session() as session:
        df = build_training_frame(session)

        if len(df) < MIN_TRAINING_ROWS:
            print(
                f"[train_model] only {len(df)} training rows (need {MIN_TRAINING_ROWS}) -- "
                "skipping training. The v1 statistical baseline remains what's served."
            )
            return {"status": "skipped_insufficient_data", "rows": len(df)}

        train_df, test_df = _time_based_split(df)
        if len(train_df) == 0 or len(test_df) == 0:
            print("[train_model] not enough rows to form a train/test split -- skipping.")
            return {"status": "skipped_insufficient_data", "rows": len(df)}

        model = lgb.LGBMRegressor(n_estimators=200, max_depth=6, random_state=42, verbosity=-1)
        model.fit(
            train_df[FEATURE_COLUMNS],
            train_df[TARGET_COLUMN],
            categorical_feature=["line", "direction"],
        )

        test_predictions = model.predict(test_df[FEATURE_COLUMNS])
        model_mae = _mae(test_df[TARGET_COLUMN], test_predictions)

        baseline_rows = session.execute(select(DelayBaseline)).scalars().all()
        baselines = {
            (b.line, b.hour_of_day, b.day_of_week): b.avg_delay_seconds for b in baseline_rows
        }
        fallback = float(train_df[TARGET_COLUMN].mean())
        baseline_predictions = [
            baselines.get((row.line, row.hour_of_day, row.day_of_week), fallback)
            for row in test_df.itertuples()
        ]
        baseline_mae = _mae(test_df[TARGET_COLUMN], baseline_predictions)

        print(
            f"[train_model] n={len(df)} (train={len(train_df)}, test={len(test_df)}) "
            f"model MAE={model_mae:.1f}s, baseline MAE={baseline_mae:.1f}s"
        )

        if model_mae >= baseline_mae:
            print("[train_model] model did not beat the baseline -- not writing predictions.")
            return {
                "status": "did_not_beat_baseline",
                "model_mae": model_mae,
                "baseline_mae": baseline_mae,
                "rows": len(df),
            }

        now = datetime.now(timezone.utc)
        written = 0
        for keys, group in df.groupby(["line", "hour_of_day", "day_of_week"], observed=True):
            line, hour_of_day, day_of_week = keys
            bucket_row = group[FEATURE_COLUMNS].iloc[[-1]].copy()
            for col in CONTINUOUS_FEATURES:
                bucket_row[col] = group[col].mean()
            predicted_delay = float(model.predict(bucket_row)[0])

            stmt = insert(MLPrediction).values(
                line=line,
                hour_of_day=int(hour_of_day),
                day_of_week=int(day_of_week),
                predicted_delay_seconds=predicted_delay,
                model_version=MODEL_VERSION,
                mae_seconds=model_mae,
                baseline_mae_seconds=baseline_mae,
                sample_size=len(df),
                computed_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["line", "hour_of_day", "day_of_week"],
                set_={
                    "predicted_delay_seconds": predicted_delay,
                    "model_version": MODEL_VERSION,
                    "mae_seconds": model_mae,
                    "baseline_mae_seconds": baseline_mae,
                    "sample_size": len(df),
                    "computed_at": now,
                },
            )
            session.execute(stmt)
            written += 1

    print(
        f"[train_model] wrote {written} prediction buckets "
        f"(model beats baseline: {model_mae:.1f}s < {baseline_mae:.1f}s)"
    )
    return {
        "status": "trained",
        "model_mae": model_mae,
        "baseline_mae": baseline_mae,
        "buckets_written": written,
    }


if __name__ == "__main__":
    run()
