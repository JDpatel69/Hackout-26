import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import RoleResearcher
from app.database import get_db
from app.models import Dataset, Farm, ResearchReport, SensorReading, User
from app.schemas import DatasetOut, ResearchReportCreate, ResearchReportOut
from app.utils.ids import new_id, now
from app.utils.mappers import dataset_out, report_out

router = APIRouter(prefix="/researcher", tags=["researcher"])


@router.get("/datasets", response_model=List[DatasetOut])
def list_datasets(
    region: Optional[str] = None,
    type: Optional[str] = None,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> List[DatasetOut]:
    q = db.query(Dataset)
    if region:
        q = q.filter(Dataset.region.ilike(f"%{region}%"))
    if type:
        q = q.filter(Dataset.type == type)
    return [dataset_out(d) for d in q.all()]


@router.get("/datasets/{dataset_id}/export")
def export_dataset(
    dataset_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> Response:
    ds = db.get(Dataset, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    # Mock export payload
    payload = {
        "id": ds.id,
        "name": ds.name,
        "region": ds.region,
        "type": ds.type,
        "rows": [
            {"farm": "sample", "value": 12.4, "unit": "tCO2e"},
            {"farm": "sample", "value": 9.1, "unit": "tCO2e"},
        ],
    }
    if format == "csv":
        body = "farm,value,unit\nsample,12.4,tCO2e\nsample,9.1,tCO2e\n"
        return Response(content=body, media_type="text/csv")
    return Response(content=json.dumps(payload), media_type="application/json")


@router.get("/carbon-trends")
def carbon_trends(
    region: Optional[str] = None,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> list:
    q = db.query(Farm)
    if region:
        q = q.filter(Farm.region.ilike(f"%{region}%"))
    farms = q.all()
    # Aggregate mock monthly series from farm averages
    series = []
    for month in range(1, 13):
        tonnes = sum((f.avg_co2_uptake_kg_day or 20) * 30 / 1000.0 for f in farms) * (0.85 + month * 0.02)
        series.append({"date": f"2025-{month:02d}-01", "tonnesCO2e": round(tonnes, 2)})
    return series


@router.get("/satellite/{farm_id}")
def satellite_data(
    farm_id: str,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> list:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return [
        {"date": "2025-01-15", "imageUrl": f"mock://satellite/{farm_id}/jan.jpg"},
        {"date": "2025-03-15", "imageUrl": f"mock://satellite/{farm_id}/mar.jpg"},
        {"date": "2025-06-15", "imageUrl": f"mock://satellite/{farm_id}/jun.jpg"},
        {"date": "2025-09-01", "imageUrl": f"mock://satellite/{farm_id}/sep.jpg"},
    ]


@router.post("/compare-farms")
def compare_farms(
    farmIds: List[str],
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> dict:
    farms = db.query(Farm).filter(Farm.id.in_(farmIds)).all()
    return {
        "farms": [
            {
                "id": f.id,
                "name": f.name,
                "areaHectares": f.area_hectares,
                "avgCo2UptakeKgDay": f.avg_co2_uptake_kg_day,
                "avgBiomassDensity": f.avg_biomass_density,
                "creditsIssued": f.carbon_credits_issued,
                "status": f.status,
            }
            for f in farms
        ]
    }


@router.get("/environmental")
def environmental_data(
    region: Optional[str] = None,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> list:
    q = db.query(SensorReading).join(Farm, Farm.id == SensorReading.farm_id)
    if region:
        q = q.filter(Farm.region.ilike(f"%{region}%"))
    rows = q.order_by(SensorReading.recorded_at.desc()).limit(200).all()
    return [
        {
            "farmId": r.farm_id,
            "recordedAt": r.recorded_at.isoformat(),
            "growthRate": r.growth_rate,
            "co2UptakeKgH": r.co2_uptake_kg_h,
            "waterPh": r.water_ph,
            "biomassDensity": r.biomass_density,
        }
        for r in rows
    ]


@router.get("/reports", response_model=List[ResearchReportOut])
def list_reports(
    status: Optional[str] = None,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> List[ResearchReportOut]:
    q = db.query(ResearchReport)
    if status:
        q = q.filter(ResearchReport.status == status)
    return [report_out(r) for r in q.order_by(ResearchReport.created_at.desc()).all()]


@router.post("/reports", response_model=ResearchReportOut, status_code=201)
def generate_report(
    body: ResearchReportCreate,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> ResearchReportOut:
    report = ResearchReport(
        id=new_id(),
        title=body.title,
        author_id=user.id,
        created_at=now(),
        related_dataset_ids=body.datasetIds,
        summary=body.summary,
        status="draft",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report_out(report)


@router.post("/reports/{report_id}/publish", response_model=ResearchReportOut)
def publish_report(
    report_id: str,
    user: User = Depends(RoleResearcher),
    db: Session = Depends(get_db),
) -> ResearchReportOut:
    report = db.get(ResearchReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not your report")
    report.status = "published"
    db.commit()
    db.refresh(report)
    return report_out(report)
