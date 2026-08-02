import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Below this many observed trip_updates in a (line, hour_of_day, day_of_week) bucket,
# the baseline is not written -- an average of 2-3 delay readings is noise, not a
# prediction. Chosen as a reasonable starting point, not tuned against real data yet
# (there isn't any); revisit once a few weeks of real ingestion history exist.
MIN_SAMPLES_THRESHOLD = 20

# Risk-level thresholds, in seconds of average historical delay for the bucket.
RISK_LOW_MAX_SECONDS = 120
RISK_MEDIUM_MAX_SECONDS = 300
# anything above RISK_MEDIUM_MAX_SECONDS is "high"

# v2 model: below this many total (deduplicated) training rows, train_model.py skips
# training entirely rather than fitting (and potentially serving) an overfit model.
# 500 is a starting guess reasoned from wanting a few dozen samples per line even
# after a train/test split across ~6-8 lines -- not tuned against real data yet
# (there isn't nearly enough yet); revisit once real volume exists.
MIN_TRAINING_ROWS = 500

# Fraction of rows (by time, not randomly -- see train_model.py) held out for
# evaluating the model against the baseline.
TEST_HOLDOUT_FRACTION = 0.2

# Track-prediction feature (compute_track_predictions.py) -- New York Penn Station
# specifically, styled after Clever Commute's published methodology: group by exact
# train_id (not line/time-of-day) and count how often each track was historically
# used for that specific train. Thresholds below are starting points reasoned from
# Clever Commute's own stated ~20-observation minimum / ~60-day-window guidance, not
# yet tuned against real NY Penn track data (there isn't any yet -- see that module's
# docstring). Revisit once real observations exist to reason about the real
# distribution.
#
# Below TRACK_MIN_SAMPLES_LOW, no row is written at all -- insufficient data, not a
# fabricated low-confidence guess (same honesty convention as MIN_SAMPLES_THRESHOLD/
# MIN_TRAINING_ROWS above).
TRACK_MIN_SAMPLES_LOW = 3
TRACK_MIN_SAMPLES_MEDIUM = 5
TRACK_MIN_SAMPLES_HIGH = 10
TRACK_SHARE_MEDIUM = 0.4
TRACK_SHARE_HIGH = 0.7

# NJT RailData's 2-character station code for New York Penn Station -- see
# ingestion/models.py's TrackAssignment docstring for the full station-identifier-
# space context.
NY_PENN_STATION_CODE = "NY"
