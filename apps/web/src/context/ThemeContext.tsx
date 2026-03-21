import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { DARK, LIGHT, type Theme } from '../lib/theme';

interface ThemeContextValue {
  theme: Theme;
  isDark: boolean;
  toggle: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

export function useT(): Theme {
  return useTheme().theme;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(true);

  const toggle = useCallback(() => setIsDark((d) => !d), []);
  const theme = isDark ? DARK : LIGHT;

  const value = useMemo(() => ({ theme, isDark, toggle }), [theme, isDark, toggle]);

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
