import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { SearchView } from '../views/SearchView';
import type { SkillBrowseResponse } from '@skillhub/shared-types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter initialEntries={['/search?q=review']}>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/search" element={children} />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_BROWSE: SkillBrowseResponse = {
  items: [
    {
      id: 'skill-1',
      slug: 'pr-review-assistant',
      name: 'PR Review Assistant',
      short_desc: 'Code reviews',
      category: 'Engineering',
      divisions: ['Engineering Org'],
      tags: ['review'],
      author: 'Platform Team',
      author_type: 'official',
      version: '2.3.1',
      install_method: 'claude-code',
      verified: true,
      featured: false,
      install_count: 100,
      fork_count: 5,
      favorite_count: 20,
      avg_rating: 4.5,
      review_count: 10,
      days_ago: 3,
    },
  ],
  total: 1,
  page: 1,
  per_page: 20,
  has_more: false,
};

function mockSuccessResponse(data: unknown = MOCK_BROWSE) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  };
}

describe('SearchView', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('renders sort selector with default "Trending"', async () => {
    mockFetch.mockResolvedValue(mockSuccessResponse());

    render(<SearchView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    const sortSelect = screen.getByLabelText('Sort by') as HTMLSelectElement;
    expect(sortSelect).toBeInTheDocument();
    expect(sortSelect.value).toBe('trending');
  });

  it('has all sort options available', async () => {
    mockFetch.mockResolvedValue(mockSuccessResponse());

    render(<SearchView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    expect(screen.getByRole('option', { name: 'Trending' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Most Installed' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Highest Rated' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Newest' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Recently Updated' })).toBeInTheDocument();
  });

  it('changing sort triggers a new API call with sort param', async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValue(mockSuccessResponse());

    render(<SearchView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    const initialCallCount = mockFetch.mock.calls.length;

    const sortSelect = screen.getByLabelText('Sort by');
    await user.selectOptions(sortSelect, 'newest');

    // Should have triggered another fetch with sort=newest
    await waitFor(() => {
      expect(mockFetch.mock.calls.length).toBeGreaterThan(initialCallCount);
    });

    // Check the most recent call includes sort=newest
    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1];
    const lastUrl = lastCall[0] as string;
    expect(lastUrl).toContain('sort=newest');
  });
});
