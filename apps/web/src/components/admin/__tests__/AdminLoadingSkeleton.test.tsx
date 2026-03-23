import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminLoadingSkeleton } from '../AdminLoadingSkeleton';

function renderWithProviders() {
  return render(
    <ThemeProvider>
      <AdminLoadingSkeleton />
    </ThemeProvider>,
  );
}

describe('AdminLoadingSkeleton', () => {
  it('renders sidebar skeleton', () => {
    renderWithProviders();
    expect(screen.getByTestId('admin-loading-sidebar')).toBeTruthy();
  });

  it('renders content skeleton', () => {
    renderWithProviders();
    expect(screen.getByTestId('admin-loading-content')).toBeTruthy();
  });

  it('renders at least 3 pulsing bars', () => {
    renderWithProviders();
    const bars = screen.getAllByTestId('admin-loading-bar');
    expect(bars.length).toBeGreaterThanOrEqual(3);
  });
});
