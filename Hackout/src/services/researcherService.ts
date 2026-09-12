import type { Dataset, ResearchReport } from '../types/models';
import { api, API_BASE, authHeaders } from './http';

/** A single environmental / sensor record as returned by the backend. */
export interface EnvironmentalRecord {
  farmId: string;
  recordedAt: string;
  growthRate: number;
  co2UptakeKgH: number;
  waterPh: number;
  biomassDensity: number;
}
export interface CarbonTrendPoint { date: string; tonnesCO2e: number }
export interface SatelliteFrame { date: string; imageUrl: string }

/**
 * Researcher analytics — backed by /api/researcher/*.
 * NOTE: getEnvironmentalData now returns the backend's real sensor records
 * (shape changed from the old farm-summary mock); the Analytics page is
 * adapted to this shape during the researcher wiring pass.
 */
export const researcherService = {
  async getDatasets(filters?: { region?: string; type?: string }): Promise<Dataset[]> {
    return api<Dataset[]>('/researcher/datasets', { query: { region: filters?.region, type: filters?.type } });
  },
  async getEnvironmentalData(filters?: { region?: string }): Promise<EnvironmentalRecord[]> {
    return api<EnvironmentalRecord[]>('/researcher/environmental', { query: { region: filters?.region } });
  },
  async getCarbonTrends(region?: string): Promise<CarbonTrendPoint[]> {
    return api<CarbonTrendPoint[]>('/researcher/carbon-trends', { query: { region } });
  },
  async getSatelliteData(farmId: string): Promise<SatelliteFrame[]> {
    return api<SatelliteFrame[]>(`/researcher/satellite/${farmId}`);
  },
  async compareFarms(farmIds: string[]): Promise<{ farms: unknown[] }> {
    return api<{ farms: unknown[] }>('/researcher/compare-farms', { method: 'POST', body: farmIds });
  },
  async generateResearchReport(input: { title: string; datasetIds: string[]; summary: string }): Promise<ResearchReport> {
    return api<ResearchReport>('/researcher/reports', { method: 'POST', body: input });
  },
  async getResearchReports(status?: string): Promise<ResearchReport[]> {
    return api<ResearchReport[]>('/researcher/reports', { query: { status } });
  },
  async publishReport(reportId: string): Promise<ResearchReport> {
    return api<ResearchReport>(`/researcher/reports/${reportId}/publish`, { method: 'POST' });
  },
  async exportDataset(datasetId: string, format: 'csv' | 'json'): Promise<Blob> {
    const res = await fetch(`${API_BASE}/researcher/datasets/${datasetId}/export?format=${format}`, { headers: authHeaders() });
    if (!res.ok) throw new Error('Dataset export failed');
    return res.blob();
  },
};
