import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { SubmissionCard } from '../SubmissionCard';
import type { ReviewQueueItem } from '../../../hooks/useAdminQueue';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

function makeItem(overrides: Partial<ReviewQueueItem> = {}): ReviewQueueItem {
  return {
    submission_id: 'sub-1',
    display_id: 'SKL-001',
    skill_name: 'Code Reviewer',
    short_desc: 'Automated code review',
    category: 'development',
    submitter_name: 'Alice Smith',
    submitted_at: new Date().toISOString(),
    gate1_passed: true,
    gate2_score: 85,
    gate2_summary: 'Good quality',
    content_preview: 'function review() {}',
    wait_time_hours: 2,
    divisions: ['engineering'],
    revision_number: 1,
    status: 'pending_review',
    ...overrides,
  };
}

describe('SubmissionCard', () => {
  it('renders skill name', () => {
    render(
      <SubmissionCard item={makeItem()} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByText('Code Reviewer')).toBeInTheDocument();
  });

  it('renders submitter name', () => {
    render(
      <SubmissionCard item={makeItem()} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByText('Alice Smith')).toBeInTheDocument();
  });

  it('renders category badge', () => {
    render(
      <SubmissionCard item={makeItem()} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByText('development')).toBeInTheDocument();
  });

  it('renders SLA timer', () => {
    render(
      <SubmissionCard item={makeItem({ wait_time_hours: 2 })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    const sla = screen.getByTestId('sla-timer');
    expect(sla).toHaveTextContent('2h ago');
  });

  it('renders SLA at risk for 24-48h wait', () => {
    render(
      <SubmissionCard item={makeItem({ wait_time_hours: 30 })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    const sla = screen.getByTestId('sla-timer');
    expect(sla).toHaveTextContent('SLA at risk');
  });

  it('renders SLA breached for > 48h wait', () => {
    render(
      <SubmissionCard item={makeItem({ wait_time_hours: 50 })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    const sla = screen.getByTestId('sla-timer');
    expect(sla).toHaveTextContent('SLA breached');
  });

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(
      <SubmissionCard item={makeItem()} selected={false} onClick={handleClick} />,
      { wrapper },
    );
    fireEvent.click(screen.getByTestId('submission-card'));
    expect(handleClick).toHaveBeenCalledOnce();
  });

  it('does not render revision badge for round 1', () => {
    render(
      <SubmissionCard item={makeItem({ revision_number: 1 })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.queryByTestId('revision-badge')).not.toBeInTheDocument();
  });

  it('renders revision badge for round 2+', () => {
    render(
      <SubmissionCard item={makeItem({ revision_number: 2 })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByTestId('revision-badge')).toHaveTextContent('Round 2');
  });

  it('renders status badge', () => {
    render(
      <SubmissionCard item={makeItem({ status: 'in_review' })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByTestId('status-badge')).toHaveTextContent('In Review');
  });

  it('renders division badge', () => {
    render(
      <SubmissionCard item={makeItem({ divisions: ['security', 'engineering'] })} selected={false} onClick={vi.fn()} />,
      { wrapper },
    );
    expect(screen.getByText('security')).toBeInTheDocument();
  });
});
