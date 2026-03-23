import type { PropsWithChildren } from 'react';

const stub = (name: string) => {
  const C = ({ children, ...props }: PropsWithChildren<Record<string, unknown>>) => (
    <div data-testid={`recharts-${name.toLowerCase()}`} {...(typeof props === 'object' ? {} : {})}>{children}</div>
  );
  C.displayName = name;
  return C;
};

export const AreaChart = stub('AreaChart');
export const LineChart = stub('LineChart');
export const Area = stub('Area');
export const Line = stub('Line');
export const XAxis = stub('XAxis');
export const YAxis = stub('YAxis');
export const CartesianGrid = stub('CartesianGrid');
export const Tooltip = stub('Tooltip');
export const ResponsiveContainer = ({ children }: PropsWithChildren) => <div>{children}</div>;
