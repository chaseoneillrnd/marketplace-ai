import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { CustomTooltip } from '../CustomTooltip';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('CustomTooltip', () => {
  it('renders null when inactive', () => {
    const { container } = render(<CustomTooltip active={false} />, { wrapper });
    expect(container.innerHTML).toBe('');
  });

  it('renders null when payload is undefined', () => {
    const { container } = render(<CustomTooltip active={true} />, { wrapper });
    expect(container.innerHTML).toBe('');
  });

  it('renders label and values when active', () => {
    const payload = [
      { name: 'Installs', value: 42, color: '#4b7dff' },
      { name: 'Users', value: 18, color: '#1fd49e' },
    ];
    render(<CustomTooltip active={true} payload={payload} label="2026-03-01" />, { wrapper });
    expect(screen.getByText('2026-03-01')).toBeInTheDocument();
    expect(screen.getByText('Installs')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('18')).toBeInTheDocument();
  });
});
