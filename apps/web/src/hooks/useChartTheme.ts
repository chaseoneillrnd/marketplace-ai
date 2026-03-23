import { useMemo } from 'react';
import { useT } from '../context/ThemeContext';

export function useChartTheme() {
  const C = useT();
  return useMemo(() => ({
    gridStroke: C.border,
    axisStroke: C.muted,
    tooltipBg: C.surface,
    tooltipBorder: C.borderHi,
    tooltipText: C.text,
    activeDot: C.accent,
    seriesColors: {
      installs: C.accent,
      submissions: C.green,
      reviews: C.purple,
      flagged: C.amber,
      rejected: C.red,
      forks: '#22d3ee',
      favorites: '#fb923c',
      views: C.muted,
      comments: '#84cc16',
    },
    gradientOpacity: { start: 0.094, end: 0 },
  }), [C]);
}
