"""IoT sensor ingestion + AI model endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.ai.registry import model_status
from app.api.deps import RoleAny, RoleFarm, RoleResearcher, RoleVerifier, get_current_user
from app.database import get_db
from app.models import CarbonProject, Farm, ImageAnalysis, SensorReading, SensorVerification, User
from app.schemas import (
    AiFarmRefOut,
    AiTrustScoreOut,
    DualAiVerifyOut,
    DualAiVerifyRequest,
    ImageAnalysisOut,
    ImageAnalysisRequest,
    SensorBatchIn,
    SensorReadingIn,
    SensorReadingOut,
    SensorVerificationOut,
    SensorVerifyRequest,
)
from app.services.ai_service import (
    get_trust_score,
    run_dual_ai_verify,
    run_image_analysis,
    run_sensor_verification,
)
from app.utils.ids import new_id, now
from app.utils.mappers import image_analysis_out, sensor_out, sensor_verification_out

router = APIRouter(tags=["iot-ai"])

# Roles permitted to *trigger* AI analysis. All authenticated roles may VIEW;
# investor is view-only (per the locked "all view; limited run" access decision).
RUN_ROLES = ("farm_operator", "verifier", "researcher")


def _get_farm(db: Session, farm_id: str) -> Farm:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@router.get("/ai/status")
def ai_status(_: User = Depends(RoleAny)) -> dict:
    """Inspect which AI backends are active (stub vs trained vs remote)."""
    return model_status()


@router.post("/iot/sensors", response_model=SensorReadingOut, status_code=201)
def ingest_sensor(
    body: SensorReadingIn,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> SensorReadingOut:
    farm = _get_farm(db, body.farmId)
    if farm.operator_id != user.id:
        raise HTTPException(status_code=403, detail="Not your farm")
    row = SensorReading(
        id=new_id(),
        farm_id=farm.id,
        recorded_at=body.recordedAt or now(),
        growth_rate=body.growthRate,
        co2_uptake_kg_h=body.co2UptakeKgH,
        biomass_density=body.biomassDensity,
        water_ph=body.waterPh,
        water_temperature_c=body.waterTemperatureC,
        dissolved_oxygen=body.dissolvedOxygen,
        turbidity_ntu=body.turbidityNtu,
        light_intensity_umol=body.lightIntensityUmol,
        nutrient_n_mg_l=body.nutrientNMgL,
        nutrient_p_mg_l=body.nutrientPMgL,
        device_id=body.deviceId,
        raw_payload=body.rawPayload,
    )
    farm.last_sensor_at = row.recorded_at
    if body.co2UptakeKgH is not None:
        farm.avg_co2_uptake_kg_day = round(body.co2UptakeKgH * 24, 3)
    if body.biomassDensity is not None:
        farm.avg_biomass_density = body.biomassDensity
    db.add(row)
    db.commit()
    db.refresh(row)
    return sensor_out(row)


@router.post("/iot/sensors/batch", response_model=List[SensorReadingOut], status_code=201)
def ingest_sensor_batch(
    body: SensorBatchIn,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> List[SensorReadingOut]:
    out: List[SensorReadingOut] = []
    for item in body.readings:
        out.append(ingest_sensor(item, user, db))
    return out


@router.get("/iot/sensors/{farm_id}", response_model=List[SensorReadingOut])
def list_sensors(
    farm_id: str,
    limit: int = Query(100, ge=1, le=1000),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SensorReadingOut]:
    farm = _get_farm(db, farm_id)
    if user.role == "farm_operator" and farm.operator_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    rows = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return [sensor_out(r) for r in rows]


@router.post("/ai/image/analyze", response_model=ImageAnalysisOut)
async def analyze_algae_image(
    body: ImageAnalysisRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageAnalysisOut:
    """
    Model 1 — Algae image analysis.

    Accepts a farm + image URL (drone/satellite/camera). Uses stub until
    AI_IMAGE_MODEL_ENABLED=true and trained weights are wired in.
    """
    if user.role not in RUN_ROLES:
        raise HTTPException(status_code=403, detail="Role not allowed to run image analysis")
    farm = _get_farm(db, body.farmId)
    if user.role == "farm_operator" and farm.operator_id != user.id:
        raise HTTPException(status_code=403, detail="Not your farm")
    image_url = body.imageUrl or (farm.images[0] if farm.images else None) or f"mock://farm/{farm.id}/algae.jpg"
    row = await run_image_analysis(db, farm, image_url, body.source)
    return image_analysis_out(row)


@router.get("/ai/image/{farm_id}", response_model=List[ImageAnalysisOut])
def list_image_analyses(
    farm_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ImageAnalysisOut]:
    _get_farm(db, farm_id)
    rows = (
        db.query(ImageAnalysis)
        .filter(ImageAnalysis.farm_id == farm_id)
        .order_by(ImageAnalysis.created_at.desc())
        .limit(50)
        .all()
    )
    return [image_analysis_out(r) for r in rows]


@router.post("/ai/sensor/verify", response_model=SensorVerificationOut)
async def verify_sensor_data(
    body: SensorVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SensorVerificationOut:
    """
    Model 2 — Sensor-data verification.

    Validates IoT readings for a time window and estimates sequestration.
    Stubbed until AI_SENSOR_MODEL_ENABLED=true.
    """
    if user.role not in RUN_ROLES:
        raise HTTPException(status_code=403, detail="Role not allowed to run sensor verification")
    farm = _get_farm(db, body.farmId)
    cross: Optional[ImageAnalysis] = None
    if body.crossCheckImageAnalysisId:
        cross = db.get(ImageAnalysis, body.crossCheckImageAnalysisId)
    row = await run_sensor_verification(
        db,
        farm,
        window_hours=body.windowHours,
        sensor_reading_id=body.sensorReadingId,
        cross_check_image=cross,
    )
    return sensor_verification_out(row)


@router.get("/ai/sensor/{farm_id}", response_model=List[SensorVerificationOut])
def list_sensor_verifications(
    farm_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SensorVerificationOut]:
    _get_farm(db, farm_id)
    rows = (
        db.query(SensorVerification)
        .filter(SensorVerification.farm_id == farm_id)
        .order_by(SensorVerification.created_at.desc())
        .limit(50)
        .all()
    )
    return [sensor_verification_out(r) for r in rows]


@router.post("/ai/dual-verify", response_model=DualAiVerifyOut)
async def dual_verify(
    body: DualAiVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DualAiVerifyOut:
    """
    Run both AI models together and return a composite dual-AI score + recommendation.
    Primary path used by verifiers before approve/reject.
    """
    if user.role not in RUN_ROLES:
        raise HTTPException(status_code=403, detail="Forbidden")
    farm = _get_farm(db, body.farmId)
    return await run_dual_ai_verify(
        db,
        farm,
        image_url=body.imageUrl,
        image_source=body.imageSource,
        window_hours=body.windowHours,
    )


# ── AI Trust Score: unified view + real-image upload + farm selector ──────────
@router.get("/ai/trust-score/{farm_id}", response_model=AiTrustScoreOut)
def ai_trust_score(
    farm_id: str,
    _: User = Depends(RoleAny),
    db: Session = Depends(get_db),
) -> AiTrustScoreOut:
    """Unified 'AI Trust Score' for a farm — readable by EVERY role (incl. investor).

    Composites the latest stored image analysis + sensor verification. Returns
    status='pending' (HTTP 200) when the farm has no AI analysis yet.
    """
    farm = _get_farm(db, farm_id)
    return get_trust_score(db, farm)


@router.post("/ai/image/analyze/upload", response_model=ImageAnalysisOut)
async def analyze_algae_image_upload(
    farmId: str = Form(...),
    source: str = Form("phone"),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImageAnalysisOut:
    """Model 1 — run image analysis on an UPLOADED photo (the real-image path).

    Limited to run-capable roles; farm operators may only analyze their own farm.
    """
    if user.role not in RUN_ROLES:
        raise HTTPException(status_code=403, detail="Role not allowed to run image analysis")
    farm = _get_farm(db, farmId)
    if user.role == "farm_operator" and farm.operator_id != user.id:
        raise HTTPException(status_code=403, detail="Not your farm")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file upload")
    image_url = f"upload://{farm.id}/{file.filename or 'image'}"
    row = await run_image_analysis(db, farm, image_url, source, image_bytes=data)
    return image_analysis_out(row)


@router.get("/ai/farms", response_model=List[AiFarmRefOut])
def ai_farms(
    user: User = Depends(RoleAny),
    db: Session = Depends(get_db),
) -> List[AiFarmRefOut]:
    """Farms the caller may view on the AI Trust Score page.

    operator → own farms; verifier/researcher → all; investor → farms that have a
    published carbon project. Powers the page's farm selector uniformly.
    """
    if user.role == "farm_operator":
        rows = db.query(Farm).filter(Farm.operator_id == user.id).order_by(Farm.name.asc()).all()
    elif user.role == "investor":
        rows = (
            db.query(Farm)
            .join(CarbonProject, CarbonProject.farm_id == Farm.id)
            .order_by(Farm.name.asc())
            .distinct()
            .all()
        )
    else:  # verifier, researcher
        rows = db.query(Farm).order_by(Farm.name.asc()).all()
    return [AiFarmRefOut(id=f.id, name=f.name, status=f.status) for f in rows]
