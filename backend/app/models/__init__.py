"""SQLAlchemy ORM models for the Algae Carbon MRV platform."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    role: Mapped[str] = mapped_column(String(32), index=True)  # farm_operator|verifier|researcher|investor
    organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    farms: Mapped[list["Farm"]] = relationship(back_populates="operator")
    investments: Mapped[list["Investment"]] = relationship(back_populates="investor")
    notifications: Mapped[list["AppNotification"]] = relationship(back_populates="user")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    # Geo
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    address: Mapped[str] = mapped_column(String(500))
    region: Mapped[str] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(80))
    # Algae-specific + shared MRV fields
    area_hectares: Mapped[float] = mapped_column(Float)
    farm_type: Mapped[str] = mapped_column(String(40), default="algae")  # algae | regenerative_ag
    algae_species: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cultivation_system: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)  # open_pond|photobioreactor|raceway
    crop_types: Mapped[list] = mapped_column(JSON, default=list)
    farming_practices: Mapped[list] = mapped_column(JSON, default=list)
    established_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    carbon_credits_issued: Mapped[float] = mapped_column(Float, default=0.0)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    images: Mapped[list] = mapped_column(JSON, default=list)
    # Aggregated sensor / AI metrics (updated by IoT + AI pipelines)
    avg_co2_uptake_kg_day: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_biomass_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_sensor_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_image_analysis_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    operator: Mapped["User"] = relationship(back_populates="farms")
    documents: Mapped[list["FarmDocument"]] = relationship(back_populates="farm")
    sensor_readings: Mapped[list["SensorReading"]] = relationship(back_populates="farm")
    image_analyses: Mapped[list["ImageAnalysis"]] = relationship(back_populates="farm")
    verification_requests: Mapped[list["VerificationRequest"]] = relationship(back_populates="farm")
    carbon_credits: Mapped[list["CarbonCredit"]] = relationship(back_populates="farm")
    carbon_projects: Mapped[list["CarbonProject"]] = relationship(back_populates="farm")


class FarmDocument(Base):
    __tablename__ = "farm_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))  # land_title|soil_test|practice_photo|satellite_image|sensor_log|algae_photo|other
    file_name: Mapped[str] = mapped_column(String(255))
    file_url: Mapped[str] = mapped_column(String(512))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    verified_status: Mapped[str] = mapped_column(String(20), default="pending")

    farm: Mapped["Farm"] = relationship(back_populates="documents")


class SensorReading(Base):
    """IoT / simulated sensor telemetry for algae cultivation sites."""

    __tablename__ = "sensor_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    # Core algae MRV sensors
    growth_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # g/L/day
    co2_uptake_kg_h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    biomass_density: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # g/L
    water_ph: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    water_temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dissolved_oxygen: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # mg/L
    turbidity_ntu: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    light_intensity_umol: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nutrient_n_mg_l: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    nutrient_p_mg_l: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    farm: Mapped["Farm"] = relationship(back_populates="sensor_readings")
    sensor_verifications: Mapped[list["SensorVerification"]] = relationship(back_populates="sensor_reading")


class ImageAnalysis(Base):
    """Stores results from the algae image AI model (stub until model is trained)."""

    __tablename__ = "image_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    image_url: Mapped[str] = mapped_column(String(512))
    source: Mapped[str] = mapped_column(String(40), default="drone")  # drone|satellite|phone|camera
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    # Model outputs
    model_version: Mapped[str] = mapped_column(String(40), default="stub-v0")
    status: Mapped[str] = mapped_column(String(20), default="completed")  # pending|completed|failed
    algae_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_biomass_tonnes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    health_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    bloom_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    species_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    predicted_species: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    anomaly_flags: Mapped[list] = mapped_column(JSON, default=list)
    raw_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_stub: Mapped[bool] = mapped_column(Boolean, default=True)

    farm: Mapped["Farm"] = relationship(back_populates="image_analyses")


class SensorVerification(Base):
    """Stores results from the sensor-data AI verification model."""

    __tablename__ = "sensor_verifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    sensor_reading_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sensor_readings.id"), nullable=True
    )
    window_start: Mapped[datetime] = mapped_column(DateTime)
    window_end: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    model_version: Mapped[str] = mapped_column(String(40), default="stub-v0")
    status: Mapped[str] = mapped_column(String(20), default="completed")
    # Model outputs
    data_quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-100
    sequestration_kg_co2e: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sequestration_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_details: Mapped[list] = mapped_column(JSON, default=list)
    consistency_with_image: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verdict: Mapped[str] = mapped_column(String(40), default="plausible")  # plausible|suspicious|invalid
    raw_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_stub: Mapped[bool] = mapped_column(Boolean, default=True)

    farm: Mapped["Farm"] = relationship()
    sensor_reading: Mapped[Optional["SensorReading"]] = relationship(back_populates="sensor_verifications")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    farm_name: Mapped[str] = mapped_column(String(200))
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    operator_name: Mapped[str] = mapped_column(String(120))
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    assigned_verifier_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    estimated_credits: Mapped[float] = mapped_column(Float, default=0.0)
    verified_credits: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    review_notes: Mapped[list] = mapped_column(JSON, default=list)
    decision_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    decision_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Dual-AI verification snapshot attached at decision time
    image_analysis_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    sensor_verification_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    dual_ai_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    farm: Mapped["Farm"] = relationship(back_populates="verification_requests")


class CarbonCredit(Base):
    __tablename__ = "carbon_credits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("carbon_projects.id", use_alter=True), nullable=True
    )
    amount_tonnes_co2e: Mapped[float] = mapped_column(Float)
    vintage_year: Mapped[int] = mapped_column(Integer)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    price_per_credit: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="available")  # available|reserved|sold|retired

    farm: Mapped["Farm"] = relationship(back_populates="carbon_credits")
    project: Mapped[Optional["CarbonProject"]] = relationship(back_populates="credits")


class CarbonProject(Base):
    __tablename__ = "carbon_projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(36), ForeignKey("farms.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(120))
    images: Mapped[list] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String(20), default="verified")
    verified_by: Mapped[str] = mapped_column(String(120))
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    total_credits_available: Mapped[float] = mapped_column(Float)
    price_per_credit: Mapped[float] = mapped_column(Float)
    risk: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_roi_percent: Mapped[float] = mapped_column(Float)
    environmental_impact: Mapped[dict] = mapped_column(JSON, default=dict)
    operator_story: Mapped[str] = mapped_column(Text, default="")

    farm: Mapped["Farm"] = relationship(back_populates="carbon_projects")
    credits: Mapped[list["CarbonCredit"]] = relationship(back_populates="project")
    investments: Mapped[list["Investment"]] = relationship(back_populates="project")


class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("carbon_projects.id"), index=True)
    amount_invested: Mapped[float] = mapped_column(Float)
    credits_purchased: Mapped[float] = mapped_column(Float)
    invested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_value: Mapped[float] = mapped_column(Float)
    return_percent: Mapped[float] = mapped_column(Float, default=0.0)

    investor: Mapped["User"] = relationship(back_populates="investments")
    project: Mapped["CarbonProject"] = relationship(back_populates="investments")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    investor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))  # investment|payout|credit_retirement|withdrawal
    amount: Mapped[float] = mapped_column(Float)
    related_project_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    status: Mapped[str] = mapped_column(String(20), default="completed")


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(40))  # soil|satellite|climate|carbon_flux|sensor_timeseries|algae_imagery
    date_range_start: Mapped[str] = mapped_column(String(32))
    date_range_end: Mapped[str] = mapped_column(String(32))
    farms_covered: Mapped[int] = mapped_column(Integer, default=0)
    size_mb: Mapped[float] = mapped_column(Float, default=0.0)
    format: Mapped[str] = mapped_column(String(20), default="CSV")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    author_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    related_dataset_ids: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")


class AppNotification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    link_to: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped["User"] = relationship(back_populates="notifications")
