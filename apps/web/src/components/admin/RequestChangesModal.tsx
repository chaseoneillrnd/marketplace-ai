import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { ModalShell } from './ModalShell';

interface RequestChangesModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { flags: string[]; notes: string }) => void;
  submissionName: string;
}

const FLAG_OPTIONS: { key: string; label: string }[] = [
  { key: 'missing_front_matter', label: 'Missing or incomplete front matter' },
  { key: 'security_concern', label: 'Security concern identified' },
  { key: 'scope_too_broad', label: 'Scope too broad — consider splitting' },
  { key: 'quality_insufficient', label: 'Quality does not meet standards' },
  { key: 'division_mismatch', label: 'Division selection needs adjustment' },
  { key: 'needs_changelog', label: 'Changelog or description update needed' },
];

const MIN_NOTES_LENGTH = 20;

export function RequestChangesModal({
  open,
  onClose,
  onSubmit,
  submissionName,
}: RequestChangesModalProps) {
  const C = useT();
  const [flags, setFlags] = useState<string[]>([]);
  const [notes, setNotes] = useState('');

  const canSubmit = flags.length >= 1 && notes.trim().length >= MIN_NOTES_LENGTH;

  const handleToggleFlag = (key: string) => {
    setFlags((prev) =>
      prev.includes(key) ? prev.filter((f) => f !== key) : [...prev, key]
    );
  };

  const handleSubmit = () => {
    if (!canSubmit) return;
    onSubmit({ flags, notes: notes.trim() });
  };

  const handleClose = () => {
    setFlags([]);
    setNotes('');
    onClose();
  };

  return (
    <ModalShell
      open={open}
      onClose={handleClose}
      title={`Request Changes — ${submissionName}`}
      width="520px"
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
              background: canSubmit ? C.amber : C.dim,
              color: canSubmit ? '#fff' : C.muted,
              fontSize: '13px',
              fontWeight: 600,
              cursor: canSubmit ? 'pointer' : 'not-allowed',
              opacity: canSubmit ? 1 : 0.6,
            }}
          >
            Request Changes
          </button>
        </>
      }
    >
      <fieldset
        style={{
          border: 'none',
          margin: 0,
          padding: 0,
        }}
      >
        <legend
          style={{
            fontSize: '13px',
            fontWeight: 600,
            color: C.muted,
            marginBottom: '12px',
          }}
        >
          Select applicable flags
        </legend>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {FLAG_OPTIONS.map(({ key, label }) => (
            <label
              key={key}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                fontSize: '13px',
                color: C.text,
                cursor: 'pointer',
                padding: '6px 10px',
                borderRadius: '8px',
                background: flags.includes(key) ? C.amberDim : 'transparent',
                border: `1px solid ${flags.includes(key) ? C.amber : C.border}`,
                transition: 'all 0.15s',
              }}
            >
              <input
                type="checkbox"
                checked={flags.includes(key)}
                onChange={() => handleToggleFlag(key)}
                style={{ accentColor: C.amber }}
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>
      <div style={{ marginTop: '20px' }}>
        <label
          htmlFor="request-changes-notes"
          style={{
            display: 'block',
            fontSize: '13px',
            fontWeight: 600,
            color: C.muted,
            marginBottom: '8px',
          }}
        >
          Notes (min {MIN_NOTES_LENGTH} characters) *
        </label>
        <textarea
          id="request-changes-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Describe what changes are needed..."
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
        <div
          style={{
            fontSize: '11px',
            color: notes.trim().length >= MIN_NOTES_LENGTH ? C.green : C.muted,
            marginTop: '4px',
            textAlign: 'right',
          }}
        >
          {notes.trim().length}/{MIN_NOTES_LENGTH}
        </div>
      </div>
    </ModalShell>
  );
}
