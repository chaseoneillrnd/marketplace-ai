import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminFlagsView } from '../AdminFlagsView';

vi.mock('../../../lib/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { api } from '../../../lib/api';
const mockGet = vi.mocked(api.get);
const mockPatch = vi.mocked(api.patch);
const mockPost = vi.mocked(api.post);
const mockDelete = vi.mocked(api.delete);

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>{children}</ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_FLAGS = [
  {
    key: 'submission.llm_judge_gate2',
    enabled: true,
    description: 'Enable LLM Judge for Gate 2 evaluation',
    division_overrides: null,
  },
  {
    key: 'hitl.revision_tracking',
    enabled: false,
    description: 'Enable revision tracking in HITL queue',
    division_overrides: { 'engineering-org': true },
  },
  {
    key: 'docs.vitepress_portal',
    enabled: false,
    description: 'Enable VitePress documentation portal',
    division_overrides: null,
  },
];

describe('AdminFlagsView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGet.mockResolvedValue(MOCK_FLAGS);
    mockPatch.mockResolvedValue({});
    mockPost.mockResolvedValue({});
    mockDelete.mockResolvedValue(undefined);
  });

  it('renders Feature Flags heading', async () => {
    render(<AdminFlagsView />, { wrapper });
    expect(screen.getByRole('heading', { name: /feature flags/i })).toBeInTheDocument();
  });

  it('has data-testid', async () => {
    render(<AdminFlagsView />, { wrapper });
    expect(screen.getByTestId('admin-flags-view')).toBeInTheDocument();
  });

  it('renders flag list after loading', async () => {
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('submission.llm_judge_gate2')).toBeInTheDocument();
    });
    expect(screen.getByText('hitl.revision_tracking')).toBeInTheDocument();
    expect(screen.getByText('docs.vitepress_portal')).toBeInTheDocument();
  });

  it('shows domain prefix badges', async () => {
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('submission.llm_judge_gate2')).toBeInTheDocument();
    });
    expect(screen.getByText('submission')).toBeInTheDocument();
    expect(screen.getByText('hitl')).toBeInTheDocument();
    expect(screen.getByText('docs')).toBeInTheDocument();
  });

  it('shows ON/OFF pill for each flag', async () => {
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('submission.llm_judge_gate2')).toBeInTheDocument();
    });
    const onButtons = screen.getAllByText('ON');
    const offButtons = screen.getAllByText('OFF');
    expect(onButtons.length).toBe(1);
    expect(offButtons.length).toBe(2);
  });

  it('toggle calls updateFlag', async () => {
    const user = userEvent.setup();
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('submission.llm_judge_gate2')).toBeInTheDocument();
    });
    const toggle = screen.getByTestId('flag-toggle-submission.llm_judge_gate2');
    await user.click(toggle);
    expect(mockPatch).toHaveBeenCalledWith(
      '/api/v1/admin/flags/submission.llm_judge_gate2',
      { enabled: false },
    );
  });

  it('opens detail panel when flag row is clicked', async () => {
    const user = userEvent.setup();
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('submission.llm_judge_gate2')).toBeInTheDocument();
    });
    await user.click(screen.getByTestId('flag-row-submission.llm_judge_gate2'));
    expect(screen.getByTestId('flag-detail-panel')).toBeInTheDocument();
  });

  it('shows create flag modal', async () => {
    const user = userEvent.setup();
    render(<AdminFlagsView />, { wrapper });
    await user.click(screen.getByTestId('create-flag-btn'));
    expect(screen.getByTestId('create-flag-modal')).toBeInTheDocument();
  });

  it('creates a new flag via modal', async () => {
    const user = userEvent.setup();
    render(<AdminFlagsView />, { wrapper });
    await user.click(screen.getByTestId('create-flag-btn'));

    await user.type(screen.getByTestId('create-flag-key'), 'test.new_flag');
    await user.type(screen.getByTestId('create-flag-description'), 'A test flag');
    await user.click(screen.getByTestId('create-flag-submit'));

    expect(mockPost).toHaveBeenCalledWith('/api/v1/admin/flags', {
      key: 'test.new_flag',
      enabled: true,
      description: 'A test flag',
    });
  });

  it('shows description in flag list', async () => {
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('Enable LLM Judge for Gate 2 evaluation')).toBeInTheDocument();
    });
  });

  it('shows division override dots for flags with overrides', async () => {
    render(<AdminFlagsView />, { wrapper });
    await waitFor(() => {
      expect(screen.getByText('hitl.revision_tracking')).toBeInTheDocument();
    });
    // The engineering-org override dot should have a title attribute
    const dot = screen.getByTitle('engineering-org: enabled');
    expect(dot).toBeInTheDocument();
  });
});
