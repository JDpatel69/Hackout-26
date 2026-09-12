import type { CarbonProject, Investment, PortfolioSummary, RiskBreakdown, RiskTier, Transaction } from '../types/models';
import { api } from './http';

/**
 * Investor marketplace + portfolio — backed by /api/investor/*.
 * Method names/signatures are unchanged from the old mock so pages keep working.
 */
export const investorService = {
  async getProjects(filters?: { region?: string; riskTier?: RiskTier; minROI?: number }): Promise<CarbonProject[]> {
    return api<CarbonProject[]>('/investor/projects', {
      query: { region: filters?.region, riskTier: filters?.riskTier, minROI: filters?.minROI },
    });
  },
  async getProjectDetails(projectId: string): Promise<CarbonProject> {
    return api<CarbonProject>(`/investor/projects/${projectId}`);
  },
  async calculateROI(projectId: string, amount: number): Promise<number> {
    const res = await api<{ roiPercent: number }>(`/investor/projects/${projectId}/roi`, { query: { amount } });
    return Math.round(amount * res.roiPercent) / 100;
  },
  async calculateRiskScore(projectId: string): Promise<RiskBreakdown> {
    const project = await this.getProjectDetails(projectId);
    return project.risk;
  },
  async investInProject(projectId: string, amount: number): Promise<Investment> {
    return api<Investment>(`/investor/projects/${projectId}/invest`, { method: 'POST', body: { amount } });
  },
  async getPortfolio(_investorId: string): Promise<PortfolioSummary> {
    return api<PortfolioSummary>('/investor/portfolio');
  },
  async getInvestments(): Promise<Investment[]> {
    return api<Investment[]>('/investor/investments');
  },
  async getTransactionHistory(_investorId: string): Promise<Transaction[]> {
    return api<Transaction[]>('/investor/transactions');
  },
};
