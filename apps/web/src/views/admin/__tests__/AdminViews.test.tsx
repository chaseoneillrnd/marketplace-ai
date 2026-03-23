import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminDashboardView } from '../AdminDashboardView';
import { AdminQueueView } from '../AdminQueueView';
import { AdminFeedbackView } from '../AdminFeedbackView';
import { AdminSkillsView } from '../AdminSkillsView';
import { AdminRoadmapView } from '../AdminRoadmapView';
import { AdminExportView } from '../AdminExportView';

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}

describe('AdminDashboardView', () => {
  it('renders Dashboard heading', () => {
    render(<AdminDashboardView />, { wrapper });
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
  });

  it('renders Coming soon text', () => {
    render(<AdminDashboardView />, { wrapper });
    expect(screen.getByText('Coming soon')).toBeInTheDocument();
  });
});

describe('AdminQueueView', () => {
  it('renders Queue heading', () => {
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByRole('heading', { name: /queue/i })).toBeInTheDocument();
  });

  it('renders Coming soon text', () => {
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByText('Coming soon')).toBeInTheDocument();
  });
});

describe('AdminFeedbackView', () => {
  it('renders Feedback heading', () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByRole('heading', { name: /feedback/i })).toBeInTheDocument();
  });

  it('renders Coming soon text', () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByText('Coming soon')).toBeInTheDocument();
  });
});

describe('AdminSkillsView', () => {
  it('renders Skills heading', () => {
    render(<AdminSkillsView />, { wrapper });
    expect(screen.getByRole('heading', { name: /skills/i })).toBeInTheDocument();
  });

  it('renders Coming soon text', () => {
    render(<AdminSkillsView />, { wrapper });
    expect(screen.getByText('Coming soon')).toBeInTheDocument();
  });
});

describe('AdminRoadmapView', () => {
  it('renders Roadmap heading', () => {
    render(<AdminRoadmapView />, { wrapper });
    expect(screen.getByRole('heading', { name: /roadmap/i })).toBeInTheDocument();
  });

  it('renders Coming soon text', () => {
    render(<AdminRoadmapView />, { wrapper });
    expect(screen.getByText('Coming soon')).toBeInTheDocument();
  });
});

describe('AdminExportView', () => {
  it('renders Export heading', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByRole('heading', { name: /export/i })).toBeInTheDocument();
  });

  it('renders Coming soon text', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByText('Coming soon')).toBeInTheDocument();
  });
});
