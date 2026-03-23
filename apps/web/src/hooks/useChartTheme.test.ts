import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { createElement } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { useChartTheme } from './useChartTheme';
import { DARK } from '../lib/theme';

function wrapper({ children }: { children: ReactNode }) {
  return createElement(ThemeProvider, null, children);
}

describe('useChartTheme', () => {
  it('returns gridStroke matching theme border token', () => {
    const { result } = renderHook(() => useChartTheme(), { wrapper });
    expect(result.current.gridStroke).toBe(DARK.border);
  });

  it('returns seriesColors with all 9 series', () => {
    const { result } = renderHook(() => useChartTheme(), { wrapper });
    const keys = Object.keys(result.current.seriesColors);
    expect(keys).toHaveLength(9);
    expect(keys).toEqual(
      expect.arrayContaining([
        'installs', 'submissions', 'reviews', 'flagged',
        'rejected', 'forks', 'favorites', 'views', 'comments',
      ]),
    );
  });

  it('gradientOpacity.start is 0.094', () => {
    const { result } = renderHook(() => useChartTheme(), { wrapper });
    expect(result.current.gradientOpacity.start).toBe(0.094);
  });

  it('memoizes on theme reference', () => {
    const { result, rerender } = renderHook(() => useChartTheme(), { wrapper });
    const first = result.current;
    rerender();
    expect(result.current).toBe(first);
  });
});
