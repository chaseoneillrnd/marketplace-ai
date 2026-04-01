import { useEffect, useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { api } from '../../lib/api';

interface GateStatus {
  label: string;
  status: 'passed' | 'in_progress' | 'pending' | 'failed';
}

interface SubmissionResponse {
  display_id: string;
  status: string;
  name?: string;
}

function deriveGates(submissionStatus: string): GateStatus[] {
  const gates: GateStatus[] = [
    { label: 'Gate 1 — Validation', status: 'pending' },
    { label: 'Gate 2 — LLM Scan', status: 'pending' },
    { label: 'Gate 3 — Human Review', status: 'pending' },
  ];

  switch (submissionStatus) {
    case 'pending':
      gates[0].status = 'in_progress';
      break;
    case 'gate1_passed':
      gates[0].status = 'passed';
      gates[1].status = 'in_progress';
      break;
    case 'gate1_failed':
      gates[0].status = 'failed';
      break;
    case 'gate2_passed':
      gates[0].status = 'passed';
      gates[1].status = 'passed';
      gates[2].status = 'in_progress';
      break;
    case 'gate2_failed':
      gates[0].status = 'passed';
      gates[1].status = 'failed';
      break;
    case 'approved':
    case 'published':
      gates[0].status = 'passed';
      gates[1].status = 'passed';
      gates[2].status = 'passed';
      break;
    case 'rejected':
      gates[0].status = 'passed';
      gates[1].status = 'passed';
      gates[2].status = 'failed';
      break;
    case 'changes_requested':
      gates[0].status = 'passed';
      gates[1].status = 'passed';
      gates[2].status = 'failed';
      break;
    default:
      break;
  }

  return gates;
}

function statusIcon(status: GateStatus['status']): string {
  switch (status) {
    case 'passed':
      return '\u2705';
    case 'in_progress':
      return '\u{1F7E1}';
    case 'failed':
      return '\u274C';
    case 'pending':
    default:
      return '\u26AA';
  }
}

interface Props {
  displayId: string;
}

export function SubmissionStatusTracker({ displayId }: Props) {
  const C = useT();
  const [status, setStatus] = useState<string>('pending');
  const [name, setName] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const result = await api.get<SubmissionResponse>(`/api/v1/submissions/${displayId}`);
        if (!cancelled) {
          setStatus(result.status);
          setName(result.name ?? '');
        }
      } catch {
        if (!cancelled) setError('Failed to load submission status');
      }
    };

    poll();
    const interval = setInterval(poll, 5000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [displayId]);

  const gates = deriveGates(status);

  return (
    <div
      data-testid="submission-status-tracker"
      style={{ maxWidth: '600px', margin: '0 auto', padding: '48px 24px' }}
    >
      <h2 style={{ fontSize: '20px', fontWeight: 700, color: C.text, marginBottom: '4px' }}>
        Submission Submitted
      </h2>
      <p style={{ fontSize: '13px', color: C.muted, marginBottom: '24px' }}>
        {name && <span style={{ fontWeight: 600 }}>{name} &mdash; </span>}
        Tracking ID: <code style={{ fontFamily: "'JetBrains Mono',monospace" }}>{displayId}</code>
      </p>

      {error && (
        <div role="alert" style={{ color: C.red ?? '#ff3b30', marginBottom: '16px', fontSize: '13px' }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {gates.map((gate) => (
          <div
            key={gate.label}
            data-testid={`gate-${gate.label}`}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '14px 16px',
              borderRadius: '10px',
              background: C.surface,
              border: `1px solid ${C.border}`,
            }}
          >
            <span style={{ fontSize: '18px' }}>{statusIcon(gate.status)}</span>
            <span style={{ fontSize: '14px', fontWeight: 500, color: C.text, flex: 1 }}>
              {gate.label}
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 600,
                textTransform: 'uppercase' as const,
                color:
                  gate.status === 'passed'
                    ? C.green ?? '#30d158'
                    : gate.status === 'failed'
                      ? C.red ?? '#ff3b30'
                      : gate.status === 'in_progress'
                        ? C.amber ?? '#ffd60a'
                        : C.dim,
                fontFamily: "'JetBrains Mono',monospace",
              }}
            >
              {gate.status.replace('_', ' ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
