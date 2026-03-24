import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { ModalShell } from '../ModalShell';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

const defaultProps = {
  open: true,
  onClose: vi.fn(),
  title: 'Test Modal',
  children: <p>Modal body content</p>,
};

describe('ModalShell', () => {
  it('renders when open=true', () => {
    render(<ModalShell {...defaultProps} />, { wrapper });
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
  });

  it('does not render when open=false', () => {
    render(<ModalShell {...defaultProps} open={false} />, { wrapper });
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onClose when escape pressed', async () => {
    const onClose = vi.fn();
    render(<ModalShell {...defaultProps} onClose={onClose} />, { wrapper });
    await userEvent.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop clicked', async () => {
    const onClose = vi.fn();
    render(<ModalShell {...defaultProps} onClose={onClose} />, { wrapper });
    await userEvent.click(screen.getByTestId('modal-shell-backdrop'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders title and children', () => {
    render(<ModalShell {...defaultProps} />, { wrapper });
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal body content')).toBeInTheDocument();
  });

  it('renders footer when provided', () => {
    render(
      <ModalShell {...defaultProps} footer={<button>Save</button>} />,
      { wrapper }
    );
    expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
  });

  it('has aria-modal="true" and role="dialog"', () => {
    render(<ModalShell {...defaultProps} />, { wrapper });
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('renders close X button that calls onClose', async () => {
    const onClose = vi.fn();
    render(<ModalShell {...defaultProps} onClose={onClose} />, { wrapper });
    await userEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
