import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { BrowseView } from '../views/BrowseView';
import type { SkillBrowseResponse } from '@skillhub/shared-types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter initialEntries={['/browse']}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_SKILLS: SkillBrowseResponse = {
  items: [
    {
      id: '00000000-0000-0000-0000-000000000010',
      slug: 'pr-review-assistant',
      name: 'PR Review Assistant',
      short_desc: 'Surgical code reviews',
      category: 'Engineering',
      divisions: ['Engineering Org'],
      tags: ['code-review'],
      author: 'Platform Team',
      author_type: 'official',
      version: '2.3.1',
      install_method: 'claude-code',
      verified: true,
      featured: true,
      install_count: 1842,
      fork_count: 34,
      favorite_count: 156,
      avg_rating: 4.9,
      review_count: 218,
      days_ago: 2,
    },
    {
      id: '00000000-0000-0000-0000-000000000020',
      slug: 'test-writer',
      name: 'Test Writer',
      short_desc: 'Generates tests',
      category: 'Engineering',
      divisions: ['Engineering Org', 'Product Org'],
      tags: ['testing'],
      author: 'Jane',
      author_type: 'community',
      version: '1.0.0',
      install_method: 'mcp',
      verified: false,
      featured: false,
      install_count: 100,
      fork_count: 5,
      favorite_count: 20,
      avg_rating: 4.2,
      review_count: 10,
      days_ago: 5,
    },
  ],
  total: 2,
  page: 1,
  per_page: 20,
  has_more: false,
};

const EMPTY_RESPONSE: SkillBrowseResponse = {
  items: [],
  total: 0,
  page: 1,
  per_page: 20,
  has_more: false,
};

const HAS_MORE_RESPONSE: SkillBrowseResponse = {
  ...MOCK_SKILLS,
  total: 50,
  has_more: true,
};

describe('BrowseView', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(MOCK_SKILLS),
    });
  });

  // --- Category Filter Selection ---

  it('renders category filter pills', async () => {
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('All')).toBeInTheDocument();
    });

    expect(screen.getByText('Engineering')).toBeInTheDocument();
    expect(screen.getByText('Product')).toBeInTheDocument();
    expect(screen.getByText('Data')).toBeInTheDocument();
    expect(screen.getByText('Security')).toBeInTheDocument();
  });

  it('clicking a category triggers API call with category param', async () => {
    const user = userEvent.setup();
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    await user.click(screen.getByText('Engineering'));

    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      const lastCall = calls[calls.length - 1];
      const url = lastCall[0] as string;
      expect(url).toContain('category=engineering');
    });
  });

  it('clicking All removes category from API call', async () => {
    const user = userEvent.setup();
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    // Click Engineering then All
    await user.click(screen.getByText('Engineering'));
    await user.click(screen.getByText('All'));

    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      const lastCall = calls[calls.length - 1];
      const url = lastCall[0] as string;
      expect(url).not.toContain('category=');
    });
  });

  // --- Division Filter Multi-Select ---

  it('renders division filter bar', () => {
    render(<BrowseView />, { wrapper });

    // Division labels should be present (may appear in both filter bar and cards)
    expect(screen.getAllByText('Engineering Org').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Product Org').length).toBeGreaterThan(0);
  });

  it('clicking a division triggers API call with divisions param', async () => {
    const user = userEvent.setup();
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    const chips = screen.getAllByText('Engineering Org');
    await user.click(chips[0]);

    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      const lastCall = calls[calls.length - 1];
      const url = lastCall[0] as string;
      expect(url).toContain('divisions=engineering-org');
    });
  });

  // --- Skill Grid Rendering ---

  it('renders skill cards after data loads', async () => {
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getAllByTestId('skill-card').length).toBe(2);
    });

    expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    expect(screen.getByText('Test Writer')).toBeInTheDocument();
  });

  it('renders skeleton cards during loading', () => {
    mockFetch.mockReturnValue(new Promise(() => {}));

    render(<BrowseView />, { wrapper });

    const skeletons = screen.getAllByTestId('skeleton-card');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders total skills count', async () => {
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('2 skills')).toBeInTheDocument();
    });
  });

  // --- Empty State ---

  it('renders empty state when no skills found', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(EMPTY_RESPONSE),
    });

    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  // --- Error State ---

  it('renders error state on API failure', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Server Error',
      json: () => Promise.resolve({ detail: 'Server error' }),
    });

    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });
  });

  // --- Load More / Pagination ---

  it('renders Load more button when has_more is true', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(HAS_MORE_RESPONSE),
    });

    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Load more')).toBeInTheDocument();
    });
  });

  it('does not render Load more when has_more is false', async () => {
    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getAllByTestId('skill-card').length).toBe(2);
    });

    expect(screen.queryByText('Load more')).not.toBeInTheDocument();
  });

  it('clicking Load more increments page parameter', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(HAS_MORE_RESPONSE),
    });

    render(<BrowseView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Load more')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Load more'));

    await waitFor(() => {
      const calls = mockFetch.mock.calls;
      const lastCall = calls[calls.length - 1];
      const url = lastCall[0] as string;
      expect(url).toContain('page=2');
    });
  });

  // --- Advanced Filters Button ---

  it('renders Advanced Filters button', () => {
    render(<BrowseView />, { wrapper });

    expect(screen.getByText('Advanced Filters')).toBeInTheDocument();
  });

  // --- Page Title ---

  it('renders page title All Skills', async () => {
    render(<BrowseView />, { wrapper });

    expect(screen.getByText('All Skills')).toBeInTheDocument();
  });
});
