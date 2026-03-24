import { useT } from '../../context/ThemeContext';
import { ModalShell } from './ModalShell';

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
  const accentColor = destructive ? C.red : C.accent;

  return (
    <ModalShell
      open={true}
      onClose={onCancel}
      title={title}
      width="420px"
      data-testid="admin-confirm-dialog"
      footer={
        <>
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
        </>
      }
    >
      <p
        style={{
          fontSize: '14px',
          color: C.muted,
          margin: '0 0 0 0',
          lineHeight: '1.5',
        }}
      >
        {message}
      </p>
    </ModalShell>
  );
}
