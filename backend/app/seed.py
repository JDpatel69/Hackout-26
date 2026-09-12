"""Seed demo users, algae farms, sensors, projects — consistent across roles."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    AppNotification,
    CarbonCredit,
    CarbonProject,
    Dataset,
    Farm,
    FarmDocument,
    Investment,
    ResearchReport,
    SensorReading,
    Transaction,
    User,
    VerificationRequest,
)
from app.utils.ids import new_id

PASSWORD = "password123"  # demo password for all seeded users

DEMO_USERS = [
    {
        "id": "u-farm-1",
        "name": "Amina Okello",
        "email": "amina@greenalgae.co",
        "role": "farm_operator",
        "organization": "Green Tide Algae Farms",
    },
    {
        "id": "u-farm-2",
        "name": "Rajesh Patel",
        "email": "rajesh@aquacarbon.in",
        "role": "farm_operator",
        "organization": "AquaCarbon India",
    },
    {
        "id": "u-verifier-1",
        "name": "Elena Vargas",
        "email": "elena@ecoaudit.org",
        "role": "verifier",
        "organization": "EcoAudit Partners",
    },
    {
        "id": "u-researcher-1",
        "name": "Dr. Marcus Chen",
        "email": "marcus@oceanlab.edu",
        "role": "researcher",
        "organization": "Ocean Lab Research",
    },
    {
        "id": "u-investor-1",
        "name": "Sofia Berg",
        "email": "sofia@impactvault.io",
        "role": "investor",
        "organization": "Impact Vault Capital",
    },
]


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    _seed(db)


def _seed(db: Session) -> None:
    hashed = hash_password(PASSWORD)
    now = datetime.utcnow()

    for u in DEMO_USERS:
        db.add(
            User(
                id=u["id"],
                name=u["name"],
                email=u["email"],
                hashed_password=hashed,
                avatar_url=None,
                role=u["role"],
                organization=u["organization"],
                phone=None,
                created_at=now - timedelta(days=90),
                last_login_at=now - timedelta(days=1),
            )
        )
    db.flush()  # ensure users exist before FK dependents

    farms_spec = [
        {
            "id": "farm-nakuru",
            "operator_id": "u-farm-1",
            "name": "Nakuru Spirulina Ponds",
            "lat": -0.3031,
            "lng": 36.0800,
            "address": "Lake Nakuru Road, Nakuru",
            "region": "Nakuru County",
            "country": "Kenya",
            "area": 12.5,
            "species": "Spirulina platensis",
            "system": "raceway",
            "status": "approved",
            "credits": 86.4,
        },
        {
            "id": "farm-goa",
            "operator_id": "u-farm-2",
            "name": "Konkan Photobioreactor Hub",
            "lat": 15.2993,
            "lng": 74.1240,
            "address": "Coastal Industrial Zone, Goa",
            "region": "Goa",
            "country": "India",
            "area": 4.2,
            "species": "Chlorella vulgaris",
            "system": "photobioreactor",
            "status": "in_review",
            "credits": 0.0,
        },
        {
            "id": "farm-iowa",
            "operator_id": "u-farm-1",
            "name": "Prairie Algae Loop",
            "lat": 41.8780,
            "lng": -93.0977,
            "address": "Rural Route 7, Story County",
            "region": "Iowa",
            "country": "USA",
            "area": 8.0,
            "species": "Nannochloropsis",
            "system": "open_pond",
            "status": "submitted",
            "credits": 0.0,
        },
        {
            "id": "farm-chiang",
            "operator_id": "u-farm-2",
            "name": "Chiang Mai Biofilm Raceways",
            "lat": 18.7883,
            "lng": 98.9853,
            "address": "Mae Rim Valley",
            "region": "Chiang Mai",
            "country": "Thailand",
            "area": 6.7,
            "species": "Spirulina platensis",
            "system": "raceway",
            "status": "draft",
            "credits": 0.0,
        },
        {
            "id": "farm-minas",
            "operator_id": "u-farm-1",
            "name": "Minas Gerais Green Film Estate",
            "lat": -19.9167,
            "lng": -43.9345,
            "address": "Zona Rural, Belo Horizonte",
            "region": "Minas Gerais",
            "country": "Brazil",
            "area": 15.0,
            "species": "Scenedesmus",
            "system": "open_pond",
            "status": "approved",
            "credits": 124.0,
        },
        {
            "id": "farm-punjab",
            "operator_id": "u-farm-2",
            "name": "Punjab Dual-Crop Algae Co-op",
            "lat": 30.9010,
            "lng": 75.8573,
            "address": "Ludhiana Agri Corridor",
            "region": "Punjab",
            "country": "India",
            "area": 9.3,
            "species": "Chlorella vulgaris",
            "system": "raceway",
            "status": "correction_required",
            "credits": 0.0,
        },
        {
            "id": "farm-bali",
            "operator_id": "u-farm-1",
            "name": "Bali Coastal Microalgae Collective",
            "lat": -8.4095,
            "lng": 115.1889,
            "address": "Sanur Coastal Road",
            "region": "Bali",
            "country": "Indonesia",
            "area": 5.5,
            "species": "Tetraselmis",
            "system": "photobioreactor",
            "status": "approved",
            "credits": 52.8,
        },
        {
            "id": "farm-andalucia",
            "operator_id": "u-farm-2",
            "name": "Andalucía Solar Raceways",
            "lat": 37.3891,
            "lng": -5.9845,
            "address": "Parque Tecnológico, Sevilla",
            "region": "Andalucía",
            "country": "Spain",
            "area": 11.0,
            "species": "Dunaliella salina",
            "system": "raceway",
            "status": "rejected",
            "credits": 0.0,
        },
    ]

    rng = random.Random(42)
    for fs in farms_spec:
        farm = Farm(
            id=fs["id"],
            operator_id=fs["operator_id"],
            name=fs["name"],
            lat=fs["lat"],
            lng=fs["lng"],
            address=fs["address"],
            region=fs["region"],
            country=fs["country"],
            area_hectares=fs["area"],
            farm_type="algae",
            algae_species=fs["species"],
            cultivation_system=fs["system"],
            crop_types=["algae_biomass", "biofuel_feedstock"],
            farming_practices=["algae_cultivation", fs["system"] if fs["system"] != "open_pond" else "water_conservation"],
            established_date="2022-06-01",
            status=fs["status"],
            carbon_credits_issued=fs["credits"],
            thumbnail_url=f"https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&sig={fs['id']}",
            images=[f"mock://farm/{fs['id']}/1.jpg", f"mock://farm/{fs['id']}/2.jpg"],
            avg_co2_uptake_kg_day=round(18 + rng.random() * 40, 2),
            avg_biomass_density=round(1.5 + rng.random() * 3.5, 2),
            last_sensor_at=now - timedelta(hours=2),
            last_image_analysis_at=now - timedelta(days=1),
            created_at=now - timedelta(days=60),
            updated_at=now - timedelta(days=2),
        )
        db.add(farm)

        # Documents
        for dtype, fname in [
            ("land_title", "title_deed.pdf"),
            ("algae_photo", "pond_overview.jpg"),
            ("satellite_image", "sentinel2_tile.tif"),
            ("sensor_log", "iot_export_30d.csv"),
        ]:
            db.add(
                FarmDocument(
                    id=new_id(),
                    farm_id=fs["id"],
                    type=dtype,
                    file_name=fname,
                    file_url=f"/uploads/{fs['id']}/{fname}",
                    uploaded_at=now - timedelta(days=rng.randint(5, 40)),
                    verified_status="verified" if fs["status"] == "approved" else "pending",
                )
            )

        # Sensor history (48 hourly points)
        for h in range(48):
            ts = now - timedelta(hours=48 - h)
            db.add(
                SensorReading(
                    id=new_id(),
                    farm_id=fs["id"],
                    recorded_at=ts,
                    growth_rate=round(0.4 + rng.random() * 1.2, 3),
                    co2_uptake_kg_h=round(0.6 + rng.random() * 1.8, 3),
                    biomass_density=round(1.2 + rng.random() * 3.0, 3),
                    water_ph=round(7.2 + rng.random() * 1.4, 2),
                    water_temperature_c=round(22 + rng.random() * 8, 1),
                    dissolved_oxygen=round(4 + rng.random() * 5, 2),
                    turbidity_ntu=round(8 + rng.random() * 20, 1),
                    light_intensity_umol=round(200 + rng.random() * 800, 0),
                    nutrient_n_mg_l=round(5 + rng.random() * 15, 2),
                    nutrient_p_mg_l=round(0.5 + rng.random() * 3, 2),
                    device_id=f"IOT-{fs['id'][-4:].upper()}-01",
                )
            )
    db.flush()

    # Verification requests linked to farms
    ver_specs = [
        ("farm-nakuru", "approved", 86.4),
        ("farm-minas", "approved", 124.0),
        ("farm-bali", "approved", 52.8),
        ("farm-goa", "in_review", 38.0),
        ("farm-iowa", "pending", 44.0),
        ("farm-punjab", "correction_required", 51.0),
        ("farm-andalucia", "rejected", 0.0),
    ]
    for farm_id, status, credits in ver_specs:
        farm = next(f for f in farms_spec if f["id"] == farm_id)
        op = next(u for u in DEMO_USERS if u["id"] == farm["operator_id"])
        req = VerificationRequest(
            id=f"vr-{farm_id}",
            farm_id=farm_id,
            farm_name=farm["name"],
            operator_id=farm["operator_id"],
            operator_name=op["name"],
            submitted_at=now - timedelta(days=20),
            status=status,
            assigned_verifier_id="u-verifier-1" if status != "pending" else None,
            evidence_count=4,
            estimated_credits=credits or 30.0,
            verified_credits=credits if status == "approved" else None,
            review_notes=(
                [{"authorId": "u-verifier-1", "note": "Sensor + imagery consistent.", "createdAt": now.isoformat()}]
                if status == "approved"
                else (
                    [{"authorId": "u-verifier-1", "note": "Please re-upload water quality lab sheet.", "createdAt": now.isoformat()}]
                    if status == "correction_required"
                    else (
                        [{"authorId": "u-verifier-1", "note": "CO2 uptake readings inconsistent with biomass.", "createdAt": now.isoformat()}]
                        if status == "rejected"
                        else []
                    )
                )
            ),
            decision_at=now - timedelta(days=10) if status in ("approved", "rejected", "correction_required") else None,
            decision_by="u-verifier-1" if status in ("approved", "rejected", "correction_required") else None,
            rejection_reason="Inconsistent CO2 uptake vs biomass growth." if status == "rejected" else None,
            dual_ai_score=82.0 if status == "approved" else None,
        )
        db.add(req)
    db.flush()

    # Marketplace projects for approved farms
    approved = [f for f in farms_spec if f["status"] == "approved"]
    project_prices: dict[str, float] = {}
    for fs in approved:
        pid = f"proj-{fs['id']}"
        price = round(16 + rng.random() * 10, 2)
        project_prices[pid] = price
        project = CarbonProject(
            id=pid,
            farm_id=fs["id"],
            title=f"{fs['name']} — Verified Algae Carbon",
            description=f"Verified algae MRV project in {fs['region']}, {fs['country']} cultivating {fs['species']}.",
            region=f"{fs['region']}, {fs['country']}",
            images=[f"mock://farm/{fs['id']}/1.jpg"],
            verification_status="verified",
            verified_by="EcoAudit Partners",
            verified_at=now - timedelta(days=10),
            total_credits_available=fs["credits"] * 0.6,
            price_per_credit=price,
            risk={
                "climateRisk": 25,
                "verificationConfidence": 84,
                "operatorTrackRecord": 78,
                "marketLiquidity": 60,
                "composite": 72,
                "tier": "low",
            },
            expected_roi_percent=round(7 + rng.random() * 5, 2),
            environmental_impact={
                "co2OffsetTonnes": fs["credits"],
                "biodiversityScore": 70,
                "waterSavedLiters": int(fs["area"] * 10000),
            },
            operator_story=f"{fs['name']} converts CO2-rich flue streams into biomass for biofuel and feed.",
        )
        db.add(project)
    db.flush()

    for fs in approved:
        pid = f"proj-{fs['id']}"
        db.add(
            CarbonCredit(
                id=new_id(),
                farm_id=fs["id"],
                project_id=pid,
                amount_tonnes_co2e=fs["credits"],
                vintage_year=2025,
                issued_at=now - timedelta(days=10),
                price_per_credit=project_prices[pid],
                status="available",
            )
        )
    db.flush()

    # Investor seed activity
    inv = Investment(
        id=new_id(),
        investor_id="u-investor-1",
        project_id="proj-farm-nakuru",
        amount_invested=5000,
        credits_purchased=round(5000 / 20.0, 4),
        invested_at=now - timedelta(days=5),
        status="active",
        current_value=5250,
        return_percent=5.0,
    )
    db.add(inv)
    db.add(
        Transaction(
            id=new_id(),
            investor_id="u-investor-1",
            type="investment",
            amount=5000,
            related_project_id="proj-farm-nakuru",
            date=now - timedelta(days=5),
            status="completed",
        )
    )

    # Datasets + report
    for i, (name, dtype, region) in enumerate(
        [
            ("East Africa Algae Sensor Archive", "sensor_timeseries", "Nakuru County, Kenya"),
            ("Global Pond Satellite NDVI 2024-25", "satellite", "Global"),
            ("Algae Imagery Labeled Set v0", "algae_imagery", "Multi-region"),
            ("Carbon Flux Reanalysis Coastal", "carbon_flux", "Coastal"),
            ("Climate Forcing for Raceways", "climate", "Global"),
            ("India PBR Water Quality Panel", "sensor_timeseries", "Goa, India"),
            ("Brazil Open-Pond Biomass Survey", "soil", "Minas Gerais, Brazil"),
            ("Thailand Raceway Growth Campaign", "sensor_timeseries", "Chiang Mai, Thailand"),
        ]
    ):
        db.add(
            Dataset(
                id=f"ds-{i+1}",
                name=name,
                region=region,
                type=dtype,
                date_range_start="2024-01-01",
                date_range_end="2025-09-01",
                farms_covered=8 + i,
                size_mb=round(12 + i * 7.5, 1),
                format="CSV" if "sensor" in dtype else "GeoTIFF" if dtype == "satellite" else "JSON",
            )
        )
    db.flush()

    db.add(
        ResearchReport(
            id=new_id(),
            title="Cross-site CO2 uptake consistency under dual-AI MRV",
            author_id="u-researcher-1",
            created_at=now - timedelta(days=14),
            related_dataset_ids=["ds-1", "ds-3"],
            summary="Preliminary findings show image-sensor agreement above 0.78 for raceway systems.",
            status="published",
        )
    )
    db.add(
        ResearchReport(
            id=new_id(),
            title="Draft: Photobioreactor bloom early-warning signals",
            author_id="u-researcher-1",
            created_at=now - timedelta(days=3),
            related_dataset_ids=["ds-3", "ds-6"],
            summary="Exploring turbidity + coverage anomalies as bloom precursors.",
            status="draft",
        )
    )

    # Notifications
    for uid, title, msg, typ in [
        ("u-farm-1", "Credits issued", "Nakuru Spirulina Ponds credits are live.", "credits"),
        ("u-farm-2", "Corrections requested", "Punjab Dual-Crop Algae Co-op needs a lab sheet.", "verification"),
        ("u-verifier-1", "New queue item", "Prairie Algae Loop awaits review.", "verification"),
        ("u-investor-1", "Portfolio update", "Nakuru project value up 5%.", "investment"),
        ("u-researcher-1", "Dataset refreshed", "East Africa sensor archive updated.", "system"),
    ]:
        db.add(
            AppNotification(
                id=new_id(),
                user_id=uid,
                type=typ,
                title=title,
                message=msg,
                is_read=False,
                created_at=now - timedelta(hours=rng.randint(1, 48)),
                link_to=None,
            )
        )

    db.commit()
