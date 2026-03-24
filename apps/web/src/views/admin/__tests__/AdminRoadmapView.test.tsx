import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminRoadmapView } from '../AdminRoadmapView';

vi.mock('../../../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { api } from '../../../lib/api';
const mockGet = vi.mocked(api.get);
const mockPost = vi.mocked(api.post);

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_ITEMS = {
  items: [
    { id: 'r1', title: 'Dark mode', body: 'Add dark mode support', status: 'planned', created_at: '2026-03-15T10:00:00Z' },
    { id: 'r2', title: 'MCP v2', body: 'Upgrade MCP protocol', status: 'in_progress', created_at: '2026-03-16T10:00:00Z' },
    { id: 'r3', title: 'Search v2', body: 'Better search', status: 'shipped', shipped_at: '2026-03-17T10:00:00Z', version_tag: 'v1.2.0', created_at: '2026-03-10T10:00:00Z' },
    { id: 'r4', title: 'Old feature', body: 'Deprecated', status: 'cancelled', created_at: '2026-03-01T10:00:00Z' },
  ],
};

describe('AdminRoadmapView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(MOCK_ITEMS);
    mockPost.mockResolvedValue({});
  });

  it('renders Roadmap heading', async () => {
    render(<AdminRoadmapView />, { wrapper });
    expect(screen.getByRole('heading', { name: /roadmap/i })).toBeInTheDocument();
  });

  it('has data-testid', async () => {
    render(<AdminRoadmapView />, { wrapper });
    expect(screen.getByTestId('admin-roadmap-view')).toBeInTheDocument();
  });

  it('renders four kanban columns', async () => {
    render(<AdminRoadmapView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('PLANNED')).toBeInTheDocument();
    });
    expect(screen.getByText('IN PROGRESS')).toBeInTheDocument();
    expect(screen.getByText('SHIPPED')).toBeInTheDocument();
    expect(screen.getByText('CANCELLED')).toBeInTheDocument();
  });

  it('renders cards in correct columns', async () => {
    render(<AdminRoadmapView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Dark mode')).toBeInTheDocument();
    });
    expect(screen.getByText('MCP v2')).toBeInTheDocument();
    expect(screen.getByText('Search v2')).toBeInTheDocument();
    expect(screen.getByText('Old feature')).toBeInTheDocument();
  });

  it('shows New Item button in Planned column', async () => {
    render(<AdminRoadmapView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Dark mode')).toBeInTheDocument();
    });
    expect(screen.getByText('+ New Item')).toBeInTheDocument();
  });

  it('opens inline form on New Item click', async () => {
    const user = userEvent.setup();
    render(<AdminRoadmapView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Dark mode')).toBeInTheDocument();
    });
    await user.click(screen.getByText('+ New Item'));
    expect(screen.getByPlaceholderText('Title')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Description')).toBeInTheDocument();
  });

  it('shows Mark as Shipped on in-progress items', async () => {
    render(<AdminRoadmapView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('MCP v2')).toBeInTheDocument();
    });
    expect(screen.getByText('Mark as Shipped')).toBeInTheDocument();
  });

  it('renders column card count badges', async () => {
    render(<AdminRoadmapView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Dark mode')).toBeInTheDocument();
    });
    // Each column header should show a count
    const badges = screen.getAllByTestId('column-count');
    expect(badges.length).toBe(4);
  });
});
