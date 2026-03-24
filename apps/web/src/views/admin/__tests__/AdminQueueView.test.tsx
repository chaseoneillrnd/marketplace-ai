import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminQueueView } from '../AdminQueueView';

const mockQueueData = {
  items: [
    {
      submission_id: 'sub-1',
      display_id: 'SKL-001',
      skill_name: 'Code Reviewer',
      short_desc: 'Automated code review skill',
      category: 'development',
      submitter_name: 'Alice Smith',
      submitted_at: new Date().toISOString(),
      gate1_passed: true,
      gate2_score: 85,
      gate2_summary: 'Good quality submission',
      content_preview: 'function review(code) { ... }',
      wait_time_hours: 2,
      divisions: ['engineering'],
    },
    {
      submission_id: 'sub-2',
      display_id: 'SKL-002',
      skill_name: 'Bug Finder',
      short_desc: 'Find bugs automatically',
      category: 'testing',
      submitter_name: 'Bob Jones',
      submitted_at: new Date(Date.now() - 50 * 60 * 60 * 1000).toISOString(),
      gate1_passed: true,
      gate2_score: 72,
      gate2_summary: 'Needs minor improvements',
      content_preview: 'function findBugs(code) { ... }',
      wait_time_hours: 50,
      divisions: ['engineering', 'security'],
    },
  ],
  total: 2,
  page: 1,
  per_page: 20,
  has_more: false,
};

const mockUseAdminQueue = vi.fn();

vi.mock('../../../hooks/useAdminQueue', () => ({
  useAdminQueue: () => mockUseAdminQueue(),
}));

vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: { user_id: 'user-1', name: 'Test Admin', username: 'testadmin', email: 'admin@test.com', division: 'engineering', role: 'admin', is_admin: true },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  }),
}));

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}

describe('AdminQueueView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Review Queue" heading', () => {
    mockUseAdminQueue.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      refetch: vi.fn(),
      claim: vi.fn(),
      decide: vi.fn(),
    });
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByRole('heading', { name: /review queue/i })).toBeInTheDocument();
  });

  it('renders loading state', () => {
    mockUseAdminQueue.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
      claim: vi.fn(),
      decide: vi.fn(),
    });
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders empty state when no items', () => {
    mockUseAdminQueue.mockReturnValue({
      data: { items: [], total: 0, page: 1, per_page: 20, has_more: false },
      loading: false,
      error: null,
      refetch: vi.fn(),
      claim: vi.fn(),
      decide: vi.fn(),
    });
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByText(/no items/i)).toBeInTheDocument();
  });

  it('renders queue items when data exists', () => {
    mockUseAdminQueue.mockReturnValue({
      data: mockQueueData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      claim: vi.fn(),
      decide: vi.fn(),
    });
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByText('Code Reviewer')).toBeInTheDocument();
    expect(screen.getByText('Bug Finder')).toBeInTheDocument();
  });

  it('shows SLA badge for old items', () => {
    mockUseAdminQueue.mockReturnValue({
      data: mockQueueData,
      loading: false,
      error: null,
      refetch: vi.fn(),
      claim: vi.fn(),
      decide: vi.fn(),
    });
    render(<AdminQueueView />, { wrapper });
    expect(screen.getByText('SLA breached')).toBeInTheDocument();
  });
});
