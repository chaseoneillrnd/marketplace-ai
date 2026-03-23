import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { DivisionChartGrid } from '../DivisionChartGrid';

vi.mock('recharts', async () => await import('../../../__mocks__/recharts'));

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('DivisionChartGrid', () => {
  const data = {
    'engineering-org': [{ date: '2026-03-10', value: 12 }],
    'product-org': [{ date: '2026-03-10', value: 8 }],
    'design-org': [{ date: '2026-03-10', value: 5 }],
  };
  const colors = {
    'engineering-org': '#4b7dff',
    'product-org': '#1fd49e',
    'design-org': '#a78bfa',
  };

  it('renders grid', () => {
    render(<DivisionChartGrid data={data} colors={colors} />, { wrapper });
    expect(screen.getByTestId('division-chart-grid')).toBeInTheDocument();
  });

  it('renders correct number of mini charts', () => {
    render(<DivisionChartGrid data={data} colors={colors} />, { wrapper });
    const miniCharts = screen.getAllByTestId('division-mini-chart');
    expect(miniCharts).toHaveLength(3);
  });
});
