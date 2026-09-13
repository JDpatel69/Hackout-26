import type {
  AiFarmRef,
  AiModelStatus,
  AiRecommendation,
  AiTrustScore,
  ImageAnalysis,
  SensorVerification,
} from '../types/models';
import { api } from './http';

/**
 * "AI Trust Score" — the unified surface over the two trained models
 * (image segmentation + XGBoost biomass), backed by /api/ai/*.
 *
 * View calls (status, farms, trust-score, list*) work for every role.
 * Run calls (dual-verify, image upload, sensor verify) are limited server-side
 * to farm_operator/verifier/researcher; the UI hides them for investors.
 */

/** Backend DualAiVerifyOut — same fields as AiTrustScore but always "ready". */
interface DualAiVerifyResponse {
  farmId: string;
  imageAnalysis: ImageAnalysis;
  sensorVerification: SensorVerification;
  dualAiScore: number;
  recommendation: AiRecommendation;
  notes: string[];
}

export interface DualVerifyOptions {
  imageUrl?: string;
  imageSource?: 'drone' | 'satellite' | 'phone' | 'camera';
  windowHours?: number;
}

export const aiService = {
  /** Which backends are live (stub vs trained vs remote) for the status chip. */
  async getModelStatus(): Promise<AiModelStatus> {
    return api<AiModelStatus>('/ai/status');
  },

  /** Farms the current role may view — powers the page's farm selector. */
  async getFarms(): Promise<AiFarmRef[]> {
    return api<AiFarmRef[]>('/ai/farms');
  },

  /** Latest composited image + sensor result for a farm (view; all roles). */
  async getTrustScore(farmId: string): Promise<AiTrustScore> {
    return api<AiTrustScore>(`/ai/trust-score/${farmId}`);
  },

  /** Run BOTH models now and return a fresh composite (run-roles only). */
  async runDualVerify(farmId: string, opts: DualVerifyOptions = {}): Promise<AiTrustScore> {
    const res = await api<DualAiVerifyResponse>('/ai/dual-verify', {
      method: 'POST',
      body: {
        farmId,
        imageUrl: opts.imageUrl,
        imageSource: opts.imageSource ?? 'drone',
        windowHours: opts.windowHours ?? 24,
      },
    });
    return { ...res, status: 'ready' as const };
  },

  /** Run the image model on an uploaded photo (the real-image path). */
  async analyzeImageUpload(
    farmId: string,
    file: File,
    source: 'drone' | 'satellite' | 'phone' | 'camera' = 'phone',
  ): Promise<ImageAnalysis> {
    const form = new FormData();
    form.append('farmId', farmId);
    form.append('source', source);
    form.append('file', file);
    return api<ImageAnalysis>('/ai/image/analyze/upload', { method: 'POST', form });
  },

  /** Run the sensor model over a recent window (run-roles only). */
  async runSensorVerify(farmId: string, windowHours = 24): Promise<SensorVerification> {
    return api<SensorVerification>('/ai/sensor/verify', {
      method: 'POST',
      body: { farmId, windowHours },
    });
  },

  async listImageAnalyses(farmId: string): Promise<ImageAnalysis[]> {
    return api<ImageAnalysis[]>(`/ai/image/${farmId}`);
  },

  async listSensorVerifications(farmId: string): Promise<SensorVerification[]> {
    return api<SensorVerification[]>(`/ai/sensor/${farmId}`);
  },
};
