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
