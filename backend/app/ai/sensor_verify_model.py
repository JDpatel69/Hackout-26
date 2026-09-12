"""
Sensor-data verification model.

Validates IoT streams (growth rate, CO2 uptake, water quality) and estimates
carbon sequestration. Stubbed until training completes.
"""

from __future__ import annotations

import hashlib
import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.ai import BaseSensorVerifyModel, SensorModelInput, SensorModelOutput
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _safe_mean(values: list[float]) -> Optional[float]:
    return statistics.mean(values) if values else None


class StubSensorVerifyModel(BaseSensorVerifyModel):
    """Heuristic stub that mimics a trained sensor verifier."""

    name = "sensor_verify_model_stub"

    def __init__(self) -> None:
        self._ready = True

    def is_ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        logger.info("StubSensorVerifyModel loaded (no weights).")

    async def predict(self, payload: SensorModelInput) -> SensorModelOutput:
        readings = payload.readings
        seed = int(
            hashlib.sha256(
                f"{payload.farm_id}:{payload.window_start.isoformat()}:{len(readings)}".encode()
            ).hexdigest()[:8],
            16,
        )

        co2_vals = [r["co2UptakeKgH"] for r in readings if r.get("co2UptakeKgH") is not None]
        growth_vals = [r["growthRate"] for r in readings if r.get("growthRate") is not None]
        ph_vals = [r["waterPh"] for r in readings if r.get("waterPh") is not None]
        do_vals = [r["dissolvedOxygen"] for r in readings if r.get("dissolvedOxygen") is not None]

        hours = max(
            (payload.window_end - payload.window_start).total_seconds() / 3600.0,
            1.0,
        )
        mean_co2 = _safe_mean(co2_vals) or (0.8 + (seed % 120) / 100.0)
        sequestration = round(mean_co2 * hours, 3)

        anomalies: list[str] = []
        if ph_vals and (min(ph_vals) < 6.5 or max(ph_vals) > 9.0):
            anomalies.append("ph_out_of_range")
        if do_vals and min(do_vals) < 2.0:
            anomalies.append("low_dissolved_oxygen")
        if growth_vals and mean_co2 and max(growth_vals) > 0 and mean_co2 / max(max(growth_vals), 0.01) > 50:
            anomalies.append("co2_growth_inconsistency")
        if len(readings) < 3:
            anomalies.append("insufficient_samples")

        quality = 92.0 - 8.0 * len(anomalies) - (5.0 if len(readings) < 5 else 0.0)
        quality = max(35.0, min(98.0, quality + (seed % 7)))

        consistency: Optional[float] = None
        if payload.image_cross_check:
            img_biomass = payload.image_cross_check.get("estimated_biomass_tonnes")
            if img_biomass is not None and sequestration > 0:
                # crude consistency: closer biomass↔sequestration ratio → higher score
                ratio = float(img_biomass) / max(sequestration / 1000.0, 0.001)
                consistency = round(max(40.0, min(98.0, 100.0 - abs(ratio - 1.0) * 40.0)), 2)

        if "ph_out_of_range" in anomalies or "co2_growth_inconsistency" in anomalies:
            verdict = "suspicious"
        elif "insufficient_samples" in anomalies and quality < 50:
            verdict = "invalid"
        else:
            verdict = "plausible"

        confidence = round(min(0.97, 0.55 + quality / 200.0 + (seed % 10) / 100.0), 3)

        raw = {
            "mode": "stub",
            "note": "Replace StubSensorVerifyModel with trained weights when ready.",
            "sample_count": len(readings),
            "mean_co2_uptake_kg_h": mean_co2,
            "mean_growth_rate": _safe_mean(growth_vals),
            "window_hours": hours,
        }
        return SensorModelOutput(
            model_version="stub-v0.1",
            data_quality_score=round(quality, 2),
            sequestration_kg_co2e=sequestration,
            sequestration_confidence=confidence,
            anomaly_detected=bool(anomalies),
            anomaly_details=anomalies,
            consistency_with_image=consistency,
            verdict=verdict,
            raw_output=raw,
            is_stub=True,
        )


class TrainedSensorVerifyModel(BaseSensorVerifyModel):
    """
    Placeholder for the real sensor verification model.

    TODO when training finishes:
      1. Place weights under AI_SENSOR_MODEL_PATH.
      2. Implement feature engineering matching your training pipeline.
      3. Implement `load()` / `predict()`.
      4. Set AI_SENSOR_MODEL_ENABLED=true in .env.
    """

    name = "sensor_verify_model"

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = Path(model_path or settings.AI_SENSOR_MODEL_PATH)
        self._model: Any = None
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready and self._model is not None

    def load(self) -> None:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Sensor verify model not found at {self.model_path}. "
                "Train the model or keep AI_SENSOR_MODEL_ENABLED=false."
            )
        # Example:
        # import joblib
        # self._model = joblib.load(self.model_path / "model.joblib")
        # self._ready = True
        raise NotImplementedError(
            "TrainedSensorVerifyModel.load() is a placeholder. "
            "Wire your trained sensor model here."
        )

    async def predict(self, payload: SensorModelInput) -> SensorModelOutput:
        if not self.is_ready():
            raise RuntimeError("Sensor verify model is not loaded.")
        raise NotImplementedError("TrainedSensorVerifyModel.predict() not implemented yet.")


class RemoteSensorVerifyModel(BaseSensorVerifyModel):
    """HTTP client if the sensor model is served separately."""

    name = "sensor_verify_model_remote"

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (base_url or settings.AI_SENSOR_MODEL_URL).rstrip("/")
        self._ready = bool(self.base_url)

    def is_ready(self) -> bool:
        return self._ready

    def load(self) -> None:
        if not self.base_url:
            raise ValueError("AI_SENSOR_MODEL_URL is empty.")
        logger.info("RemoteSensorVerifyModel pointing at %s", self.base_url)

    async def predict(self, payload: SensorModelInput) -> SensorModelOutput:
        import httpx

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/predict",
                json={
                    "farm_id": payload.farm_id,
                    "window_start": payload.window_start.isoformat(),
                    "window_end": payload.window_end.isoformat(),
                    "readings": payload.readings,
                    "image_cross_check": payload.image_cross_check,
                    "farm_area_hectares": payload.farm_area_hectares,
                    "metadata": payload.metadata,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        return SensorModelOutput(
            model_version=data.get("model_version", "remote"),
            data_quality_score=float(data["data_quality_score"]),
            sequestration_kg_co2e=float(data["sequestration_kg_co2e"]),
            sequestration_confidence=float(data["sequestration_confidence"]),
            anomaly_detected=bool(data.get("anomaly_detected", False)),
            anomaly_details=list(data.get("anomaly_details", [])),
            consistency_with_image=data.get("consistency_with_image"),
            verdict=data.get("verdict", "plausible"),
            raw_output=data,
            is_stub=False,
        )
