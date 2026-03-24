import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { RequestChangesModal } from '../RequestChangesModal';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

const defaultProps = {
  open: true,
  onClose: vi.fn(),
  onSubmit: vi.fn(),
  submissionName: 'My Skill',
};

describe('RequestChangesModal', () => {
  it('renders title with submission name', () => {
    render(<RequestChangesModal {...defaultProps} />, { wrapper });
    expect(screen.getByText(/Request Changes — My Skill/)).toBeInTheDocument();
  });

  it('submit button disabled with no flags selected', () => {
    render(<RequestChangesModal {...defaultProps} />, { wrapper });
    const submitBtn = screen.getByRole('button', { name: /request changes/i });
    expect(submitBtn).toBeDisabled();
  });

  it('submit button disabled with <20 char notes', async () => {
    render(<RequestChangesModal {...defaultProps} />, { wrapper });
    // Check one flag
    await userEvent.click(screen.getByLabelText(/Missing or incomplete front matter/));
    // Type short notes
    await userEvent.type(screen.getByPlaceholderText(/describe what changes/i), 'short');
    const submitBtn = screen.getByRole('button', { name: /request changes/i });
    expect(submitBtn).toBeDisabled();
  });

  it('submit button enabled with >=1 flag + >=20 char notes', async () => {
    const user = userEvent.setup();
    render(<RequestChangesModal {...defaultProps} />, { wrapper });
    await user.click(screen.getByLabelText(/Security concern identified/));
    const textarea = screen.getByPlaceholderText(/describe what changes/i);
    fireEvent.change(textarea, { target: { value: 'This needs significant rework for security' } });
    const submitBtn = screen.getByRole('button', { name: /request changes/i });
    expect(submitBtn).toBeEnabled();
  });

  it('onSubmit called with correct flags and notes', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<RequestChangesModal {...defaultProps} onSubmit={onSubmit} />, { wrapper });
    await user.click(screen.getByLabelText(/Missing or incomplete front matter/));
    await user.click(screen.getByLabelText(/Scope too broad/));
    const notesText = 'Please split this skill into smaller focused parts';
    const textarea = screen.getByPlaceholderText(/describe what changes/i);
    fireEvent.change(textarea, { target: { value: notesText } });
    await user.click(screen.getByRole('button', { name: /request changes/i }));
    expect(onSubmit).toHaveBeenCalledWith({
      flags: ['missing_front_matter', 'scope_too_broad'],
      notes: notesText,
    });
  });

  it('renders all 6 flag checkboxes', () => {
    render(<RequestChangesModal {...defaultProps} />, { wrapper });
    expect(screen.getByLabelText(/Missing or incomplete front matter/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Security concern identified/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Scope too broad/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Quality does not meet standards/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Division selection needs adjustment/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Changelog or description update needed/)).toBeInTheDocument();
  });
});
