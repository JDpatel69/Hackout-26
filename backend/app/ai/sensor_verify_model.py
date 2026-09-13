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
from typing import Any, List, Optional, Tuple

from app.ai import BaseSensorVerifyModel, SensorModelInput, SensorModelOutput
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Exact feature order the XGBoost regressor was trained on (Sensor_Node/Scripts/train.py).
SENSOR_FEATURES: list[str] = [
    "Irradiance", "NO3", "Temperature", "pH", "O2 Gas", "CO2 Gas", "Conductivity",
]
# Per-feature fallback = median of the training set
# (Verrucodesmus_verrucosus_10k_augmented.csv, n=10800). Used when a reading
# does not carry that signal, so the model always gets a physically-plausible row.
FEATURE_DEFAULTS: dict[str, float] = {
    "Irradiance": 141.24,
    "NO3": 73.92,
    "Temperature": 22.24,
    "pH": 7.84,
    "O2 Gas": 9.35,
    "CO2 Gas": 647.01,
    "Conductivity": 280.39,
}
# Observed Biomass target range in training (g/L) — predictions far outside this
# are extrapolations and get flagged.
BIOMASS_TRAIN_MIN = 0.1
BIOMASS_TRAIN_MAX = 3.37


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
    In-process XGBoost biomass regressor (Sensor_Node/Outputs/xgboost_biomass_model.pkl).

    Maps each backend SensorReading onto the 7 features the model was trained on,
    predicts Biomass (g/L), and derives data-quality / sequestration / anomaly /
    consistency signals around it. Heavy libs (joblib, pandas) are imported lazily
    so a missing dependency degrades to the stub via the registry rather than
    breaking module import.
    """

    name = "sensor_verify_model"

    def __init__(self, model_path: Optional[str] = None) -> None:
        # Prefer the explicit absolute file; fall back to a *.pkl/*.joblib in the dir.
        self.model_file = (model_path or settings.AI_SENSOR_MODEL_FILE or "").strip()
        self.model_dir = Path(settings.AI_SENSOR_MODEL_PATH)
        self._model: Any = None
        self._ready = False
        self._features: list[str] = list(SENSOR_FEATURES)

    def is_ready(self) -> bool:
        return self._ready and self._model is not None

    def _resolve_path(self) -> Path:
        if self.model_file:
            p = Path(self.model_file)
            if p.exists():
                return p
        if self.model_dir.exists():
            for pat in ("*.pkl", "*.joblib"):
                hits = sorted(self.model_dir.glob(pat))
                if hits:
                    return hits[0]
        raise FileNotFoundError(
            f"Sensor model not found (file={self.model_file!r}, dir={self.model_dir}). "
            "Set AI_SENSOR_MODEL_FILE or keep AI_SENSOR_MODEL_ENABLED=false."
        )

    def load(self) -> None:
        import joblib  # lazy — see class docstring

        path = self._resolve_path()
        self._model = joblib.load(path)
        # Trust the model's own feature order if present (guards against drift).
        fn = getattr(self._model, "feature_names_in_", None)
        if fn is not None:
            self._features = [str(x) for x in fn]
        self._path = path
        self._ready = True
        logger.info("TrainedSensorVerifyModel loaded from %s (features=%s)", path, self._features)

    # ── feature extraction ────────────────────────────────────────────────
    def _extract_row(self, r: dict) -> Tuple[dict, int]:
        """Map one reading dict → {feature: value}, plus count of *real* (non-defaulted) features."""
        raw = r.get("rawPayload") or {}

        def pick(primary: Optional[str], raw_keys: list[str], feature: str) -> Tuple[float, bool]:
            if primary is not None:
                v = r.get(primary)
                if v is not None:
                    try:
                        return float(v), True
                    except (TypeError, ValueError):
                        pass
            for k in raw_keys:
                if k in raw and raw[k] is not None:
                    try:
                        return float(raw[k]), True
                    except (TypeError, ValueError):
                        pass
            return FEATURE_DEFAULTS[feature], False

        vals: dict[str, float] = {}
        real = 0
        specs = [
            ("Irradiance", "lightIntensityUmol", ["Irradiance"]),
            ("NO3", "nutrientNMgL", ["NO3"]),
            ("Temperature", "waterTemperatureC", ["Temperature"]),
            ("pH", "waterPh", ["pH"]),
            ("O2 Gas", "dissolvedOxygen", ["O2 Gas", "O2Gas", "o2_gas"]),
            ("CO2 Gas", None, ["CO2 Gas", "CO2Gas", "co2_gas"]),
            ("Conductivity", None, ["Conductivity", "conductivity"]),
        ]
        for feature, primary, raw_keys in specs:
            v, was_real = pick(primary, raw_keys, feature)
            vals[feature] = v
            real += int(was_real)
        return vals, real

    async def predict(self, payload: SensorModelInput) -> SensorModelOutput:
        if not self.is_ready():
            raise RuntimeError("Sensor verify model is not loaded.")
        import pandas as pd  # lazy — see class docstring

        readings = payload.readings or []
        hours = max((payload.window_end - payload.window_start).total_seconds() / 3600.0, 1.0)

        # Build the feature matrix (fall back to a single median row if no readings,
        # so dual-verify still works for farms without sensor history).
        used_default_row = False
        if readings:
            rows, reals = zip(*(self._extract_row(r) for r in readings))
            rows, reals = list(rows), list(reals)
        else:
            rows = [dict(FEATURE_DEFAULTS)]
            reals = [0]
            used_default_row = True

        df = pd.DataFrame(rows, columns=self._features)
        preds = [float(x) for x in self._model.predict(df)]
        biomass_mean = statistics.fmean(preds)
        biomass_std = statistics.pstdev(preds) if len(preds) > 1 else 0.0

        # Completeness = mean fraction of the 7 features that were real.
        completeness = statistics.fmean([n / len(self._features) for n in reals]) if reals else 0.0
        n = len(readings)
        count_factor = min(1.0, n / 10.0)
        cv = (biomass_std / biomass_mean) if biomass_mean > 1e-6 else 0.0
        spread_ok = max(0.0, 1.0 - min(1.0, cv))

        quality = 100.0 * (0.55 * completeness + 0.30 * count_factor + 0.15 * spread_ok)
        quality = round(max(30.0, min(99.0, quality)), 2)
        confidence = round(max(0.30, min(0.98, 0.40 + 0.35 * completeness + 0.15 * count_factor - 0.2 * min(1.0, cv))), 3)

        # ── sequestration (keep flux×hours semantics used downstream) ──
        co2_vals = [r["co2UptakeKgH"] for r in readings if r.get("co2UptakeKgH") is not None]
        if co2_vals:
            mean_co2 = statistics.fmean(co2_vals)
            sequestration = round(mean_co2 * hours, 3)
            seq_basis = "co2_flux_x_hours"
        else:
            # No measured flux: estimate a conservative uptake from predicted biomass.
            # ~1.83 g CO2 fixed per g dry biomass; scale by area as a coarse proxy.
            area = payload.farm_area_hectares or 1.0
            est_kg_h = max(0.0, biomass_mean) * area * 0.05
            sequestration = round(est_kg_h * hours, 3)
            seq_basis = "estimated_from_biomass"

        # ── anomalies ──
        ph_vals = [r["waterPh"] for r in readings if r.get("waterPh") is not None]
        do_vals = [r["dissolvedOxygen"] for r in readings if r.get("dissolvedOxygen") is not None]
        anomalies: list[str] = []
        if ph_vals and (min(ph_vals) < 6.5 or max(ph_vals) > 9.0):
            anomalies.append("ph_out_of_range")
        if do_vals and min(do_vals) < 2.0:
            anomalies.append("low_dissolved_oxygen")
        if n < 3:
            anomalies.append("insufficient_samples")
        if biomass_mean < BIOMASS_TRAIN_MIN * 0.8 or biomass_mean > BIOMASS_TRAIN_MAX * 1.2:
            anomalies.append("biomass_out_of_training_range")
        # Model value-add: reported biomassDensity vs XGBoost prediction.
        reported_bd = [r["biomassDensity"] for r in readings if r.get("biomassDensity") is not None]
        if reported_bd:
            rep_mean = statistics.fmean(reported_bd)
            if rep_mean > 0.05 and abs(biomass_mean - rep_mean) / rep_mean > 0.35:
                anomalies.append("biomass_model_mismatch")

        # ── consistency with the image model (abundance agreement, 0–100) ──
        consistency: Optional[float] = None
        if payload.image_cross_check:
            cov = payload.image_cross_check.get("algae_coverage_pct")
            if cov is not None:
                sensor_norm = max(0.0, min(1.0, (biomass_mean - BIOMASS_TRAIN_MIN) / (BIOMASS_TRAIN_MAX - BIOMASS_TRAIN_MIN))) * 100.0
                consistency = round(max(30.0, 100.0 - abs(sensor_norm - float(cov)) * 0.6), 2)

        # ── verdict ──
        if "biomass_model_mismatch" in anomalies or "ph_out_of_range" in anomalies:
            verdict = "suspicious"
        elif "insufficient_samples" in anomalies and quality < 50:
            verdict = "invalid"
        else:
            verdict = "plausible"

        raw = {
            "mode": "trained",
            "model": "xgboost_biomass",
            "model_file": Path(getattr(self, "_path", self.model_file or "")).name,
            "feature_order": self._features,
            "predicted_biomass_g_l": round(biomass_mean, 4),
            "predicted_biomass_min_g_l": round(min(preds), 4),
            "predicted_biomass_max_g_l": round(max(preds), 4),
            "predicted_biomass_std": round(biomass_std, 4),
            "sample_count": n,
            "feature_completeness": round(completeness, 3),
            "used_default_row": used_default_row,
            "sequestration_basis": seq_basis,
            "window_hours": round(hours, 3),
            "biomass_training_range_g_l": [BIOMASS_TRAIN_MIN, BIOMASS_TRAIN_MAX],
        }
        return SensorModelOutput(
            model_version="xgboost-biomass-v1",
            data_quality_score=quality,
            sequestration_kg_co2e=sequestration,
            sequestration_confidence=confidence,
            anomaly_detected=bool(anomalies),
            anomaly_details=anomalies,
            consistency_with_image=consistency,
            verdict=verdict,
            raw_output=raw,
            is_stub=False,
        )


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
