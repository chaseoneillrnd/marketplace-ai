import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);
vi.stubGlobal('location', { href: 'http://localhost:3000/', origin: 'http://localhost:3000' });

import { App } from '../App';

describe('AppShell Accessibility', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ items: [], total: 0, page: 1, per_page: 20, has_more: false }),
    });
  });

  it('renders a skip link with text "Skip to main content"', () => {
    render(<App />);
    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toBeInTheDocument();
    expect(skipLink.tagName).toBe('A');
  });

  it('skip link has href="#main-content"', () => {
    render(<App />);
    const skipLink = screen.getByText('Skip to main content');
    expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  it('renders aria-live polite region (role=status)', () => {
    render(<App />);
    const polite = screen.getByRole('status');
    expect(polite).toBeInTheDocument();
    expect(polite).toHaveAttribute('aria-live', 'polite');
  });

  it('renders aria-live assertive region (role=alert)', () => {
    render(<App />);
    const assertive = screen.getByRole('alert');
    expect(assertive).toBeInTheDocument();
    expect(assertive).toHaveAttribute('aria-live', 'assertive');
  });

  it('main content area has id="main-content"', () => {
    render(<App />);
    const mainContent = document.getElementById('main-content');
    expect(mainContent).toBeInTheDocument();
  });
});
