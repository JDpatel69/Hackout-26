"""
Algae image analysis model.

Swap `StubAlgaeImageModel` for `TrainedAlgaeImageModel` (or a remote client)
when training completes. Keep the same `BaseAlgaeImageModel` interface so
routes and services do not change.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import math
from pathlib import Path
from typing import Any, Optional

import numpy as np

from app.ai import BaseAlgaeImageModel, ImageModelInput, ImageModelOutput
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _sigmoid(x: "np.ndarray") -> "np.ndarray":
    return 1.0 / (1.0 + np.exp(-x))


def greenness_indices(rgb: "np.ndarray", mask: "np.ndarray") -> dict:
    """
    ExG / VARI / GLI averaged over the algae mask (ported from Models/serve_api.py).
    `rgb` is HxWx3 float; `mask` is HxW bool. Falls back to the whole frame if the
    mask is empty so the indices are always defined.
    """
    px = rgb[mask] if mask.any() else rgb.reshape(-1, 3)
    R, G, B = px[:, 0], px[:, 1], px[:, 2]
    total = R + G + B + 1e-6
    r, g, b = R / total, G / total, B / total
    exg = float(np.mean(2.0 * g - r - b))
    vari = float(np.mean((g - r) / (g + r - b + 1e-6)))
    gli = float(np.mean((2.0 * g - r - b) / (2.0 * g + r + b + 1e-6)))
    return {"exg": round(exg, 4), "vari": round(vari, 4), "gli": round(gli, 4)}


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
    In-process ONNX segmentation model (Models/algae_segmentation.onnx).

    Runs via onnxruntime (no torch needed). Ports the preprocessing / greenness /
    coverage logic from Models/serve_api.py. onnxruntime is imported lazily so a
    missing dependency degrades to the stub via the registry rather than breaking
    module import.
    """

    name = "algae_image_model"

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_file = (model_path or settings.AI_IMAGE_MODEL_FILE or "").strip()
        self.model_dir = Path(settings.AI_IMAGE_MODEL_PATH)
        self._session: Any = None
        self._input_name: str = "input"
        self._output_name: Optional[str] = None
        self._tile: int = settings.AI_IMAGE_TILE_SIZE
        self._mean = np.array(settings.image_norm_mean, dtype=np.float32).reshape(1, 1, 3)
        self._std = np.array(settings.image_norm_std, dtype=np.float32).reshape(1, 1, 3)
        self._threshold: float = settings.AI_IMAGE_THRESHOLD
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready and self._session is not None

    def _resolve_path(self) -> Path:
        if self.model_file:
            p = Path(self.model_file)
            if p.exists():
                return p
        if self.model_dir.exists():
            hits = sorted(self.model_dir.glob("*.onnx"))
            if hits:
                return hits[0]
        raise FileNotFoundError(
            f"Image model not found (file={self.model_file!r}, dir={self.model_dir}). "
            "Set AI_IMAGE_MODEL_FILE or keep AI_IMAGE_MODEL_ENABLED=false."
        )

    def load(self) -> None:
        import onnxruntime as ort  # lazy — see class docstring

        path = self._resolve_path()
        self._session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        inp = self._session.get_inputs()[0]
        self._input_name = inp.name
        self._output_name = self._session.get_outputs()[0].name
        # Fixed spatial dims in the ONNX graph override the configured tile size.
        if len(inp.shape) == 4 and isinstance(inp.shape[2], int) and inp.shape[2] > 0:
            self._tile = int(inp.shape[2])
        self._path = path
        self._ready = True
        logger.info(
            "TrainedAlgaeImageModel loaded from %s (input=%s tile=%d output=%s)",
            path, self._input_name, self._tile, self._output_name,
        )

    async def _fetch(self, url: str) -> Optional[bytes]:
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.content
        except Exception as exc:  # noqa: BLE001
            logger.warning("Image fetch failed for %s: %s", url, exc)
            return None

    async def predict(self, payload: ImageModelInput) -> ImageModelOutput:
        if not self.is_ready():
            raise RuntimeError("Algae image model is not loaded.")

        img_bytes = payload.image_bytes
        if img_bytes is None and payload.image_url and payload.image_url.startswith(("http://", "https://")):
            img_bytes = await self._fetch(payload.image_url)
        if not img_bytes:
            return self._degraded(payload, "no_image_bytes")

        try:
            # Preprocessing + CPU inference are blocking → run off the event loop.
            return await asyncio.to_thread(self._infer, img_bytes, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Image inference failed (%s); returning degraded result.", exc)
            return self._degraded(payload, f"inference_error:{type(exc).__name__}")

    def _infer(self, img_bytes: bytes, payload: ImageModelInput) -> ImageModelOutput:
        from PIL import Image

        pil = Image.open(io.BytesIO(img_bytes)).convert("RGB").resize((self._tile, self._tile))
        rgb = np.asarray(pil, dtype=np.float32)  # HxWx3, 0..255
        norm = (rgb / 255.0 - self._mean) / self._std
        chw = np.transpose(norm, (2, 0, 1))[None, ...].astype(np.float32)  # 1x3xHxW

        logits = self._session.run([self._output_name], {self._input_name: chw})[0]
        prob = _sigmoid(np.asarray(logits, dtype=np.float32)).reshape(-1)  # flatten HxW (1 channel)
        prob = prob[: self._tile * self._tile].reshape(self._tile, self._tile)
        mask = prob > self._threshold

        total_px = int(mask.size)
        canopy_px = int(mask.sum())
        coverage = canopy_px / max(total_px, 1)
        mean_conf_overall = float(prob.mean())
        mean_conf_in_mask = float(prob[mask].mean()) if canopy_px > 0 else mean_conf_overall
        green = greenness_indices(rgb, mask)

        # Health: blend greenness (healthy algae is green) with segmentation confidence.
        green01 = max(0.0, min(1.0, (green["exg"] + green["gli"] + 0.1) / 0.6))
        health = round(100.0 * (0.55 * green01 + 0.45 * mean_conf_in_mask), 2)

        # Provisional biomass from coverage×area — NOT calibrated (see note). The
        # XGBoost sensor model is the authoritative biomass source.
        area = payload.farm_area_hectares or 1.0
        biomass = round(area * coverage * 1.5, 3)

        bloom = coverage > 0.9 and green01 > 0.6

        flags: list[str] = []
        if coverage > 0.95:
            flags.append("coverage_near_full")
        if coverage < 0.005:
            flags.append("coverage_near_zero")
        if mean_conf_overall < 0.7:
            flags.append("low_segmentation_confidence")
        if bloom:
            flags.append("possible_bloom")

        raw = {
            "mode": "trained",
            "model": "onnx_segmentation",
            "model_file": Path(getattr(self, "_path", self.model_file or "")).name,
            "preprocess": "resize_to_tile",
            "image_size": self._tile,
            "threshold": self._threshold,
            "norm_mean": [round(float(x), 4) for x in self._mean.reshape(-1)],
            "norm_std": [round(float(x), 4) for x in self._std.reshape(-1)],
            "coverage_fraction": round(coverage, 5),
            "canopy_area_px": canopy_px,
            "total_px": total_px,
            "mean_confidence": round(mean_conf_overall, 4),
            "mean_confidence_in_mask": round(mean_conf_in_mask, 4),
            "greenness": green,
            "warnings": flags,
            "biomass_note": (
                "estimatedBiomassTonnes is a provisional coverage×area heuristic and is "
                "NOT calibrated; use the sensor XGBoost model for authoritative biomass."
            ),
            "species_note": "segmentation net does not classify species; predictedSpecies is a passthrough.",
        }
        return ImageModelOutput(
            model_version="onnx-seg-v1",
            algae_coverage_pct=round(coverage * 100.0, 2),
            estimated_biomass_tonnes=biomass,
            health_score=health,
            bloom_detected=bool(bloom),
            species_confidence=round(mean_conf_in_mask, 3),
            predicted_species=payload.algae_species,
            anomaly_flags=flags,
            raw_output=raw,
            is_stub=False,
        )

    def _degraded(self, payload: ImageModelInput, reason: str) -> ImageModelOutput:
        """No decodable image → honest neutral result (still a trained-model response)."""
        return ImageModelOutput(
            model_version="onnx-seg-v1",
            algae_coverage_pct=0.0,
            estimated_biomass_tonnes=0.0,
            health_score=60.0,
            bloom_detected=False,
            species_confidence=0.0,
            predicted_species=payload.algae_species,
            anomaly_flags=[reason],
            raw_output={
                "mode": "trained",
                "model": "onnx_segmentation",
                "note": reason,
                "detail": "No image bytes available (upload an image or provide an http(s) image_url).",
            },
            is_stub=False,
        )


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
