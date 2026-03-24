import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { RevisionBadge } from '../RevisionBadge';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('RevisionBadge', () => {
  it('renders nothing when revisionNumber is 1', () => {
    const { container } = render(<RevisionBadge revisionNumber={1} />, { wrapper });
    expect(container.innerHTML).toBe('');
  });

  it('renders nothing when revisionNumber is 0', () => {
    const { container } = render(<RevisionBadge revisionNumber={0} />, { wrapper });
    expect(container.innerHTML).toBe('');
  });

  it('renders "Round 2" badge for revisionNumber 2', () => {
    render(<RevisionBadge revisionNumber={2} />, { wrapper });
    const badge = screen.getByTestId('revision-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Round 2');
  });

  it('renders with warning color for revisionNumber >= 3', () => {
    render(<RevisionBadge revisionNumber={3} />, { wrapper });
    const badge = screen.getByTestId('revision-badge');
    expect(badge).toHaveTextContent('Round 3');
    // Amber/warning color for escalated revisions
    expect(badge.style.color).toBe('rgb(242, 160, 32)');
  });

  it('renders with accent color for revisionNumber 2 (not escalated)', () => {
    render(<RevisionBadge revisionNumber={2} />, { wrapper });
    const badge = screen.getByTestId('revision-badge');
    // Accent color (non-warning) for round 2
    expect(badge.style.color).toBe('rgb(75, 125, 255)');
  });

  it('renders high revision numbers', () => {
    render(<RevisionBadge revisionNumber={5} />, { wrapper });
    const badge = screen.getByTestId('revision-badge');
    expect(badge).toHaveTextContent('Round 5');
    expect(badge.style.color).toBe('rgb(242, 160, 32)');
  });
});
