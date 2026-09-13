"""AI orchestration: run image model, sensor model, or both (dual verify)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.ai import ImageModelInput, SensorModelInput
from app.ai.registry import get_image_model, get_sensor_model
from app.models import Farm, ImageAnalysis, SensorReading, SensorVerification
from app.utils.ids import new_id, now
from app.utils.mappers import image_analysis_out, sensor_out, sensor_verification_out
from app.schemas import AiTrustScoreOut, DualAiVerifyOut, ImageAnalysisOut, SensorVerificationOut


def _reading_dict(r: SensorReading) -> dict:
    # Include raw_payload so the trained sensor model can read features that have
    # no dedicated column (e.g. "CO2 Gas", "Conductivity"). The stub ignores it.
    return {**sensor_out(r).model_dump(mode="json"), "rawPayload": r.raw_payload}


async def run_image_analysis(
    db: Session,
    farm: Farm,
    image_url: str,
    source: str = "drone",
    image_bytes: Optional[bytes] = None,
) -> ImageAnalysis:
    model = get_image_model()
    result = await model.predict(
        ImageModelInput(
            farm_id=farm.id,
            image_url=image_url,
            source=source,
            farm_area_hectares=farm.area_hectares,
            algae_species=farm.algae_species,
            image_bytes=image_bytes,
        )
    )
    row = ImageAnalysis(
        id=new_id(),
        farm_id=farm.id,
        image_url=image_url,
        source=source,
        created_at=now(),
        model_version=result.model_version,
        status="completed",
        algae_coverage_pct=result.algae_coverage_pct,
        estimated_biomass_tonnes=result.estimated_biomass_tonnes,
        health_score=result.health_score,
        bloom_detected=result.bloom_detected,
        species_confidence=result.species_confidence,
        predicted_species=result.predicted_species,
        anomaly_flags=result.anomaly_flags,
        raw_output=result.raw_output,
        is_stub=result.is_stub,
    )
    farm.last_image_analysis_at = row.created_at
    farm.avg_biomass_density = result.estimated_biomass_tonnes / max(farm.area_hectares, 0.01)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


async def run_sensor_verification(
    db: Session,
    farm: Farm,
    window_hours: int = 24,
    sensor_reading_id: Optional[str] = None,
    cross_check_image: Optional[ImageAnalysis] = None,
) -> SensorVerification:
    window_end = now()
    window_start = window_end - timedelta(hours=window_hours)
    q = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .filter(SensorReading.recorded_at >= window_start)
        .filter(SensorReading.recorded_at <= window_end)
        .order_by(SensorReading.recorded_at.asc())
    )
    readings = q.all()
    if not readings:
        # fall back to latest N readings if window empty
        readings = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farm.id)
            .order_by(SensorReading.recorded_at.desc())
            .limit(48)
            .all()
        )
        readings = list(reversed(readings))
        if readings:
            window_start = readings[0].recorded_at
            window_end = readings[-1].recorded_at

    image_cross = None
    if cross_check_image:
        image_cross = {
            "estimated_biomass_tonnes": cross_check_image.estimated_biomass_tonnes,
            "algae_coverage_pct": cross_check_image.algae_coverage_pct,
            "health_score": cross_check_image.health_score,
        }

    model = get_sensor_model()
    result = await model.predict(
        SensorModelInput(
            farm_id=farm.id,
            window_start=window_start,
            window_end=window_end,
            readings=[_reading_dict(r) for r in readings],
            image_cross_check=image_cross,
            farm_area_hectares=farm.area_hectares,
        )
    )

    row = SensorVerification(
        id=new_id(),
        farm_id=farm.id,
        sensor_reading_id=sensor_reading_id or (readings[-1].id if readings else None),
        window_start=window_start,
        window_end=window_end,
        created_at=now(),
        model_version=result.model_version,
        status="completed",
        data_quality_score=result.data_quality_score,
        sequestration_kg_co2e=result.sequestration_kg_co2e,
        sequestration_confidence=result.sequestration_confidence,
        anomaly_detected=result.anomaly_detected,
        anomaly_details=result.anomaly_details,
        consistency_with_image=result.consistency_with_image,
        verdict=result.verdict,
        raw_output=result.raw_output,
        is_stub=result.is_stub,
    )
    if result.sequestration_kg_co2e is not None:
        hours = max((window_end - window_start).total_seconds() / 3600.0, 1.0)
        farm.avg_co2_uptake_kg_day = round(result.sequestration_kg_co2e / hours * 24.0, 3)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def compose_trust(
    img: Optional[ImageAnalysis],
    sen: Optional[SensorVerification],
) -> tuple[float, str, list[str]]:
    """Authoritative AI Trust Score composite → (dualAiScore, recommendation, notes).

    Weighted blend: 40% image health, 25% image coverage, 25% sensor data quality,
    10% image/sensor consistency. Robust to a missing side (neutral defaults + a
    note) so the view surface can score a farm that only has one analysis so far.
    """
    health = img.health_score if img is not None else None
    coverage = img.algae_coverage_pct if img is not None else None
    bloom = bool(img.bloom_detected) if img is not None else False
    img_flags = list(img.anomaly_flags or []) if img is not None else []

    quality = sen.data_quality_score if sen is not None else None
    consistency = sen.consistency_with_image if sen is not None else None
    verdict = sen.verdict if sen is not None else None
    sen_anom = list(sen.anomaly_details or []) if sen is not None else []

    dual = round(
        0.4 * (health if health is not None else 50)
        + 0.25 * (coverage if coverage is not None else 50)
        + 0.25 * (quality if quality is not None else 50)
        + 0.1 * (consistency if consistency is not None else 70),
        2,
    )

    notes: list[str] = []
    if img is None:
        notes.append("No image analysis yet — score uses a neutral image baseline.")
    if sen is None:
        notes.append("No sensor verification yet — score uses a neutral sensor baseline.")
    if bloom:
        notes.append("Image model flagged a possible bloom.")
    if img_flags:
        notes.extend([f"Image: {f}" for f in img_flags])
    if sen_anom:
        notes.extend([f"Sensor: {d}" for d in sen_anom])
    if verdict == "suspicious":
        notes.append("Sensor verifier verdict: suspicious — human review recommended.")
    if verdict == "invalid":
        notes.append("Sensor verifier verdict: invalid — reject recommended.")

    if dual >= 75 and verdict == "plausible" and not bloom:
        recommendation = "approve_ready"
    elif verdict == "invalid" or dual < 45:
        recommendation = "reject_recommended"
    else:
        recommendation = "needs_review"
    return dual, recommendation, notes


async def run_dual_ai_verify(
    db: Session,
    farm: Farm,
    image_url: Optional[str] = None,
    image_source: str = "drone",
    window_hours: int = 24,
) -> DualAiVerifyOut:
    url = image_url or (farm.images[0] if farm.images else farm.thumbnail_url) or f"mock://farm/{farm.id}/pond.jpg"
    img = await run_image_analysis(db, farm, url, image_source)
    sen = await run_sensor_verification(db, farm, window_hours=window_hours, cross_check_image=img)

    dual, recommendation, notes = compose_trust(img, sen)

    return DualAiVerifyOut(
        farmId=farm.id,
        imageAnalysis=image_analysis_out(img),
        sensorVerification=sensor_verification_out(sen),
        dualAiScore=dual,
        recommendation=recommendation,  # type: ignore[arg-type]
        notes=notes,
    )


def get_trust_score(db: Session, farm: Farm) -> AiTrustScoreOut:
    """Unified 'AI Trust Score' view read by every role (no model run).

    Reads the latest stored ImageAnalysis + SensorVerification for the farm and
    composes them. Returns status='pending' (still HTTP 200) when neither exists.
    """
    img = (
        db.query(ImageAnalysis)
        .filter(ImageAnalysis.farm_id == farm.id)
        .order_by(ImageAnalysis.created_at.desc())
        .first()
    )
    sen = (
        db.query(SensorVerification)
        .filter(SensorVerification.farm_id == farm.id)
        .order_by(SensorVerification.created_at.desc())
        .first()
    )
    if img is None and sen is None:
        return AiTrustScoreOut(
            farmId=farm.id,
            status="pending",
            notes=["No AI analysis has been run for this farm yet."],
        )

    dual, recommendation, notes = compose_trust(img, sen)
    return AiTrustScoreOut(
        farmId=farm.id,
        status="ready",
        imageAnalysis=image_analysis_out(img) if img is not None else None,
        sensorVerification=sensor_verification_out(sen) if sen is not None else None,
        dualAiScore=dual,
        recommendation=recommendation,  # type: ignore[arg-type]
        notes=notes,
    )
