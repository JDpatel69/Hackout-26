"""ORM → API response mappers (camelCase to match frontend TypeScript)."""

from __future__ import annotations

from typing import List

from app.models import (
    AppNotification,
    CarbonCredit,
    CarbonProject,
    Dataset,
    Farm,
    FarmDocument,
    ImageAnalysis,
    Investment,
    ResearchReport,
    SensorReading,
    SensorVerification,
    Transaction,
    User,
    VerificationRequest,
)
from app.schemas import (
    CarbonCreditOut,
    CarbonProjectOut,
    DatasetOut,
    FarmDocumentOut,
    FarmOut,
    GeoLocation,
    ImageAnalysisOut,
    InvestmentOut,
    NotificationOut,
    PortfolioSummaryOut,
    ResearchReportOut,
    SensorReadingOut,
    SensorVerificationOut,
    TransactionOut,
    UserOut,
    VerificationRequestOut,
)


def user_out(u: User) -> UserOut:
    return UserOut(
        id=u.id,
        name=u.name,
        email=u.email,
        avatarUrl=u.avatar_url,
        role=u.role,  # type: ignore[arg-type]
        organization=u.organization,
        phone=u.phone,
        createdAt=u.created_at,
        lastLoginAt=u.last_login_at,
    )


def farm_out(f: Farm, document_ids: List[str] | None = None) -> FarmOut:
    return FarmOut(
        id=f.id,
        operatorId=f.operator_id,
        name=f.name,
        location=GeoLocation(
            lat=f.lat,
            lng=f.lng,
            address=f.address,
            region=f.region,
            country=f.country,
        ),
        areaHectares=f.area_hectares,
        farmType=f.farm_type,
        algaeSpecies=f.algae_species,
        cultivationSystem=f.cultivation_system,
        cropTypes=list(f.crop_types or []),
        farmingPractices=list(f.farming_practices or []),
        establishedDate=f.established_date,
        status=f.status,  # type: ignore[arg-type]
        documentIds=document_ids if document_ids is not None else [d.id for d in (f.documents or [])],
        carbonCreditsIssued=f.carbon_credits_issued,
        thumbnailUrl=f.thumbnail_url,
        images=list(f.images or []),
        avgCo2UptakeKgDay=f.avg_co2_uptake_kg_day,
        avgBiomassDensity=f.avg_biomass_density,
        lastSensorAt=f.last_sensor_at,
        lastImageAnalysisAt=f.last_image_analysis_at,
        createdAt=f.created_at,
        updatedAt=f.updated_at,
    )


def document_out(d: FarmDocument) -> FarmDocumentOut:
    return FarmDocumentOut(
        id=d.id,
        farmId=d.farm_id,
        type=d.type,
        fileName=d.file_name,
        fileUrl=d.file_url,
        uploadedAt=d.uploaded_at,
        verifiedStatus=d.verified_status,
    )


def sensor_out(r: SensorReading) -> SensorReadingOut:
    return SensorReadingOut(
        id=r.id,
        farmId=r.farm_id,
        recordedAt=r.recorded_at,
        growthRate=r.growth_rate,
        co2UptakeKgH=r.co2_uptake_kg_h,
        biomassDensity=r.biomass_density,
        waterPh=r.water_ph,
        waterTemperatureC=r.water_temperature_c,
        dissolvedOxygen=r.dissolved_oxygen,
        turbidityNtu=r.turbidity_ntu,
        lightIntensityUmol=r.light_intensity_umol,
        nutrientNMgL=r.nutrient_n_mg_l,
        nutrientPMgL=r.nutrient_p_mg_l,
        deviceId=r.device_id,
    )


def image_analysis_out(a: ImageAnalysis) -> ImageAnalysisOut:
    return ImageAnalysisOut(
        id=a.id,
        farmId=a.farm_id,
        imageUrl=a.image_url,
        source=a.source,
        createdAt=a.created_at,
        modelVersion=a.model_version,
        status=a.status,
        algaeCoveragePct=a.algae_coverage_pct,
        estimatedBiomassTonnes=a.estimated_biomass_tonnes,
        healthScore=a.health_score,
        bloomDetected=a.bloom_detected,
        speciesConfidence=a.species_confidence,
        predictedSpecies=a.predicted_species,
        anomalyFlags=list(a.anomaly_flags or []),
        rawOutput=a.raw_output,
        isStub=a.is_stub,
    )


def sensor_verification_out(v: SensorVerification) -> SensorVerificationOut:
    return SensorVerificationOut(
        id=v.id,
        farmId=v.farm_id,
        sensorReadingId=v.sensor_reading_id,
        windowStart=v.window_start,
        windowEnd=v.window_end,
        createdAt=v.created_at,
        modelVersion=v.model_version,
        status=v.status,
        dataQualityScore=v.data_quality_score,
        sequestrationKgCo2e=v.sequestration_kg_co2e,
        sequestrationConfidence=v.sequestration_confidence,
        anomalyDetected=v.anomaly_detected,
        anomalyDetails=list(v.anomaly_details or []),
        consistencyWithImage=v.consistency_with_image,
        verdict=v.verdict,
        rawOutput=v.raw_output,
        isStub=v.is_stub,
    )


def verification_out(v: VerificationRequest) -> VerificationRequestOut:
    return VerificationRequestOut(
        id=v.id,
        farmId=v.farm_id,
        farmName=v.farm_name,
        operatorId=v.operator_id,
        operatorName=v.operator_name,
        submittedAt=v.submitted_at,
        status=v.status,  # type: ignore[arg-type]
        assignedVerifierId=v.assigned_verifier_id,
        evidenceCount=v.evidence_count,
        estimatedCredits=v.estimated_credits,
        verifiedCredits=v.verified_credits,
        reviewNotes=list(v.review_notes or []),
        decisionAt=v.decision_at,
        decisionBy=v.decision_by,
        rejectionReason=v.rejection_reason,
        imageAnalysisId=v.image_analysis_id,
        sensorVerificationId=v.sensor_verification_id,
        dualAiScore=v.dual_ai_score,
    )


def project_out(p: CarbonProject) -> CarbonProjectOut:
    return CarbonProjectOut(
        id=p.id,
        farmId=p.farm_id,
        title=p.title,
        description=p.description,
        region=p.region,
        images=list(p.images or []),
        verificationStatus=p.verification_status,
        verifiedBy=p.verified_by,
        verifiedAt=p.verified_at,
        totalCreditsAvailable=p.total_credits_available,
        pricePerCredit=p.price_per_credit,
        risk=dict(p.risk or {}),
        expectedROIPercent=p.expected_roi_percent,
        environmentalImpact=dict(p.environmental_impact or {}),
        operatorStory=p.operator_story,
    )


def investment_out(i: Investment) -> InvestmentOut:
    return InvestmentOut(
        id=i.id,
        investorId=i.investor_id,
        projectId=i.project_id,
        amountInvested=i.amount_invested,
        creditsPurchased=i.credits_purchased,
        investedAt=i.invested_at,
        status=i.status,
        currentValue=i.current_value,
        returnPercent=i.return_percent,
    )


def transaction_out(t: Transaction) -> TransactionOut:
    return TransactionOut(
        id=t.id,
        investorId=t.investor_id,
        type=t.type,
        amount=t.amount,
        relatedProjectId=t.related_project_id,
        date=t.date,
        status=t.status,
    )


def credit_out(c: CarbonCredit) -> CarbonCreditOut:
    return CarbonCreditOut(
        id=c.id,
        farmId=c.farm_id,
        projectId=c.project_id,
        amountTonnesCO2e=c.amount_tonnes_co2e,
        vintageYear=c.vintage_year,
        issuedAt=c.issued_at,
        pricePerCredit=c.price_per_credit,
        status=c.status,
    )


def dataset_out(d: Dataset) -> DatasetOut:
    return DatasetOut(
        id=d.id,
        name=d.name,
        region=d.region,
        type=d.type,
        dateRangeStart=d.date_range_start,
        dateRangeEnd=d.date_range_end,
        farmsCovered=d.farms_covered,
        sizeMB=d.size_mb,
        format=d.format,
    )


def report_out(r: ResearchReport) -> ResearchReportOut:
    return ResearchReportOut(
        id=r.id,
        title=r.title,
        authorId=r.author_id,
        createdAt=r.created_at,
        relatedDatasetIds=list(r.related_dataset_ids or []),
        summary=r.summary,
        status=r.status,
    )


def notification_out(n: AppNotification) -> NotificationOut:
    return NotificationOut(
        id=n.id,
        userId=n.user_id,
        type=n.type,
        title=n.title,
        message=n.message,
        isRead=n.is_read,
        createdAt=n.created_at,
        linkTo=n.link_to,
    )


def portfolio_summary(investments: List[Investment]) -> PortfolioSummaryOut:
    total_invested = sum(i.amount_invested for i in investments)
    current_value = sum(i.current_value for i in investments)
    credits = sum(i.credits_purchased for i in investments)
    projects = len({i.project_id for i in investments})
    ret = ((current_value - total_invested) / total_invested * 100.0) if total_invested else 0.0
    return PortfolioSummaryOut(
        totalInvested=round(total_invested, 2),
        currentPortfolioValue=round(current_value, 2),
        totalReturnPercent=round(ret, 2),
        totalCreditsOwned=round(credits, 3),
        projectsCount=projects,
        co2OffsetTotal=round(credits, 3),
    )
