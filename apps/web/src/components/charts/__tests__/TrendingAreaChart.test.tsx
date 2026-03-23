import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { TrendingAreaChart } from '../TrendingAreaChart';

vi.mock('recharts', async () => await import('../../../__mocks__/recharts'));

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('TrendingAreaChart', () => {
  const data = [
    { date: '2026-03-01', value: 10 },
    { date: '2026-03-02', value: 15 },
  ];

  it('renders toggle', () => {
    render(<TrendingAreaChart data={data} />, { wrapper });
    expect(screen.getByTestId('trending-area-chart')).toBeInTheDocument();
    expect(screen.getByText('DAU')).toBeInTheDocument();
    expect(screen.getByText('WAU')).toBeInTheDocument();
    expect(screen.getByText('MAU')).toBeInTheDocument();
  });

  it('renders chart', () => {
    render(<TrendingAreaChart data={data} />, { wrapper });
    expect(screen.getByTestId('area-chart-base')).toBeInTheDocument();
  });
});
