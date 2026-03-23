import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { createElement } from 'react';
import { ThemeProvider } from '../../context/ThemeContext';
import { EmptyChart } from './EmptyChart';

function wrapper({ children }: { children: ReactNode }) {
  return createElement(ThemeProvider, null, children);
}

function renderWithTheme(ui: React.ReactElement) {
  return render(ui, { wrapper });
}

describe('EmptyChart', () => {
  it('renders with default label', () => {
    renderWithTheme(createElement(EmptyChart));
    expect(screen.getByTestId('empty-chart')).toBeInTheDocument();
    expect(screen.getByText('No data yet')).toBeInTheDocument();
  });

  it('renders with custom label', () => {
    renderWithTheme(createElement(EmptyChart, { label: 'Custom message' }));
    expect(screen.getByText('Custom message')).toBeInTheDocument();
  });

  it('has dashed border style', () => {
    renderWithTheme(createElement(EmptyChart));
    const el = screen.getByTestId('empty-chart');
    expect(el.style.borderStyle).toBe('dashed');
  });
});
