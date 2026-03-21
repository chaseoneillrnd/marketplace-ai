import { useT } from '../context/ThemeContext';

interface Props {
  message?: string;
  onClear?: () => void;
}

export function EmptyState({ message = 'No skills found', onClear }: Props) {
  const C = useT();
  return (
    <div data-testid="empty-state" style={{ textAlign: 'center', padding: '60px 0', color: C.muted }}>
      <div style={{ fontSize: '32px', marginBottom: '12px' }}>&#128269;</div>
      <div style={{ fontSize: '16px', fontWeight: 600, color: C.text, marginBottom: '8px' }}>{message}</div>
      {onClear && (
        <button
          onClick={onClear}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: `1px solid ${C.border}`,
            background: C.surface,
            color: C.muted,
            cursor: 'pointer',
            fontSize: '13px',
            marginTop: '8px',
          }}
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
