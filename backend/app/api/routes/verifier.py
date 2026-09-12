from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import RoleVerifier
from app.database import get_db
from app.models import (
    CarbonCredit,
    CarbonProject,
    Farm,
    FarmDocument,
    User,
    VerificationRequest,
)
from app.schemas import (
    ApproveRequest,
    CorrectionRequest,
    FarmDocumentOut,
    MessageOut,
    RejectRequest,
    VerificationRequestOut,
)
from app.services.ai_service import run_dual_ai_verify
from app.services.notification_service import notify
from app.utils.ids import new_id, now
from app.utils.mappers import document_out, verification_out

router = APIRouter(prefix="/verifier", tags=["verifier"])


@router.get("/requests", response_model=List[VerificationRequestOut])
def list_requests(
    status: Optional[str] = Query(None),
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> List[VerificationRequestOut]:
    q = db.query(VerificationRequest)
    if status:
        q = q.filter(VerificationRequest.status == status)
    else:
        q = q.filter(VerificationRequest.status.in_(["pending", "in_review"]))
    rows = q.order_by(VerificationRequest.submitted_at.desc()).all()
    return [verification_out(r) for r in rows]


@router.get("/requests/{request_id}", response_model=VerificationRequestOut)
def get_request(
    request_id: str,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return verification_out(req)


@router.get("/requests/{request_id}/evidence", response_model=List[FarmDocumentOut])
def get_evidence(
    request_id: str,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> List[FarmDocumentOut]:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    docs = db.query(FarmDocument).filter(FarmDocument.farm_id == req.farm_id).all()
    return [document_out(d) for d in docs]


@router.post("/requests/{request_id}/review", response_model=VerificationRequestOut)
def mark_in_review(
    request_id: str,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "in_review"
    req.assigned_verifier_id = user.id
    farm = db.get(Farm, req.farm_id)
    if farm:
        farm.status = "in_review"
    db.commit()
    db.refresh(req)
    return verification_out(req)


@router.get("/requests/{request_id}/estimate-credits")
async def estimate_credits(
    request_id: str,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> dict:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    farm = db.get(Farm, req.farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    dual = await run_dual_ai_verify(db, farm)
    tonnes = round((dual.sensorVerification.sequestrationKgCo2e or 0) / 1000.0 * 30, 2)  # ~monthly→annual proxy
    if tonnes < 1:
        tonnes = req.estimated_credits
    return {
        "requestId": request_id,
        "estimatedCredits": tonnes,
        "dualAiScore": dual.dualAiScore,
        "recommendation": dual.recommendation,
        "imageAnalysisId": dual.imageAnalysis.id,
        "sensorVerificationId": dual.sensorVerification.id,
    }


@router.post("/requests/{request_id}/approve", response_model=VerificationRequestOut)
async def approve_project(
    request_id: str,
    body: ApproveRequest,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    farm = db.get(Farm, req.farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    dual = await run_dual_ai_verify(db, farm)
    notes = list(req.review_notes or [])
    if body.notes:
        notes.append({"authorId": user.id, "note": body.notes, "createdAt": now().isoformat()})
    notes.append(
        {
            "authorId": user.id,
            "note": f"Approved with {body.verifiedCredits} tCO2e. Dual-AI score {dual.dualAiScore}.",
            "createdAt": now().isoformat(),
        }
    )

    req.status = "approved"
    req.verified_credits = body.verifiedCredits
    req.decision_at = now()
    req.decision_by = user.id
    req.review_notes = notes
    req.image_analysis_id = dual.imageAnalysis.id
    req.sensor_verification_id = dual.sensorVerification.id
    req.dual_ai_score = dual.dualAiScore
    req.assigned_verifier_id = user.id

    farm.status = "approved"
    farm.carbon_credits_issued = (farm.carbon_credits_issued or 0) + body.verifiedCredits
    farm.updated_at = now()

    # Create marketplace CarbonProject (cross-role linkage)
    price = 18.5 + (body.verifiedCredits % 7)
    project = CarbonProject(
        id=new_id(),
        farm_id=farm.id,
        title=f"{farm.name} — Verified Algae Carbon",
        description=(
            f"Independently verified algae cultivation project at {farm.region}, {farm.country}. "
            f"Species: {farm.algae_species or 'mixed'}. Dual-AI MRV score: {dual.dualAiScore}."
        ),
        region=f"{farm.region}, {farm.country}",
        images=list(farm.images or []) or ([farm.thumbnail_url] if farm.thumbnail_url else []),
        verification_status="verified",
        verified_by=user.organization or user.name,
        verified_at=now(),
        total_credits_available=body.verifiedCredits,
        price_per_credit=round(price, 2),
        risk={
            "climateRisk": 28,
            "verificationConfidence": int(dual.dualAiScore),
            "operatorTrackRecord": 70,
            "marketLiquidity": 55,
            "composite": int((100 - 28 + dual.dualAiScore + 70 + 55) / 4),
            "tier": "low" if dual.dualAiScore >= 75 else "medium",
        },
        expected_roi_percent=round(6.5 + dual.dualAiScore / 40.0, 2),
        environmental_impact={
            "co2OffsetTonnes": body.verifiedCredits,
            "biodiversityScore": 72,
            "waterSavedLiters": int(farm.area_hectares * 12000),
        },
        operator_story=(
            f"{farm.name} uses {farm.cultivation_system or 'raceway'} cultivation to sequester CO2 "
            "while producing biomass for biofuel and feed."
        ),
    )
    credit = CarbonCredit(
        id=new_id(),
        farm_id=farm.id,
        project_id=project.id,
        amount_tonnes_co2e=body.verifiedCredits,
        vintage_year=now().year,
        issued_at=now(),
        price_per_credit=project.price_per_credit,
        status="available",
    )
    db.add(project)
    db.add(credit)
    notify(
        db,
        farm.operator_id,
        "credits",
        "Farm approved — credits issued",
        f"{farm.name} was approved. {body.verifiedCredits} tCO2e credits are now live.",
        link_to="/farm-operator/credits",
    )
    db.commit()
    db.refresh(req)
    return verification_out(req)


@router.post("/requests/{request_id}/reject", response_model=VerificationRequestOut)
def reject_project(
    request_id: str,
    body: RejectRequest,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    farm = db.get(Farm, req.farm_id)
    notes = list(req.review_notes or [])
    notes.append({"authorId": user.id, "note": body.reason, "createdAt": now().isoformat()})
    req.status = "rejected"
    req.rejection_reason = body.reason
    req.decision_at = now()
    req.decision_by = user.id
    req.review_notes = notes
    req.assigned_verifier_id = user.id
    if farm:
        farm.status = "rejected"
        farm.updated_at = now()
        notify(
            db,
            farm.operator_id,
            "verification",
            "Verification rejected",
            f"{farm.name}: {body.reason}",
            link_to="/farm-operator/verification",
        )
    db.commit()
    db.refresh(req)
    return verification_out(req)


@router.post("/requests/{request_id}/correction", response_model=VerificationRequestOut)
def request_correction(
    request_id: str,
    body: CorrectionRequest,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> VerificationRequestOut:
    req = db.get(VerificationRequest, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    farm = db.get(Farm, req.farm_id)
    notes = list(req.review_notes or [])
    notes.append({"authorId": user.id, "note": body.note, "createdAt": now().isoformat()})
    req.status = "correction_required"
    req.review_notes = notes
    req.decision_at = now()
    req.decision_by = user.id
    req.assigned_verifier_id = user.id
    if farm:
        farm.status = "correction_required"
        farm.updated_at = now()
        notify(
            db,
            farm.operator_id,
            "verification",
            "Corrections requested",
            f"{farm.name}: {body.note}",
            link_to=f"/farm-operator/farms/{farm.id}",
        )
    db.commit()
    db.refresh(req)
    return verification_out(req)


@router.get("/history", response_model=List[VerificationRequestOut])
def history(
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> List[VerificationRequestOut]:
    rows = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.status.in_(["approved", "rejected", "correction_required"]))
        .order_by(VerificationRequest.decision_at.desc())
        .all()
    )
    return [verification_out(r) for r in rows]


@router.get("/evidence", response_model=List[FarmDocumentOut])
def evidence_library(
    farmId: Optional[str] = None,
    type: Optional[str] = None,
    user: User = Depends(RoleVerifier),
    db: Session = Depends(get_db),
) -> List[FarmDocumentOut]:
    q = db.query(FarmDocument)
    if farmId:
        q = q.filter(FarmDocument.farm_id == farmId)
    if type:
        q = q.filter(FarmDocument.type == type)
    return [document_out(d) for d in q.order_by(FarmDocument.uploaded_at.desc()).limit(200).all()]
