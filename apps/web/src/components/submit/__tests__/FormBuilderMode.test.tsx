import { describe, it, expect, vi } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { FormBuilderMode } from '../FormBuilderMode';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

const defaultProps = {
  onSubmit: vi.fn(),
  categories: ['coding', 'writing', 'analysis'],
  divisions: ['Engineering', 'Design', 'Product'],
};

describe('FormBuilderMode', () => {
  it('renders with step indicator and step 0', () => {
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    expect(screen.getByTestId('form-builder-mode')).toBeInTheDocument();
    expect(screen.getByTestId('step-indicator')).toBeInTheDocument();
    expect(screen.getByTestId('step-0')).toBeInTheDocument();
  });

  it('shows name and description inputs on step 0', () => {
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    expect(screen.getByTestId('input-name')).toBeInTheDocument();
    expect(screen.getByTestId('input-description')).toBeInTheDocument();
  });

  it('disables Next button when name and description are empty', () => {
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    expect(screen.getByTestId('btn-next')).toBeDisabled();
  });

  it('enables Next button with valid name and description', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    expect(screen.getByTestId('btn-next')).not.toBeDisabled();
  });

  it('navigates from step 0 to step 1', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    await user.click(screen.getByTestId('btn-next'));
    expect(screen.getByTestId('step-1')).toBeInTheDocument();
    expect(screen.getByTestId('input-content')).toBeInTheDocument();
  });

  it('navigates back from step 1 to step 0', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    await user.click(screen.getByTestId('btn-next'));
    await user.click(screen.getByTestId('btn-back'));
    expect(screen.getByTestId('step-0')).toBeInTheDocument();
  });

  it('Back button is disabled on step 0', () => {
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    expect(screen.getByTestId('btn-back')).toBeDisabled();
  });

  it('requires minimum 50 chars content on step 1', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    await user.click(screen.getByTestId('btn-next'));
    await user.type(screen.getByTestId('input-content'), 'Short content');
    expect(screen.getByTestId('btn-next')).toBeDisabled();
  });

  it('enables Next when content is 50+ chars on step 1', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    await user.click(screen.getByTestId('btn-next'));
    await user.type(screen.getByTestId('input-content'), 'a'.repeat(55));
    expect(screen.getByTestId('btn-next')).not.toBeDisabled();
  });

  it('shows category dropdown and divisions on step 2', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    // Go to step 2
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    await user.click(screen.getByTestId('btn-next'));
    await user.type(screen.getByTestId('input-content'), 'a'.repeat(55));
    await user.click(screen.getByTestId('btn-next'));
    expect(screen.getByTestId('step-2')).toBeInTheDocument();
    expect(screen.getByTestId('input-category')).toBeInTheDocument();
    expect(screen.getByTestId('division-Engineering')).toBeInTheDocument();
    expect(screen.getByTestId('input-tags')).toBeInTheDocument();
  });

  it('shows review step with preview and validator on step 3', async () => {
    const user = userEvent.setup();
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    // Navigate to step 3
    await user.type(screen.getByTestId('input-name'), 'My Skill Name');
    await user.type(screen.getByTestId('input-description'), 'A valid description for this skill');
    await user.click(screen.getByTestId('btn-next'));
    await user.type(screen.getByTestId('input-content'), 'a'.repeat(55));
    await user.click(screen.getByTestId('btn-next'));
    await user.click(screen.getByTestId('btn-next'));
    expect(screen.getByTestId('step-3')).toBeInTheDocument();
    expect(screen.getByTestId('front-matter-validator')).toBeInTheDocument();
    expect(screen.getByTestId('skill-preview-panel')).toBeInTheDocument();
    expect(screen.getByTestId('btn-submit')).toBeInTheDocument();
  });

  it('calls onSubmit with correct data when Submit clicked on step 3', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const onSubmit = vi.fn();
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(
      <FormBuilderMode {...defaultProps} onSubmit={onSubmit} />,
      { wrapper }
    );
    // Fill step 0
    await user.type(screen.getByTestId('input-name'), 'My Skill');
    await user.type(screen.getByTestId('input-description'), 'A valid description for testing');
    await user.click(screen.getByTestId('btn-next'));
    // Fill step 1
    const longContent = 'a'.repeat(55);
    await user.type(screen.getByTestId('input-content'), longContent);
    await user.click(screen.getByTestId('btn-next'));
    // Skip step 2
    await user.click(screen.getByTestId('btn-next'));
    // Wait for validator debounce
    await act(async () => {
      vi.advanceTimersByTime(400);
    });
    // Submit
    await user.click(screen.getByTestId('btn-submit'));
    expect(onSubmit).toHaveBeenCalledWith({
      frontMatter: { name: 'My Skill', description: 'A valid description for testing' },
      content: longContent,
    });
    vi.useRealTimers();
  });

  it('renders step indicator with 4 steps', () => {
    render(<FormBuilderMode {...defaultProps} />, { wrapper });
    const indicator = screen.getByTestId('step-indicator');
    expect(indicator).toBeInTheDocument();
    expect(indicator.textContent).toContain('1.');
    expect(indicator.textContent).toContain('2.');
    expect(indicator.textContent).toContain('3.');
    expect(indicator.textContent).toContain('4.');
  });
});
