---
name: theme-system-builder
description: Use when working with the light/dark theme system
---

# Theme System Builder

## ThemeContext

```tsx
// apps/web/src/context/ThemeContext.tsx
const ThemeContext = createContext({ theme: 'dark', toggle: () => {} });

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');
  const toggle = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };
  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}
```

## CSS Variables

```css
[data-theme="dark"] { --bg: #0c1825; --text: #ddeaf7; --border: #1e3248; }
[data-theme="light"] { --bg: #ffffff; --text: #1a1a1a; --border: #e0e0e0; }
```

## Design Tokens

See `design/tokens.json` for spacing, colors, typography values.

## References

- Theme context: `apps/web/src/context/` or `apps/web/src/lib/theme.ts`
- Design tokens: `design/tokens.json`
- Style guide: `design/style-guide.md`
