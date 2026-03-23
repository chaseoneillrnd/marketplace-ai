import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { SubmissionFunnel } from '../SubmissionFunnel';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('SubmissionFunnel', () => {
  const props = { submitted: 45, gate1: 38, gate2: 32, approved: 28, published: 28 };

  it('renders SVG', () => {
    render(<SubmissionFunnel {...props} />, { wrapper });
    expect(screen.getByTestId('submission-funnel')).toBeInTheDocument();
    expect(screen.getByTestId('submission-funnel').querySelector('svg')).toBeInTheDocument();
  });

  it('shows all 5 stages', () => {
    render(<SubmissionFunnel {...props} />, { wrapper });
    expect(screen.getByText('Submitted')).toBeInTheDocument();
    expect(screen.getByText('Gate 1')).toBeInTheDocument();
    expect(screen.getByText('Gate 2')).toBeInTheDocument();
    expect(screen.getByText('Approved')).toBeInTheDocument();
    expect(screen.getByText('Published')).toBeInTheDocument();
  });

  it('shows percentage labels', () => {
    render(<SubmissionFunnel {...props} />, { wrapper });
    // Submitted is 100%
    expect(screen.getByText(/100\.0%/)).toBeInTheDocument();
    // gate1: 38/45 = 84.4%
    expect(screen.getByText(/84\.4%/)).toBeInTheDocument();
  });
});
