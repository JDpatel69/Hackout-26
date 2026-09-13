export type UserRole = 'farm_operator' | 'verifier' | 'researcher' | 'investor';
export interface User { id: string; name: string; email: string; avatarUrl: string; role: UserRole; organization?: string; phone?: string; createdAt: string; lastLoginAt: string; }
export interface AuthSession { user: User; token: string; expiresAt: string; }

export type FarmStatus = 'draft' | 'submitted' | 'in_review' | 'approved' | 'rejected' | 'correction_required';
export type FarmingPractice = 'no_till' | 'cover_cropping' | 'agroforestry' | 'reduced_fertilizer' | 'rotational_grazing' | 'organic_compost' | 'water_conservation';
export interface GeoLocation { lat: number; lng: number; address: string; region: string; country: string; }
export interface Farm { id: string; operatorId: string; name: string; location: GeoLocation; areaHectares: number; cropTypes: string[]; farmingPractices: FarmingPractice[]; establishedDate: string; status: FarmStatus; documentIds: string[]; carbonCreditsIssued: number; thumbnailUrl: string; images: string[]; createdAt: string; updatedAt: string; }
export type DocumentType = 'land_title' | 'soil_test' | 'practice_photo' | 'satellite_image' | 'other';
export interface FarmDocument { id: string; farmId: string; type: DocumentType; fileName: string; fileUrl: string; uploadedAt: string; verifiedStatus: 'pending' | 'verified' | 'flagged'; }
export type VerificationStatus = 'pending' | 'in_review' | 'approved' | 'rejected' | 'correction_required';
export interface VerificationRequest {
  id: string;
  farmId: string;
  farmName: string;
  operatorId: string;
  operatorName: string;
  submittedAt: string;
  status: VerificationStatus;
  assignedVerifierId?: string;
  evidenceCount: number;
  estimatedCredits: number;
  /** Verified credits (set after approval). */
  verifiedCredits?: number;
  reviewNotes: { authorId: string; note: string; createdAt: string }[];
  decisionAt?: string;
  decisionBy?: string;
  rejectionReason?: string;
  /** Dual-AI composite score (0–100), set after estimate or approval. */
  dualAiScore?: number;
  imageAnalysisId?: string;
  sensorVerificationId?: string;
}


export interface CarbonCredit { id: string; farmId: string; projectId: string; amountTonnesCO2e: number; vintageYear: number; issuedAt: string; pricePerCredit: number; status: 'available' | 'reserved' | 'sold' | 'retired'; }
export type RiskTier = 'low' | 'medium' | 'high';
export interface RiskBreakdown { climateRisk: number; verificationConfidence: number; operatorTrackRecord: number; marketLiquidity: number; composite: number; tier: RiskTier; }
export interface EnvironmentalImpact { co2OffsetTonnes: number; biodiversityScore: number; waterSavedLiters: number; }
export interface CarbonProject { id: string; farmId: string; title: string; description: string; region: string; images: string[]; verificationStatus: 'verified'; verifiedBy: string; verifiedAt: string; totalCreditsAvailable: number; pricePerCredit: number; risk: RiskBreakdown; expectedROIPercent: number; environmentalImpact: EnvironmentalImpact; operatorStory: string; }
export interface Investment { id: string; investorId: string; projectId: string; amountInvested: number; creditsPurchased: number; investedAt: string; status: 'active' | 'completed' | 'retired'; currentValue: number; returnPercent: number; }
export type TransactionType = 'investment' | 'payout' | 'credit_retirement' | 'withdrawal';
export interface Transaction { id: string; investorId: string; type: TransactionType; amount: number; relatedProjectId?: string; date: string; status: 'completed' | 'pending' | 'failed'; }
export interface PortfolioSummary { totalInvested: number; currentPortfolioValue: number; totalReturnPercent: number; totalCreditsOwned: number; projectsCount: number; co2OffsetTotal: number; }
export type DatasetType = 'soil' | 'satellite' | 'climate' | 'carbon_flux';
export interface Dataset { id: string; name: string; region: string; type: DatasetType; dateRangeStart: string; dateRangeEnd: string; farmsCovered: number; sizeMB: number; format: 'CSV' | 'GeoTIFF' | 'JSON' | 'NetCDF'; }
export interface ResearchReport { id: string; title: string; authorId: string; createdAt: string; relatedDatasetIds: string[]; summary: string; status: 'draft' | 'published'; }
export type NotificationType = 'verification' | 'credits' | 'investment' | 'system';
export interface AppNotification { id: string; userId: string; type: NotificationType; title: string; message: string; isRead: boolean; createdAt: string; linkTo?: string; }

// ─────────────────────────────────────────────────────────────────────────
// Additive "wow feature" layer (P1–P5). None of the above types are changed.
// Every live/simulated/proxy payload carries an explicit `dataSource` label.
// ─────────────────────────────────────────────────────────────────────────
export type DataSource = 'live' | 'simulation' | 'historical';

// P1 — Live pond digital twin + streaming telemetry
export interface LiveReading {
  farmId: string;
  recordedAt: string;
  growthRate?: number | null;
  co2UptakeKgH?: number | null;
  biomassDensity?: number | null;
  waterPh?: number | null;
  waterTemperatureC?: number | null;
  dissolvedOxygen?: number | null;
  turbidityNtu?: number | null;
  lightIntensityUmol?: number | null;
  nutrientNMgL?: number | null;
  nutrientPMgL?: number | null;
  deviceId?: string | null;
}
export interface PondTwinState {
  farmId: string;
  dataSource: DataSource;
  healthScore: number;       // 0–100
  algaeCoveragePct: number;  // 0–100
  biomassDensity: number;    // g/L
  turbidityNtu: number;
  waterTemperatureC: number;
  dissolvedOxygen: number;
  co2UptakeKgH: number;
  bloomRisk: number;         // 0–1
  anomaly: boolean;
  cumulativeCo2Kg: number;
  updatedAt: string;
}
export interface LiveFrame {
  farmId: string;
  dataSource: DataSource;
  reading: LiveReading;
  twin: PondTwinState;
  cumulativeCo2Kg: number;
  co2RateKgH: number;
  serverTime: string;
}

// P2 — Explainable dual-AI trust
export interface TrustFactor { key: string; label: string; weight: number; value: number; contribution: number; detail?: string; }
export interface TrustBreakdown {
  farmId: string;
  requestId?: string;
  trustScore: number; // 0–100
  recommendation: 'approve_ready' | 'needs_review' | 'reject_recommended';
  verdict: string;
  factors: TrustFactor[];
  anomalies: string[];
  notes: string[];
  imageAnalysis: { healthScore?: number | null; algaeCoveragePct?: number | null; estimatedBiomassTonnes?: number | null; bloomDetected: boolean; predictedSpecies?: string | null; anomalyFlags: string[]; isStub: boolean };
  sensorVerification: { dataQualityScore?: number | null; sequestrationKgCo2e?: number | null; sequestrationConfidence?: number | null; anomalyDetected: boolean; anomalyDetails: string[]; consistencyWithImage?: number | null; verdict: string; isStub: boolean };
  dataSource: DataSource;
}

// ─────────────────────────────────────────────────────────────────────────
// "AI Trust Score" — unified surface for the two trained models (image + sensor).
// Shapes mirror the backend DTOs (ImageAnalysisOut / SensorVerificationOut /
// AiTrustScoreOut / AiFarmRefOut). Available to every role; run/upload is gated
// to farm_operator/verifier/researcher in the UI.
// ─────────────────────────────────────────────────────────────────────────
export type AiRecommendation = 'approve_ready' | 'needs_review' | 'reject_recommended';

export interface ImageAnalysis {
  id: string;
  farmId: string;
  imageUrl: string;
  source: string;
  createdAt: string;
  modelVersion: string;
  status: string;
  algaeCoveragePct?: number | null;
  estimatedBiomassTonnes?: number | null;
  healthScore?: number | null;
  bloomDetected: boolean;
  speciesConfidence?: number | null;
  predictedSpecies?: string | null;
  anomalyFlags: string[];
  rawOutput?: Record<string, unknown> | null;
  isStub: boolean;
}

export interface SensorVerification {
  id: string;
  farmId: string;
  sensorReadingId?: string | null;
  windowStart: string;
  windowEnd: string;
  createdAt: string;
  modelVersion: string;
  status: string;
  dataQualityScore?: number | null;
  sequestrationKgCo2e?: number | null;
  sequestrationConfidence?: number | null;
  anomalyDetected: boolean;
  anomalyDetails: string[];
  consistencyWithImage?: number | null;
  verdict: string;
  rawOutput?: Record<string, unknown> | null;
  isStub: boolean;
}

export interface AiTrustScore {
  farmId: string;
  status: 'ready' | 'pending';
  imageAnalysis?: ImageAnalysis | null;
  sensorVerification?: SensorVerification | null;
  dualAiScore?: number | null;
  recommendation?: AiRecommendation | null;
  notes: string[];
}

export interface AiFarmRef { id: string; name: string; status: FarmStatus | string; }

export interface AiModelInfo { name: string; enabled_flag: boolean; ready: boolean; is_stub: boolean; path?: string; url?: string | null; }
export interface AiModelStatus { image: AiModelInfo; sensor: AiModelInfo; }


// P3 — Tamper-evident, hash-chained certificate (blockchain-inspired, NOT a blockchain)
export interface Certificate {
  id: string;
  farmId: string;
  farmName: string;
  region: string;
  country: string;
  operatorId: string;
  verifierId: string;
  verifiedBy?: string;
  projectId?: string | null;
  carbonCreditId?: string | null;
  verificationRequestId?: string | null;
  verifiedCredits: number;
  dualAiScore: number;
  vintageYear: number;
  issuedAt: string;
  sequenceNumber: number;
  previousHash: string;
  currentHash: string;
  dataSource: DataSource;
  isDemo: boolean;
  status: 'active' | 'revoked';
  verifyUrl?: string;
  payload?: Record<string, unknown>;
}
export interface CertificateVerification {
  certificateId: string;
  valid: boolean;
  chainIntact: boolean;
  recomputedHash: string;
  storedHash: string;
  sequenceNumber: number;
  previousHash: string;
  issuedAt: string;
  status: 'active' | 'revoked';
  message: string;
}

// P4 — Satellite / remote-sensing (NASA GIBS imagery + labeled proxy overlay)
export interface GibsLayer { id: string; label: string; layer: string; tileMatrixSet?: string; format?: string; date?: string; kind: 'imagery' | 'proxy'; dataSource: DataSource; }
export interface RemoteSensingPoint { date: string; ndwi: number; chlorophyllProxy: number; }
export interface SatelliteData {
  farmId: string;
  lat: number;
  lng: number;
  region?: string;
  country?: string;
  bbox: [number, number, number, number]; // minLng, minLat, maxLng, maxLat
  layers: GibsLayer[];
  series: RemoteSensingPoint[];
  dataSource: DataSource;
  note?: string;
}

// P5 — Fleet map, what-if simulator, public impact
export interface FleetSite {
  farmId: string;
  name: string;
  lat: number;
  lng: number;
  region: string;
  country: string;
  status: FarmStatus;
  areaHectares: number;
  carbonCreditsIssued: number;
  avgCo2UptakeKgDay?: number | null;
  lastSensorAt?: string | null;
  dataSource: DataSource;
}
export interface WhatIfInput {
  areaHectares: number;
  species?: string;
  cultivationSystem?: string;
  waterTemperatureC: number;
  nutrientLevel: number; // 0–100
  lightIntensityUmol: number;
  days: number;
}
export interface WhatIfPoint { day: number; biomassTonnes: number; co2Tonnes: number; }
export interface WhatIfResult {
  input: WhatIfInput;
  projectedBiomassTonnes: number;
  projectedCo2Tonnes: number;
  projectedCredits: number;
  dailyMeanCo2Kg: number;
  series: WhatIfPoint[];
  assumptions: string[];
  disclaimer: string;
  dataSource: 'simulation';
}
export interface ImpactSummary {
  totalVerifiedCredits: number;
  totalCo2Tonnes: number;
  activeFarms: number;
  approvedFarms: number;
  verifiedProjects: number;
  totalSequestrationKgDay: number;
  countriesCount: number;
  certificatesIssued: number;
  updatedAt: string;
  dataSource: DataSource;
}
