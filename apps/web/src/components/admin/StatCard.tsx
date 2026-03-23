import { useT } from '../../context/ThemeContext';
import { SparkLine } from '../charts/SparkLine';

export interface StatCardProps {
  label: string;
  value: number | string;
  delta?: number;
  sparkData?: { value: number }[];
  color?: string;
  onClick?: () => void;
}

export function StatCard({ label, value, delta, sparkData, color, onClick }: StatCardProps) {
  const C = useT();
  const accentColor = color ?? C.accent;

  return (
    <div
      data-testid="stat-card"
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      style={{
        position: 'relative',
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '12px',
        padding: '16px',
        cursor: onClick ? 'pointer' : undefined,
        overflow: 'hidden',
      }}
    >
      {/* Accent gradient bar at top */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: `linear-gradient(90deg, ${accentColor}, ${accentColor}80)`,
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontFamily: 'Outfit, sans-serif', fontSize: '28px', fontWeight: 800, color: C.text }}>
            {value}
          </div>
          <div style={{ fontFamily: 'Outfit, sans-serif', fontSize: '11px', fontWeight: 500, color: C.muted, marginTop: '2px' }}>
            {label}
          </div>
          {delta !== undefined && (
            <span
              data-testid="stat-delta"
              style={{
                display: 'inline-block',
                marginTop: '6px',
                fontFamily: 'Outfit, sans-serif',
                fontSize: '11px',
                fontWeight: 600,
                padding: '1px 8px',
                borderRadius: '99px',
                background: delta >= 0 ? `${C.green}18` : `${C.red}18`,
                color: delta >= 0 ? C.green : C.red,
              }}
            >
              {delta >= 0 ? '+' : ''}{delta}%
            </span>
          )}
        </div>
        {sparkData && sparkData.length > 0 && (
          <div style={{ alignSelf: 'flex-end' }}>
            <SparkLine data={sparkData} color={accentColor} width={64} height={32} />
          </div>
        )}
      </div>
    </div>
  );
}
