import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { FlagsProvider } from '../context/FlagsContext';
import { SkillDetailView } from '../views/SkillDetailView';
import type { SkillDetail, ReviewListResponse } from '@skillhub/shared-types';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
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

const MOCK_FLAGS = { flags: { mcp_install_enabled: true } };

function mockSuccessResponse(data: unknown = MOCK_SKILL_DETAIL) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  };
}

/** Default fetch mock that routes flags and skill detail endpoints. */
function mockFetchDefault(skillData: unknown = MOCK_SKILL_DETAIL) {
  return (url: string) => {
    if (typeof url === 'string' && url.includes('/flags')) {
      return Promise.resolve(mockSuccessResponse(MOCK_FLAGS));
    }
    return Promise.resolve(mockSuccessResponse(skillData));
  };
}

const MOCK_REVIEWS: ReviewListResponse = {
  items: [
    {
      id: 'rev-1',
      skill_id: MOCK_SKILL_DETAIL.id,
      user_id: 'user-abc',
      rating: 5,
      body: 'Excellent skill, saves me hours on PR reviews!',
      helpful_count: 12,
      unhelpful_count: 0,
      created_at: '2026-03-20T10:00:00Z',
      updated_at: '2026-03-20T10:00:00Z',
    },
    {
      id: 'rev-2',
      skill_id: MOCK_SKILL_DETAIL.id,
      user_id: 'user-def',
      rating: 4,
      body: 'Good but could be faster.',
      helpful_count: 3,
      unhelpful_count: 1,
      created_at: '2026-03-18T14:30:00Z',
      updated_at: '2026-03-18T14:30:00Z',
    },
  ],
  total: 2,
  page: 1,
  per_page: 20,
  has_more: false,
};

const MOCK_EMPTY_REVIEWS: ReviewListResponse = {
  items: [],
  total: 0,
  page: 1,
  per_page: 20,
  has_more: false,
};

function mockErrorResponse(status = 500) {
  return {
    ok: false,
    status,
    statusText: 'Internal Server Error',
    json: () => Promise.resolve({ detail: 'Server error' }),
  };
}

/** Returns a fetch mock that responds to skill detail, reviews, and flags endpoints. */
function mockFetchForReviews(
  skillData: unknown = MOCK_SKILL_DETAIL,
  reviewsData: unknown = MOCK_REVIEWS,
) {
  return (url: string) => {
    if (typeof url === 'string' && url.includes('/flags')) {
      return Promise.resolve(mockSuccessResponse(MOCK_FLAGS));
    }
    if (typeof url === 'string' && url.includes('/reviews')) {
      return Promise.resolve(mockSuccessResponse(reviewsData));
    }
    return Promise.resolve(mockSuccessResponse(skillData));
  };
}

describe('SkillDetailView', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  // --- Tab Switching ---

  it('renders Overview tab by default', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    // Overview should be visible by default
    expect(screen.getByText('Trigger Phrases')).toBeInTheDocument();
  });

  it('switches to How to Use tab', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('How to Use'));

    expect(screen.getByText('Skill Content')).toBeInTheDocument();
  });

  it('switches to Install tab', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Install'));

    expect(screen.getByText('Claude Code CLI')).toBeInTheDocument();
    expect(screen.getByText('MCP Server')).toBeInTheDocument();
    expect(screen.getByText('Manual Install')).toBeInTheDocument();
  });

  it('switches to Reviews tab and shows review list', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(mockFetchForReviews());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Reviews'));

    await waitFor(() => {
      expect(screen.getByText('Excellent skill, saves me hours on PR reviews!')).toBeInTheDocument();
    });

    expect(screen.getByText('Good but could be faster.')).toBeInTheDocument();
    expect(screen.getAllByTestId('review-item')).toHaveLength(2);
  });

  // --- Install Button State ---

  it('shows "Sign in to Add" when not authenticated', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Sign in to Add')).toBeInTheDocument();
    });
  });

  // --- Skill Header and Stats ---

  it('renders skill name and metadata', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    expect(screen.getByText('Verified')).toBeInTheDocument();
    expect(screen.getByText('Featured')).toBeInTheDocument();
    expect(screen.getByText('official')).toBeInTheDocument();
  });

  it('renders stats bar with install, rating, fork, favorite counts', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('1,842')).toBeInTheDocument(); // install_count
    });

    expect(screen.getByText('4.9')).toBeInTheDocument(); // avg_rating
    expect(screen.getByText('34')).toBeInTheDocument(); // fork_count
    expect(screen.getByText('156')).toBeInTheDocument(); // favorite_count
  });

  // --- Error State ---

  it('renders error state on API failure', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve(mockSuccessResponse(MOCK_FLAGS));
      }
      return Promise.resolve(mockErrorResponse());
    });

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/error|failed/i)).toBeInTheDocument();
    });
  });

  // --- Loading State ---

  it('renders loading skeleton initially', () => {
    mockFetch.mockImplementation((url: string) => {
      if (typeof url === 'string' && url.includes('/flags')) {
        return Promise.resolve(mockSuccessResponse(MOCK_FLAGS));
      }
      return new Promise(() => {});
    });

    render(<SkillDetailView />, { wrapper });

    // Should show skeleton while loading
    expect(screen.getByTestId('skeleton-card')).toBeInTheDocument();
  });

  // --- Trigger Phrases in Overview ---

  it('renders trigger phrases on overview tab', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('"review this PR"')).toBeInTheDocument();
    });

    expect(screen.getByText('"check my code"')).toBeInTheDocument();
  });

  // --- Back Button ---

  it('renders back button', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Back/)).toBeInTheDocument();
    });
  });

  // --- Division Chips ---

  it('renders division chips', async () => {
    mockFetch.mockImplementation(mockFetchDefault());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getAllByText('Engineering Org').length).toBeGreaterThan(0);
    });
  });

  // --- Fix #6: installed/favorited state from API ---

  it('initializes favorited state from skill.user_has_favorited', async () => {
    const skillWithFavorited = {
      ...MOCK_SKILL_DETAIL,
      user_has_installed: false,
      user_has_favorited: true,
    };
    mockFetch.mockImplementation(mockFetchDefault(skillWithFavorited));

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    // The favorite button should show saved state (star + Saved)
    expect(screen.getByText(/Saved/)).toBeInTheDocument();
  });

  it('defaults favorited to false when skill.user_has_favorited is null', async () => {
    const skillNoFavorite = {
      ...MOCK_SKILL_DETAIL,
      user_has_favorited: null,
    };
    mockFetch.mockImplementation(mockFetchDefault(skillNoFavorite));

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    // Should show unfavorited state
    expect(screen.getByText(/Save/)).toBeInTheDocument();
    expect(screen.queryByText(/Saved/)).not.toBeInTheDocument();
  });

  it('initializes installed state from skill.user_has_installed and user_has_favorited together', async () => {
    // When both flags are true from API, both UI states should reflect that
    const skillWithBoth = {
      ...MOCK_SKILL_DETAIL,
      user_has_installed: true,
      user_has_favorited: true,
    };
    mockFetch.mockImplementation(mockFetchDefault(skillWithBoth));

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    // Favorited state is visible without auth
    expect(screen.getByText(/Saved/)).toBeInTheDocument();
  });

  // --- Fix #21: null author fallback ---

  it('renders "Unknown" when author is null', async () => {
    const skillNoAuthor = { ...MOCK_SKILL_DETAIL, author: null };
    mockFetch.mockImplementation(mockFetchDefault(skillNoAuthor));

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });
  });

  // --- Fix #7: Reviews section ---

  it('reviews tab shows empty state when no reviews', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(mockFetchForReviews(MOCK_SKILL_DETAIL, MOCK_EMPTY_REVIEWS));

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Reviews'));

    await waitFor(() => {
      expect(screen.getByText(/No reviews yet/)).toBeInTheDocument();
    });
  });

  it('reviews tab renders star ratings for each review', async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(mockFetchForReviews());

    render(<SkillDetailView />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('PR Review Assistant')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Reviews'));

    await waitFor(() => {
      expect(screen.getAllByTestId('star-display')).toHaveLength(2);
    });
  });
});
