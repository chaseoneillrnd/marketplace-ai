import { useT } from '../../context/ThemeContext';

export interface SubmissionFunnelProps {
  submitted: number;
  gate1: number;
  gate2: number;
  approved: number;
  published: number;
}

interface Stage {
  label: string;
  value: number;
  color: string;
}

export function SubmissionFunnel({ submitted, gate1, gate2, approved, published }: SubmissionFunnelProps) {
  const C = useT();

  const max = Math.max(submitted, 1);
  const stages: Stage[] = [
    { label: 'Submitted', value: submitted, color: C.muted },
    { label: 'Gate 1', value: gate1, color: C.amber },
    { label: 'Gate 2', value: gate2, color: C.accent },
    { label: 'Approved', value: approved, color: C.green },
    { label: 'Published', value: published, color: C.green },
  ];

  const barHeight = 28;
  const gap = 8;
  const labelWidth = 80;
  const chartWidth = 320;
  const svgWidth = labelWidth + chartWidth + 60;
  const svgHeight = stages.length * (barHeight + gap) + gap;

  return (
    <div data-testid="submission-funnel">
      <svg width="100%" viewBox={`0 0 ${svgWidth} ${svgHeight}`} role="img" aria-label="Submission funnel">
        {stages.map((stage, i) => {
          const y = gap + i * (barHeight + gap);
          const width = (stage.value / max) * chartWidth;
          const pct = submitted > 0 ? ((stage.value / submitted) * 100).toFixed(1) : '0.0';

          return (
            <g key={stage.label}>
              <text
                x={labelWidth - 8}
                y={y + barHeight / 2 + 4}
                textAnchor="end"
                fill={C.muted}
                fontSize={11}
                fontFamily="Outfit, sans-serif"
              >
                {stage.label}
              </text>
              <rect
                x={labelWidth}
                y={y}
                width={Math.max(width, 2)}
                height={barHeight}
                rx={4}
                fill={stage.color}
                opacity={0.7}
              />
              <text
                x={labelWidth + Math.max(width, 2) + 6}
                y={y + barHeight / 2 + 4}
                fill={C.text}
                fontSize={11}
                fontFamily="JetBrains Mono, monospace"
                fontWeight={600}
              >
                {stage.value} ({pct}%)
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
