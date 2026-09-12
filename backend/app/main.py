"""FastAPI entrypoint — Algae Carbon Credit MRV Backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.ai.registry import model_status
from app.api.routes import api_router
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.schemas import HealthOut
from app.seed import seed_if_empty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path("./models/algae_image_model").mkdir(parents=True, exist_ok=True)
    Path("./models/sensor_verify_model").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
        logger.info("Database ready. Demo password for all users: password123")
        logger.info("AI model status: %s", model_status())
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description=(
        "Backend for the Algae Carbon Credit MRV marketplace. "
        "Includes IoT sensor ingestion and stub hooks for two AI models "
        "(algae image analysis + sensor verification) that will be swapped "
        "in once training completes."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", response_model=HealthOut, tags=["system"])
def health() -> HealthOut:
    status = model_status()
    return HealthOut(
        status="ok",
        app=settings.APP_NAME,
        version=__version__,
        aiImageModel=status["image"],
        aiSensorModel=status["sensor"],
    )


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "message": "Algae Carbon MRV API",
        "docs": "/docs",
        "health": "/health",
        "api": "/api",
    }
