import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { FilteredView } from './FilteredView';
import type { SkillBrowseResponse } from '@skillhub/shared-types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter initialEntries={['/filtered']}>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_RESPONSE: SkillBrowseResponse = {
  items: [
    {
      id: '00000000-0000-0000-0000-000000000010',
      slug: 'test-skill',
      name: 'Test Skill',
      short_desc: 'A test skill',
      category: 'Engineering',
      divisions: ['Engineering Org'],
      tags: ['test'],
      author: 'Test',
      author_type: 'community',
      version: '1.0.0',
      install_method: 'claude-code',
      verified: true,
      featured: false,
      install_count: 100,
      fork_count: 5,
      favorite_count: 20,
      avg_rating: 4.5,
      review_count: 10,
      days_ago: 1,
    },
  ],
  total: 1,
  page: 1,
  per_page: 20,
  has_more: false,
};

describe('FilteredView', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(MOCK_RESPONSE),
    });
  });

  it('passes division filter params to API', async () => {
    const user = userEvent.setup();

    render(<FilteredView />, { wrapper });

    // Wait for initial fetch
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });

    // Click on Engineering Org division checkbox
    const engButton = screen.getAllByText('Engineering Org')[0];
    await user.click(engButton);

    // Verify the API was called with divisions param
    await waitFor(() => {
      const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
      const url = lastCall[0] as string;
      expect(url).toContain('divisions=engineering-org');
    });
  });

  it('renders skill cards after loading', async () => {
    render(<FilteredView />, { wrapper });

    await waitFor(() => {
      expect(screen.getAllByTestId('skill-card').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('Test Skill')).toBeInTheDocument();
  });

  it('renders category sidebar with All selected by default', () => {
    render(<FilteredView />, { wrapper });

    // Categories should be visible in the sidebar
    expect(screen.getByText('Category')).toBeInTheDocument();
    expect(screen.getByText('Sort By')).toBeInTheDocument();
    expect(screen.getByText('Install Method')).toBeInTheDocument();
    expect(screen.getByText('Quality')).toBeInTheDocument();
  });

  it('renders empty state when no skills found', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          items: [],
          total: 0,
          page: 1,
          per_page: 20,
          has_more: false,
        }),
    });

    render(<FilteredView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
    });
  });

  it('renders error state on fetch failure', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Server Error',
      json: () => Promise.resolve({ detail: 'Server error' }),
    });

    render(<FilteredView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });
  });
});
