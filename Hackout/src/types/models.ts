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
export interface VerificationRequest { id: string; farmId: string; farmName: string; operatorId: string; operatorName: string; submittedAt: string; status: VerificationStatus; assignedVerifierId?: string; evidenceCount: number; estimatedCredits: number; reviewNotes: { authorId: string; note: string; createdAt: string }[]; decisionAt?: string; decisionBy?: string; rejectionReason?: string; }

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
