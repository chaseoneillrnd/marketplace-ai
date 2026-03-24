import { useRef } from 'react';
import { useT } from '../../context/ThemeContext';
import { useFocusTrap } from '../../hooks/useFocusTrap';

interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  destructive?: boolean;
}

export function AdminConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirm',
  onConfirm,
  onCancel,
  destructive = false,
}: Props) {
  const C = useT();
  const dialogRef = useRef<HTMLDivElement>(null);
  useFocusTrap(dialogRef, { onEscape: onCancel });

  const accentColor = destructive ? C.red : C.accent;
  const accentDimColor = destructive ? C.redDim : C.accentDim;

  return (
    <div
      data-testid="admin-confirm-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,8,16,0.85)',
        backdropFilter: 'blur(10px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onCancel}
    >
      <div
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          width: '420px',
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: C.cardShadow,
        }}
      >
        <div
          style={{
            height: '3px',
            background: destructive
              ? `linear-gradient(90deg,${C.red},${C.amber})`
              : `linear-gradient(90deg,${C.accent},${C.purple},${C.green})`,
          }}
        />
        <div style={{ padding: '28px' }}>
          <h2
            id="confirm-dialog-title"
            style={{
              fontSize: '17px',
              fontWeight: 700,
              color: C.text,
              margin: '0 0 12px 0',
            }}
          >
            {title}
          </h2>
          <p
            style={{
              fontSize: '14px',
              color: C.muted,
              margin: '0 0 24px 0',
              lineHeight: '1.5',
            }}
          >
            {message}
          </p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
            <button
              onClick={onCancel}
              autoFocus={destructive}
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
              onClick={onConfirm}
              autoFocus={!destructive}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                background: accentColor,
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {confirmLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
