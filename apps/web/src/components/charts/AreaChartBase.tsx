import { ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { useChartTheme } from '../../hooks/useChartTheme';
import { CustomTooltip } from './CustomTooltip';
import { formatTick } from './chartUtils';

export interface AreaChartBaseSeries {
  key: string;
  color: string;
  name: string;
}

export interface AreaChartBaseProps {
  data: Record<string, unknown>[];
  series: AreaChartBaseSeries[];
  height?: number;
  xAxisKey?: string;
}

export function AreaChartBase({ data, series, height = 240, xAxisKey = 'date' }: AreaChartBaseProps) {
  const ct = useChartTheme();

  return (
    <div data-testid="area-chart-base" style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            {series.map((s) => (
              <linearGradient key={s.key} id={`grad-${s.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity={0.094} />
                <stop offset="100%" stopColor={s.color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid stroke={ct.gridStroke} strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} stroke={ct.axisStroke} tick={{ fontSize: 11 }} />
          <YAxis stroke={ct.axisStroke} tickFormatter={formatTick} tick={{ fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          {series.map((s) => (
            <Area
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.name}
              stroke={s.color}
              fill={`url(#grad-${s.key})`}
              strokeWidth={2}
              isAnimationActive={false}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
