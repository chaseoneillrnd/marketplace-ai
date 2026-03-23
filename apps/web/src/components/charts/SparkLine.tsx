import { LineChart, Line } from 'recharts';

interface SparkLineProps {
  data: { value: number }[];
  color: string;
  width?: number;
  height?: number;
}

export function SparkLine({ data, color, width = 64, height = 32 }: SparkLineProps) {
  return (
    <div data-testid="sparkline">
      <LineChart width={width} height={height} data={data}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </div>
  );
}
