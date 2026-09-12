from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import RoleFarm, get_current_user
from app.database import get_db
from app.models import CarbonCredit, Farm, FarmDocument, User, VerificationRequest
from app.schemas import (
    CarbonCreditOut,
    FarmCreate,
    FarmDocumentOut,
    FarmOut,
    FarmUpdate,
    VerificationRequestOut,
)
from app.services.notification_service import notify
from app.utils.ids import new_id, now
from app.utils.mappers import credit_out, document_out, farm_out, verification_out

router = APIRouter(prefix="/farms", tags=["farm-operator"])


def _owned_farm(db: Session, farm_id: str, user: User) -> Farm:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    if farm.operator_id != user.id and user.role != "verifier":
        raise HTTPException(status_code=403, detail="Not your farm")
    return farm


@router.get("", response_model=List[FarmOut])
def list_farms(
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> List[FarmOut]:
    farms = db.query(Farm).filter(Farm.operator_id == user.id).order_by(Farm.created_at.desc()).all()
    return [farm_out(f) for f in farms]


@router.post("", response_model=FarmOut, status_code=201)
def create_farm(
    body: FarmCreate,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> FarmOut:
    farm = Farm(
        id=new_id(),
        operator_id=user.id,
        name=body.name,
        lat=body.location.lat,
        lng=body.location.lng,
        address=body.location.address,
        region=body.location.region,
        country=body.location.country,
        area_hectares=body.areaHectares,
        farm_type=body.farmType,
        algae_species=body.algaeSpecies,
        cultivation_system=body.cultivationSystem,
        crop_types=body.cropTypes,
        farming_practices=body.farmingPractices,
        established_date=body.establishedDate,
        status="draft",
        carbon_credits_issued=0.0,
        thumbnail_url=body.thumbnailUrl,
        images=body.images,
        created_at=now(),
        updated_at=now(),
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm_out(farm)


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(
    farm_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FarmOut:
    farm = _owned_farm(db, farm_id, user)
    return farm_out(farm)


@router.patch("/{farm_id}", response_model=FarmOut)
def update_farm(
    farm_id: str,
    body: FarmUpdate,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> FarmOut:
    farm = _owned_farm(db, farm_id, user)
    if farm.status not in ("draft", "correction_required"):
        raise HTTPException(status_code=400, detail="Farm can only be edited in draft or correction_required")
    data = body.model_dump(exclude_unset=True)
    if "location" in data and data["location"]:
        loc = data.pop("location")
        farm.lat = loc["lat"]
        farm.lng = loc["lng"]
        farm.address = loc["address"]
        farm.region = loc["region"]
        farm.country = loc["country"]
    mapping = {
        "name": "name",
        "areaHectares": "area_hectares",
        "algaeSpecies": "algae_species",
        "cultivationSystem": "cultivation_system",
        "cropTypes": "crop_types",
        "farmingPractices": "farming_practices",
        "status": "status",
        "thumbnailUrl": "thumbnail_url",
        "images": "images",
    }
    for api_key, attr in mapping.items():
        if api_key in data:
            setattr(farm, attr, data[api_key])
    farm.updated_at = now()
    db.commit()
    db.refresh(farm)
    return farm_out(farm)


@router.post("/{farm_id}/documents", response_model=FarmDocumentOut, status_code=201)
async def upload_document(
    farm_id: str,
    type: str = Form(...),
    file: UploadFile = File(...),
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> FarmDocumentOut:
    farm = _owned_farm(db, farm_id, user)
    # Store as a mock URL (no real cloud storage in hackathon scaffold)
    file_url = f"/uploads/{farm_id}/{file.filename}"
    doc = FarmDocument(
        id=new_id(),
        farm_id=farm.id,
        type=type,
        file_name=file.filename or "upload.bin",
        file_url=file_url,
        uploaded_at=now(),
        verified_status="pending",
    )
    db.add(doc)
    farm.updated_at = now()
    db.commit()
    db.refresh(doc)
    return document_out(doc)


@router.get("/{farm_id}/documents", response_model=List[FarmDocumentOut])
def list_documents(
    farm_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[FarmDocumentOut]:
    farm = _owned_farm(db, farm_id, user)
    docs = db.query(FarmDocument).filter(FarmDocument.farm_id == farm.id).all()
    return [document_out(d) for d in docs]


@router.post("/{farm_id}/submit", response_model=VerificationRequestOut)
def submit_for_verification(
    farm_id: str,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    farm = _owned_farm(db, farm_id, user)
    if farm.status not in ("draft", "correction_required", "rejected"):
        raise HTTPException(status_code=400, detail=f"Cannot submit farm in status '{farm.status}'")
    docs = db.query(FarmDocument).filter(FarmDocument.farm_id == farm.id).count()
    # Rough credit estimate from area + algae uptake if available
    base = farm.area_hectares * 12.5
    if farm.avg_co2_uptake_kg_day:
        base = max(base, farm.avg_co2_uptake_kg_day * 365 / 1000.0)
    estimated = round(base, 2)

    req = VerificationRequest(
        id=new_id(),
        farm_id=farm.id,
        farm_name=farm.name,
        operator_id=user.id,
        operator_name=user.name,
        submitted_at=now(),
        status="pending",
        evidence_count=docs,
        estimated_credits=estimated,
        review_notes=[],
    )
    farm.status = "submitted"
    farm.updated_at = now()
    db.add(req)
    # notify all verifiers
    verifiers = db.query(User).filter(User.role == "verifier").all()
    for v in verifiers:
        notify(
            db,
            v.id,
            "verification",
            "New verification request",
            f"{farm.name} submitted for review ({estimated} tCO2e est.).",
            link_to=f"/verifier/requests/{req.id}",
        )
    db.commit()
    db.refresh(req)
    return verification_out(req)


@router.get("/{farm_id}/verification", response_model=VerificationRequestOut)
def get_verification_status(
    farm_id: str,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    farm = _owned_farm(db, farm_id, user)
    req = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.farm_id == farm.id)
        .order_by(VerificationRequest.submitted_at.desc())
        .first()
    )
    if not req:
        raise HTTPException(status_code=404, detail="No verification request for this farm")
    return verification_out(req)


@router.get("/operator/{operator_id}/credits", response_model=List[CarbonCreditOut])
def view_carbon_credits(
    operator_id: str,
    user: User = Depends(RoleFarm),
    db: Session = Depends(get_db),
) -> List[CarbonCreditOut]:
    if user.id != operator_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    farm_ids = [f.id for f in db.query(Farm).filter(Farm.operator_id == operator_id).all()]
    credits = db.query(CarbonCredit).filter(CarbonCredit.farm_id.in_(farm_ids)).all() if farm_ids else []
    return [credit_out(c) for c in credits]
