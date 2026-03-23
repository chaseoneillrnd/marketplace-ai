import { useT } from '../../context/ThemeContext';
import { AreaChartBase } from './AreaChartBase';

export interface DivisionMiniChartProps {
  division: string;
  color: string;
  data: { date: string; value: number }[];
  total?: number;
}

export function DivisionMiniChart({ division, color, data, total }: DivisionMiniChartProps) {
  const C = useT();

  return (
    <div
      data-testid="division-mini-chart"
      style={{
        width: '100%',
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: '8px',
        padding: '8px 10px 4px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
        <span style={{ fontFamily: 'Outfit, sans-serif', fontSize: '12px', fontWeight: 600, color: C.text }}>
          {division}
        </span>
        {total !== undefined && (
          <span
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: '11px',
              fontWeight: 600,
              color,
              background: `${color}18`,
              padding: '1px 6px',
              borderRadius: '99px',
            }}
          >
            {total}
          </span>
        )}
      </div>
      <AreaChartBase
        data={data}
        series={[{ key: 'value', color, name: division }]}
        height={80}
        xAxisKey="date"
      />
    </div>
  );
}
