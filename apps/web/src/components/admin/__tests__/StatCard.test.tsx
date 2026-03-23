import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { StatCard } from '../StatCard';

vi.mock('recharts', async () => await import('../../../__mocks__/recharts'));

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('StatCard', () => {
  it('renders label and value', () => {
    render(<StatCard label="Daily Active Users" value={142} />, { wrapper });
    expect(screen.getByTestId('stat-card')).toBeInTheDocument();
    expect(screen.getByText('Daily Active Users')).toBeInTheDocument();
    expect(screen.getByText('142')).toBeInTheDocument();
  });

  it('renders positive delta with green styling', () => {
    render(<StatCard label="Installs" value={87} delta={12} />, { wrapper });
    const delta = screen.getByTestId('stat-delta');
    expect(delta).toHaveTextContent('+12%');
  });

  it('renders negative delta with red styling', () => {
    render(<StatCard label="Reviews" value={3} delta={-5} />, { wrapper });
    const delta = screen.getByTestId('stat-delta');
    expect(delta).toHaveTextContent('-5%');
  });

  it('renders sparkline when data provided', () => {
    const sparkData = [{ value: 10 }, { value: 20 }, { value: 15 }];
    render(<StatCard label="Users" value={100} sparkData={sparkData} />, { wrapper });
    expect(screen.getByTestId('sparkline')).toBeInTheDocument();
  });
});
