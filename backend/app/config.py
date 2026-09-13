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

    # AI model integration flags. Both trained models now ship in-process
    # (XGBoost via joblib, ONNX via onnxruntime). The registry falls back to the
    # deterministic stub on any load error, so a missing file degrades safely.
    AI_IMAGE_MODEL_ENABLED: bool = True
    AI_SENSOR_MODEL_ENABLED: bool = True
    AI_IMAGE_MODEL_PATH: str = "./models/algae_image_model"
    AI_SENSOR_MODEL_PATH: str = "./models/sensor_verify_model"
    AI_IMAGE_MODEL_URL: str = ""
    AI_SENSOR_MODEL_URL: str = ""

    # Absolute paths to the trained model artifacts (no file-copying required).
    # If blank, the registry looks for a .onnx / .pkl|.joblib under the *_PATH dir.
    AI_IMAGE_MODEL_FILE: str = r"C:\Users\dharm\OneDrive\Desktop\Models\algae_segmentation.onnx"
    AI_SENSOR_MODEL_FILE: str = r"C:\Users\dharm\OneDrive\Desktop\Sensor_Node\Outputs\xgboost_biomass_model.pkl"

    # Image preprocessing knobs for the ONNX segmentation net (env-overridable).
    # ONNX does not carry the checkpoint's norm constants / tile size, so we
    # default to the training values (ImageNet stats unless inspect_checkpoint.py
    # says otherwise) and allow overrides without touching code.
    AI_IMAGE_TILE_SIZE: int = 512
    AI_IMAGE_NORM_MEAN: str = "0.485,0.456,0.406"
    AI_IMAGE_NORM_STD: str = "0.229,0.224,0.225"
    AI_IMAGE_THRESHOLD: float = 0.5

    UPLOAD_DIR: str = "./uploads"

    # ── Additive "wow feature" flags (P1–P5). All default ON; set false to
    #    disable a feature and fall back to the original app behavior. ──────
    ENABLE_LIVE_TELEMETRY: bool = True   # P1: live pond twin + streaming telemetry
    ENABLE_DUAL_AI_PANEL: bool = True    # P2: explainable dual-AI trust endpoint
    ENABLE_CERTIFICATES: bool = True     # P3: tamper-evident hash-chained certificates
    ENABLE_SATELLITE: bool = True        # P4: NASA GIBS remote-sensing view
    ENABLE_IMPACT_PUBLIC: bool = True    # P5: public impact aggregates
    ENABLE_FLEET: bool = True            # P5: fleet map sites
    ENABLE_WHATIF: bool = True           # P5: what-if modeled projection
    # When true, live endpoints synthesize gradual *simulated* readings (clearly
    # labeled dataSource="simulation") if a farm has no recent live device data.
    LIVE_DEMO_MODE: bool = True
    # Frontend origin embedded in issued certificates (QR + public verify link).
    PUBLIC_APP_URL: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @staticmethod
    def _parse_triple(raw: str, fallback: tuple) -> tuple:
        try:
            vals = tuple(float(x.strip()) for x in raw.split(",") if x.strip())
            return vals if len(vals) == 3 else fallback
        except (ValueError, AttributeError):
            return fallback

    @property
    def image_norm_mean(self) -> tuple:
        return self._parse_triple(self.AI_IMAGE_NORM_MEAN, (0.485, 0.456, 0.406))

    @property
    def image_norm_std(self) -> tuple:
        return self._parse_triple(self.AI_IMAGE_NORM_STD, (0.229, 0.224, 0.225))


@lru_cache
def get_settings() -> Settings:
    return Settings()
