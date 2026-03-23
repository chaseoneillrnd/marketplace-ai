import { DivisionMiniChart } from './DivisionMiniChart';

export interface DivisionChartGridProps {
  data: Record<string, { date: string; value: number }[]>;
  colors: Record<string, string>;
}

export function DivisionChartGrid({ data, colors }: DivisionChartGridProps) {
  const divisions = Object.keys(data);

  return (
    <div
      data-testid="division-chart-grid"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '12px',
      }}
    >
      {divisions.map((div) => {
        const series = data[div];
        const total = series.reduce((sum, d) => sum + d.value, 0);
        return (
          <DivisionMiniChart
            key={div}
            division={div}
            color={colors[div] ?? '#4b7dff'}
            data={series}
            total={total}
          />
        );
      })}
    </div>
  );
}
