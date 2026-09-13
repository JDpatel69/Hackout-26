import type { CarbonProject } from '../types/models';
const images: string[] = [];
const project = (id: string, farmId: string, title: string, region: string, credits: number, price: number, roi: number, tier: CarbonProject['risk']['tier'], impact: number): CarbonProject => ({ id, farmId, title, description: `A verified regenerative agriculture project in ${region}, combining evidence-led land stewardship with long-term carbon monitoring.`, region, images, verificationStatus: 'verified', verifiedBy: 'EcoAudit Partners', verifiedAt: '2026-08-25', totalCreditsAvailable: credits, pricePerCredit: price, risk: { climateRisk: tier === 'low' ? 22 : 45, verificationConfidence: 91, operatorTrackRecord: 84, marketLiquidity: 66, composite: tier === 'low' ? 28 : 48, tier }, expectedROIPercent: roi, environmentalImpact: { co2OffsetTonnes: impact, biodiversityScore: 78, waterSavedLiters: impact * 6200 }, operatorStory: 'The farming team shifted to soil-first practices to improve resilience, crop diversity, and local water retention.' });
export const carbonProjects: CarbonProject[] = [
  project('project-green-valley','farm-green-valley','Green Valley Rice Renewal','Punjab, India',126.4,28,12.8,'low',126.4),
  project('project-highland','farm-highland','Highland Dairy Carbon Reserve','Otago, New Zealand',201.8,31,10.6,'low',201.8),
  project('project-golden','farm-golden','Golden Plains No-Till Transition','Saskatchewan, Canada',188.2,26,14.1,'medium',188.2),
  project('project-redwood','farm-redwood','Redwood Orchard Soil Initiative','California, USA',74.6,35,9.5,'low',74.6),
  project('project-cerrado','farm-cerrado','Cerrado Regeneration Corridor','Mato Grosso, Brazil',164,29,13.4,'medium',164),
  project('project-kilimanjaro','farm-kilimanjaro','Kilimanjaro Mixed-Crop Alliance','Arusha, Tanzania',91,27,15.2,'medium',91),
  project('project-delta','farm-delta','Delta Wetland Buffer Project','Mekong Delta, Vietnam',113,33,11.7,'low',113),
  project('project-patagonia','farm-patagonia','Patagonia Grazing Collective','Chubut, Argentina',156,25,16.1,'high',156)
];
