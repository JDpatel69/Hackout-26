import type { CarbonCredit, DocumentType, Farm, FarmDocument, VerificationRequest } from '../types/models';
import { api } from './http';

/**
 * Farm operator data — backed by /api/farms/*.
 * The authenticated operator is derived from the JWT server-side, so
 * getFarmsByOperator ignores its argument (kept for signature-compatibility).
 * farmType/algaeSpecies/cultivationSystem default on the backend, so the
 * existing wizard payload posts cleanly with no reshaping.
 */
export const farmService = {
  async createFarm(
    data: Omit<Farm, 'id' | 'status' | 'carbonCreditsIssued' | 'createdAt' | 'updatedAt' | 'documentIds'>,
  ): Promise<Farm> {
    return api<Farm>('/farms', { method: 'POST', body: data });
  },
  async updateFarm(farmId: string, updates: Partial<Farm>): Promise<Farm> {
    return api<Farm>(`/farms/${farmId}`, { method: 'PATCH', body: updates });
  },
  async getFarmDetails(farmId: string): Promise<Farm> {
    return api<Farm>(`/farms/${farmId}`);
  },
  async getFarmsByOperator(_operatorId: string): Promise<Farm[]> {
    return api<Farm[]>('/farms');
  },
  async uploadFarmDocument(farmId: string, file: File, type: DocumentType): Promise<FarmDocument> {
    const form = new FormData();
    form.append('type', type);
    form.append('file', file);
    return api<FarmDocument>(`/farms/${farmId}/documents`, { method: 'POST', form });
  },
  async getFarmDocuments(farmId: string): Promise<FarmDocument[]> {
    return api<FarmDocument[]>(`/farms/${farmId}/documents`);
  },
  async submitForVerification(farmId: string): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/farms/${farmId}/submit`, { method: 'POST' });
  },
  async getVerificationStatus(farmId: string): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/farms/${farmId}/verification`);
  },
  async viewCarbonCredits(operatorId: string): Promise<CarbonCredit[]> {
    return api<CarbonCredit[]>(`/farms/operator/${operatorId}/credits`);
  },
};
