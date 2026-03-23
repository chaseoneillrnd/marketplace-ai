import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { DivisionMiniChart } from '../DivisionMiniChart';

vi.mock('recharts', async () => await import('../../../__mocks__/recharts'));

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('DivisionMiniChart', () => {
  const data = [
    { date: '2026-03-10', value: 12 },
    { date: '2026-03-11', value: 18 },
  ];

  it('renders with division name', () => {
    render(<DivisionMiniChart division="engineering-org" color="#4b7dff" data={data} />, { wrapper });
    expect(screen.getByTestId('division-mini-chart')).toBeInTheDocument();
    expect(screen.getByText('engineering-org')).toBeInTheDocument();
  });

  it('renders chart area', () => {
    render(<DivisionMiniChart division="product-org" color="#1fd49e" data={data} total={30} />, { wrapper });
    expect(screen.getByTestId('area-chart-base')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
  });
});
