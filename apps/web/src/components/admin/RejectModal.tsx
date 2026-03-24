import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { ModalShell } from './ModalShell';

interface RejectModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { reason: string; details: string }) => void;
  submissionName: string;
}

const REASON_OPTIONS: { value: string; label: string }[] = [
  { value: 'malicious_content', label: 'Malicious content detected' },
  { value: 'policy_violation', label: 'Policy violation' },
  { value: 'duplicate', label: 'Duplicate of existing skill' },
  { value: 'low_quality', label: 'Quality below minimum standards' },
  { value: 'out_of_scope', label: 'Out of scope for the platform' },
  { value: 'other', label: 'Other (specify below)' },
];

export function RejectModal({
  open,
  onClose,
  onSubmit,
  submissionName,
}: RejectModalProps) {
  const C = useT();
  const [reason, setReason] = useState('');
  const [details, setDetails] = useState('');

  const detailsRequired = reason === 'other';
  const canSubmit = reason !== '' && (!detailsRequired || details.trim().length > 0);

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit({ reason, details: details.trim() });
  };

  const handleClose = () => {
    setReason('');
    setDetails('');
    onClose();
  };

  return (
    <ModalShell
      open={open}
      onClose={handleClose}
      title={`Reject — ${submissionName}`}
      width="480px"
      footer={
        <>
          <button
            onClick={handleClose}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              border: `1px solid ${C.border}`,
              background: C.bg,
              color: C.text,
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            style={{
              padding: '8px 18px',
              borderRadius: '8px',
              border: 'none',
              background: canSubmit ? C.red : C.dim,
              color: canSubmit ? '#fff' : C.muted,
              fontSize: '13px',
              fontWeight: 600,
              cursor: canSubmit ? 'pointer' : 'not-allowed',
              opacity: canSubmit ? 1 : 0.6,
            }}
          >
            Reject Submission
          </button>
        </>
      }
    >
      <div>
        <label
          htmlFor="reject-reason"
          style={{
            display: 'block',
            fontSize: '13px',
            fontWeight: 600,
            color: C.muted,
            marginBottom: '8px',
          }}
        >
          Rejection reason *
        </label>
        <select
          id="reject-reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: '8px',
            border: `1px solid ${C.border}`,
            background: C.inputBg,
            color: C.text,
            fontSize: '13px',
            fontFamily: 'inherit',
            boxSizing: 'border-box',
            cursor: 'pointer',
          }}
        >
          <option value="">Select a reason...</option>
          {REASON_OPTIONS.map(({ value, label }) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      <div style={{ marginTop: '16px' }}>
        <label
          htmlFor="reject-details"
          style={{
            display: 'block',
            fontSize: '13px',
            fontWeight: 600,
            color: C.muted,
            marginBottom: '8px',
          }}
        >
          Details{detailsRequired ? ' (required) *' : ' (optional)'}
        </label>
        <textarea
          id="reject-details"
          value={details}
          onChange={(e) => setDetails(e.target.value)}
          placeholder={
            detailsRequired
              ? 'Please specify the reason for rejection...'
              : 'Additional details (optional)...'
          }
          rows={4}
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: '8px',
            border: `1px solid ${C.border}`,
            background: C.inputBg,
            color: C.text,
            fontSize: '13px',
            fontFamily: 'inherit',
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
        />
      </div>
    </ModalShell>
  );
}
