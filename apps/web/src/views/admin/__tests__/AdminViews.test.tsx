import { describe, it, expect, vi } from 'vitest';
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

vi.mock('recharts', async () => await import('../../../__mocks__/recharts'));

vi.mock('../../../hooks/useAdminQueue', () => ({
  useAdminQueue: () => ({
    data: null,
    loading: false,
    error: null,
    refetch: vi.fn(),
    claim: vi.fn(),
    decide: vi.fn(),
  }),
}));

vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { user_id: 'u1', name: 'Admin', username: 'admin', email: 'a@b.com', division: 'eng', role: 'admin', is_admin: true },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock('../../../lib/api', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 }),
    post: vi.fn().mockResolvedValue({}),
    patch: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('../../../hooks/useAdminDashboard', () => ({
  useAdminDashboard: () => ({
    summary: {
      dau: 0,
      new_installs_7d: 0,
      active_installs: 0,
      published_skills: 0,
      pending_reviews: 0,
      submission_pass_rate: 0,
      period: '7d',
    },
    timeSeries: [],
    funnel: {
      submitted: 0,
      gate1_passed: 0,
      gate2_passed: 0,
      approved: 0,
      published: 0,
    },
    topSkills: [],
    divisionData: {},
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}));

vi.mock('../../../hooks/useAdminSkills', () => ({
  useAdminSkills: () => ({
    skills: [],
    total: 0,
    page: 1,
    loading: false,
    error: null,
    featureSkill: vi.fn(),
    deprecateSkill: vi.fn(),
    removeSkill: vi.fn(),
    setPage: vi.fn(),
    setSearch: vi.fn(),
  }),
}));

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

  it('renders stat cards', () => {
    render(<AdminDashboardView />, { wrapper });
    expect(screen.getByTestId('stat-cards-grid')).toBeInTheDocument();
    const cards = screen.getAllByTestId('stat-card');
    expect(cards.length).toBeGreaterThanOrEqual(6);
  });

  it('renders charts area', () => {
    render(<AdminDashboardView />, { wrapper });
    expect(screen.getByTestId('charts-area')).toBeInTheDocument();
  });
});

describe('AdminQueueView', () => {
  it('renders Review Queue heading', () => {
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByRole('heading', { name: /review queue/i })).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByText(/no items/i)).toBeInTheDocument();
  });
});

describe('AdminFeedbackView', () => {
  it('renders Feedback heading', () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByRole('heading', { name: /feedback/i })).toBeInTheDocument();
  });

  it('renders data-testid', () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByTestId('admin-feedback-view')).toBeInTheDocument();
  });
});

describe('AdminSkillsView', () => {
  it('renders Skills heading', () => {
    render(<AdminSkillsView />, { wrapper });
    expect(screen.getByRole('heading', { name: /skills/i })).toBeInTheDocument();
  });

  it('renders search input', () => {
    render(<AdminSkillsView />, { wrapper });
    expect(screen.getByTestId('skills-search-input')).toBeInTheDocument();
  });

  it('renders empty state when no skills', () => {
    render(<AdminSkillsView />, { wrapper });
    expect(screen.getByText('No skills found.')).toBeInTheDocument();
  });
});

describe('AdminRoadmapView', () => {
  it('renders Roadmap heading', () => {
    render(<AdminRoadmapView />, { wrapper });
    expect(screen.getByRole('heading', { name: /roadmap/i })).toBeInTheDocument();
  });

  it('renders data-testid', () => {
    render(<AdminRoadmapView />, { wrapper });
    expect(screen.getByTestId('admin-roadmap-view')).toBeInTheDocument();
  });
});

describe('AdminExportView', () => {
  it('renders Export heading', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByRole('heading', { name: /export/i })).toBeInTheDocument();
  });

  it('renders data-testid', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByTestId('admin-export-view')).toBeInTheDocument();
  });
});
