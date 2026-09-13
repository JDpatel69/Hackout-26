import type { FarmDocument, VerificationRequest, VerificationStatus } from '../types/models';
import { api } from './http';

/**
 * Verifier workflow — backed by /api/verifier/*.
 * `calculateVerifiedCredits` hits the dual-AI estimate endpoint, which runs
 * BOTH ML models (image + sensor) server-side and returns the credit estimate.
 */
export const verifierService = {
  async getPendingProjects(): Promise<VerificationRequest[]> {
    const all = await api<VerificationRequest[]>('/verifier/requests');
    return all.filter((r) => ['pending', 'in_review', 'correction_required'].includes(r.status));
  },
  async getRequestsByStatus(status: VerificationStatus): Promise<VerificationRequest[]> {
    return api<VerificationRequest[]>('/verifier/requests', { query: { status } });
  },
  async getRequestById(requestId: string): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/verifier/requests/${requestId}`);
  },
  async getHistory(): Promise<VerificationRequest[]> {
    return api<VerificationRequest[]>('/verifier/history');
  },
  async getProjectEvidence(requestId: string): Promise<FarmDocument[]> {
    return api<FarmDocument[]>(`/verifier/requests/${requestId}/evidence`);
  },
  async reviewProject(requestId: string, _status: VerificationStatus): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/verifier/requests/${requestId}/review`, { method: 'POST' });
  },
  async approveProject(requestId: string, verifiedCredits: number): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/verifier/requests/${requestId}/approve`, { method: 'POST', body: { verifiedCredits } });
  },
  async rejectProject(requestId: string, reason: string): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/verifier/requests/${requestId}/reject`, { method: 'POST', body: { reason } });
  },
  async requestCorrection(requestId: string, note: string): Promise<VerificationRequest> {
    return api<VerificationRequest>(`/verifier/requests/${requestId}/correction`, { method: 'POST', body: { note } });
  },
  async calculateVerifiedCredits(requestId: string): Promise<number> {
    const res = await api<{ estimatedCredits: number }>(`/verifier/requests/${requestId}/estimate-credits`);
    return res.estimatedCredits;
  },
};
