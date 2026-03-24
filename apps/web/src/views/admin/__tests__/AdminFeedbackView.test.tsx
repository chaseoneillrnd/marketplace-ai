import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminFeedbackView } from '../AdminFeedbackView';

vi.mock('../../../lib/api', () => ({
  api: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

import { api } from '../../../lib/api';
const mockGet = vi.mocked(api.get);
const mockPatch = vi.mocked(api.patch);

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_FEEDBACK = {
  items: [
    {
      id: 'f1',
      category: 'feature_request',
      sentiment: 'positive',
      body: 'Great skill marketplace!',
      upvotes: 5,
      status: 'open',
      skill_name: 'code-review',
      created_at: '2026-03-20T10:00:00Z',
      user_display_name: 'Alice',
    },
    {
      id: 'f2',
      category: 'bug_report',
      sentiment: 'critical',
      body: 'Install button broken',
      upvotes: 12,
      status: 'open',
      skill_name: null,
      created_at: '2026-03-19T08:00:00Z',
      user_display_name: 'Bob',
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

describe('AdminFeedbackView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(MOCK_FEEDBACK);
  });

  it('renders Feedback heading', async () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByRole('heading', { name: /feedback/i })).toBeInTheDocument();
  });

  it('has data-testid', async () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByTestId('admin-feedback-view')).toBeInTheDocument();
  });

  it('shows loading state then content', async () => {
    render(<AdminFeedbackView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Great skill marketplace!')).toBeInTheDocument();
    });
  });

  it('renders category filter chips', async () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Feature Request')).toBeInTheDocument();
    expect(screen.getByText('Bug Report')).toBeInTheDocument();
    expect(screen.getByText('Praise')).toBeInTheDocument();
    expect(screen.getByText('Complaint')).toBeInTheDocument();
  });

  it('renders sentiment filter chips', async () => {
    render(<AdminFeedbackView />, { wrapper });
    expect(screen.getByText('Positive')).toBeInTheDocument();
    expect(screen.getByText('Neutral')).toBeInTheDocument();
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('renders feedback rows with upvote count and status', async () => {
    render(<AdminFeedbackView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Great skill marketplace!')).toBeInTheDocument();
    });
    expect(screen.getByText('Install button broken')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders skill chip when linked', async () => {
    render(<AdminFeedbackView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('code-review')).toBeInTheDocument();
    });
  });

  it('calls archive on button click', async () => {
    const user = userEvent.setup();
    mockPatch.mockResolvedValue({});
    render(<AdminFeedbackView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Great skill marketplace!')).toBeInTheDocument();
    });
    const archiveButtons = screen.getAllByText('Archive');
    await user.click(archiveButtons[0]);
    expect(mockPatch).toHaveBeenCalledWith('/api/v1/admin/feedback/f1/status', { status: 'archived' });
  });

  it('changes category filter on chip click', async () => {
    const user = userEvent.setup();
    render(<AdminFeedbackView />, { wrapper });
    await user.click(screen.getByText('Bug Report'));
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        '/api/v1/admin/feedback',
        expect.objectContaining({ category: 'bug_report' }),
      );
    });
  });
});
