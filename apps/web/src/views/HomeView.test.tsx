import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { FlagsProvider } from '../context/FlagsContext';
import { HomeView } from './HomeView';
import type { SkillBrowseResponse } from '@skillhub/shared-types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>
        <AuthProvider>
          <FlagsProvider>{children}</FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_BROWSE_RESPONSE: SkillBrowseResponse = {
  items: [
    {
      id: '00000000-0000-0000-0000-000000000010',
      slug: 'pr-review-assistant',
      name: 'PR Review Assistant',
      short_desc: 'Surgical code reviews with security analysis',
      category: 'Engineering',
      divisions: ['Engineering Org'],
      tags: ['code-review', 'git'],
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
  ],
  total: 1,
  page: 1,
  per_page: 8,
  has_more: false,
};

const EMPTY_RESPONSE: SkillBrowseResponse = {
  items: [],
  total: 0,
  page: 1,
  per_page: 8,
  has_more: false,
};

describe('HomeView', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('renders skeleton during loading', () => {
    // Never resolve the fetch so we stay in loading state
    mockFetch.mockReturnValue(new Promise(() => {}));

    render(<HomeView />, { wrapper });

    const skeletons = screen.getAllByTestId('skeleton-card');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders skill cards after successful fetch', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve({ flags: {} }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(MOCK_BROWSE_RESPONSE),
      });
    });

    render(<HomeView />, { wrapper });

    await waitFor(() => {
      expect(screen.getAllByTestId('skill-card').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
  });

  it('renders error state on API failure', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: () => Promise.resolve({ detail: 'Server error' }),
    });

    render(<HomeView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toBeInTheDocument();
    });
  });

  it('renders the hero search section', () => {
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(EMPTY_RESPONSE),
    });

    render(<HomeView />, { wrapper });

    expect(screen.getByPlaceholderText('What do you need help with today?')).toBeInTheDocument();
    expect(screen.getByText('shared intelligence')).toBeInTheDocument();
  });
});
