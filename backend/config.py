import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# Mirrors /ingestion/config.py's NEWARK_AREA_LINES -- kept in sync manually, see the
# note in backend/models.py about why these aren't shared via cross-directory import.
# Verified route_short_name codes -- see ENGINEERING_LOG.md (2026-07-30).
NEWARK_AREA_LINES = ["NEC", "NJCL", "NJCLL", "RARV", "BNTN", "BNTNM", "MNE", "MNEG"]

NEWARK_STATION_STOP_IDS = {"106": "Newark Broad Street", "107": "Newark Penn Station"}

# route_short_name -> route_long_name, from the static GTFS routes.txt (2026-07-30).
LINE_DISPLAY_NAMES = {
    "NEC": "Northeast Corridor",
    "NJCL": "North Jersey Coast Line",
    "NJCLL": "North Jersey Coast Line",
    "RARV": "Raritan Valley Line",
    "BNTN": "Montclair-Boonton Line",
    "BNTNM": "Montclair-Boonton Line",
    "MNE": "Morris & Essex Line",
    "MNEG": "Gladstone Branch",
}

# Mirrors /ml/config.py's risk thresholds -- see that file for reasoning.
RISK_LOW_MAX_SECONDS = 120
RISK_MEDIUM_MAX_SECONDS = 300
