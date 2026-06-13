from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes_admin import router as admin_router
from app.api.routes_ai import router as ai_router
from app.api.routes_health import router as health_router
from app.api.routes_parking import router as parking_router
from app.logging_config import configure_logging
from app.settings import get_settings

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Urban smart parking backend for one parking lot in Prishtina",
)

app.include_router(health_router)
app.include_router(parking_router)
app.include_router(ai_router)
app.include_router(admin_router)

STATIC_DIR = Path(__file__).resolve().parent / "static"
IMAGES_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


@app.get("/", include_in_schema=False)
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "locations.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
