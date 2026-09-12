from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Algae Carbon MRV API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///./mrv.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # AI model integration flags (models train later — stubs used until enabled)
    AI_IMAGE_MODEL_ENABLED: bool = False
    AI_SENSOR_MODEL_ENABLED: bool = False
    AI_IMAGE_MODEL_PATH: str = "./models/algae_image_model"
    AI_SENSOR_MODEL_PATH: str = "./models/sensor_verify_model"
    AI_IMAGE_MODEL_URL: str = ""
    AI_SENSOR_MODEL_URL: str = ""

    UPLOAD_DIR: str = "./uploads"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
