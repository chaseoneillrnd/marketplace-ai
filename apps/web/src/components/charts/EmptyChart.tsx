import { useT } from '../../context/ThemeContext';

interface EmptyChartProps {
  width?: string;
  height?: string;
  label?: string;
}

export function EmptyChart({ width = '100%', height = '200px', label = 'No data yet' }: EmptyChartProps) {
  const C = useT();
  return (
    <div
      data-testid="empty-chart"
      style={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: C.surfaceHi,
        borderWidth: '1px',
        borderStyle: 'dashed',
        borderColor: C.border,
        borderRadius: '8px',
      }}
    >
      <span style={{ color: C.dim, fontSize: '14px' }}>{label}</span>
    </div>
  );
}
