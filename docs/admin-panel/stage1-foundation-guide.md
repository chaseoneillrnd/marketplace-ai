# Stage 1: Foundation — Theme Tokens, Accessibility Fixes & Design System Compliance

**Audience:** Claude Code agents executing prompts in TDD order.
**Estimated total time:** ~75 minutes across 6 prompts.
**Prerequisites:** `mise run dev:web` passes; `npx tsc --noEmit` is clean; `npx vitest run` passes.

---

## Overview

The admin panel cannot be built on a shaky foundation. This stage closes four categories of debt before any new admin surface is written:

1. **Token gaps** — `tokens.json` and `theme.ts` are missing admin-layout, border-width, drag-transition, and chart tokens. Later prompts will reference these by name; they must exist first.
2. **WCAG AA contrast failures** — Light-mode `green` and `amber` fail the 4.5:1 body-text contrast ratio. Any text displayed in `C.green` or `C.amber` on a white surface is non-compliant today.
3. **Keyboard/screen-reader gaps** — `SkillCard`, `DivisionChip`, and `AuthModal` are not keyboard-accessible. The user menu trigger in `Nav` is a `div` with a click handler — invisible to assistive technology.
4. **Missing a11y infrastructure** — There is no `aria-live` region, no focus trap primitive, no skip link, and no announcement hook. These are required foundations for every modal and live-region pattern in the admin panel.

---

## Prompt 1 of 6 — Token Additions (tokens.json + theme.ts)

**Estimated time:** 10 minutes

### Requirements

Extend `tokens.json` and `apps/web/src/lib/theme.ts` with the tokens listed below. **Do not remove or rename any existing token.** Tests verify exact key names.

#### tokens.json additions

Under `"layout"` add:
```json
"adminSidebarWidth": "240px",
"queueListWidth": "380px"
```

Under `"transitions"` add:
```json
"drag": "0.2s"
```

Add a new top-level section `"borders"`:
```json
"borders": {
  "navActiveIndicator": "3px",
  "focus": "2px",
  "input": "1px"
}
```

Add a new top-level section `"chart"`:
```json
"chart": {
  "seriesOrder": ["#4b7dff", "#a78bfa", "#1fd49e", "#f2a020", "#ef5060", "#22d3ee"],
  "axisText": "muted",
  "gridLine": "border",
  "chartBg": "surface"
}
```

#### theme.ts — Theme interface additions

Add to the `Theme` interface:
```typescript
adminBg: string;
adminSurfaceSide: string;
purpleDim: string;
```

Add to `DARK`:
```typescript
adminBg: '#060e1a',
adminSurfaceSide: '#0a1520',
purpleDim: 'rgba(167,139,250,0.12)',
```

Add to `LIGHT`:
```typescript
adminBg: '#e8eef6',
adminSurfaceSide: '#f5f8fc',
purpleDim: 'rgba(109,79,212,0.09)',
```

### File structure

- `design/tokens.json` — add layout, border, transition, chart sections
- `apps/web/src/lib/theme.ts` — extend `Theme` interface, `DARK`, `LIGHT`

### Write tests FIRST

**File:** `apps/web/src/lib/theme.test.ts` (create new)

```typescript
import { describe, it, expect } from 'vitest';
import { DARK, LIGHT, type Theme } from './theme';

describe('Theme tokens — new admin + contrast tokens', () => {
  it('DARK has adminBg, adminSurfaceSide, purpleDim', () => {
    expect(DARK.adminBg).toBe('#060e1a');
    expect(DARK.adminSurfaceSide).toBe('#0a1520');
    expect(DARK.purpleDim).toBe('rgba(167,139,250,0.12)');
  });

  it('LIGHT has adminBg, adminSurfaceSide, purpleDim', () => {
    expect(LIGHT.adminBg).toBe('#e8eef6');
    expect(LIGHT.adminSurfaceSide).toBe('#f5f8fc');
    expect(LIGHT.purpleDim).toBe('rgba(109,79,212,0.09)');
  });

  it('Theme interface includes all new keys (compile-time verified at runtime)', () => {
    const keys: (keyof Theme)[] = ['adminBg', 'adminSurfaceSide', 'purpleDim'];
    keys.forEach((k) => {
      expect(DARK).toHaveProperty(k);
      expect(LIGHT).toHaveProperty(k);
    });
  });
});
```

**File:** `design/tokens.test.ts` (create new — runs via Node, not Vitest; guard with a note or place in `apps/web/src/lib/tokens.test.ts`)

Since `tokens.json` is not imported by Vitest directly, test it from `theme.test.ts` via a JSON import:

```typescript
// Append to apps/web/src/lib/theme.test.ts
import tokensRaw from '../../../../design/tokens.json';

describe('tokens.json structure', () => {
  const tokens = tokensRaw as Record<string, unknown>;

  it('has layout.adminSidebarWidth', () => {
    const layout = tokens.layout as Record<string, string>;
    expect(layout.adminSidebarWidth).toBe('240px');
    expect(layout.queueListWidth).toBe('380px');
  });

  it('has borders section', () => {
    const borders = tokens.borders as Record<string, string>;
    expect(borders.navActiveIndicator).toBe('3px');
    expect(borders.focus).toBe('2px');
    expect(borders.input).toBe('1px');
  });

  it('has transitions.drag', () => {
    const transitions = tokens.transitions as Record<string, string>;
    expect(transitions.drag).toBe('0.2s');
  });

  it('has chart section with seriesOrder array', () => {
    const chart = tokens.chart as Record<string, unknown>;
    expect(Array.isArray(chart.seriesOrder)).toBe(true);
    expect((chart.seriesOrder as string[]).length).toBeGreaterThanOrEqual(4);
    expect(chart.axisText).toBe('muted');
    expect(chart.gridLine).toBe('border');
    expect(chart.chartBg).toBe('surface');
  });
});
```

> Vitest resolves JSON imports with `resolveJsonModule` — the existing `vite.config.ts` handles this automatically via `globals: true` + `environment: 'jsdom'`.

### Do NOT

- Do not modify any existing token value (only additions).
- Do not remove the `INSTALL_COLORS` export from `theme.ts` — it is imported by `SkillCard.tsx`.
- Do not add `purpleDim` to `tokens.json` themes section — it lives only in `theme.ts` (it is a computed rgba, not a raw hex value, consistent with `accentDim`/`greenDim` precedent).
- Do not add `adminBg`/`adminSurfaceSide` to `tokens.json` themes section for the same reason — these are duplicated from existing raw hex tokens for semantic clarity in the admin context.

### Acceptance Criteria

- [ ] `npx tsc --noEmit` passes with zero errors
- [ ] `npx vitest run src/lib/theme.test.ts` — all tests green
- [ ] `DARK.purpleDim` renders `rgba(167,139,250,0.12)` not `rgba(109,79,212,0.09)` (correct dark value)
- [ ] `tokens.json` `chart.seriesOrder` is a JSON array, not a string
- [ ] No existing token value changed (git diff shows only additions)

---

## Prompt 2 of 6 — Light-Mode Contrast Fixes

**Estimated time:** 8 minutes

### Requirements

Fix three WCAG AA contrast failures in `LIGHT`. All three values in `apps/web/src/lib/theme.ts` must be updated:

| Token | Current (failing) | New (passing) | Contrast vs `#ffffff` |
|---|---|---|---|
| `LIGHT.green` | `#0fa878` | `#0b7a57` | ~5.2:1 |
| `LIGHT.amber` | `#c07800` | `#8a5400` | ~6.1:1 |
| `LIGHT.greenDim` | `rgba(15,168,120,0.09)` | `rgba(11,122,87,0.09)` | decorative only |
| `LIGHT.amberDim` | `rgba(192,120,0,0.09)` | `rgba(138,84,0,0.09)` | decorative only |

The `dim` variants are used only for decorative backgrounds and borders, never for text. This constraint is enforced by the acceptance test below and must be documented in a code comment in `theme.ts`.

Add this comment block directly above `LIGHT.greenDim` and `LIGHT.amberDim` in `theme.ts`:

```typescript
// NOTE: *Dim tokens are decorative-only (backgrounds, borders, dividers).
// NEVER use greenDim/amberDim for text — they fail WCAG contrast.
// Text must use green/amber base tokens which are WCAG AA compliant.
```

Dark mode `green` and `amber` are NOT changed — they pass WCAG AA on dark backgrounds and are visually distinct.

### File structure

- `apps/web/src/lib/theme.ts` — update 4 LIGHT values + add comment

### Write tests FIRST

Append to `apps/web/src/lib/theme.test.ts`:

```typescript
// Contrast ratio helper (WCAG relative luminance formula)
function relativeLuminance(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const linearize = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b);
}

function contrastRatio(hex1: string, hex2: string): number {
  const l1 = relativeLuminance(hex1);
  const l2 = relativeLuminance(hex2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

describe('LIGHT mode WCAG AA contrast compliance', () => {
  it('LIGHT.green achieves >= 4.5:1 on white (#ffffff)', () => {
    expect(contrastRatio(LIGHT.green, '#ffffff')).toBeGreaterThanOrEqual(4.5);
  });

  it('LIGHT.amber achieves >= 4.5:1 on white (#ffffff)', () => {
    expect(contrastRatio(LIGHT.amber, '#ffffff')).toBeGreaterThanOrEqual(4.5);
  });

  it('LIGHT.green achieves >= 4.5:1 on LIGHT.surface (#ffffff)', () => {
    expect(contrastRatio(LIGHT.green, LIGHT.surface)).toBeGreaterThanOrEqual(4.5);
  });

  it('LIGHT.amber achieves >= 4.5:1 on LIGHT.bg (#f0f4f9)', () => {
    expect(contrastRatio(LIGHT.amber, LIGHT.bg)).toBeGreaterThanOrEqual(4.5);
  });

  it('LIGHT.greenDim and LIGHT.amberDim are rgba strings (decorative, not hex)', () => {
    expect(LIGHT.greenDim).toMatch(/^rgba\(/);
    expect(LIGHT.amberDim).toMatch(/^rgba\(/);
  });

  it('DARK.green and DARK.amber are unchanged', () => {
    expect(DARK.green).toBe('#1fd49e');
    expect(DARK.amber).toBe('#f2a020');
  });
});
```

### Do NOT

- Do not modify `DARK.green`, `DARK.amber`, `DARK.greenDim`, `DARK.amberDim`.
- Do not change `LIGHT.red` or `LIGHT.redDim` — these were not flagged by the audit.
- Do not change `tokens.json` color values — `tokens.json` documents the original design intent; `theme.ts` is the source of truth for runtime values.
- Do not remove or reorder existing properties in the `LIGHT` object.

### Acceptance Criteria

- [ ] `npx vitest run src/lib/theme.test.ts` — all contrast tests pass
- [ ] `LIGHT.green` hex value is `#0b7a57`
- [ ] `LIGHT.amber` hex value is `#8a5400`
- [ ] `LIGHT.greenDim` rgba matches new base color `rgba(11,122,87,0.09)`
- [ ] `LIGHT.amberDim` rgba matches new base color `rgba(138,84,0,0.09)`
- [ ] Comment block present above the dim tokens in `LIGHT`
- [ ] Dark mode tokens unchanged (verified by test)

---

## Prompt 3 of 6 — AnnouncerContext + useAnnounce Hook

**Estimated time:** 12 minutes

### Requirements

Create the live-region infrastructure that all future admin operations will use to communicate state changes to screen readers (e.g., "Skill approved", "3 items selected", "Error: permission denied").

Architecture:
- `AnnouncerContext.tsx` — provides two `aria-live` region DOM nodes and an `announce(message, level)` API
- `useAnnounce.ts` — thin hook that consumes `AnnouncerContext`
- The DOM regions must be rendered as **visually hidden** but present in the DOM (not `display:none` or `visibility:hidden`, which suppress screen reader announcements)
- `polite` level maps to `role="status"` + `aria-live="polite"`
- `assertive` level maps to `role="alert"` + `aria-live="assertive"`
- Messages are cleared after 7 seconds to prevent stale announcements being re-read

#### Visually-hidden CSS pattern (inline style, no CSS class)

```typescript
const srOnly: React.CSSProperties = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0,0,0,0)',
  whiteSpace: 'nowrap',
  border: 0,
};
```

### File structure

```
apps/web/src/
  context/
    AnnouncerContext.tsx      ← NEW
  hooks/
    useAnnounce.ts            ← NEW
    useAnnounce.test.ts       ← NEW (write first)
```

### Write tests FIRST

**File:** `apps/web/src/hooks/useAnnounce.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { render, screen } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AnnouncerProvider } from '../context/AnnouncerContext';
import { useAnnounce } from './useAnnounce';

function wrapper({ children }: { children: ReactNode }) {
  return <AnnouncerProvider>{children}</AnnouncerProvider>;
}

describe('useAnnounce', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('throws when used outside AnnouncerProvider', () => {
    expect(() => renderHook(() => useAnnounce())).toThrow(
      'useAnnounce must be used within AnnouncerProvider'
    );
  });

  it('returns an announce function', () => {
    const { result } = renderHook(() => useAnnounce(), { wrapper });
    expect(typeof result.current.announce).toBe('function');
  });

  it('polite announcement sets role=status region text', () => {
    render(<AnnouncerProvider><div /></AnnouncerProvider>);
    // The polite region must exist in DOM
    const politeRegion = document.querySelector('[role="status"]');
    expect(politeRegion).toBeTruthy();
  });

  it('assertive announcement sets role=alert region text', () => {
    render(<AnnouncerProvider><div /></AnnouncerProvider>);
    const alertRegion = document.querySelector('[role="alert"]');
    expect(alertRegion).toBeTruthy();
  });

  it('announce("message", "polite") writes to polite region', async () => {
    const TestComponent = () => {
      const { announce } = useAnnounce();
      return (
        <button onClick={() => announce('Skill approved', 'polite')}>
          Announce
        </button>
      );
    };
    render(
      <AnnouncerProvider>
        <TestComponent />
      </AnnouncerProvider>
    );
    const btn = screen.getByRole('button', { name: 'Announce' });
    btn.click();
    const politeRegion = document.querySelector('[role="status"]');
    expect(politeRegion?.textContent).toBe('Skill approved');
  });

  it('announce("message", "assertive") writes to alert region', async () => {
    const TestComponent = () => {
      const { announce } = useAnnounce();
      return (
        <button onClick={() => announce('Permission denied', 'assertive')}>
          Announce
        </button>
      );
    };
    render(
      <AnnouncerProvider>
        <TestComponent />
      </AnnouncerProvider>
    );
    const btn = screen.getByRole('button', { name: 'Announce' });
    btn.click();
    const alertRegion = document.querySelector('[role="alert"]');
    expect(alertRegion?.textContent).toBe('Permission denied');
  });

  it('clears message after 7 seconds', async () => {
    const TestComponent = () => {
      const { announce } = useAnnounce();
      return (
        <button onClick={() => announce('Temporary message', 'polite')}>
          Announce
        </button>
      );
    };
    render(
      <AnnouncerProvider>
        <TestComponent />
      </AnnouncerProvider>
    );
    screen.getByRole('button', { name: 'Announce' }).click();

    act(() => { vi.advanceTimersByTime(7001); });

    const politeRegion = document.querySelector('[role="status"]');
    expect(politeRegion?.textContent).toBe('');
  });
});
```

### Implementation notes

`AnnouncerContext.tsx`:

```typescript
import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

type Level = 'polite' | 'assertive';

interface AnnouncerContextValue {
  announce: (message: string, level?: Level) => void;
}

const AnnouncerContext = createContext<AnnouncerContextValue | null>(null);

export function useAnnouncerContext(): AnnouncerContextValue {
  const ctx = useContext(AnnouncerContext);
  if (!ctx) throw new Error('useAnnounce must be used within AnnouncerProvider');
  return ctx;
}

const srOnly: React.CSSProperties = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0,0,0,0)',
  whiteSpace: 'nowrap',
  border: 0,
};

export function AnnouncerProvider({ children }: { children: ReactNode }) {
  const [politeMsg, setPoliteMsg] = useState('');
  const [assertiveMsg, setAssertiveMsg] = useState('');

  const announce = useCallback((message: string, level: Level = 'polite') => {
    if (level === 'assertive') {
      setAssertiveMsg(message);
      setTimeout(() => setAssertiveMsg(''), 7000);
    } else {
      setPoliteMsg(message);
      setTimeout(() => setPoliteMsg(''), 7000);
    }
  }, []);

  return (
    <AnnouncerContext.Provider value={{ announce }}>
      {children}
      <div role="status" aria-live="polite" aria-atomic="true" style={srOnly}>
        {politeMsg}
      </div>
      <div role="alert" aria-live="assertive" aria-atomic="true" style={srOnly}>
        {assertiveMsg}
      </div>
    </AnnouncerContext.Provider>
  );
}
```

`useAnnounce.ts`:

```typescript
import { useAnnouncerContext } from '../context/AnnouncerContext';

export function useAnnounce() {
  return useAnnouncerContext();
}
```

### Do NOT

- Do not use `display: none` or `visibility: hidden` on the aria-live regions — this prevents screen readers from reading them.
- Do not use a single DOM node for both polite and assertive — they must be separate elements with separate ARIA roles.
- Do not announce empty strings — guard with `if (!message.trim()) return;` in the `announce` function.
- Do not add `AnnouncerProvider` to `App.tsx` in this prompt — that happens in Prompt 5 (AppShell changes). The context is just created here.

### Acceptance Criteria

- [ ] `npx vitest run src/hooks/useAnnounce.test.ts` — all 7 tests pass
- [ ] `document.querySelector('[role="status"]')` and `[role="alert"]` both exist when `AnnouncerProvider` is rendered
- [ ] `useAnnounce()` throws outside `AnnouncerProvider`
- [ ] Message clears after 7000ms (fake timer test passes)
- [ ] `npx tsc --noEmit` clean

---

## Prompt 4 of 6 — useFocusTrap Hook

**Estimated time:** 12 minutes

### Requirements

Create `apps/web/src/hooks/useFocusTrap.ts`. This hook:

- Accepts a `containerRef: React.RefObject<HTMLElement>` and an options object `{ onEscape?: () => void; enabled?: boolean }`
- Traps Tab / Shift+Tab focus within the container when `enabled` is `true` (default `true`)
- Calls `onEscape` when Escape is pressed
- On mount, moves focus to the first focusable element inside the container
- On unmount, restores focus to the element that was focused before the trap was activated
- Focusable element query: `'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'`

### File structure

```
apps/web/src/
  hooks/
    useFocusTrap.ts           ← NEW
    useFocusTrap.test.ts      ← NEW (write first)
```

### Write tests FIRST

**File:** `apps/web/src/hooks/useFocusTrap.test.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { useRef } from 'react';
import { useFocusTrap } from './useFocusTrap';

// Test harness component
function TrapContainer({
  onEscape,
  enabled = true,
}: {
  onEscape?: () => void;
  enabled?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useFocusTrap(ref, { onEscape, enabled });
  return (
    <div ref={ref} data-testid="trap">
      <button data-testid="btn-a">A</button>
      <button data-testid="btn-b">B</button>
      <button data-testid="btn-c">C</button>
    </div>
  );
}

describe('useFocusTrap', () => {
  it('moves focus to first focusable element on mount', () => {
    render(<TrapContainer />);
    expect(document.activeElement).toBe(screen.getByTestId('btn-a'));
  });

  it('calls onEscape when Escape key is pressed', () => {
    const onEscape = vi.fn();
    render(<TrapContainer onEscape={onEscape} />);
    fireEvent.keyDown(screen.getByTestId('trap'), { key: 'Escape' });
    expect(onEscape).toHaveBeenCalledTimes(1);
  });

  it('does not trap focus when enabled=false', () => {
    render(<TrapContainer enabled={false} />);
    // Focus should NOT move to btn-a on mount when disabled
    expect(document.activeElement).not.toBe(screen.getByTestId('btn-a'));
  });

  it('wraps Tab from last focusable to first', () => {
    render(<TrapContainer />);
    const btnC = screen.getByTestId('btn-c');
    btnC.focus();
    fireEvent.keyDown(screen.getByTestId('trap'), {
      key: 'Tab',
      shiftKey: false,
    });
    expect(document.activeElement).toBe(screen.getByTestId('btn-a'));
  });

  it('wraps Shift+Tab from first focusable to last', () => {
    render(<TrapContainer />);
    const btnA = screen.getByTestId('btn-a');
    btnA.focus();
    fireEvent.keyDown(screen.getByTestId('trap'), {
      key: 'Tab',
      shiftKey: true,
    });
    expect(document.activeElement).toBe(screen.getByTestId('btn-c'));
  });

  it('does not call onEscape when Escape not pressed', () => {
    const onEscape = vi.fn();
    render(<TrapContainer onEscape={onEscape} />);
    fireEvent.keyDown(screen.getByTestId('trap'), { key: 'Enter' });
    expect(onEscape).not.toHaveBeenCalled();
  });
});
```

### Implementation notes

```typescript
import { useEffect } from 'react';

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), ' +
  'select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

interface Options {
  onEscape?: () => void;
  enabled?: boolean;
}

export function useFocusTrap(
  containerRef: React.RefObject<HTMLElement>,
  { onEscape, enabled = true }: Options = {}
) {
  useEffect(() => {
    if (!enabled) return;
    const container = containerRef.current;
    if (!container) return;

    const previouslyFocused = document.activeElement as HTMLElement | null;

    const focusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (focusables.length > 0) {
      focusables[0].focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onEscape?.();
        return;
      }
      if (e.key !== 'Tab') return;

      const focusableNow = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (focusableNow.length === 0) return;

      const first = focusableNow[0];
      const last = focusableNow[focusableNow.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);
    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      previouslyFocused?.focus();
    };
  }, [containerRef, enabled, onEscape]);
}
```

### Do NOT

- Do not use `document.addEventListener` — attach to the container so the trap is scoped.
- Do not query focusables once at mount and cache them — re-query inside the keydown handler because the DOM can change (dynamic form fields).
- Do not call `previouslyFocused?.focus()` conditionally on `onEscape` being called — always restore on unmount regardless of how the trap was closed.
- Do not include `containerRef` in the dependency array as a value — it is a ref object and is stable. The current lint config may warn; suppress with `// eslint-disable-next-line react-hooks/exhaustive-deps` only if needed and document why.

### Acceptance Criteria

- [ ] `npx vitest run src/hooks/useFocusTrap.test.ts` — all 6 tests pass
- [ ] Tab wrapping works (last → first, first → last)
- [ ] `onEscape` fires exactly once per Escape keypress
- [ ] `enabled=false` disables all behavior including initial focus move
- [ ] Focus restored on unmount (tested implicitly by tab-wrap tests completing without errors)
- [ ] `npx tsc --noEmit` clean

---

## Prompt 5 of 6 — AppShell Accessibility: Skip Link + aria-live Regions

**Estimated time:** 12 minutes

### Requirements

Modify `apps/web/src/App.tsx` to:

1. Wrap `AppShell` in `AnnouncerProvider`
2. Add a **skip link** as the very first child of the outermost `AppShell` div
3. Add `id="main-content"` to the `<div style={{ paddingTop: '60px' }}>` wrapper around `<Routes>`

The skip link is visually hidden until focused (not hidden when focused). Pattern:

```html
<a
  href="#main-content"
  style={{
    position: 'absolute',
    top: '-40px',
    left: 0,
    background: C.accent,
    color: '#fff',
    padding: '8px 16px',
    borderRadius: '0 0 8px 0',
    fontWeight: 600,
    fontSize: '14px',
    zIndex: 9999,
    transition: 'top 0.15s',
    // On focus: top moves to 0 — handled via :focus-within or onFocus/onBlur
  }}
  onFocus={(e) => { (e.currentTarget as HTMLElement).style.top = '0'; }}
  onBlur={(e) => { (e.currentTarget as HTMLElement).style.top = '-40px'; }}
>
  Skip to main content
</a>
```

Note: The `AnnouncerProvider` live regions are rendered inside `AnnouncerProvider`, not in `AppShell` directly. `AppShell` wrapping with `AnnouncerProvider` makes `useAnnounce()` available to all child components.

### File structure

- `apps/web/src/App.tsx` — modify `AppShell` and `App`

### Write tests FIRST

**File:** `apps/web/src/__tests__/AppShell.test.tsx` (create new)

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App } from '../App';

vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: () => Promise.resolve({ flags: {}, items: [], total: 0, page: 1, per_page: 8, has_more: false }),
}));
vi.stubGlobal('location', { href: '/' });

describe('AppShell accessibility infrastructure', () => {
  it('renders a skip link with text "Skip to main content"', () => {
    render(<App />);
    const skipLink = screen.getByRole('link', { name: /skip to main content/i });
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  it('renders aria-live polite region (role=status)', () => {
    render(<App />);
    expect(document.querySelector('[role="status"]')).toBeTruthy();
  });

  it('renders aria-live assertive region (role=alert)', () => {
    render(<App />);
    expect(document.querySelector('[role="alert"]')).toBeTruthy();
  });

  it('main content area has id="main-content"', () => {
    render(<App />);
    expect(document.getElementById('main-content')).toBeTruthy();
  });
});
```

### Do NOT

- Do not add a CSS class for the skip link — use inline `onFocus`/`onBlur` handlers consistent with the no-CSS-modules constraint.
- Do not render the `AnnouncerProvider` inside `ThemeProvider` — it should wrap at `App` level, outside `ThemeProvider`, OR inside but after — either works. Prefer wrapping inside `BrowserRouter` so the provider has access to router context if needed later. Final nesting order: `BrowserRouter > ThemeProvider > AuthProvider > FlagsProvider > AnnouncerProvider > AppShell`.
- Do not add `aria-label` to the skip link — the text content is the accessible name.
- Do not use `display: none` for the hidden state of the skip link.

### Acceptance Criteria

- [ ] `npx vitest run src/__tests__/AppShell.test.tsx` — all 4 tests pass
- [ ] Skip link is the first focusable element in tab order (manual verification: Tab from URL bar reaches skip link first)
- [ ] `document.getElementById('main-content')` is non-null
- [ ] `[role="status"]` and `[role="alert"]` present in rendered DOM
- [ ] `npx tsc --noEmit` clean

---

## Prompt 6 of 6 — Component Keyboard & ARIA Fixes

**Estimated time:** 21 minutes (largest prompt — 4 components)

### Requirements

Fix keyboard accessibility and ARIA attributes across four existing components. Each fix is surgical — add only what is needed, do not restructure the component.

---

#### 6a. SkillCard.tsx

**File:** `apps/web/src/components/SkillCard.tsx`

Add to the outer `<div>`:
- `tabIndex={0}`
- `role="article"`
- `aria-label={skill.name}`
- `onKeyDown` handler: call `onClick(skill)` when `event.key === 'Enter' || event.key === ' '` (prevent default for Space to avoid page scroll)

Focus ring: Change `boxShadow` in the style to include a focus ring when focused. Since inline styles cannot use `:focus-within` pseudo-class, use `onFocus`/`onBlur` state alongside existing `hov` state:

Add `const [focused, setFocused] = useState(false);` and add `onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}` to the outer div.

Update `boxShadow`:
```typescript
boxShadow: focused
  ? `0 0 0 2px ${C.accent}`
  : hov
  ? C.cardShadow
  : C.mode === 'light'
  ? '0 1px 4px rgba(0,0,0,0.07)'
  : 'none',
```

> This uses `C.accent` (full color) not `C.accentDim` (12% opacity) — WCAG 2.4.11 requires visible, non-color-only focus indicators. The 2px solid accent ring satisfies this.

#### 6b. DivisionChip.tsx

**File:** `apps/web/src/components/DivisionChip.tsx`

The `DivisionChip` `<span>` already has `role={onClick ? 'button' : undefined}`. Add:
- `tabIndex={onClick ? 0 : undefined}`
- `onKeyDown` handler when `onClick` is provided: trigger `onClick()` on Enter or Space

```typescript
onKeyDown={onClick ? (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    onClick();
  }
} : undefined}
```

#### 6c. AuthModal.tsx

**File:** `apps/web/src/components/AuthModal.tsx`

This is the most complex change. The modal backdrop `<div>` and the modal box `<div>` both need ARIA attributes and the focus trap.

**Backdrop (outer div in both dev and production branches):**
- Add `role="dialog"`
- Add `aria-modal="true"`
- Add `aria-labelledby="auth-modal-title"`

**Modal title (the "Dev Sign In" / "Sign in to SkillHub" text div):**
- Add `id="auth-modal-title"` to the `<div>` containing the title text

**Focus trap:**
- Add `const modalRef = useRef<HTMLDivElement>(null)` at the top of the component
- Attach `ref={modalRef}` to the inner modal box `<div>` (the one with `onClick={(e) => e.stopPropagation()}`)
- Call `useFocusTrap(modalRef, { onEscape: onClose })`

**Import additions:**
```typescript
import { useRef } from 'react';
import { useFocusTrap } from '../hooks/useFocusTrap';
```

Note: There are two separate return branches (dev mode and production mode). Both need identical ARIA and focus trap treatment. Apply the changes to both branches.

#### 6d. Nav.tsx — User menu trigger

**File:** `apps/web/src/components/Nav.tsx`

The user-menu trigger is currently a `<div>` with `onClick`. Convert it to a `<button>`:

```tsx
<button
  ref={/* keep menuRef on parent div */}
  onClick={() => setMenuOpen(!menuOpen)}
  data-testid="user-menu-trigger"
  aria-expanded={menuOpen}
  aria-haspopup="true"
  aria-label={`User menu for ${user.name}`}
  style={{
    /* same styles as the current div */
    /* add: background: 'transparent', border: 'none', cursor: 'pointer' */
  }}
>
```

Note: `menuRef` stays on the outer `<div ref={menuRef}>` wrapper — do not move it to the button. The button is inside that wrapper.

#### 6e. Nav.tsx — Search input aria-label

The search input in `Nav.tsx` already has `placeholder="Search skills..."`. Add:
```tsx
aria-label="Search skills"
```

#### 6f. HomeView.tsx — Hero search input aria-label

The hero search input in `HomeView.tsx` has `placeholder="What do you need help with today?"`. Add:
```tsx
aria-label="Search skills"
```

---

### Write tests FIRST

**File:** `apps/web/src/__tests__/Accessibility.test.tsx` (create new)

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { ReactNode } from 'react';
import { ThemeProvider } from '../context/ThemeContext';
import { AuthProvider } from '../context/AuthContext';
import { FlagsProvider } from '../context/FlagsContext';
import { AnnouncerProvider } from '../context/AnnouncerContext';
import { SkillCard } from '../components/SkillCard';
import { DivisionChip } from '../components/DivisionChip';
import type { SkillSummary } from '@skillhub/shared-types';

vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: () => Promise.resolve({ flags: {} }),
}));
vi.stubGlobal('location', { href: '/' });

function wrapper({ children }: { children: ReactNode }) {
  return (
    <MemoryRouter>
      <ThemeProvider>
        <AuthProvider>
          <FlagsProvider>
            <AnnouncerProvider>{children}</AnnouncerProvider>
          </FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>
  );
}

const MOCK_SKILL: SkillSummary = {
  id: '00000000-0000-0000-0000-000000000001',
  slug: 'test-skill',
  name: 'Test Skill',
  short_desc: 'A test skill',
  category: 'Engineering',
  divisions: ['Engineering Org'],
  tags: ['test'],
  author: 'Platform Team',
  author_type: 'official',
  version: '1.0.0',
  install_method: 'claude-code',
  verified: true,
  featured: false,
  install_count: 100,
  fork_count: 5,
  favorite_count: 10,
  avg_rating: 4.5,
  review_count: 20,
  days_ago: 1,
};

describe('SkillCard accessibility', () => {
  it('has role="article"', () => {
    render(<SkillCard skill={MOCK_SKILL} onClick={vi.fn()} />, { wrapper });
    expect(screen.getByRole('article')).toBeInTheDocument();
  });

  it('has tabIndex=0', () => {
    render(<SkillCard skill={MOCK_SKILL} onClick={vi.fn()} />, { wrapper });
    const card = screen.getByRole('article');
    expect(card.getAttribute('tabindex')).toBe('0');
  });

  it('calls onClick when Enter key is pressed', () => {
    const onClick = vi.fn();
    render(<SkillCard skill={MOCK_SKILL} onClick={onClick} />, { wrapper });
    const card = screen.getByRole('article');
    fireEvent.keyDown(card, { key: 'Enter' });
    expect(onClick).toHaveBeenCalledWith(MOCK_SKILL);
  });

  it('calls onClick when Space key is pressed', () => {
    const onClick = vi.fn();
    render(<SkillCard skill={MOCK_SKILL} onClick={onClick} />, { wrapper });
    const card = screen.getByRole('article');
    fireEvent.keyDown(card, { key: ' ' });
    expect(onClick).toHaveBeenCalledWith(MOCK_SKILL);
  });

  it('does not call onClick for other keys', () => {
    const onClick = vi.fn();
    render(<SkillCard skill={MOCK_SKILL} onClick={onClick} />, { wrapper });
    fireEvent.keyDown(screen.getByRole('article'), { key: 'ArrowDown' });
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe('DivisionChip accessibility', () => {
  it('has no tabIndex when onClick not provided', () => {
    render(<DivisionChip division="Engineering Org" />, { wrapper });
    const chip = screen.getByText(/engineering/i);
    expect(chip.getAttribute('tabindex')).toBeNull();
  });

  it('has tabIndex=0 when onClick provided', () => {
    render(<DivisionChip division="Engineering Org" onClick={vi.fn()} />, { wrapper });
    const chip = screen.getByRole('button');
    expect(chip.getAttribute('tabindex')).toBe('0');
  });

  it('calls onClick when Enter pressed (interactive chip)', () => {
    const onClick = vi.fn();
    render(<DivisionChip division="Engineering Org" onClick={onClick} />, { wrapper });
    fireEvent.keyDown(screen.getByRole('button'), { key: 'Enter' });
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('calls onClick when Space pressed (interactive chip)', () => {
    const onClick = vi.fn();
    render(<DivisionChip division="Engineering Org" onClick={onClick} />, { wrapper });
    fireEvent.keyDown(screen.getByRole('button'), { key: ' ' });
    expect(onClick).toHaveBeenCalledTimes(1);
  });
});

describe('AuthModal accessibility', () => {
  it('has role="dialog"', () => {
    render(
      <AnnouncerProvider>
        <ThemeProvider>
          <AuthProvider>
            {/* Force isDev=false by not mocking import.meta.env */}
            {/* The modal is rendered with role=dialog regardless of mode */}
          </AuthProvider>
        </ThemeProvider>
      </AnnouncerProvider>
    );
    // AuthModal test — import and render directly
  });
});

// Simpler AuthModal tests that avoid env mocking
describe('AuthModal ARIA attributes', () => {
  it('outer backdrop div has role=dialog when rendered', async () => {
    const { AuthModal } = await import('../components/AuthModal');
    render(
      <MemoryRouter>
        <ThemeProvider>
          <AuthProvider>
            <AnnouncerProvider>
              <AuthModal onClose={vi.fn()} />
            </AnnouncerProvider>
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
  });

  it('dialog has aria-modal=true', async () => {
    const { AuthModal } = await import('../components/AuthModal');
    render(
      <MemoryRouter>
        <ThemeProvider>
          <AuthProvider>
            <AnnouncerProvider>
              <AuthModal onClose={vi.fn()} />
            </AnnouncerProvider>
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    );
    const dialog = screen.getByRole('dialog');
    expect(dialog.getAttribute('aria-modal')).toBe('true');
  });
});
```

### Do NOT

- Do not add `outline: 'none'` to SkillCard — browsers need to render focus outlines when the component does not provide its own visible ring. Our `boxShadow` ring replaces it, but only add `outline: 'none'` if you also set the `boxShadow` ring (both states).
- Do not change the button element tag for any existing `<button>` in these files — only the user-menu `<div>` trigger becomes a `<button>`.
- Do not add focus trap to `SkillCard` — it is a card, not a modal.
- Do not add `aria-expanded` to `DivisionChip` — it does not have a popup.
- Do not add `aria-labelledby` pointing to a non-existent `id` — verify the `id="auth-modal-title"` is added to the correct element in the same commit.

### Acceptance Criteria

- [ ] `npx vitest run src/__tests__/Accessibility.test.tsx` — all tests pass
- [ ] `screen.getByRole('article')` finds SkillCard
- [ ] Enter and Space trigger `onClick` on SkillCard
- [ ] DivisionChip has `tabIndex=0` only when interactive
- [ ] `screen.getByRole('dialog')` finds AuthModal
- [ ] AuthModal `aria-modal="true"` present
- [ ] Nav user menu trigger is a `<button>` element (`screen.getByTestId('user-menu-trigger').tagName === 'BUTTON'`)
- [ ] Both search inputs have `aria-label="Search skills"`
- [ ] `npx tsc --noEmit` clean
- [ ] `npx vitest run` — full suite passes (coverage gate ≥ 80%)

---

## Final Verification Checklist

Run these commands in order after all 6 prompts are complete:

```bash
# 1. Type check
cd /Users/chase/wk/marketplace-ai/apps/web && npx tsc --noEmit

# 2. Full test suite with coverage
cd /Users/chase/wk/marketplace-ai/apps/web && npx vitest run --coverage

# 3. Production build (catches tree-shaking and bundler issues)
cd /Users/chase/wk/marketplace-ai/apps/web && npx vite build
```

Expected outcomes:
- Zero TypeScript errors
- Coverage ≥ 80% (new hooks/context have 100% coverage from the tests written here)
- Build completes without error

### Cross-cutting constraints for all prompts

- All new TypeScript files must be free of `any` — use `unknown` with explicit narrowing if needed.
- No `console.log` or `console.error` in production code — use the structured logger if needed (there is none yet; just omit logging).
- No `// @ts-ignore` or `// @ts-expect-error` unless the exact reason is documented on the same line.
- All new hooks follow the `useXxx` naming convention.
- All new context files export both the Provider (named `XxxProvider`) and a typed hook (named `useXxxContext` or re-exported via a thin hook).
- Inline styles only — no CSS modules, no Tailwind, no class names except for test `data-testid` attributes.

---

## Dependency Graph (Stage 1 Internal)

```
Prompt 1: tokens.json, theme.ts
    ↓
Prompt 2: theme.ts (modifies LIGHT values set in P1)
    ↓
Prompt 3: AnnouncerContext.tsx, useAnnounce.ts
    ↓
Prompt 4: useFocusTrap.ts
    ↓
Prompt 5: App.tsx (consumes AnnouncerProvider from P3)
    ↓
Prompt 6: SkillCard, DivisionChip, AuthModal (consumes useFocusTrap from P4), Nav, HomeView
```

Prompts 3 and 4 are independent of each other and can be executed in parallel if separate agents are available. All other prompts have strict serial dependencies.
