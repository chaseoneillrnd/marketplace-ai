import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AreaChartBase } from '../AreaChartBase';

vi.mock('recharts', async () => await import('../../../__mocks__/recharts'));

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('AreaChartBase', () => {
  it('renders without crashing', () => {
    render(
      <AreaChartBase
        data={[]}
        series={[{ key: 'installs', color: '#4b7dff', name: 'Installs' }]}
      />,
      { wrapper },
    );
    expect(screen.getByTestId('area-chart-base')).toBeInTheDocument();
  });

  it('renders with data array', () => {
    const data = [
      { date: '2026-03-01', installs: 10 },
      { date: '2026-03-02', installs: 20 },
    ];
    render(
      <AreaChartBase
        data={data}
        series={[{ key: 'installs', color: '#4b7dff', name: 'Installs' }]}
      />,
      { wrapper },
    );
    expect(screen.getByTestId('area-chart-base')).toBeInTheDocument();
  });
});
