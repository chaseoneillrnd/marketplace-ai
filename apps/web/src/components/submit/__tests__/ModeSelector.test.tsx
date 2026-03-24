import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { ModeSelector } from '../ModeSelector';

function wrapper({ children }: { children: ReactNode }) {
  return <ThemeProvider>{children}</ThemeProvider>;
}

describe('ModeSelector', () => {
  it('renders three tabs', () => {
    render(<ModeSelector mode="form" onModeChange={() => {}} />, { wrapper });

    expect(screen.getByTestId('mode-tab-form')).toBeDefined();
    expect(screen.getByTestId('mode-tab-upload')).toBeDefined();
    expect(screen.getByTestId('mode-tab-mcp')).toBeDefined();
  });

  it('marks the active tab with aria-selected true', () => {
    render(<ModeSelector mode="upload" onModeChange={() => {}} />, { wrapper });

    expect(screen.getByTestId('mode-tab-upload').getAttribute('aria-selected')).toBe('true');
    expect(screen.getByTestId('mode-tab-form').getAttribute('aria-selected')).toBe('false');
    expect(screen.getByTestId('mode-tab-mcp').getAttribute('aria-selected')).toBe('false');
  });

  it('calls onModeChange when a tab is clicked', async () => {
    const onModeChange = vi.fn();
    const user = userEvent.setup();

    render(<ModeSelector mode="form" onModeChange={onModeChange} />, { wrapper });

    await user.click(screen.getByTestId('mode-tab-upload'));
    expect(onModeChange).toHaveBeenCalledWith('upload');

    await user.click(screen.getByTestId('mode-tab-mcp'));
    expect(onModeChange).toHaveBeenCalledWith('mcp');
  });

  it('displays labels for each mode', () => {
    render(<ModeSelector mode="form" onModeChange={() => {}} />, { wrapper });

    expect(screen.getByText('Guided Form')).toBeDefined();
    expect(screen.getByText('Upload .md')).toBeDefined();
    expect(screen.getByText('MCP Sync')).toBeDefined();
  });

  it('shows Advanced badge on MCP tab', () => {
    render(<ModeSelector mode="form" onModeChange={() => {}} />, { wrapper });

    expect(screen.getByText('Advanced')).toBeDefined();
  });

  it('has tablist role on the container', () => {
    render(<ModeSelector mode="form" onModeChange={() => {}} />, { wrapper });

    expect(screen.getByRole('tablist')).toBeDefined();
  });
});
