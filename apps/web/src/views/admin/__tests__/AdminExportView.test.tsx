import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminExportView } from '../AdminExportView';

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

describe('AdminExportView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders Export heading', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByRole('heading', { name: /export/i })).toBeInTheDocument();
  });

  it('has data-testid', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByTestId('admin-export-view')).toBeInTheDocument();
  });

  it('renders scope selector buttons', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByText('Installs')).toBeInTheDocument();
    expect(screen.getByText('Submissions')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
  });

  it('renders format toggle', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
  });

  it('renders date range inputs', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
  });

  it('renders Request Export button', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByText('Request Export')).toBeInTheDocument();
  });

  it('renders rate limit display', () => {
    render(<AdminExportView />, { wrapper });
    expect(screen.getByText(/exports remaining today/i)).toBeInTheDocument();
  });

  it('submits export request on button click', async () => {
    vi.useRealTimers();
    const user = userEvent.setup();
    mockPost.mockResolvedValue({ id: 'exp1', status: 'pending' });
    mockGet.mockResolvedValue({ id: 'exp1', status: 'pending' });
    render(<AdminExportView />, { wrapper });
    await user.click(screen.getByText('Request Export'));
    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/admin/exports',
      expect.objectContaining({ scope: 'installs', format: 'csv' }),
    );
  });

  it('shows processing state after request', async () => {
    vi.useRealTimers();
    const user = userEvent.setup();
    mockPost.mockResolvedValue({ id: 'exp1', status: 'pending' });
    mockGet.mockResolvedValue({ id: 'exp1', status: 'processing' });
    render(<AdminExportView />, { wrapper });
    await user.click(screen.getByText('Request Export'));
    await waitFor(() => {
      expect(screen.getByText(/processing/i)).toBeInTheDocument();
    });
  });
});
