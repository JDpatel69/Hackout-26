"""
AI model integration layer.

Two models will be trained later and plugged in here:

1. AlgaeImageModel  — vision model that estimates algae coverage, biomass,
                      health, and species from drone/satellite/pond photos.
2. SensorVerifyModel — time-series / tabular model that validates IoT sensor
                       streams (growth rate, CO2 uptake, water quality) and
                       estimates sequestration with a confidence score.

Until `AI_*_MODEL_ENABLED=true` in settings, both return deterministic stub
outputs so the rest of the API and frontend can be developed end-to-end.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ImageModelInput:
    farm_id: str
    image_url: str
    source: str = "drone"
    farm_area_hectares: Optional[float] = None
    algae_species: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageModelOutput:
    model_version: str
    algae_coverage_pct: float
    estimated_biomass_tonnes: float
    health_score: float
    bloom_detected: bool
    species_confidence: float
    predicted_species: Optional[str]
    anomaly_flags: List[str]
    raw_output: Dict[str, Any]
    is_stub: bool


@dataclass
class SensorModelInput:
    farm_id: str
    window_start: datetime
    window_end: datetime
    readings: List[Dict[str, Any]]
    image_cross_check: Optional[Dict[str, Any]] = None
    farm_area_hectares: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorModelOutput:
    model_version: str
    data_quality_score: float
    sequestration_kg_co2e: float
    sequestration_confidence: float
    anomaly_detected: bool
    anomaly_details: List[str]
    consistency_with_image: Optional[float]
    verdict: str  # plausible | suspicious | invalid
    raw_output: Dict[str, Any]
    is_stub: bool


class BaseAlgaeImageModel(ABC):
    """Contract for the algae image analysis model."""

    name: str = "algae_image_model"

    @abstractmethod
    def is_ready(self) -> bool:
        ...

    @abstractmethod
    def load(self) -> None:
        """Load weights from disk / remote. Called once at startup when enabled."""

    @abstractmethod
    async def predict(self, payload: ImageModelInput) -> ImageModelOutput:
        ...


class BaseSensorVerifyModel(ABC):
    """Contract for the sensor-data verification model."""

    name: str = "sensor_verify_model"

    @abstractmethod
    def is_ready(self) -> bool:
        ...

    @abstractmethod
    def load(self) -> None:
        ...

    @abstractmethod
    async def predict(self, payload: SensorModelInput) -> SensorModelOutput:
        ...
