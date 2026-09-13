import {
  Activity,
  AlertTriangle,
  Camera,
  CheckCircle2,
  Gauge,
  Leaf,
  RefreshCw,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import { useRef } from 'react';
import type { ReactNode } from 'react';
import type { AiModelStatus, AiRecommendation, AiTrustScore as AiTrustScoreData } from '../../types/models';
import { EmptyState, GlassButton, GlassCard, LoadingSkeleton, ProgressRing, StatusBadge } from '../shared';

/**
 * "AI Trust Score" — shared, presentational panel over the two trained models
 * (image segmentation + XGBoost biomass). Controlled: the parent owns fetching
 * and passes `score` + callbacks. Run/Upload controls render only when
 * `canRun` (farm_operator / verifier / researcher); investors see it read-only.
 */

interface AiTrustScoreProps {
  score: AiTrustScoreData | null;
  loading?: boolean;
  canRun?: boolean;
  modelStatus?: AiModelStatus | null;
  running?: boolean;
  error?: string | null;
  onRunDual?: () => void;
  onRunSensor?: () => void;
  onUploadImage?: (file: File) => void;
}

const RECO: Record<AiRecommendation, { label: string; tone: string }> = {
  approve_ready: { label: 'Approve ready', tone: 'approved' },
  needs_review: { label: 'Needs review', tone: 'in_review' },
  reject_recommended: { label: 'Reject recommended', tone: 'rejected' },
};

const dash = '—';
const pct = (n?: number | null): string => (n == null ? dash : `${n.toFixed(1)}%`);
const num = (n?: number | null, digits = 2, suffix = ''): string =>
  n == null ? dash : `${n.toFixed(digits)}${suffix}`;

function Metric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="glass-inset key">
      <span className="tiny muted">{label}</span>
      <b>{value}</b>
    </div>
  );
}

function FlagList({ items, tone }: { items: string[]; tone: 'warn' | 'muted' }) {
  if (!items.length) return <p className="tiny muted">None detected.</p>;
  return (
    <div className="list" style={{ gap: 6 }}>
      {items.map((f) => (
        <div key={f} className="glass-inset" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px' }}>
          <AlertTriangle size={14} color={tone === 'warn' ? '#fca5a5' : 'var(--accent)'} />
          <span className="tiny">{f.replaceAll('_', ' ')}</span>
        </div>
      ))}
    </div>
  );
}

function ModelChip({ label, isStub, ready }: { label: string; isStub?: boolean; ready?: boolean }) {
  const tone = !ready ? 'rejected' : isStub ? 'in_review' : 'approved';
  const text = !ready ? `${label}: offline` : isStub ? `${label}: demo` : `${label}: trained`;
  return <span className={`status ${tone}`}>{text}</span>;
}

export function AiTrustScore({
  score,
  loading = false,
  canRun = false,
  modelStatus = null,
  running = false,
  error = null,
  onRunDual,
  onRunSensor,
  onUploadImage,
}: AiTrustScoreProps) {
  const fileRef = useRef<HTMLInputElement>(null);

  const img = score?.imageAnalysis ?? null;
  const sen = score?.sensorVerification ?? null;
  const reco = score?.recommendation ? RECO[score.recommendation] : null;
  const ringValue = score?.dualAiScore != null ? Math.round(score.dualAiScore) : 0;
  const biomassGl = (sen?.rawOutput?.['predicted_biomass_g_l'] as number | undefined) ?? null;
  const greenExg = ((img?.rawOutput?.['greenness'] as { exg?: number } | undefined)?.exg) ?? null;

  const controls = canRun ? (
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      <GlassButton onClick={onRunDual} loading={running} disabled={running}>
        <RefreshCw size={15} /> Run full analysis
      </GlassButton>
      <GlassButton variant="secondary" onClick={onRunSensor} disabled={running}>
        <Activity size={15} /> Sensor only
      </GlassButton>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        disabled={running}
        onClick={() => fileRef.current?.click()}
      >
        <UploadCloud size={15} /> Upload photo
      </button>
      <input
        ref={fileRef}
        hidden
        type="file"
        accept="image/*"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) onUploadImage?.(file);
          e.target.value = '';
        }}
      />
    </div>
  ) : (
    <span className="tiny muted">View-only — analysis is run by operators, verifiers, and researchers.</span>
  );

  return (
    <div className="stack">
      <GlassCard className="section">
        <div className="section-title">
          <h2><Sparkles size={18} style={{ verticalAlign: '-3px', marginRight: 6 }} />AI Trust Score</h2>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {modelStatus && <ModelChip label="Image" isStub={modelStatus.image.is_stub} ready={modelStatus.image.ready} />}
            {modelStatus && <ModelChip label="Sensor" isStub={modelStatus.sensor.is_stub} ready={modelStatus.sensor.ready} />}
          </div>
        </div>

        {error && <p className="tiny" style={{ color: '#fca5a5' }}>{error}</p>}

        {loading ? (
          <LoadingSkeleton lines={4} />
        ) : score && score.status === 'ready' ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <ProgressRing value={ringValue} label="Trust" />
            <div className="stack" style={{ gap: 8, flex: 1, minWidth: 220 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                {reco ? <span className={`status ${reco.tone}`}>{reco.label}</span> : <StatusBadge status="pending" />}
                {sen?.verdict && <span className="tiny muted">Sensor verdict: <b>{sen.verdict}</b></span>}
              </div>
              {controls}
            </div>
          </div>
        ) : (
          <EmptyState
            icon={<Sparkles size={34} />}
            title="No AI analysis yet"
            body={
              canRun
                ? 'Run the models to generate an AI Trust Score for this farm.'
                : 'This farm has not been analyzed yet. Check back once an operator or verifier runs the models.'
            }
            action={canRun ? controls : undefined}
          />
        )}
      </GlassCard>

      {score && score.status === 'ready' && (
        <div className="content-grid">
          <GlassCard className="section">
            <div className="section-title">
              <h2><Camera size={17} style={{ verticalAlign: '-3px', marginRight: 6 }} />Image model</h2>
              {img && <span className={`status ${img.isStub ? 'in_review' : 'approved'}`}>{img.isStub ? 'demo' : 'trained'}</span>}
            </div>
            {img ? (
              <>
                <div className="key-grid">
                  <Metric label="Algae coverage" value={pct(img.algaeCoveragePct)} />
                  <Metric label="Health score" value={num(img.healthScore, 1, ' / 100')} />
                  <Metric label="Bloom detected" value={img.bloomDetected ? 'Yes' : 'No'} />
                  <Metric label="Greenness (ExG)" value={greenExg == null ? dash : greenExg.toFixed(3)} />
                  <Metric label="Species" value={img.predictedSpecies || dash} />
                  <Metric label="Seg. confidence" value={num(img.speciesConfidence, 3)} />
                </div>
                <div style={{ marginTop: 10 }}>
                  <span className="eyebrow"><Leaf size={12} /> Image flags</span>
                  <FlagList items={img.anomalyFlags} tone="warn" />
                </div>
              </>
            ) : (
              <p className="muted tiny">No image analysis stored for this farm yet.</p>
            )}
          </GlassCard>

          <GlassCard className="section">
            <div className="section-title">
              <h2><Gauge size={17} style={{ verticalAlign: '-3px', marginRight: 6 }} />Sensor model</h2>
              {sen && <span className={`status ${sen.isStub ? 'in_review' : 'approved'}`}>{sen.isStub ? 'demo' : 'trained'}</span>}
            </div>
            {sen ? (
              <>
                <div className="key-grid">
                  <Metric label="Predicted biomass" value={biomassGl == null ? dash : `${biomassGl.toFixed(2)} g/L`} />
                  <Metric label="Data quality" value={num(sen.dataQualityScore, 1, ' / 100')} />
                  <Metric label="Sequestration" value={num(sen.sequestrationKgCo2e, 1, ' kg CO₂e')} />
                  <Metric label="Confidence" value={num(sen.sequestrationConfidence, 2)} />
                  <Metric label="Consistency w/ image" value={num(sen.consistencyWithImage, 0, ' / 100')} />
                  <Metric label="Verdict" value={<StatusBadge status={sen.verdict} />} />
                </div>
                <div style={{ marginTop: 10 }}>
                  <span className="eyebrow"><CheckCircle2 size={12} /> Sensor anomalies</span>
                  <FlagList items={sen.anomalyDetails} tone="warn" />
                </div>
              </>
            ) : (
              <p className="muted tiny">No sensor verification stored for this farm yet.</p>
            )}
          </GlassCard>
        </div>
      )}

      {score?.notes && score.notes.length > 0 && (
        <GlassCard className="section">
          <h2>Notes</h2>
          <div className="list" style={{ gap: 6 }}>
            {score.notes.map((n, i) => (
              <div key={i} className="glass-inset" style={{ padding: '8px 10px' }}>
                <span className="tiny muted">{n}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}
    </div>
  );
}
