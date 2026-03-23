import { useState } from 'react';
import { useT } from '../../context/ThemeContext';
import { AreaChartBase } from './AreaChartBase';

export interface TrendingAreaChartProps {
  data: { date: string; value: number }[];
  mode?: 'dau' | 'wau' | 'mau';
}

const MODES = ['dau', 'wau', 'mau'] as const;
const MODE_LABELS: Record<string, string> = { dau: 'DAU', wau: 'WAU', mau: 'MAU' };

export function TrendingAreaChart({ data, mode: initialMode = 'dau' }: TrendingAreaChartProps) {
  const C = useT();
  const [mode, setMode] = useState<'dau' | 'wau' | 'mau'>(initialMode);

  return (
    <div data-testid="trending-area-chart">
      <div style={{ display: 'flex', gap: '4px', marginBottom: '8px' }} role="group" aria-label="Trending mode toggle">
        {MODES.map((m) => (
          <button
            key={m}
            onClick={() => setMode(m)}
            aria-pressed={mode === m}
            style={{
              fontFamily: 'Outfit, sans-serif',
              fontSize: '11px',
              fontWeight: 600,
              padding: '3px 10px',
              borderRadius: '99px',
              border: `1px solid ${mode === m ? C.accent : C.border}`,
              background: mode === m ? C.accentDim : 'transparent',
              color: mode === m ? C.accent : C.muted,
              cursor: 'pointer',
            }}
          >
            {MODE_LABELS[m]}
          </button>
        ))}
      </div>
      <AreaChartBase
        data={data}
        series={[{ key: 'value', color: C.accent, name: MODE_LABELS[mode] }]}
        height={200}
      />
    </div>
  );
}
