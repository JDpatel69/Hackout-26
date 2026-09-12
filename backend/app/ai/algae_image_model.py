"""
Algae image analysis model.

Swap `StubAlgaeImageModel` for `TrainedAlgaeImageModel` (or a remote client)
when training completes. Keep the same `BaseAlgaeImageModel` interface so
routes and services do not change.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any, Optional

from app.ai import BaseAlgaeImageModel, ImageModelInput, ImageModelOutput
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StubAlgaeImageModel(BaseAlgaeImageModel):
    """Deterministic pseudo-inference used until the real model is trained."""

    name = "algae_image_model_stub"

    def __init__(self) -> None:
        self._ready = True

    def is_ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        logger.info("StubAlgaeImageModel loaded (no weights).")

    async def predict(self, payload: ImageModelInput) -> ImageModelOutput:
        # Stable pseudo-random values derived from farm_id + image_url
        seed = int(hashlib.sha256(f"{payload.farm_id}:{payload.image_url}".encode()).hexdigest()[:8], 16)
        coverage = 45.0 + (seed % 4500) / 100.0  # 45–90%
        health = 55.0 + (seed % 4000) / 100.0  # 55–95
        area = payload.farm_area_hectares or 1.0
        biomass = round(area * (coverage / 100.0) * (1.2 + (seed % 80) / 100.0), 3)
        bloom = (seed % 17) == 0
        species = payload.algae_species or "Chlorella vulgaris"
        confidence = 0.62 + (seed % 35) / 100.0
        flags: list[str] = []
        if bloom:
            flags.append("possible_bloom")
        if health < 60:
            flags.append("low_health_signal")
        if coverage < 50:
            flags.append("sparse_coverage")

        raw = {
            "mode": "stub",
            "note": "Replace StubAlgaeImageModel with trained weights when ready.",
            "seed": seed,
            "input": {
                "farm_id": payload.farm_id,
                "image_url": payload.image_url,
                "source": payload.source,
            },
        }
        return ImageModelOutput(
            model_version="stub-v0.1",
            algae_coverage_pct=round(coverage, 2),
            estimated_biomass_tonnes=biomass,
            health_score=round(health, 2),
            bloom_detected=bloom,
            species_confidence=round(min(confidence, 0.99), 3),
            predicted_species=species,
            anomaly_flags=flags,
            raw_output=raw,
            is_stub=True,
        )


class TrainedAlgaeImageModel(BaseAlgaeImageModel):
    """
    Placeholder for the real vision model.

    TODO when training finishes:
      1. Place weights under AI_IMAGE_MODEL_PATH (e.g. TorchScript / ONNX / .pt).
      2. Implement `load()` to deserialize the model.
      3. Implement `predict()` to preprocess the image and run inference.
      4. Set AI_IMAGE_MODEL_ENABLED=true in .env.
    """

    name = "algae_image_model"

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = Path(model_path or settings.AI_IMAGE_MODEL_PATH)
        self._model: Any = None
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready and self._model is not None

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Algae image model not found at {self.model_path}. "
                "Train the model or keep AI_IMAGE_MODEL_ENABLED=false."
            )
        # Example hooks (uncomment / adapt when ready):
        # import torch
        # self._model = torch.jit.load(str(self.model_path / "model.pt"))
        # self._model.eval()
        #
        # Or ONNX:
        # import onnxruntime as ort
        # self._model = ort.InferenceSession(str(self.model_path / "model.onnx"))
        raise NotImplementedError(
            "TrainedAlgaeImageModel.load() is a placeholder. "
            "Wire your trained vision weights here."
        )

    async def predict(self, payload: ImageModelInput) -> ImageModelOutput:
        if not self.is_ready():
            raise RuntimeError("Algae image model is not loaded.")
        # TODO: download/open image from payload.image_url, preprocess, infer
        raise NotImplementedError("TrainedAlgaeImageModel.predict() not implemented yet.")


class RemoteAlgaeImageModel(BaseAlgaeImageModel):
    """Optional HTTP client if the image model runs as a separate inference service."""

    name = "algae_image_model_remote"

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.AI_IMAGE_MODEL_URL).rstrip("/")
        self._ready = bool(self.base_url)

    def is_ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        if not self.base_url:
            raise ValueError("AI_IMAGE_MODEL_URL is empty.")
        logger.info("RemoteAlgaeImageModel pointing at %s", self.base_url)

    async def predict(self, payload: ImageModelInput) -> ImageModelOutput:
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/predict",
                json={
                    "farm_id": payload.farm_id,
                    "image_url": payload.image_url,
                    "source": payload.source,
                    "farm_area_hectares": payload.farm_area_hectares,
                    "algae_species": payload.algae_species,
                    "metadata": payload.metadata,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return ImageModelOutput(
            model_version=data.get("model_version", "remote"),
            algae_coverage_pct=float(data["algae_coverage_pct"]),
            estimated_biomass_tonnes=float(data["estimated_biomass_tonnes"]),
            health_score=float(data["health_score"]),
            bloom_detected=bool(data.get("bloom_detected", False)),
            species_confidence=float(data.get("species_confidence", 0.0)),
            predicted_species=data.get("predicted_species"),
            anomaly_flags=list(data.get("anomaly_flags", [])),
            raw_output=data,
            is_stub=False,
        )
