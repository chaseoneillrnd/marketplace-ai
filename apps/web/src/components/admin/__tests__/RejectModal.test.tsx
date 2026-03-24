import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { RejectModal } from '../RejectModal';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

const defaultProps = {
  open: true,
  onClose: vi.fn(),
  onSubmit: vi.fn(),
  submissionName: 'Bad Skill',
};

describe('RejectModal', () => {
  it('renders dropdown with 6 options plus placeholder', () => {
    render(<RejectModal {...defaultProps} />, { wrapper });
    const select = screen.getByRole('combobox');
    // 6 reason options + 1 placeholder "Select a reason..."
    const options = select.querySelectorAll('option');
    expect(options).toHaveLength(7);
  });

  it('submit button disabled when no reason selected', () => {
    render(<RejectModal {...defaultProps} />, { wrapper });
    const submitBtn = screen.getByRole('button', { name: /reject submission/i });
    expect(submitBtn).toBeDisabled();
  });

  it('submit button enabled when reason (not other) selected without details', async () => {
    render(<RejectModal {...defaultProps} />, { wrapper });
    await userEvent.selectOptions(screen.getByRole('combobox'), 'policy_violation');
    const submitBtn = screen.getByRole('button', { name: /reject submission/i });
    expect(submitBtn).toBeEnabled();
  });

  it('details field required when "other" selected', async () => {
    const user = userEvent.setup();
    render(<RejectModal {...defaultProps} />, { wrapper });
    await user.selectOptions(screen.getByRole('combobox'), 'other');
    // Submit should be disabled without details
    const submitBtn = screen.getByRole('button', { name: /reject submission/i });
    expect(submitBtn).toBeDisabled();
    // Fill details
    const textarea = screen.getByPlaceholderText(/please specify the reason/i);
    fireEvent.change(textarea, { target: { value: 'Custom rejection reason' } });
    expect(submitBtn).toBeEnabled();
  });

  it('onSubmit called with reason and details', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<RejectModal {...defaultProps} onSubmit={onSubmit} />, { wrapper });
    await user.selectOptions(screen.getByRole('combobox'), 'duplicate');
    const textarea = screen.getByPlaceholderText(/additional details/i);
    fireEvent.change(textarea, { target: { value: 'Duplicate of SkillXYZ' } });
    await user.click(screen.getByRole('button', { name: /reject submission/i }));
    expect(onSubmit).toHaveBeenCalledWith({
      reason: 'duplicate',
      details: 'Duplicate of SkillXYZ',
    });
  });

  it('renders title with submission name', () => {
    render(<RejectModal {...defaultProps} />, { wrapper });
    expect(screen.getByText(/Reject — Bad Skill/)).toBeInTheDocument();
  });
});
