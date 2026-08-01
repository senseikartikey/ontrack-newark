from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from routers import alerts, lines

app = FastAPI(title="OnTrack Newark API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(lines.router)
app.include_router(alerts.router)


@app.get("/health")
def health():
    return {"status": "ok"}
