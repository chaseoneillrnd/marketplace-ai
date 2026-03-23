import { useT } from '../../context/ThemeContext';

export interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}

export function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  const C = useT();

  if (!active || !payload) return null;

  return (
    <div
      data-testid="custom-tooltip"
      style={{
        background: C.surface,
        border: `1px solid ${C.borderHi}`,
        borderRadius: '8px',
        padding: '8px 12px',
        boxShadow: C.cardShadow,
      }}
    >
      {label && (
        <div style={{ fontFamily: 'Outfit, sans-serif', fontSize: '11px', color: C.muted, marginBottom: '4px' }}>
          {label}
        </div>
      )}
      {payload.map((item) => (
        <div key={item.name} style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', marginTop: '2px' }}>
          <span style={{ fontFamily: 'Outfit, sans-serif', fontSize: '11px', color: C.muted }}>{item.name}</span>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '13px', fontWeight: 600, color: item.color }}>
            {item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
