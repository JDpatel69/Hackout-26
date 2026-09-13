"""Pydantic request/response schemas aligned with the frontend TypeScript models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────
UserRole = Literal["farm_operator", "verifier", "researcher", "investor"]


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    avatarUrl: Optional[str] = None
    role: UserRole
    organization: Optional[str] = None
    phone: Optional[str] = None
    createdAt: datetime
    lastLoginAt: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class AuthSessionOut(BaseModel):
    user: UserOut
    token: str
    expiresAt: datetime


class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: datetime


# ── Geo / Farm ────────────────────────────────────────────
class GeoLocation(BaseModel):
    lat: float
    lng: float
    address: str
    region: str
    country: str


FarmStatus = Literal["draft", "submitted", "in_review", "approved", "rejected", "correction_required"]
FarmingPractice = Literal[
    "no_till",
    "cover_cropping",
    "agroforestry",
    "reduced_fertilizer",
    "rotational_grazing",
    "organic_compost",
    "water_conservation",
    "algae_cultivation",
    "photobioreactor",
    "raceway_pond",
]


class FarmCreate(BaseModel):
    name: str
    location: GeoLocation
    areaHectares: float = Field(gt=0)
    farmType: Literal["algae", "regenerative_ag"] = "algae"
    algaeSpecies: Optional[str] = None
    cultivationSystem: Optional[Literal["open_pond", "photobioreactor", "raceway"]] = None
    cropTypes: List[str] = Field(default_factory=list)
    farmingPractices: List[str] = Field(default_factory=list)
    establishedDate: Optional[str] = None
    thumbnailUrl: Optional[str] = None
    images: List[str] = Field(default_factory=list)


class FarmUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[GeoLocation] = None
    areaHectares: Optional[float] = None
    algaeSpecies: Optional[str] = None
    cultivationSystem: Optional[str] = None
    cropTypes: Optional[List[str]] = None
    farmingPractices: Optional[List[str]] = None
    status: Optional[FarmStatus] = None
    thumbnailUrl: Optional[str] = None
    images: Optional[List[str]] = None


class FarmOut(BaseModel):
    id: str
    operatorId: str
    name: str
    location: GeoLocation
    areaHectares: float
    farmType: str
    algaeSpecies: Optional[str] = None
    cultivationSystem: Optional[str] = None
    cropTypes: List[str]
    farmingPractices: List[str]
    establishedDate: Optional[str] = None
    status: FarmStatus
    documentIds: List[str] = Field(default_factory=list)
    carbonCreditsIssued: float
    thumbnailUrl: Optional[str] = None
    images: List[str]
    avgCo2UptakeKgDay: Optional[float] = None
    avgBiomassDensity: Optional[float] = None
    lastSensorAt: Optional[datetime] = None
    lastImageAnalysisAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime


class FarmDocumentOut(BaseModel):
    id: str
    farmId: str
    type: str
    fileName: str
    fileUrl: str
    uploadedAt: datetime
    verifiedStatus: str


# ── Sensors / IoT ─────────────────────────────────────────
class SensorReadingIn(BaseModel):
    farmId: str
    recordedAt: Optional[datetime] = None
    growthRate: Optional[float] = None
    co2UptakeKgH: Optional[float] = None
    biomassDensity: Optional[float] = None
    waterPh: Optional[float] = None
    waterTemperatureC: Optional[float] = None
    dissolvedOxygen: Optional[float] = None
    turbidityNtu: Optional[float] = None
    lightIntensityUmol: Optional[float] = None
    nutrientNMgL: Optional[float] = None
    nutrientPMgL: Optional[float] = None
    deviceId: Optional[str] = None
    rawPayload: Optional[Dict[str, Any]] = None


class SensorReadingOut(BaseModel):
    id: str
    farmId: str
    recordedAt: datetime
    growthRate: Optional[float] = None
    co2UptakeKgH: Optional[float] = None
    biomassDensity: Optional[float] = None
    waterPh: Optional[float] = None
    waterTemperatureC: Optional[float] = None
    dissolvedOxygen: Optional[float] = None
    turbidityNtu: Optional[float] = None
    lightIntensityUmol: Optional[float] = None
    nutrientNMgL: Optional[float] = None
    nutrientPMgL: Optional[float] = None
    deviceId: Optional[str] = None


class SensorBatchIn(BaseModel):
    readings: List[SensorReadingIn]


# ── AI model I/O ──────────────────────────────────────────
class ImageAnalysisRequest(BaseModel):
    farmId: str
    imageUrl: Optional[str] = None
    source: Literal["drone", "satellite", "phone", "camera"] = "drone"


class ImageAnalysisOut(BaseModel):
    id: str
    farmId: str
    imageUrl: str
    source: str
    createdAt: datetime
    modelVersion: str
    status: str
    algaeCoveragePct: Optional[float] = None
    estimatedBiomassTonnes: Optional[float] = None
    healthScore: Optional[float] = None
    bloomDetected: bool = False
    speciesConfidence: Optional[float] = None
    predictedSpecies: Optional[str] = None
    anomalyFlags: List[str] = Field(default_factory=list)
    rawOutput: Optional[Dict[str, Any]] = None
    isStub: bool = True


class SensorVerifyRequest(BaseModel):
    farmId: str
    windowHours: int = Field(default=24, ge=1, le=720)
    sensorReadingId: Optional[str] = None
    crossCheckImageAnalysisId: Optional[str] = None


class SensorVerificationOut(BaseModel):
    id: str
    farmId: str
    sensorReadingId: Optional[str] = None
    windowStart: datetime
    windowEnd: datetime
    createdAt: datetime
    modelVersion: str
    status: str
    dataQualityScore: Optional[float] = None
    sequestrationKgCo2e: Optional[float] = None
    sequestrationConfidence: Optional[float] = None
    anomalyDetected: bool = False
    anomalyDetails: List[str] = Field(default_factory=list)
    consistencyWithImage: Optional[float] = None
    verdict: str
    rawOutput: Optional[Dict[str, Any]] = None
    isStub: bool = True


class DualAiVerifyRequest(BaseModel):
    farmId: str
    imageUrl: Optional[str] = None
    imageSource: Literal["drone", "satellite", "phone", "camera"] = "drone"
    windowHours: int = 24


class DualAiVerifyOut(BaseModel):
    farmId: str
    imageAnalysis: ImageAnalysisOut
    sensorVerification: SensorVerificationOut
    dualAiScore: float
    recommendation: Literal["approve_ready", "needs_review", "reject_recommended"]
    notes: List[str]


class AiTrustScoreOut(BaseModel):
    """Unified 'AI Trust Score' view surface read by every role.

    status="ready" when at least one stored analysis exists; "pending" when the
    farm has neither an image analysis nor a sensor verification yet.
    """

    farmId: str
    status: Literal["ready", "pending"]
    imageAnalysis: Optional[ImageAnalysisOut] = None
    sensorVerification: Optional[SensorVerificationOut] = None
    dualAiScore: Optional[float] = None
    recommendation: Optional[Literal["approve_ready", "needs_review", "reject_recommended"]] = None
    notes: List[str] = Field(default_factory=list)


class AiFarmRefOut(BaseModel):
    """Lightweight farm reference for the AI Trust Score farm selector."""

    id: str
    name: str
    status: str


# ── Verification ──────────────────────────────────────────
VerificationStatus = Literal["pending", "in_review", "approved", "rejected", "correction_required"]


class VerificationRequestOut(BaseModel):
    id: str
    farmId: str
    farmName: str
    operatorId: str
    operatorName: str
    submittedAt: datetime
    status: VerificationStatus
    assignedVerifierId: Optional[str] = None
    evidenceCount: int
    estimatedCredits: float
    verifiedCredits: Optional[float] = None
    reviewNotes: List[Dict[str, Any]] = Field(default_factory=list)
    decisionAt: Optional[datetime] = None
    decisionBy: Optional[str] = None
    rejectionReason: Optional[str] = None
    imageAnalysisId: Optional[str] = None
    sensorVerificationId: Optional[str] = None
    dualAiScore: Optional[float] = None


class ApproveRequest(BaseModel):
    verifiedCredits: float = Field(ge=0)
    notes: Optional[str] = None


class RejectRequest(BaseModel):
    reason: str = Field(min_length=5)


class CorrectionRequest(BaseModel):
    note: str = Field(min_length=5)


# ── Investor ──────────────────────────────────────────────
class CarbonProjectOut(BaseModel):
    id: str
    farmId: str
    title: str
    description: str
    region: str
    images: List[str]
    verificationStatus: str
    verifiedBy: str
    verifiedAt: datetime
    totalCreditsAvailable: float
    pricePerCredit: float
    risk: Dict[str, Any]
    expectedROIPercent: float
    environmentalImpact: Dict[str, Any]
    operatorStory: str


class InvestRequest(BaseModel):
    amount: float = Field(gt=0)


class InvestmentOut(BaseModel):
    id: str
    investorId: str
    projectId: str
    amountInvested: float
    creditsPurchased: float
    investedAt: datetime
    status: str
    currentValue: float
    returnPercent: float


class TransactionOut(BaseModel):
    id: str
    investorId: str
    type: str
    amount: float
    relatedProjectId: Optional[str] = None
    date: datetime
    status: str


class PortfolioSummaryOut(BaseModel):
    totalInvested: float
    currentPortfolioValue: float
    totalReturnPercent: float
    totalCreditsOwned: float
    projectsCount: int
    co2OffsetTotal: float


class CarbonCreditOut(BaseModel):
    id: str
    farmId: str
    projectId: Optional[str] = None
    amountTonnesCO2e: float
    vintageYear: int
    issuedAt: datetime
    pricePerCredit: float
    status: str


# ── Researcher ────────────────────────────────────────────
class DatasetOut(BaseModel):
    id: str
    name: str
    region: str
    type: str
    dateRangeStart: str
    dateRangeEnd: str
    farmsCovered: int
    sizeMB: float
    format: str


class ResearchReportCreate(BaseModel):
    title: str
    datasetIds: List[str]
    summary: str


class ResearchReportOut(BaseModel):
    id: str
    title: str
    authorId: str
    createdAt: datetime
    relatedDatasetIds: List[str]
    summary: str
    status: str


# ── Notifications ─────────────────────────────────────────
class NotificationOut(BaseModel):
    id: str
    userId: str
    type: str
    title: str
    message: str
    isRead: bool
    createdAt: datetime
    linkTo: Optional[str] = None


# ── Generic ───────────────────────────────────────────────
class MessageOut(BaseModel):
    message: str


class HealthOut(BaseModel):
    status: str
    app: str
    version: str
    aiImageModel: Dict[str, Any]
    aiSensorModel: Dict[str, Any]
