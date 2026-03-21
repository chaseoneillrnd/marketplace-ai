import { useT } from '../context/ThemeContext';

interface Props {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = 'Failed to load skills. Try again.', onRetry }: Props) {
  const C = useT();
  return (
    <div data-testid="error-state" style={{ textAlign: 'center', padding: '60px 0', color: C.muted }}>
      <div style={{ fontSize: '32px', marginBottom: '12px' }}>&#9888;</div>
      <div style={{ fontSize: '16px', fontWeight: 600, color: C.text, marginBottom: '8px' }}>{message}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            padding: '8px 20px',
            borderRadius: '8px',
            border: `1px solid ${C.accent}`,
            background: C.accentDim,
            color: C.accent,
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 600,
            marginTop: '8px',
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
