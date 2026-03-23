# Frontend Architecture

React 18 + Vite + TypeScript. Located at `apps/web/`.

## Component Tree

```
App
  BrowserRouter
    ThemeProvider
      AuthProvider
        FlagsProvider
          AppShell
            Nav
            AuthModal (conditional)
            Routes
              / -> HomeView
              /browse -> BrowseView
              /search -> SearchView
              /filtered -> FilteredView
              /skills/:slug -> SkillDetailView
```

## Routing

| Path | View | Description |
|---|---|---|
| `/` | HomeView | Landing with featured skills |
| `/browse` | BrowseView | Category browsing |
| `/search` | SearchView | Full-text search |
| `/filtered` | FilteredView | Filtered skill list |
| `/skills/:slug` | SkillDetailView | Skill detail page |

Uses `react-router-dom` with `BrowserRouter`.

## State Management

Three React contexts, no external state library:

### ThemeContext
- Light/dark theme toggle
- Exposes `useT()` hook for theme colors
- Theme object defines: `bg`, `text`, `dim`, `scrollThumb`, etc.
- Config: `apps/web/src/lib/theme.ts`

### AuthContext
- JWT token storage and user claims
- `useAuth()` hook
- Login via `POST /auth/token`
- Token passed to API client

### FlagsContext
- Fetches `GET /api/v1/flags` on mount
- `useFlags()` returns full map
- `useFlag(key)` returns boolean for single flag

## API Client

`apps/web/src/lib/api.ts` — centralized HTTP client.
- Base URL from env or defaults
- Injects `Authorization: Bearer <token>` when authenticated
- Used by all views and hooks

## Shared Components

| Component | Description |
|---|---|
| `Nav` | Top navigation bar with auth trigger |
| `SkillCard` | Skill summary card for lists |
| `AuthModal` | Login/signup modal |
| `ErrorState` | Error display |
| `SkeletonCard` | Loading placeholder |
| `EmptyState` | No results display |
| `DivisionChip` | Division badge with color |

## Custom Hooks

| Hook | File | Purpose |
|---|---|---|
| `useAuth` | `hooks/useAuth.ts` | Auth state + login/logout |
| `useFlag` | `hooks/useFlag.ts` | Single flag boolean |
| `useFlags` | `hooks/useFlag.ts` | Full flags map |
| `useSkills` | `hooks/useSkills.ts` | Skill data fetching |

## Key Files

- `apps/web/src/App.tsx` — app shell + routing
- `apps/web/src/context/` — ThemeContext, AuthContext, FlagsContext
- `apps/web/src/views/` — page components
- `apps/web/src/components/` — shared UI
- `apps/web/src/hooks/` — custom hooks
- `apps/web/src/lib/` — api client, auth utils, theme config
- `apps/web/vite.config.ts` — build config
