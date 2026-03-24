import { useRef } from 'react';
import { useT } from '../../context/ThemeContext';
import { useFocusTrap } from '../../hooks/useFocusTrap';

interface ModalShellProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  width?: string;
  'data-testid'?: string;
}

export function ModalShell({
  open,
  onClose,
  title,
  children,
  footer,
  width = '480px',
  'data-testid': testId,
}: ModalShellProps) {
  const C = useT();
  const dialogRef = useRef<HTMLDivElement>(null);
  useFocusTrap(dialogRef, { onEscape: onClose, enabled: open });

  if (!open) return null;

  return (
    <div
      data-testid={testId ?? 'modal-shell-backdrop'}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-shell-title"
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
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        style={{
          background: C.surface,
          border: `1px solid ${C.borderHi}`,
          borderRadius: '18px',
          width,
          maxHeight: '90vh',
          overflow: 'auto',
          boxShadow: C.cardShadow,
        }}
      >
        <div
          style={{
            height: '3px',
            background: `linear-gradient(90deg,${C.accent},${C.purple},${C.green})`,
          }}
        />
        <div style={{ padding: '28px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '20px',
            }}
          >
            <h2
              id="modal-shell-title"
              style={{
                fontSize: '17px',
                fontWeight: 700,
                color: C.text,
                margin: 0,
              }}
            >
              {title}
            </h2>
            <button
              aria-label="Close"
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: C.muted,
                fontSize: '20px',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '6px',
                lineHeight: 1,
              }}
            >
              ×
            </button>
          </div>
          <div>{children}</div>
          {footer && (
            <div
              style={{
                display: 'flex',
                gap: '10px',
                justifyContent: 'flex-end',
                marginTop: '24px',
              }}
            >
              {footer}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
