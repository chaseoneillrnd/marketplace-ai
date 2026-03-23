import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { FlagsProvider } from '../context/FlagsContext';
import { SkillDetailView } from '../views/SkillDetailView';
import { HomeView } from '../views/HomeView';
import type { SkillDetail, SkillBrowseResponse } from '@skillhub/shared-types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

const MOCK_SKILL_DETAIL: SkillDetail = {
  id: '00000000-0000-0000-0000-000000000010',
  slug: 'pr-review-assistant',
  name: 'PR Review Assistant',
  short_desc: 'Surgical code reviews with security analysis',
  category: 'Engineering',
  divisions: ['Engineering Org'],
  tags: ['code-review', 'git'],
  author: 'Platform Team',
  author_id: '00000000-0000-0000-0000-000000000099',
  author_type: 'official',
  current_version: '2.3.1',
  install_method: 'claude-code',
  data_sensitivity: 'low',
  external_calls: false,
  verified: true,
  featured: true,
  status: 'published',
  install_count: 1842,
  fork_count: 34,
  favorite_count: 156,
  view_count: 5000,
  review_count: 218,
  avg_rating: 4.9,
  trending_score: 95.5,
  published_at: '2026-01-15T00:00:00Z',
  deprecated_at: null,
  trigger_phrases: [
    { id: 'tp-1', phrase: 'review this PR' },
    { id: 'tp-2', phrase: 'check my code' },
  ],
  current_version_content: {
    id: 'v-1',
    version: '2.3.1',
    content: '# PR Review Assistant\n\nHelps review PRs.',
    frontmatter: { name: 'PR Review Assistant' },
    changelog: 'Bug fixes',
    published_at: '2026-01-15T00:00:00Z',
  },
};

const MOCK_BROWSE_RESPONSE: SkillBrowseResponse = {
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
  ],
  total: 1,
  page: 1,
  per_page: 8,
  has_more: false,
};

function successResponse(data: unknown) {
  return { ok: true, status: 200, json: () => Promise.resolve(data) };
}

// --- #10: MCP install flag gating ---

describe('Flag: mcp_install_enabled', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  function detailWrapper({ children }: { children: ReactNode }) {
    return (
      <MemoryRouter initialEntries={['/skills/pr-review-assistant']}>
        <ThemeProvider>
          <AuthProvider>
            <FlagsProvider>
              <Routes>
                <Route path="/skills/:slug" element={children} />
              </Routes>
            </FlagsProvider>
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    );
  }

  it('shows MCP Server install option when mcp_install_enabled is true', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve(successResponse({ flags: { mcp_install_enabled: true } }));
      }
      return Promise.resolve(successResponse(MOCK_SKILL_DETAIL));
    });

    render(<SkillDetailView />, { wrapper: detailWrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Install'));

    expect(screen.getByText('Claude Code CLI')).toBeInTheDocument();
    expect(screen.getByText('MCP Server')).toBeInTheDocument();
    expect(screen.getByText('Manual Install')).toBeInTheDocument();
  });

  it('hides MCP Server install option when mcp_install_enabled is false', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve(successResponse({ flags: { mcp_install_enabled: false } }));
      }
      return Promise.resolve(successResponse(MOCK_SKILL_DETAIL));
    });

    render(<SkillDetailView />, { wrapper: detailWrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Install'));

    expect(screen.getByText('Claude Code CLI')).toBeInTheDocument();
    expect(screen.queryByText('MCP Server')).not.toBeInTheDocument();
    expect(screen.getByText('Manual Install')).toBeInTheDocument();
  });

  it('hides MCP Server install option when flags endpoint fails (defaults to false)', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) });
      }
      return Promise.resolve(successResponse(MOCK_SKILL_DETAIL));
    });

    render(<SkillDetailView />, { wrapper: detailWrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Install'));

    expect(screen.getByText('Claude Code CLI')).toBeInTheDocument();
    expect(screen.queryByText('MCP Server')).not.toBeInTheDocument();
    expect(screen.getByText('Manual Install')).toBeInTheDocument();
  });
});

// --- #10: Featured skills v2 flag ---

describe('Flag: featured_skills_v2', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  function homeWrapper({ children }: { children: ReactNode }) {
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

  it('adds featured-v2 class and data attribute when flag is true', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve(successResponse({ flags: { featured_skills_v2: true } }));
      }
      return Promise.resolve(successResponse(MOCK_BROWSE_RESPONSE));
    });

    render(<HomeView />, { wrapper: homeWrapper });

    await waitFor(() => {
      expect(screen.getByText('Featured Skills')).toBeInTheDocument();
    });

    const section = screen.getByText('Featured Skills').closest('section');
    expect(section).toHaveAttribute('data-featured-v2', 'true');
    expect(section).toHaveClass('featured-v2');
  });

  it('does not add featured-v2 class when flag is false', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve(successResponse({ flags: { featured_skills_v2: false } }));
      }
      return Promise.resolve(successResponse(MOCK_BROWSE_RESPONSE));
    });

    render(<HomeView />, { wrapper: homeWrapper });

    await waitFor(() => {
      expect(screen.getByText('Featured Skills')).toBeInTheDocument();
    });

    const section = screen.getByText('Featured Skills').closest('section');
    expect(section).toHaveAttribute('data-featured-v2', 'false');
    expect(section).not.toHaveClass('featured-v2');
  });
});
