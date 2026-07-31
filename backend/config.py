import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]

# Mirrors /ingestion/config.py's NEWARK_AREA_LINES -- kept in sync manually, see the
# note in backend/models.py about why these aren't shared via cross-directory import.
NEWARK_AREA_LINES = [
    "Northeast Corridor",
    "North Jersey Coast Line",
    "Raritan Valley Line",
    "Morristown Line",
    "Gladstone Branch",
    "Montclair-Boonton Line",
]
