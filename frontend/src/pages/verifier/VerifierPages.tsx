import {
  Check,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileText,
  XCircle,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  DataTable,
  EmptyState,
  GlassButton,
  GlassCard,
  GlassInput,
  GlassModal,
  LoadingSkeleton,
  PageHeader,
  StatCard,
  StatusBadge,
  Toast,
} from '../../components/shared';
import { useNotifications } from '../../hooks/useNotifications';
import { verifierService } from '../../services/verifierService';
import { aiService } from '../../services/aiService';
import { AiTrustScore } from '../../components/ai/AiTrustScore';
import { features } from '../../config/features';
import { shortDate, tonnes } from '../../utils/formatters';
import type { AiModelStatus, AiTrustScore as AiTrustScoreData, VerificationRequest } from '../../types/models';

// ── Chart stub data ─────────────────────────────────────────────────────────
const loadWorkload = [
  { week: 'W1', requests: 12 },
  { week: 'W2', requests: 18 },
  { week: 'W3', requests: 16 },
  { week: 'W4', requests: 22 },
  { week: 'W5', requests: 19 },
  { week: 'W6', requests: 25 },
];

// ── Shared hook: always fetches from the live API ────────────────────────────
const useRequests = (mode: 'pending' | 'all' | 'history' = 'pending') => {
  const [requests, setRequests] = useState<VerificationRequest[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    setLoading(true);
    let work: Promise<VerificationRequest[]>;
    if (mode === 'pending') {
      work = verifierService.getPendingProjects();
    } else if (mode === 'history') {
      work = verifierService.getHistory();
    } else {
      // 'all' — fetch all statuses from the backend
      work = verifierService.getRequestsByStatus('pending').then(async (pending) => {
        const [inReview, approved, rejected, correction] = await Promise.all([
          verifierService.getRequestsByStatus('in_review'),
          verifierService.getRequestsByStatus('approved'),
          verifierService.getRequestsByStatus('rejected'),
          verifierService.getRequestsByStatus('correction_required'),
        ]);
        return [...pending, ...inReview, ...approved, ...rejected, ...correction];
      });
    }
    void work.then(setRequests).finally(() => setLoading(false));
  }, [mode]);

  useEffect(() => { refresh(); }, [refresh]);
  return { requests, loading, refresh };
};

// ── Dashboard ────────────────────────────────────────────────────────────────
export function VerifierDashboardPage() {
  const { requests, loading } = useRequests('pending');
  const approved = useRequests('all').requests.filter((r) => r.status === 'approved').length;
  const rejected = useRequests('all').requests.filter((r) => r.status === 'rejected').length;

  return (
    <div className="page">
      <PageHeader
        eyebrow="Verifier workspace"
        title="Review with confidence."
        description="An evidence-led queue for every climate claim."
        action={
          <Link to="/verifier/requests">
            <GlassButton>Open review queue</GlassButton>
          </Link>
        }
      />
      {loading ? (
        <LoadingSkeleton lines={4} />
      ) : (
        <>
          <div className="stats-grid">
            <StatCard label="Pending requests" value={String(requests.length)} icon={<ClipboardCheck size={19} />} trend="4 due this week" />
            <StatCard label="Approved this month" value={String(approved)} icon={<CheckCircle2 size={19} />} trend="8.4% above July" />
            <StatCard label="Rejected this month" value={String(rejected)} icon={<XCircle size={19} />} trend="All decisions logged" />
            <StatCard label="Avg review time" value="3.2 days" icon={<Clock3 size={19} />} trend="0.6 days faster" />
          </div>
          <div className="content-grid" style={{ marginTop: 18 }}>
            <GlassCard className="section">
              <div className="section-title">
                <h2>Review workload</h2>
                <span className="tiny muted">Requests closed</span>
              </div>
              <div className="chart">
                <ResponsiveContainer>
                  <AreaChart data={loadWorkload}>
                    <defs>
                      <linearGradient id="verifierGradient" x1="0" x2="0" y1="0" y2="1">
                        <stop stopColor="var(--accent)" stopOpacity={0.45} />
                        <stop offset="1" stopColor="var(--accent)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,.07)" vertical={false} />
                    <XAxis dataKey="week" />
                    <YAxis />
                    <Tooltip />
                    <Area dataKey="requests" stroke="var(--accent)" strokeWidth={3} fill="url(#verifierGradient)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </GlassCard>
            <GlassCard className="section">
              <div className="section-title">
                <h2>Next in queue</h2>
              </div>
              <div className="list">
                {requests.slice(0, 4).map((request) => (
                  <Link
                    className="glass-inset list-item"
                    to={`/verifier/requests/${request.id}`}
                    key={request.id}
                  >
                    <span>
                      <b>{request.farmName}</b>
                      <small className="muted" style={{ display: 'block' }}>
                        {request.evidenceCount} evidence files
                      </small>
                    </span>
                    <StatusBadge status={request.status} />
                  </Link>
                ))}
              </div>
            </GlassCard>
          </div>
        </>
      )}
    </div>
  );
}

// ── Requests list ────────────────────────────────────────────────────────────
export function RequestsPage() {
  const { requests, loading } = useRequests('all');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

  const shown = requests.filter(
    (r) =>
      (filter === 'all' || r.status === filter) &&
      `${r.farmName} ${r.operatorName}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Verification queue"
        title="Project requests"
        description="Prioritize incoming evidence and keep every decision auditable."
      />
      <GlassCard className="section">
        <div className="toolbar">
          <input
            className="input"
            placeholder="Search farm or operator"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select className="select" value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All requests</option>
            {['pending', 'in_review', 'approved', 'rejected', 'correction_required'].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </div>
        {loading ? (
          <LoadingSkeleton />
        ) : (
          <DataTable headers={['Farm', 'Operator', 'Submitted', 'Evidence', 'Status', '']}>
            {shown.map((request) => (
              <tr key={request.id}>
                <td><b>{request.farmName}</b></td>
                <td>{request.operatorName}</td>
                <td>{shortDate(request.submittedAt)}</td>
                <td>{request.evidenceCount} files</td>
                <td><StatusBadge status={request.status} /></td>
                <td>
                  <Link className="table-link" to={`/verifier/requests/${request.id}`}>
                    Review
                  </Link>
                </td>
              </tr>
            ))}
          </DataTable>
        )}
      </GlassCard>
    </div>
  );
}

// ── Request detail (the page with the Approve/Reject button) ─────────────────
export function RequestDetailPage() {
  const { id = '' } = useParams();
  const navigate = useNavigate();
  const { refresh: refreshNotifications } = useNotifications();

  // Load request from the LIVE API (not the mock fixture store)
  const [request, setRequest] = useState<VerificationRequest | null>(null);
  const [reqLoading, setReqLoading] = useState(true);
  const [evidence, setEvidence] = useState<Awaited<ReturnType<typeof verifierService.getProjectEvidence>>>([]);
  const [estimate, setEstimate] = useState(0);
  const [estimateLoading, setEstimateLoading] = useState(true);

  const [action, setAction] = useState<'approve' | 'correction' | 'reject' | null>(null);
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  // AI Trust Score panel — dual-model explainability for this farm.
  const [aiScore, setAiScore] = useState<AiTrustScoreData | null>(null);
  const [aiLoading, setAiLoading] = useState(features.dualAi);
  const [aiRunning, setAiRunning] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [modelStatus, setModelStatus] = useState<AiModelStatus | null>(null);

  const loadAiScore = useCallback((farmId: string) => {
    if (!farmId) return;
    setAiLoading(true);
    setAiError(null);
    void aiService
      .getTrustScore(farmId)
      .then(setAiScore)
      .catch((e) => {
        setAiScore(null);
        setAiError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => setAiLoading(false));
  }, []);

  // Dismiss toast after 3 s
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3000);
    return () => clearTimeout(t);
  }, [toast]);

  useEffect(() => {
    if (!id) return;
    setReqLoading(true);
    setEstimateLoading(true);

    // Fetch the request from the API
    void verifierService.getRequestById(id)
      .then(setRequest)
      .catch(() => setRequest(null))
      .finally(() => setReqLoading(false));

    // Fetch evidence files
    void verifierService.getProjectEvidence(id).then(setEvidence);

    // Fetch AI credit estimate (also caches AI results server-side)
    void verifierService.calculateVerifiedCredits(id)
      .then(setEstimate)
      .finally(() => setEstimateLoading(false));
  }, [id]);

  // Model status once (drives the trained/demo indicator).
  useEffect(() => {
    if (!features.dualAi) return;
    void aiService.getModelStatus().then(setModelStatus).catch(() => setModelStatus(null));
  }, []);

  // Load the composite once the estimate resolves (estimate persists a dual-verify
  // server-side, so reading after it avoids a stale/pending score).
  useEffect(() => {
    if (!features.dualAi || estimateLoading || !request?.farmId) return;
    loadAiScore(request.farmId);
  }, [estimateLoading, request?.farmId, loadAiScore]);

  const runAiDual = async () => {
    if (!request?.farmId) return;
    setAiRunning(true);
    setAiError(null);
    try {
      setAiScore(await aiService.runDualVerify(request.farmId));
    } catch (e) {
      setAiError(e instanceof Error ? e.message : String(e));
    } finally {
      setAiRunning(false);
    }
  };

  const runAiSensor = async () => {
    if (!request?.farmId) return;
    setAiRunning(true);
    setAiError(null);
    try {
      await aiService.runSensorVerify(request.farmId);
      loadAiScore(request.farmId);
    } catch (e) {
      setAiError(e instanceof Error ? e.message : String(e));
    } finally {
      setAiRunning(false);
    }
  };

  const uploadAiImage = async (file: File) => {
    if (!request?.farmId) return;
    setAiRunning(true);
    setAiError(null);
    try {
      await aiService.analyzeImageUpload(request.farmId, file);
      loadAiScore(request.farmId);
      setToast('Image uploaded successfully!');
    } catch (e) {
      setAiError(e instanceof Error ? e.message : String(e));
    } finally {
      setAiRunning(false);
    }
  };

  const decide = async () => {
    if (!request || !action) return;

    // Guard: don't submit if estimate hasn't loaded yet
    if (action === 'approve' && estimateLoading) {
      setToast('Please wait for the credit estimate to load.');
      return;
    }

    setSubmitting(true);
    try {
      let updated: VerificationRequest;
      if (action === 'approve') {
        updated = await verifierService.approveProject(request.id, estimate);
      } else if (action === 'correction') {
        updated = await verifierService.requestCorrection(
          request.id,
          note || 'Please attach clarification for the submitted evidence.',
        );
      } else {
        updated = await verifierService.rejectProject(
          request.id,
          note || 'Evidence was not sufficient to verify this project.',
        );
      }

      // Update local state with the server response
      setRequest(updated);
      setAction(null);
      setNote('');

      // Show success toast
      const label = action === 'approve' ? 'approved' : action === 'correction' ? 'sent for correction' : 'rejected';
      setToast(`Project successfully ${label}!`);

      // Refresh the notification bell so the verifier sees their own action reflected
      refreshNotifications();

      // Navigate after a short delay so the toast is visible
      setTimeout(() => navigate('/verifier/requests'), 1200);
    } catch (e) {
      setToast(`Error: ${String(e)}`);
    } finally {
      setSubmitting(false);
    }
  };

  if (reqLoading) return <div className="page"><LoadingSkeleton lines={6} /></div>;
  if (!request) return (
    <div className="page">
      <EmptyState title="Request not found" body="This verification request does not exist or you do not have access to it." />
    </div>
  );

  // Farm metadata is embedded in the VerificationRequest fields returned by the API.
  // The farmName, operatorName, evidenceCount, estimatedCredits are all present.
  // For farming practices we fall back to the evidence list.
  return (
    <div className="page">
      {toast && <Toast message={toast} />}

      <PageHeader
        eyebrow="Evidence review"
        title={request.farmName}
        description={`Submitted by ${request.operatorName} on ${shortDate(request.submittedAt)}`}
      />

      <div className="content-grid">
        <div className="stack">
          <GlassCard className="section">
            <div className="section-title">
              <h2>Farm information</h2>
              <StatusBadge status={request.status} />
            </div>
            <div className="key-grid">
              <Metric label="Estimated (original)" value={tonnes(request.estimatedCredits)} />
              <Metric label="AI-calculated issue" value={estimateLoading ? 'Calculating…' : tonnes(estimate)} />
              <Metric label="Evidence files" value={`${request.evidenceCount} files`} />
              <Metric
                label="AI Trust Score"
                value={
                  aiScore?.dualAiScore != null
                    ? `${aiScore.dualAiScore.toFixed(1)} / 100`
                    : request.dualAiScore != null
                    ? `${request.dualAiScore.toFixed(1)} / 100`
                    : aiLoading
                    ? 'Calculating…'
                    : '—'
                }
              />
            </div>
          </GlassCard>

          <GlassCard className="section">
            <h2>Review notes</h2>
            {request.reviewNotes.length ? (
              <div className="list">
                {request.reviewNotes.map((item, index) => (
                  <div key={index} className="glass-inset section">
                    <b className="tiny">Verifier note</b>
                    <p className="muted">{item.note}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted">No reviewer notes yet. Add one with a correction or rejection decision.</p>
            )}
          </GlassCard>
        </div>

        <GlassCard className="section">
          <div className="section-title">
            <h2>Evidence gallery</h2>
            <span className="tiny muted">Click to inspect</span>
          </div>
          <div className="feature-grid">
            {evidence.map((doc) => (
              <div className="glass-inset feature" key={doc.id}>
                <FileText color="var(--accent)" />
                <h3>{doc.type.replace('_', ' ')}</h3>
                <p className="tiny muted">{doc.fileName}</p>
                <StatusBadge status={doc.verifiedStatus} />
              </div>
            ))}
            {evidence.length === 0 && (
              <p className="muted tiny">No evidence documents uploaded yet.</p>
            )}
          </div>
        </GlassCard>
      </div>

      {/* AI Trust Score — full dual-model explainability panel */}
      {features.dualAi && (
        <div style={{ marginTop: 18 }}>
          <AiTrustScore
            score={aiScore}
            loading={aiLoading}
            canRun
            modelStatus={modelStatus}
            running={aiRunning}
            error={aiError}
            onRunDual={() => void runAiDual()}
            onRunSensor={() => void runAiSensor()}
            onUploadImage={(f) => void uploadAiImage(f)}
          />
        </div>
      )}

      {/* Sticky action bar — only show for pending/in_review requests */}
      {['pending', 'in_review', 'correction_required'].includes(request.status) && (
        <GlassCard className="section" style={{ position: 'sticky', bottom: 14, marginTop: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span>
              <span className="eyebrow">AI-calculated issue</span>
              <b style={{ display: 'block', fontSize: '1.25rem' }}>
                {estimateLoading ? 'Calculating…' : tonnes(estimate)}
              </b>
            </span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <GlassButton onClick={() => setAction('approve')} disabled={estimateLoading}>
                <Check size={16} /> Approve
              </GlassButton>
              <GlassButton variant="secondary" onClick={() => setAction('correction')}>
                Request correction
              </GlassButton>
              <GlassButton variant="danger" onClick={() => setAction('reject')}>
                Reject
              </GlassButton>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Decision modal */}
      <GlassModal
        open={Boolean(action)}
        onClose={() => { setAction(null); setNote(''); }}
        title={
          action === 'approve'
            ? 'Approve this project'
            : action === 'correction'
            ? 'Request a correction'
            : 'Reject this project'
        }
      >
        <div className="form-grid">
          {action === 'approve' ? (
            <p className="muted">
              Approve <strong>{request.farmName}</strong> for{' '}
              <strong>{estimateLoading ? '…' : tonnes(estimate)}</strong>. This will issue a credit
              batch and create the marketplace project.
            </p>
          ) : (
            <GlassInput
              label="Decision note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Explain what needs to change"
            />
          )}
          <GlassButton onClick={() => void decide()} loading={submitting} disabled={submitting}>
            {action === 'approve'
              ? 'Approve & issue credits'
              : action === 'correction'
              ? 'Send correction request'
              : 'Confirm rejection'}
          </GlassButton>
        </div>
      </GlassModal>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="glass-inset key">
      <span className="tiny muted">{label}</span>
      <b>{value}</b>
    </div>
  );
}

// ── Evidence library ─────────────────────────────────────────────────────────
export function EvidencePage() {
  const [search, setSearch] = useState('');
  const [docs, setDocs] = useState<Awaited<ReturnType<typeof verifierService.getProjectEvidence>>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch all evidence from the backend evidence-library endpoint
    void fetch(
      `${import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'}/verifier/evidence`,
      { headers: { Authorization: `Bearer ${localStorage.getItem('terra-ledger-token') ?? ''}` } },
    )
      .then((r) => r.json() as Promise<typeof docs>)
      .then(setDocs)
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  }, []);

  const shown = docs.filter((doc) =>
    `${doc.fileName} ${doc.type}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Evidence library"
        title="Cross-project evidence"
        description="Spot-check submitted sources across all active reviews."
      />
      <GlassCard className="section">
        <div className="toolbar">
          <input
            className="input"
            placeholder="Search evidence"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        {loading ? <LoadingSkeleton /> : (
          <DataTable headers={['Document', 'Farm ID', 'Type', 'Uploaded', 'Status']}>
            {shown.map((doc) => (
              <tr key={doc.id}>
                <td>{doc.fileName}</td>
                <td>{doc.farmId}</td>
                <td>{doc.type.replace('_', ' ')}</td>
                <td>{shortDate(doc.uploadedAt)}</td>
                <td><StatusBadge status={doc.verifiedStatus} /></td>
              </tr>
            ))}
          </DataTable>
        )}
      </GlassCard>
    </div>
  );
}

// ── Verification board (kanban) ───────────────────────────────────────────────
export function VerificationBoardPage() {
  const { requests, loading } = useRequests('all');
  const groups: Array<[string, VerificationRequest['status'][], string]> = [
    ['Pending',   ['pending'],                           '#f59e0b'],
    ['In review', ['in_review', 'correction_required'],  '#3b82f6'],
    ['Decided',   ['approved', 'rejected'],               '#22c55e'],
  ];

  return (
    <div className="page">
      <PageHeader
        eyebrow="Pipeline view"
        title="Verification board"
        description="A visual view of every decision in progress."
      />
      <div className="kanban">
        {groups.map(([label, statuses, accentColor]) => {
          const cards = requests.filter((r) => statuses.includes(r.status));
          return (
            <GlassCard key={label} className="kanban-col" style={{ padding: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 16px 12px',
                borderBottom: '1px solid rgba(255,255,255,.07)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{
                    display: 'inline-block',
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    background: accentColor,
                    boxShadow: `0 0 8px ${accentColor}88`,
                  }} />
                  <h2 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 600 }}>{label}</h2>
                </div>
                <span style={{
                  background: `${accentColor}22`,
                  color: accentColor,
                  borderRadius: 20,
                  padding: '2px 10px',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  border: `1px solid ${accentColor}44`,
                }}>
                  {loading ? '…' : cards.length}
                </span>
              </div>
              
              <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 10, flex: 1, overflowY: 'auto' }}>
                {loading ? (
                  <LoadingSkeleton lines={2} />
                ) : cards.length === 0 ? (
                  <p className="muted tiny" style={{ textAlign: 'center', padding: '24px 0' }}>
                    No items
                  </p>
                ) : (
                  cards.map((request) => (
                    <KanbanCard key={request.id} request={request} />
                  ))
                )}
              </div>
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}

function KanbanCard({ request }: { request: VerificationRequest }) {
  const [hovered, setHovered] = useState(false);
  const borderColor =
    request.status === 'approved'            ? '#22c55e' :
    request.status === 'rejected'            ? '#ef4444' :
    request.status === 'in_review'           ? '#3b82f6' :
    request.status === 'correction_required' ? '#f59e0b' :
                                               '#64748b';

  return (
    <Link
      to={`/verifier/requests/${request.id}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        padding: '13px 14px',
        borderRadius: 10,
        background: hovered ? 'rgba(255,255,255,.09)' : 'rgba(255,255,255,.05)',
        border: '1px solid rgba(255,255,255,.08)',
        borderLeft: `3px solid ${borderColor}`,
        textDecoration: 'none',
        color: 'inherit',
        transform: hovered ? 'translateY(-1px)' : 'none',
        transition: 'background .15s, transform .12s',
        boxShadow: hovered ? `0 4px 16px rgba(0,0,0,.25)` : 'none',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <b style={{
        fontSize: '0.88rem',
        lineHeight: 1.35,
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
      }}>
        {request.farmName}
      </b>
      <span style={{
        fontSize: '0.74rem',
        color: '#8fa3b8',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        minWidth: 0,
      }}>
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 18,
          height: 18,
          borderRadius: '50%',
          background: 'rgba(255,255,255,.13)',
          fontSize: '0.6rem',
          fontWeight: 700,
          flexShrink: 0,
        }}>
          {request.operatorName.charAt(0).toUpperCase()}
        </span>
        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }}>
          {request.operatorName}
        </span>
        <span style={{ flexShrink: 0, color: '#5a7a93' }}>· {request.evidenceCount} files</span>
      </span>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 2 }}>
        <StatusBadge status={request.status} />
        <span style={{ fontSize: '0.68rem', color: '#5a7a93' }}>
          {shortDate(request.submittedAt)}
        </span>
      </div>
    </Link>
  );
}

// ── Approved / Rejected pages ─────────────────────────────────────────────────
function DecisionList({ status }: { status: 'approved' | 'rejected' }) {
  const [requests, setRequests] = useState<VerificationRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void verifierService.getRequestsByStatus(status).then(setRequests).finally(() => setLoading(false));
  }, [status]);

  return (
    <div className="page">
      <PageHeader
        eyebrow="Audit decisions"
        title={status === 'approved' ? 'Approved projects' : 'Rejected projects'}
        description={
          status === 'approved'
            ? 'Verified farms with credit issuance values.'
            : 'Requests that need a new evidence baseline before resubmission.'
        }
      />
      <GlassCard className="section">
        {loading ? <LoadingSkeleton /> : requests.length ? (
          <DataTable
            headers={[
              'Farm',
              'Operator',
              'Decision date',
              status === 'approved' ? 'Credits issued' : 'Decision note',
              '',
            ]}
          >
            {requests.map((r) => (
              <tr key={r.id}>
                <td>{r.farmName}</td>
                <td>{r.operatorName}</td>
                <td>{r.decisionAt ? shortDate(r.decisionAt) : '—'}</td>
                <td>
                  {status === 'approved'
                    ? tonnes(r.verifiedCredits ?? r.estimatedCredits)
                    : r.rejectionReason}
                </td>
                <td>
                  <Link className="table-link" to={`/verifier/requests/${r.id}`}>
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </DataTable>
        ) : (
          <EmptyState
            title={`No ${status} projects`}
            body="Decisions will appear here as the review queue progresses."
          />
        )}
      </GlassCard>
    </div>
  );
}

export const ApprovedPage = () => <DecisionList status="approved" />;
export const RejectedPage = () => <DecisionList status="rejected" />;

// ── History ───────────────────────────────────────────────────────────────────
export function HistoryPage() {
  const { requests, loading } = useRequests('history');
  const sorted = useMemo(
    () =>
      [...requests].sort(
        (a, b) =>
          new Date(b.decisionAt ?? b.submittedAt).getTime() -
          new Date(a.decisionAt ?? a.submittedAt).getTime(),
      ),
    [requests],
  );

  return (
    <div className="page">
      <PageHeader
        eyebrow="Audit trail"
        title="Decision history"
        description="A chronological record that can be exported for internal assurance."
        action={
          <GlassButton variant="secondary" onClick={() => window.print()}>
            Export history
          </GlassButton>
        }
      />
      <GlassCard className="section">
        {loading ? <LoadingSkeleton /> : (
          <DataTable headers={['Farm', 'Activity', 'Date', 'Outcome']}>
            {sorted.map((r) => (
              <tr key={r.id}>
                <td>{r.farmName}</td>
                <td>{r.decisionAt ? 'Decision recorded' : 'Submitted for review'}</td>
                <td>{shortDate(r.decisionAt ?? r.submittedAt)}</td>
                <td><StatusBadge status={r.status} /></td>
              </tr>
            ))}
          </DataTable>
        )}
      </GlassCard>
    </div>
  );
}
