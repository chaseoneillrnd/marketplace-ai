import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AuditLogPanel } from '../AuditLogPanel';

const mockUseAuditLog = vi.fn();

vi.mock('../../../hooks/useAuditLog', () => ({
  useAuditLog: (displayId: string | null) => mockUseAuditLog(displayId),
}));

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('AuditLogPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when displayId is null', () => {
    mockUseAuditLog.mockReturnValue({ entries: [], loading: false, error: null, refresh: vi.fn() });
    const { container } = render(<AuditLogPanel displayId={null} />, { wrapper });
    expect(container.innerHTML).toBe('');
  });

  it('renders loading state', () => {
    mockUseAuditLog.mockReturnValue({ entries: [], loading: true, error: null, refresh: vi.fn() });
    render(<AuditLogPanel displayId="SKL-001" />, { wrapper });
    expect(screen.getByTestId('audit-log-loading')).toBeInTheDocument();
    expect(screen.getByText(/loading activity/i)).toBeInTheDocument();
  });

  it('renders empty state', () => {
    mockUseAuditLog.mockReturnValue({ entries: [], loading: false, error: null, refresh: vi.fn() });
    render(<AuditLogPanel displayId="SKL-001" />, { wrapper });
    expect(screen.getByTestId('audit-log-empty')).toBeInTheDocument();
    expect(screen.getByText(/no activity yet/i)).toBeInTheDocument();
  });

  it('renders error state', () => {
    mockUseAuditLog.mockReturnValue({ entries: [], loading: false, error: 'Network error', refresh: vi.fn() });
    render(<AuditLogPanel displayId="SKL-001" />, { wrapper });
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('renders audit log entries', () => {
    mockUseAuditLog.mockReturnValue({
      entries: [
        {
          id: 'entry-1',
          actor_name: 'Alice',
          action: 'submitted',
          from_status: null,
          to_status: 'pending_review',
          notes: null,
          created_at: '2026-03-20T10:00:00Z',
        },
        {
          id: 'entry-2',
          actor_name: 'Bob Admin',
          action: 'approved',
          from_status: 'pending_review',
          to_status: 'approved',
          notes: 'Looks great!',
          created_at: '2026-03-21T14:30:00Z',
        },
      ],
      loading: false,
      error: null,
      refresh: vi.fn(),
    });
    render(<AuditLogPanel displayId="SKL-001" />, { wrapper });

    const entries = screen.getAllByTestId('audit-log-entry');
    expect(entries).toHaveLength(2);

    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('submitted')).toBeInTheDocument();
    expect(screen.getByText('Bob Admin')).toBeInTheDocument();
    expect(screen.getByText('approved')).toBeInTheDocument();
    expect(screen.getByText('Looks great!')).toBeInTheDocument();
  });

  it('renders status transitions', () => {
    mockUseAuditLog.mockReturnValue({
      entries: [
        {
          id: 'entry-1',
          actor_name: 'Admin',
          action: 'changes_requested',
          from_status: 'pending_review',
          to_status: 'changes_requested',
          notes: 'Fix formatting',
          created_at: '2026-03-20T10:00:00Z',
        },
      ],
      loading: false,
      error: null,
      refresh: vi.fn(),
    });
    render(<AuditLogPanel displayId="SKL-001" />, { wrapper });

    expect(screen.getByText('changes requested')).toBeInTheDocument();
    expect(screen.getByText('Fix formatting')).toBeInTheDocument();
  });

  it('passes displayId to useAuditLog hook', () => {
    mockUseAuditLog.mockReturnValue({ entries: [], loading: false, error: null, refresh: vi.fn() });
    render(<AuditLogPanel displayId="SKL-042" />, { wrapper });
    expect(mockUseAuditLog).toHaveBeenCalledWith('SKL-042');
  });
});
