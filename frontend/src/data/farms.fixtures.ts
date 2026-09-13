import type { Farm, FarmDocument } from '../types/models';
const now = '2026-09-01';
const farm = (id: string, name: string, region: string, country: string, area: number, crops: string[], status: Farm['status'], credits: number): Farm => ({ id, operatorId: 'op-ava', name, location: { lat: 0, lng: 0, address: `${area} hectare holding`, region, country }, areaHectares: area, cropTypes: crops, farmingPractices: ['no_till', 'cover_cropping', 'reduced_fertilizer'], establishedDate: '2018-03-01', status, documentIds: [`doc-${id}`], carbonCreditsIssued: credits, thumbnailUrl: '', images: [], createdAt: '2025-01-10', updatedAt: now });
export const farms: Farm[] = [
  farm('farm-green-valley', 'Green Valley Rice Farm', 'Punjab', 'India', 64, ['Rice', 'Chickpea'], 'approved', 126.4),
  farm('farm-sunrise', 'Sunrise Agroforestry Collective', 'Nakuru County', 'Kenya', 88, ['Maize', 'Moringa'], 'in_review', 0),
  farm('farm-highland', 'Highland Dairy Pastures', 'Otago', 'New Zealand', 115, ['Pasture'], 'approved', 201.8),
  farm('farm-blue-river', 'Blue River Vegetable Co-op', 'Iowa', 'USA', 42, ['Kale', 'Beans'], 'submitted', 0),
  farm('farm-golden', 'Golden Plains Wheat Farm', 'Saskatchewan', 'Canada', 142, ['Wheat'], 'approved', 188.2),
  farm('farm-terra-verde', 'Terra Verde Coffee Estate', 'Minas Gerais', 'Brazil', 57, ['Coffee'], 'correction_required', 0),
  farm('farm-mekong', 'Mekong Regeneration Farm', 'Chiang Mai', 'Thailand', 39, ['Rice', 'Sesame'], 'in_review', 0),
  farm('farm-redwood', 'Redwood Orchard Alliance', 'California', 'USA', 32, ['Almond', 'Cover crop'], 'approved', 74.6),
  farm('farm-savanna', 'Savanna Soil Stewards', 'Kajiado County', 'Kenya', 73, ['Sorghum', 'Pasture'], 'rejected', 0),
  farm('farm-andes', 'Andes Polyculture Farm', 'Cusco', 'Peru', 48, ['Quinoa', 'Beans'], 'draft', 0)
];
export const documents: FarmDocument[] = farms.flatMap((item, index) => [
  { id: `doc-${item.id}`, farmId: item.id, type: index % 3 === 0 ? 'soil_test' : 'practice_photo', fileName: `${item.name.toLowerCase().replaceAll(' ', '-')}-evidence.pdf`, fileUrl: '#', uploadedAt: `2026-0${(index % 8) + 1}-14`, verifiedStatus: item.status === 'approved' ? 'verified' : 'pending' },
  { id: `sat-${item.id}`, farmId: item.id, type: 'satellite_image', fileName: `${item.id}-satellite-index.png`, fileUrl: '#', uploadedAt: `2026-0${(index % 8) + 1}-20`, verifiedStatus: index % 5 === 0 ? 'flagged' : 'verified' }
]);
