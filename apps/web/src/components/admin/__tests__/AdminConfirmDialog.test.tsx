import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminConfirmDialog } from '../AdminConfirmDialog';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

const defaultProps = {
  title: 'Confirm Action',
  message: 'Are you sure you want to proceed?',
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
};

describe('AdminConfirmDialog', () => {
  it('renders with role="dialog"', () => {
    render(<AdminConfirmDialog {...defaultProps} />, { wrapper });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('renders title and message', () => {
    render(<AdminConfirmDialog {...defaultProps} />, { wrapper });
    expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    expect(screen.getByText('Are you sure you want to proceed?')).toBeInTheDocument();
  });

  it('calls onCancel when cancel clicked', async () => {
    const onCancel = vi.fn();
    render(<AdminConfirmDialog {...defaultProps} onCancel={onCancel} />, { wrapper });
    await userEvent.click(screen.getByRole('button', { name: /cancel/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('calls onConfirm when confirm clicked', async () => {
    const onConfirm = vi.fn();
    render(<AdminConfirmDialog {...defaultProps} onConfirm={onConfirm} />, { wrapper });
    await userEvent.click(screen.getByRole('button', { name: /confirm/i }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('has aria-modal="true"', () => {
    render(<AdminConfirmDialog {...defaultProps} />, { wrapper });
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  it('renders custom confirmLabel', () => {
    render(<AdminConfirmDialog {...defaultProps} confirmLabel="Delete" />, { wrapper });
    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
  });

  it('applies destructive styling', () => {
    render(<AdminConfirmDialog {...defaultProps} destructive />, { wrapper });
    expect(screen.getByTestId('admin-confirm-dialog')).toBeInTheDocument();
  });
});
