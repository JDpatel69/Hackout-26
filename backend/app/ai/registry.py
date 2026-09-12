"""Factory that picks stub vs trained vs remote AI models based on settings."""

from __future__ import annotations

import logging
from typing import Optional

from app.ai import BaseAlgaeImageModel, BaseSensorVerifyModel
from app.ai.algae_image_model import (
    RemoteAlgaeImageModel,
    StubAlgaeImageModel,
    TrainedAlgaeImageModel,
)
from app.ai.sensor_verify_model import (
    RemoteSensorVerifyModel,
    StubSensorVerifyModel,
    TrainedSensorVerifyModel,
)
from app.config import get_settings

logger = logging.getLogger(__name__)

_image_model: Optional[BaseAlgaeImageModel] = None
_sensor_model: Optional[BaseSensorVerifyModel] = None


def get_image_model() -> BaseAlgaeImageModel:
    global _image_model
    if _image_model is None:
        _image_model = _build_image_model()
    return _image_model


def get_sensor_model() -> BaseSensorVerifyModel:
    global _sensor_model
    if _sensor_model is None:
        _sensor_model = _build_sensor_model()
    return _sensor_model


def _build_image_model() -> BaseAlgaeImageModel:
    settings = get_settings()
    if settings.AI_IMAGE_MODEL_ENABLED:
        if settings.AI_IMAGE_MODEL_URL:
            model: BaseAlgaeImageModel = RemoteAlgaeImageModel()
        else:
            model = TrainedAlgaeImageModel()
        try:
            model.load()
            logger.info("Using ENABLED algae image model: %s", model.name)
            return model
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load trained image model (%s); falling back to stub.", exc)
    stub = StubAlgaeImageModel()
    stub.load()
    logger.info("Using stub algae image model.")
    return stub


def _build_sensor_model() -> BaseSensorVerifyModel:
    settings = get_settings()
    if settings.AI_SENSOR_MODEL_ENABLED:
        if settings.AI_SENSOR_MODEL_URL:
            model: BaseSensorVerifyModel = RemoteSensorVerifyModel()
        else:
            model = TrainedSensorVerifyModel()
        try:
            model.load()
            logger.info("Using ENABLED sensor verify model: %s", model.name)
            return model
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load trained sensor model (%s); falling back to stub.", exc)
    stub = StubSensorVerifyModel()
    stub.load()
    logger.info("Using stub sensor verify model.")
    return stub


def model_status() -> dict:
    settings = get_settings()
    img = get_image_model()
    sen = get_sensor_model()
    return {
        "image": {
            "name": img.name,
            "enabled_flag": settings.AI_IMAGE_MODEL_ENABLED,
            "ready": img.is_ready(),
            "is_stub": isinstance(img, StubAlgaeImageModel),
            "path": settings.AI_IMAGE_MODEL_PATH,
            "url": settings.AI_IMAGE_MODEL_URL or None,
        },
        "sensor": {
            "name": sen.name,
            "enabled_flag": settings.AI_SENSOR_MODEL_ENABLED,
            "ready": sen.is_ready(),
            "is_stub": isinstance(sen, StubSensorVerifyModel),
            "path": settings.AI_SENSOR_MODEL_PATH,
            "url": settings.AI_SENSOR_MODEL_URL or None,
        },
    }
