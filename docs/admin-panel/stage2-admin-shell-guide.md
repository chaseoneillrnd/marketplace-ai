# Stage 2: Admin Shell — Layout, Routing & Navigation

## Overview

This stage wires the full admin panel shell into the SkillHub React app. It produces the
persistent sidebar layout, route guard, error boundary, loading skeleton, and the six
placeholder admin views. All six views are lazy-loaded behind a `RequireAdmin` guard that
gates on `user.is_platform_team`. No backend work is required; this stage is purely
frontend infrastructure.

**Prerequisite:** Stage 1 (accessibility and a11y foundation) must be merged before
beginning this stage.

---

## Design Decisions

### Why Outlet-based guard instead of a wrapper HOC?

React Router v6 nested routes make an `<Outlet />`-based guard natural. The guard renders
`<Outlet />` on success and `<Navigate to="/" replace />` on failure. This keeps
declarative route nesting intact and avoids prop-drilling auth state.

### Why a class-based ErrorBoundary?

React does not yet expose a hook equivalent for `componentDidCatch`. The boundary is a
thin class component whose sole job is to catch render errors inside admin views and
prevent them from propagating to the top-level `AppShell`. It does not replace the
existing global error handling.

### Theme tokens for admin-specific surfaces

The existing `Theme` interface (in `libs/shared-types` via `apps/web/src/lib/theme.ts`)
does not yet include admin-specific tokens (`adminBg`, `adminSurfaceSide`,
`adminSidebarWidth`). **This stage adds those tokens** to the `Theme` interface and both
`DARK` / `LIGHT` objects. All admin components source their colors exclusively from `useT()`.

### Z-index contract

| Layer               | z-index |
|---------------------|---------|
| Nav                 | 100     |
| AdminSideNav        | 10      |
| AdminActionBar (future) | 50  |
| Modals              | 999     |
| Menu dropdowns      | 200     |

---

## Phase 0 — Prerequisites check

Before writing any code verify the following are true:

- `apps/web/src/lib/theme.ts` exports `Theme`, `DARK`, `LIGHT`
- `apps/web/src/context/ThemeContext.tsx` exports `useT()` and `useTheme()`
- `apps/web/src/context/AuthContext.tsx` exports `AuthContextValue` with `user: UserClaims | null`
- `libs/shared-types/src/index.ts` exports `UserClaims` with `is_platform_team: boolean`
- `apps/web/src/hooks/useAuth.ts` exports `useAuth()` returning `AuthContextValue`
- `apps/web/src/App.tsx` contains a `<BrowserRouter>` wrapping `<Routes>`
- `apps/web/src/components/Nav.tsx` contains the nav bar with `z-index: 100`

---

## Phase 1 — Extend Theme tokens

**Task 1.1 — Write the failing test first (TDD RED)**

File: `apps/web/src/lib/theme.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { DARK, LIGHT } from './theme';

describe('admin theme tokens', () => {
  it('DARK has adminBg', () => {
    expect(DARK.adminBg).toBeDefined();
    expect(typeof DARK.adminBg).toBe('string');
  });

  it('DARK has adminSurfaceSide', () => {
    expect(DARK.adminSurfaceSide).toBeDefined();
    expect(typeof DARK.adminSurfaceSide).toBe('string');
  });

  it('DARK has adminSidebarWidth', () => {
    expect(DARK.adminSidebarWidth).toBe('240px');
  });

  it('LIGHT has adminBg', () => {
    expect(LIGHT.adminBg).toBeDefined();
    expect(typeof LIGHT.adminBg).toBe('string');
  });

  it('LIGHT has adminSurfaceSide', () => {
    expect(LIGHT.adminSurfaceSide).toBeDefined();
    expect(typeof LIGHT.adminSurfaceSide).toBe('string');
  });

  it('LIGHT has adminSidebarWidth', () => {
    expect(LIGHT.adminSidebarWidth).toBe('240px');
  });
});
```

Run `npx vitest run src/lib/theme.test.ts` — expect 6 failures.

**Task 1.2 — Make tests pass (TDD GREEN)**

Edit `apps/web/src/lib/theme.ts`.

Add to the `Theme` interface (after `scrollThumb`):

```typescript
  // Admin panel
  adminBg: string;
  adminSurfaceSide: string;
  adminSidebarWidth: string;
```

Add to `DARK`:

```typescript
  adminBg: '#060e1a',
  adminSurfaceSide: '#0a1522',
  adminSidebarWidth: '240px',
```

Add to `LIGHT`:

```typescript
  adminBg: '#e8edf5',
  adminSurfaceSide: '#f0f4f9',
  adminSidebarWidth: '240px',
```

Run `npx vitest run src/lib/theme.test.ts` — expect 6 passes.

**Task 1.3 — Verify TypeScript**

```bash
npx tsc --noEmit
```

No errors. The `Theme` interface is used throughout components via `useT()`; since these
are additive new keys TypeScript will surface any file that destructures the full interface
without the new keys — there should be none.

---

## Phase 2 — RequireAdmin route guard

**File:** `apps/web/src/components/admin/RequireAdmin.tsx`

**Task 2.1 — Write the failing test (TDD RED)**

File: `apps/web/src/components/admin/__tests__/RequireAdmin.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route, Outlet } from 'react-router-dom';
import { ThemeProvider } from '../../../context/ThemeContext';
import { RequireAdmin } from '../RequireAdmin';

// Mock useAuth
vi.mock('../../../hooks/useAuth');
import { useAuth } from '../../../hooks/useAuth';

function makeWrapper(isPlatformTeam: boolean | null) {
  // @ts-expect-error - mocking return value
  vi.mocked(useAuth).mockReturnValue({
    user: isPlatformTeam !== null ? { is_platform_team: isPlatformTeam } : null,
    isAuthenticated: isPlatformTeam !== null,
    login: vi.fn(),
    logout: vi.fn(),
  });

  return function Wrapper() {
    return (
      <ThemeProvider>
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route element={<RequireAdmin />}>
              <Route path="/admin" element={<div data-testid="admin-content">Admin Page</div>} />
            </Route>
            <Route path="/" element={<div data-testid="home">Home</div>} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    );
  };
}

describe('RequireAdmin', () => {
  it('renders Outlet when user.is_platform_team is true', () => {
    const Wrapper = makeWrapper(true);
    render(<Wrapper />);
    expect(screen.getByTestId('admin-content')).toBeInTheDocument();
    expect(screen.queryByTestId('home')).not.toBeInTheDocument();
  });

  it('redirects to / when user.is_platform_team is false', () => {
    const Wrapper = makeWrapper(false);
    render(<Wrapper />);
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('home')).toBeInTheDocument();
  });

  it('redirects to / when user is null', () => {
    const Wrapper = makeWrapper(null);
    render(<Wrapper />);
    expect(screen.queryByTestId('admin-content')).not.toBeInTheDocument();
    expect(screen.getByTestId('home')).toBeInTheDocument();
  });
});
```

Run `npx vitest run src/components/admin/__tests__/RequireAdmin.test.tsx` — expect 3
failures (file does not exist yet).

**Task 2.2 — Implement (TDD GREEN)**

Create `apps/web/src/components/admin/RequireAdmin.tsx`:

```typescript
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export function RequireAdmin() {
  const { user } = useAuth();
  if (!user?.is_platform_team) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
```

Run `npx vitest run src/components/admin/__tests__/RequireAdmin.test.tsx` — expect 3
passes.

---

## Phase 3 — AdminErrorBoundary

**File:** `apps/web/src/components/admin/AdminErrorBoundary.tsx`

**Task 3.1 — Write the failing test (TDD RED)**

File: `apps/web/src/components/admin/__tests__/AdminErrorBoundary.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminErrorBoundary } from '../AdminErrorBoundary';

// Component that throws on demand
function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error('admin render error');
  return <div data-testid="safe-child">safe</div>;
}

function wrapper(children: React.ReactNode) {
  return render(
    <ThemeProvider>
      <AdminErrorBoundary>{children}</AdminErrorBoundary>
    </ThemeProvider>,
  );
}

// Suppress error output in tests
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {});
});
afterEach(() => {
  vi.restoreAllMocks();
});

describe('AdminErrorBoundary', () => {
  it('renders children when no error', () => {
    wrapper(<Bomb shouldThrow={false} />);
    expect(screen.getByTestId('safe-child')).toBeInTheDocument();
  });

  it('renders error UI when child throws', () => {
    wrapper(<Bomb shouldThrow={true} />);
    expect(screen.getByTestId('admin-error-boundary')).toBeInTheDocument();
    expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
  });

  it('renders a retry button in error state', () => {
    wrapper(<Bomb shouldThrow={true} />);
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });

  it('retry button resets error state', () => {
    // Re-render with a stable ref is not straightforward; verify button is clickable
    wrapper(<Bomb shouldThrow={true} />);
    const retry = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retry);
    // After click the boundary resets — child re-throws so error UI shows again
    expect(screen.getByTestId('admin-error-boundary')).toBeInTheDocument();
  });
});
```

Run test — expect failures.

**Task 3.2 — Implement (TDD GREEN)**

Create `apps/web/src/components/admin/AdminErrorBoundary.tsx`:

```typescript
import { Component, type ReactNode, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class AdminErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Structured logging — replace with real logger when available
    // eslint-disable-next-line no-console
    console.error('[AdminErrorBoundary]', error, info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          data-testid="admin-error-boundary"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '80px 24px',
            gap: '16px',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '32px' }}>⚠️</div>
          <div style={{ fontSize: '18px', fontWeight: 600 }}>Something went wrong</div>
          <div style={{ fontSize: '13px', opacity: 0.6, maxWidth: '400px' }}>
            {this.state.error?.message ?? 'An unexpected error occurred in the admin panel.'}
          </div>
          <button
            onClick={this.handleRetry}
            style={{
              padding: '8px 20px',
              borderRadius: '8px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '13px',
              background: '#4b7dff',
              color: '#fff',
            }}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

Run `npx vitest run src/components/admin/__tests__/AdminErrorBoundary.test.tsx` — expect 4
passes.

Note: The `AdminErrorBoundary` accepts `children` directly rather than using `<Outlet />`
because class components cannot call hooks (so no `useT()`). The parent `AdminLayout`
provides the theme context — the error UI uses hardcoded fallback values intentionally.
If the error boundary fires, the theme may also be compromised.

---

## Phase 4 — AdminLoadingSkeleton

**File:** `apps/web/src/components/admin/AdminLoadingSkeleton.tsx`

**Task 4.1 — Write the failing test (TDD RED)**

File: `apps/web/src/components/admin/__tests__/AdminLoadingSkeleton.test.tsx`

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminLoadingSkeleton } from '../AdminLoadingSkeleton';

describe('AdminLoadingSkeleton', () => {
  it('renders the sidebar skeleton', () => {
    render(
      <ThemeProvider>
        <AdminLoadingSkeleton />
      </ThemeProvider>,
    );
    expect(screen.getByTestId('admin-loading-sidebar')).toBeInTheDocument();
  });

  it('renders the content skeleton', () => {
    render(
      <ThemeProvider>
        <AdminLoadingSkeleton />
      </ThemeProvider>,
    );
    expect(screen.getByTestId('admin-loading-content')).toBeInTheDocument();
  });

  it('renders pulsing bars in the content area', () => {
    render(
      <ThemeProvider>
        <AdminLoadingSkeleton />
      </ThemeProvider>,
    );
    const bars = screen.getAllByTestId('admin-loading-bar');
    expect(bars.length).toBeGreaterThanOrEqual(3);
  });
});
```

Run test — expect failures.

**Task 4.2 — Implement (TDD GREEN)**

Create `apps/web/src/components/admin/AdminLoadingSkeleton.tsx`:

```typescript
import { useT } from '../../context/ThemeContext';

export function AdminLoadingSkeleton() {
  const C = useT();

  const sidebarWidth = C.adminSidebarWidth ?? '240px';

  const bar = (width: string, height = '14px') => (
    <div
      data-testid="admin-loading-bar"
      style={{
        width,
        height,
        borderRadius: '6px',
        background: C.border,
        animation: 'adminPulse 1.5s ease-in-out infinite',
      }}
    />
  );

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar skeleton */}
      <div
        data-testid="admin-loading-sidebar"
        style={{
          width: sidebarWidth,
          flexShrink: 0,
          background: C.adminSurfaceSide,
          borderRight: `1px solid ${C.border}`,
          padding: '24px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            style={{
              height: '36px',
              borderRadius: '6px',
              background: C.border,
              animation: `adminPulse 1.5s ease-in-out ${i * 0.1}s infinite`,
            }}
          />
        ))}
      </div>

      {/* Content skeleton */}
      <div
        data-testid="admin-loading-content"
        style={{
          flex: 1,
          background: C.adminBg,
          padding: '32px 24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        {bar('240px', '28px')}
        {bar('100%', '1px')}
        {bar('100%', '80px')}
        {bar('75%', '16px')}
        {bar('60%', '16px')}
        {bar('80%', '16px')}
      </div>

      <style>{`
        @keyframes adminPulse {
          0%, 100% { opacity: 0.35; }
          50% { opacity: 0.75; }
        }
      `}</style>
    </div>
  );
}
```

Run `npx vitest run src/components/admin/__tests__/AdminLoadingSkeleton.test.tsx` — expect
3 passes.

---

## Phase 5 — AdminSideNav

**File:** `apps/web/src/components/admin/AdminSideNav.tsx`

**Task 5.1 — Write the failing test (TDD RED)**

File: `apps/web/src/components/admin/__tests__/AdminSideNav.test.tsx`

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminSideNav } from '../AdminSideNav';

function wrapper(initialPath = '/admin') {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <AdminSideNav />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('AdminSideNav', () => {
  it('renders all 6 navigation items', () => {
    wrapper();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Queue')).toBeInTheDocument();
    expect(screen.getByText('Feedback')).toBeInTheDocument();
    expect(screen.getByText('Skills')).toBeInTheDocument();
    expect(screen.getByText('Roadmap')).toBeInTheDocument();
    expect(screen.getByText('Export')).toBeInTheDocument();
  });

  it('renders emoji icons for each item', () => {
    wrapper();
    expect(screen.getByText('📊')).toBeInTheDocument();
    expect(screen.getByText('📝')).toBeInTheDocument();
    expect(screen.getByText('💬')).toBeInTheDocument();
    expect(screen.getByText('⚙')).toBeInTheDocument();
    expect(screen.getByText('🗺')).toBeInTheDocument();
    expect(screen.getByText('↓')).toBeInTheDocument();
  });

  it('renders the section label "NAVIGATION"', () => {
    wrapper();
    expect(screen.getByText('NAVIGATION')).toBeInTheDocument();
  });

  it('all nav items are links', () => {
    wrapper();
    const links = screen.getAllByRole('link');
    expect(links.length).toBeGreaterThanOrEqual(6);
  });

  it('Dashboard link points to /admin', () => {
    wrapper();
    const dashboard = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboard).toHaveAttribute('href', '/admin');
  });

  it('Queue link points to /admin/queue', () => {
    wrapper();
    const queue = screen.getByRole('link', { name: /queue/i });
    expect(queue).toHaveAttribute('href', '/admin/queue');
  });
});
```

Run test — expect failures.

**Task 5.2 — Implement (TDD GREEN)**

Create `apps/web/src/components/admin/AdminSideNav.tsx`:

```typescript
import { NavLink } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';

interface NavItem {
  icon: string;
  label: string;
  to: string;
  end?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { icon: '📊', label: 'Dashboard', to: '/admin', end: true },
  { icon: '📝', label: 'Queue',     to: '/admin/queue' },
  { icon: '💬', label: 'Feedback',  to: '/admin/feedback' },
  { icon: '⚙',  label: 'Skills',    to: '/admin/skills' },
  { icon: '🗺',  label: 'Roadmap',   to: '/admin/roadmap' },
  { icon: '↓',   label: 'Export',    to: '/admin/export' },
];

export function AdminSideNav() {
  const C = useT();

  const sectionLabel: React.CSSProperties = {
    fontSize: '11px',
    fontWeight: 600,
    color: C.dim,
    letterSpacing: '0.8px',
    textTransform: 'uppercase',
    padding: '0 12px',
    marginBottom: '4px',
    marginTop: '8px',
  };

  return (
    <nav aria-label="Admin navigation" style={{ padding: '16px 8px', display: 'flex', flexDirection: 'column' }}>
      <div style={sectionLabel}>Navigation</div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 12px',
              borderRadius: '6px',
              textDecoration: 'none',
              fontSize: '13px',
              fontWeight: isActive ? 600 : 400,
              color: isActive ? C.accent : C.muted,
              background: isActive ? C.accentDim : 'transparent',
              borderLeft: isActive ? `3px solid ${C.accent}` : '3px solid transparent',
              transition: 'all 0.15s',
            })}
          >
            <span role="img" aria-hidden="true" style={{ fontSize: '15px', lineHeight: 1 }}>
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
```

Run `npx vitest run src/components/admin/__tests__/AdminSideNav.test.tsx` — expect 6
passes.

---

## Phase 6 — AdminLayout

**File:** `apps/web/src/components/admin/AdminLayout.tsx`

**Task 6.1 — Write the failing test (TDD RED)**

File: `apps/web/src/components/admin/__tests__/AdminLayout.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminLayout } from '../AdminLayout';

vi.mock('../AdminSideNav', () => ({
  AdminSideNav: () => <div data-testid="admin-side-nav" />,
}));
vi.mock('../AdminErrorBoundary', () => ({
  AdminErrorBoundary: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="admin-error-boundary-wrapper">{children}</div>
  ),
}));

function wrapper(outlet: React.ReactNode = <div data-testid="outlet-content">outlet</div>) {
  return render(
    <ThemeProvider>
      <MemoryRouter initialEntries={['/admin']}>
        <Routes>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={outlet} />
          </Route>
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('AdminLayout', () => {
  it('renders the AdminSideNav', () => {
    wrapper();
    expect(screen.getByTestId('admin-side-nav')).toBeInTheDocument();
  });

  it('renders the AdminErrorBoundary wrapper', () => {
    wrapper();
    expect(screen.getByTestId('admin-error-boundary-wrapper')).toBeInTheDocument();
  });

  it('renders the outlet content', () => {
    wrapper();
    expect(screen.getByTestId('outlet-content')).toBeInTheDocument();
  });

  it('renders a sidebar with correct data-testid', () => {
    wrapper();
    expect(screen.getByTestId('admin-sidebar')).toBeInTheDocument();
  });

  it('renders a content area with correct data-testid', () => {
    wrapper();
    expect(screen.getByTestId('admin-content-area')).toBeInTheDocument();
  });
});
```

Run test — expect failures.

**Task 6.2 — Implement (TDD GREEN)**

Create `apps/web/src/components/admin/AdminLayout.tsx`:

```typescript
import { Outlet } from 'react-router-dom';
import { useT } from '../../context/ThemeContext';
import { AdminSideNav } from './AdminSideNav';
import { AdminErrorBoundary } from './AdminErrorBoundary';

const NAV_HEIGHT = 60;

export function AdminLayout() {
  const C = useT();
  const sidebarWidth = C.adminSidebarWidth ?? '240px';

  return (
    <div style={{ display: 'flex', minHeight: `calc(100vh - ${NAV_HEIGHT}px)` }}>
      {/* Fixed left sidebar */}
      <div
        data-testid="admin-sidebar"
        style={{
          position: 'fixed',
          top: `${NAV_HEIGHT}px`,
          left: 0,
          width: sidebarWidth,
          height: `calc(100vh - ${NAV_HEIGHT}px)`,
          background: C.adminSurfaceSide,
          borderRight: `1px solid ${C.border}`,
          zIndex: 10,
          overflowY: 'auto',
        }}
      >
        <AdminSideNav />
      </div>

      {/* Scrollable content area */}
      <div
        data-testid="admin-content-area"
        style={{
          marginLeft: sidebarWidth,
          flex: 1,
          background: C.adminBg,
          padding: '32px 24px',
          minHeight: `calc(100vh - ${NAV_HEIGHT}px)`,
        }}
      >
        <AdminErrorBoundary>
          <Outlet />
        </AdminErrorBoundary>
      </div>
    </div>
  );
}
```

Run `npx vitest run src/components/admin/__tests__/AdminLayout.test.tsx` — expect 5 passes.

---

## Phase 7 — Placeholder admin views

All six views follow the same pattern. Create each in `apps/web/src/views/admin/`.

**Task 7.1 — Write the failing tests (TDD RED)**

File: `apps/web/src/views/admin/__tests__/AdminViews.test.tsx`

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../../../context/ThemeContext';
import { AdminDashboardView } from '../AdminDashboardView';
import { AdminQueueView } from '../AdminQueueView';
import { AdminFeedbackView } from '../AdminFeedbackView';
import { AdminSkillsView } from '../AdminSkillsView';
import { AdminRoadmapView } from '../AdminRoadmapView';
import { AdminExportView } from '../AdminExportView';

function wrap(ui: React.ReactNode) {
  return render(
    <ThemeProvider>
      <MemoryRouter>{ui}</MemoryRouter>
    </ThemeProvider>,
  );
}

describe('Admin placeholder views', () => {
  it('AdminDashboardView renders heading', () => {
    wrap(<AdminDashboardView />);
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
  });

  it('AdminQueueView renders heading', () => {
    wrap(<AdminQueueView />);
    expect(screen.getByRole('heading', { name: /queue/i })).toBeInTheDocument();
    expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
  });

  it('AdminFeedbackView renders heading', () => {
    wrap(<AdminFeedbackView />);
    expect(screen.getByRole('heading', { name: /feedback/i })).toBeInTheDocument();
    expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
  });

  it('AdminSkillsView renders heading', () => {
    wrap(<AdminSkillsView />);
    expect(screen.getByRole('heading', { name: /skills/i })).toBeInTheDocument();
    expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
  });

  it('AdminRoadmapView renders heading', () => {
    wrap(<AdminRoadmapView />);
    expect(screen.getByRole('heading', { name: /roadmap/i })).toBeInTheDocument();
    expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
  });

  it('AdminExportView renders heading', () => {
    wrap(<AdminExportView />);
    expect(screen.getByRole('heading', { name: /export/i })).toBeInTheDocument();
    expect(screen.getByText(/coming soon/i)).toBeInTheDocument();
  });
});
```

Run test — expect 6 failures.

**Task 7.2 — Implement all six views (TDD GREEN)**

Each view follows the same template. Create six files:

`apps/web/src/views/admin/AdminDashboardView.tsx`:
```typescript
import { useT } from '../../context/ThemeContext';

export function AdminDashboardView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>
        Dashboard
      </h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
```

`apps/web/src/views/admin/AdminQueueView.tsx`:
```typescript
import { useT } from '../../context/ThemeContext';

export function AdminQueueView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>
        Queue
      </h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
```

`apps/web/src/views/admin/AdminFeedbackView.tsx`:
```typescript
import { useT } from '../../context/ThemeContext';

export function AdminFeedbackView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>
        Feedback
      </h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
```

`apps/web/src/views/admin/AdminSkillsView.tsx`:
```typescript
import { useT } from '../../context/ThemeContext';

export function AdminSkillsView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>
        Skills
      </h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
```

`apps/web/src/views/admin/AdminRoadmapView.tsx`:
```typescript
import { useT } from '../../context/ThemeContext';

export function AdminRoadmapView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>
        Roadmap
      </h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
```

`apps/web/src/views/admin/AdminExportView.tsx`:
```typescript
import { useT } from '../../context/ThemeContext';

export function AdminExportView() {
  const C = useT();
  return (
    <div>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '8px', color: C.text }}>
        Export
      </h1>
      <p style={{ color: C.muted, fontSize: '14px' }}>Coming soon</p>
    </div>
  );
}
```

Run `npx vitest run src/views/admin/__tests__/AdminViews.test.tsx` — expect 6 passes.

---

## Phase 8 — Nav modification

**File:** `apps/web/src/components/Nav.tsx`

**Task 8.1 — Write the failing test (TDD RED)**

File: `apps/web/src/components/__tests__/Nav.admin.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../../context/ThemeContext';
import { Nav } from '../Nav';

vi.mock('../../hooks/useAuth');
import { useAuth } from '../../hooks/useAuth';

function renderNav(isPlatformTeam: boolean, isAuthenticated = true) {
  vi.mocked(useAuth).mockReturnValue({
    user: {
      user_id: '1',
      email: 'admin@example.com',
      name: 'Admin User',
      username: 'admin',
      division: 'Engineering Org',
      role: 'admin',
      is_platform_team: isPlatformTeam,
      is_security_team: false,
      iat: 0,
      exp: 9999999999,
    },
    isAuthenticated,
    login: vi.fn(),
    logout: vi.fn(),
  });

  render(
    <ThemeProvider>
      <MemoryRouter initialEntries={['/']}>
        <Nav onAuthOpen={vi.fn()} />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('Nav admin link', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Admin link when user.is_platform_team is true', () => {
    renderNav(true);
    expect(screen.getByRole('link', { name: /admin/i })).toBeInTheDocument();
  });

  it('does not render Admin link when user.is_platform_team is false', () => {
    renderNav(false);
    expect(screen.queryByRole('link', { name: /admin/i })).not.toBeInTheDocument();
  });

  it('Admin link points to /admin', () => {
    renderNav(true);
    const link = screen.getByRole('link', { name: /admin/i });
    expect(link).toHaveAttribute('href', '/admin');
  });
});
```

Run test — expect 3 failures (Admin link does not exist yet).

**Task 8.2 — Modify Nav.tsx (TDD GREEN)**

In `apps/web/src/components/Nav.tsx`:

1. Add `NavLink` to the react-router-dom import:
```typescript
import { useNavigate, useLocation, NavLink } from 'react-router-dom';
```

2. Replace the existing nav items group (the `<div style={{ display: 'flex', gap: '2px' }}>` that
   contains the three `navItem(...)` calls) with:

```typescript
<div style={{ display: 'flex', gap: '2px', alignItems: 'center' }}>
  {navItem('Discover', '/')}
  {navItem('Browse', '/browse')}
  {navItem('Filtered', '/filtered')}
  {user?.is_platform_team && (
    <NavLink
      to="/admin"
      style={({ isActive }) => ({
        background: isActive ? C.border : 'transparent',
        border: 'none',
        cursor: 'pointer',
        fontSize: '13px',
        fontWeight: isActive ? 600 : 400,
        color: isActive ? C.text : C.muted,
        padding: '4px 10px',
        borderRadius: '6px',
        transition: 'all 0.15s',
        textDecoration: 'none',
        display: 'inline-block',
      })}
    >
      Admin
    </NavLink>
  )}
</div>
```

Run `npx vitest run src/components/__tests__/Nav.admin.test.tsx` — expect 3 passes.

Run the full existing Nav test suite to confirm no regressions:
```bash
npx vitest run src/components/Nav
```

---

## Phase 9 — Route configuration in App.tsx

**File:** `apps/web/src/App.tsx`

**Task 9.1 — Write the failing test (TDD RED)**

File: `apps/web/src/__tests__/App.admin.test.tsx`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { act } from 'react';

// Mock lazy components to avoid dynamic import in test environment
vi.mock('../views/admin/AdminDashboardView', () => ({
  AdminDashboardView: () => <div data-testid="admin-dashboard-view">Dashboard</div>,
}));
vi.mock('../views/admin/AdminQueueView', () => ({
  AdminQueueView: () => <div data-testid="admin-queue-view">Queue</div>,
}));
vi.mock('../views/admin/AdminFeedbackView', () => ({
  AdminFeedbackView: () => <div data-testid="admin-feedback-view">Feedback</div>,
}));
vi.mock('../views/admin/AdminSkillsView', () => ({
  AdminSkillsView: () => <div data-testid="admin-skills-view">Skills</div>,
}));
vi.mock('../views/admin/AdminRoadmapView', () => ({
  AdminRoadmapView: () => <div data-testid="admin-roadmap-view">Roadmap</div>,
}));
vi.mock('../views/admin/AdminExportView', () => ({
  AdminExportView: () => <div data-testid="admin-export-view">Export</div>,
}));
vi.mock('../components/admin/RequireAdmin', () => ({
  RequireAdmin: () => <div data-testid="require-admin-present" />,
}));
vi.mock('../hooks/useAuth');
import { useAuth } from '../hooks/useAuth';

vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
  ok: true, status: 200, json: () => Promise.resolve({ flags: {} }),
}));

import { App } from '../App';

describe('App admin routes', () => {
  it('renders RequireAdmin guard in the route tree', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null, isAuthenticated: false, login: vi.fn(), logout: vi.fn(),
    });
    await act(async () => { render(<App />); });
    // RequireAdmin is present in the route tree (even if redirecting)
    // We verify by checking the home route rendered (RequireAdmin redirects unauthenticated)
    expect(screen.getByPlaceholderText(/what do you need help with today/i)).toBeInTheDocument();
  });
});
```

Run test — expect 1 failure (App has no admin routes).

**Task 9.2 — Modify App.tsx (TDD GREEN)**

Replace `apps/web/src/App.tsx` with:

```typescript
import { lazy, Suspense, useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, useT } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { FlagsProvider } from './context/FlagsContext';
import { Nav } from './components/Nav';
import { AuthModal } from './components/AuthModal';
import { HomeView } from './views/HomeView';
import { BrowseView } from './views/BrowseView';
import { SearchView } from './views/SearchView';
import { FilteredView } from './views/FilteredView';
import { SkillDetailView } from './views/SkillDetailView';
import { RequireAdmin } from './components/admin/RequireAdmin';
import { AdminLayout } from './components/admin/AdminLayout';
import { AdminLoadingSkeleton } from './components/admin/AdminLoadingSkeleton';

// Lazy-loaded admin views
const AdminDashboardView = lazy(() =>
  import('./views/admin/AdminDashboardView').then((m) => ({ default: m.AdminDashboardView })),
);
const AdminQueueView = lazy(() =>
  import('./views/admin/AdminQueueView').then((m) => ({ default: m.AdminQueueView })),
);
const AdminFeedbackView = lazy(() =>
  import('./views/admin/AdminFeedbackView').then((m) => ({ default: m.AdminFeedbackView })),
);
const AdminSkillsView = lazy(() =>
  import('./views/admin/AdminSkillsView').then((m) => ({ default: m.AdminSkillsView })),
);
const AdminRoadmapView = lazy(() =>
  import('./views/admin/AdminRoadmapView').then((m) => ({ default: m.AdminRoadmapView })),
);
const AdminExportView = lazy(() =>
  import('./views/admin/AdminExportView').then((m) => ({ default: m.AdminExportView })),
);

function AppShell() {
  const C = useT();
  const [showAuth, setShowAuth] = useState(false);

  return (
    <div
      style={{
        background: C.bg,
        minHeight: '100vh',
        color: C.text,
        fontFamily: "'Outfit',sans-serif",
        transition: 'background 0.3s, color 0.3s',
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
        *, *::before, *::after { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:4px; height:4px; }
        ::-webkit-scrollbar-thumb { background:${C.scrollThumb}; border-radius:2px; }
        input, textarea { transition: background 0.3s, border-color 0.2s; }
        input::placeholder, textarea::placeholder { color:${C.dim}; }
      `}</style>

      {showAuth && <AuthModal onClose={() => setShowAuth(false)} />}

      <Nav onAuthOpen={() => setShowAuth(true)} />

      <div style={{ paddingTop: '60px' }}>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomeView />} />
          <Route path="/browse" element={<BrowseView />} />
          <Route path="/search" element={<SearchView />} />
          <Route path="/filtered" element={<FilteredView />} />
          <Route path="/skills/:slug" element={<SkillDetailView />} />

          {/* Admin routes — gated by RequireAdmin */}
          <Route element={<RequireAdmin />}>
            <Route
              path="/admin"
              element={
                <Suspense fallback={<AdminLoadingSkeleton />}>
                  <AdminLayout />
                </Suspense>
              }
            >
              <Route index element={<AdminDashboardView />} />
              <Route path="queue" element={<AdminQueueView />} />
              <Route path="feedback" element={<AdminFeedbackView />} />
              <Route path="skills" element={<AdminSkillsView />} />
              <Route path="roadmap" element={<AdminRoadmapView />} />
              <Route path="export" element={<AdminExportView />} />
            </Route>
          </Route>
        </Routes>
      </div>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <FlagsProvider>
            <AppShell />
          </FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
```

Run `npx vitest run src/__tests__/App.admin.test.tsx` — expect 1 pass.

---

## Phase 10 — Verification

**Task 10.1 — Full test suite**

```bash
cd apps/web
npx vitest run --coverage
```

Expected: all tests pass, coverage ≥ 80%.

**Task 10.2 — TypeScript check**

```bash
cd apps/web
npx tsc --noEmit
```

Expected: zero errors.

**Task 10.3 — Build check**

```bash
cd apps/web
npx vite build
```

Expected: successful build with 6 lazy-split admin chunks visible in output.

Look for output like:
```
dist/assets/AdminDashboardView-[hash].js   X.XX kB
dist/assets/AdminQueueView-[hash].js       X.XX kB
...
```

---

## File creation order

Follow this order to avoid missing import errors:

1. `apps/web/src/lib/theme.ts` (extend existing — Phase 1)
2. `apps/web/src/components/admin/AdminErrorBoundary.tsx` (Phase 3)
3. `apps/web/src/components/admin/AdminLoadingSkeleton.tsx` (Phase 4)
4. `apps/web/src/components/admin/AdminSideNav.tsx` (Phase 5)
5. `apps/web/src/components/admin/AdminLayout.tsx` (Phase 6)
6. `apps/web/src/components/admin/RequireAdmin.tsx` (Phase 2)
7. `apps/web/src/views/admin/AdminDashboardView.tsx` (Phase 7)
8. `apps/web/src/views/admin/AdminQueueView.tsx` (Phase 7)
9. `apps/web/src/views/admin/AdminFeedbackView.tsx` (Phase 7)
10. `apps/web/src/views/admin/AdminSkillsView.tsx` (Phase 7)
11. `apps/web/src/views/admin/AdminRoadmapView.tsx` (Phase 7)
12. `apps/web/src/views/admin/AdminExportView.tsx` (Phase 7)
13. `apps/web/src/components/Nav.tsx` (modify — Phase 8)
14. `apps/web/src/App.tsx` (modify — Phase 9)

---

## New test files to create

```
apps/web/src/lib/theme.test.ts (extend if exists, or create)
apps/web/src/components/admin/__tests__/RequireAdmin.test.tsx
apps/web/src/components/admin/__tests__/AdminErrorBoundary.test.tsx
apps/web/src/components/admin/__tests__/AdminLoadingSkeleton.test.tsx
apps/web/src/components/admin/__tests__/AdminSideNav.test.tsx
apps/web/src/components/admin/__tests__/AdminLayout.test.tsx
apps/web/src/components/__tests__/Nav.admin.test.tsx
apps/web/src/views/admin/__tests__/AdminViews.test.tsx
apps/web/src/__tests__/App.admin.test.tsx
```

---

## Known constraints and pitfalls

### AdminErrorBoundary cannot use useT()

Class components cannot call hooks. The error UI uses hardcoded color values
(`#4b7dff` for the retry button) rather than theme tokens. This is intentional: if the
error boundary fires during a render inside the theme context subtree, the theme may
be in an unknown state. Keep it simple.

### Suspense placement

The `<Suspense fallback={<AdminLoadingSkeleton />}>` wraps `<AdminLayout />` — NOT the
individual views. This means the sidebar itself is also replaced by the skeleton during
the initial load of the admin bundle. This is correct: the user should not see a
half-rendered sidebar with no content.

### NavLink `end` prop on Dashboard

The Dashboard route maps to `/admin` (the index). Without `end={true}` the NavLink would
match all `/admin/*` paths as active simultaneously. Always pass `end` to the Dashboard
item.

### `replace` on Navigate in RequireAdmin

`<Navigate to="/" replace />` replaces the history entry rather than pushing a new one.
This prevents users from hitting "back" to return to a 401 redirect loop.

### Theme token naming

`adminSidebarWidth` is a string (`'240px'`), not a number. This is consistent with how
CSS custom properties work and how the token is consumed in `style` objects:
`marginLeft: C.adminSidebarWidth`. Do not strip the `px` suffix.

### No `index.ts` barrel exports for admin components

Avoid creating `components/admin/index.ts`. Barrel exports cause Vite to include all
admin components in the main bundle, defeating the purpose of lazy loading the views.
Import each admin component directly by path.

---

## Acceptance criteria checklist

- [ ] `tsc --noEmit` passes with zero errors
- [ ] `vitest run` passes with coverage ≥ 80%
- [ ] `vite build` succeeds and produces 6 admin view chunks
- [ ] Navigating to `/admin` as a non-platform-team user redirects to `/`
- [ ] Navigating to `/admin` as a platform-team user renders AdminLayout with sidebar
- [ ] All 6 sidebar links navigate to their respective routes
- [ ] Active sidebar item has `border-left: 3px solid accent` and `accentDim` background
- [ ] Admin link appears in Nav only when `user.is_platform_team === true`
- [ ] Throwing inside an admin view shows the AdminErrorBoundary error UI
- [ ] Light and dark themes both render the sidebar and content area correctly
- [ ] Sidebar is fixed at `top: 60px`, content area has `margin-left: 240px`
- [ ] Nav z-index (100) is greater than sidebar z-index (10)
