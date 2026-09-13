import { useCallback, useEffect, useMemo, useState } from 'react';
import { AiTrustScore } from '../../components/ai/AiTrustScore';
import { EmptyState, GlassCard, GlassSelect, LoadingSkeleton, PageHeader, Toast } from '../../components/shared';
import { features } from '../../config/features';
import { useAuth } from '../../hooks/useAuth';
import { aiService } from '../../services/aiService';
import type { AiFarmRef, AiModelStatus, AiTrustScore as AiTrustScoreData } from '../../types/models';

const RUN_ROLES = ['farm_operator', 'verifier', 'researcher'];

/**
 * "AI Trust Score" — one page reused by every role. All roles can view; only
 * operators/verifiers/researchers see Run/Upload controls (also enforced by the
 * backend). Farm list is scoped server-side by role via /api/ai/farms.
 */
export function AiTrustScorePage() {
  const { user } = useAuth();
  const canRun = useMemo(() => !!user && RUN_ROLES.includes(user.role), [user]);

  const [farms, setFarms] = useState<AiFarmRef[]>([]);
  const [farmsLoading, setFarmsLoading] = useState(true);
  const [selectedFarmId, setSelectedFarmId] = useState('');
  const [modelStatus, setModelStatus] = useState<AiModelStatus | null>(null);

  const [score, setScore] = useState<AiTrustScoreData | null>(null);
  const [scoreLoading, setScoreLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  // Dismiss toast after 3 s
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  // Farm selector + model status on mount
  useEffect(() => {
    if (!features.dualAi) return;
    setFarmsLoading(true);
    void aiService
      .getFarms()
      .then((rows) => {
        setFarms(rows);
        setSelectedFarmId((cur) => cur || rows[0]?.id || '');
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setFarmsLoading(false));
    void aiService.getModelStatus().then(setModelStatus).catch(() => setModelStatus(null));
  }, []);

  const loadScore = useCallback((farmId: string) => {
    if (!farmId) return;
    setScoreLoading(true);
    setError(null);
    void aiService
      .getTrustScore(farmId)
      .then(setScore)
      .catch((e) => {
        setScore(null);
        setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => setScoreLoading(false));
  }, []);

  // (Re)load the composite whenever the selected farm changes
  useEffect(() => {
    if (selectedFarmId) loadScore(selectedFarmId);
    else setScore(null);
  }, [selectedFarmId, loadScore]);

  const runDual = async () => {
    if (!selectedFarmId) return;
    setRunning(true);
    setError(null);
    try {
      setScore(await aiService.runDualVerify(selectedFarmId));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  const runSensor = async () => {
    if (!selectedFarmId) return;
    setRunning(true);
    setError(null);
    try {
      await aiService.runSensorVerify(selectedFarmId);
      loadScore(selectedFarmId);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  const uploadImage = async (file: File) => {
    if (!selectedFarmId) return;
    setRunning(true);
    setError(null);
    try {
      await aiService.analyzeImageUpload(selectedFarmId, file);
      loadScore(selectedFarmId);
      setToast('Image uploaded successfully!');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

  if (!features.dualAi) {
    return (
      <div className="page">
        <PageHeader eyebrow="AI" title="AI Trust Score" description="Dual-model verification." />
        <EmptyState title="Feature disabled" body="AI Trust Score is turned off for this environment." />
      </div>
    );
  }

  return (
    <div className="page">
      {toast && <Toast message={toast} />}
      <PageHeader
        eyebrow="Dual-model AI"
        title="AI Trust Score"
        description="Algae image segmentation + sensor biomass models, combined into one trust score."
        action={
          farms.length > 0 ? (
            <div style={{ minWidth: 240 }}>
              <GlassSelect
                label="Farm"
                value={selectedFarmId}
                onChange={(e) => setSelectedFarmId(e.target.value)}
              >
                {farms.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name} · {f.status.replaceAll('_', ' ')}
                  </option>
                ))}
              </GlassSelect>
            </div>
          ) : undefined
        }
      />

      {farmsLoading ? (
        <LoadingSkeleton lines={6} />
      ) : farms.length === 0 ? (
        <GlassCard className="section">
          <EmptyState
            title="No farms available"
            body={
              canRun
                ? 'Register or get assigned a farm to run AI analysis.'
                : 'No published projects to view yet. Once operators submit farms, their AI Trust Score appears here.'
            }
          />
        </GlassCard>
      ) : (
        <AiTrustScore
          score={score}
          loading={scoreLoading}
          canRun={canRun}
          modelStatus={modelStatus}
          running={running}
          error={error}
          onRunDual={runDual}
          onRunSensor={runSensor}
          onUploadImage={uploadImage}
        />
      )}
    </div>
  );
}
