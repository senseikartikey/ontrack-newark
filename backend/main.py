from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routers import advisories, alerts, data_confidence, lines, stations, trips

app = FastAPI(title="OnTrack API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(lines.router)
app.include_router(alerts.router)
app.include_router(advisories.router)
app.include_router(data_confidence.router)
app.include_router(stations.router)
app.include_router(trips.router)


@app.get("/health")
def health():
    return {"status": "ok"}
