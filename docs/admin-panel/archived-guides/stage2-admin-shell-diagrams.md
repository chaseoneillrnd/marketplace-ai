# Stage 2: Admin Shell — Visual Architecture Companion

---

## Diagram 1 — Full component tree after Stage 2

```
App
└── BrowserRouter
    └── ThemeProvider
        └── AuthProvider
            └── FlagsProvider
                └── AppShell
                    ├── <style> (global CSS reset + fonts)
                    ├── AuthModal (conditional)
                    ├── Nav  ──────────────────────────── z-index: 100
                    │   └── [Admin NavLink]  (only when is_platform_team)
                    └── <div paddingTop="60px">
                        └── Routes
                            ├── /           → HomeView
                            ├── /browse     → BrowseView
                            ├── /search     → SearchView
                            ├── /filtered   → FilteredView
                            ├── /skills/:slug → SkillDetailView
                            └── RequireAdmin (Outlet guard)
                                └── /admin  → Suspense[AdminLoadingSkeleton]
                                    └── AdminLayout
                                        ├── AdminSideNav  ──── z-index: 10
                                        │   ├── [NAVIGATION label]
                                        │   ├── 📊 Dashboard  → /admin (index)
                                        │   ├── 📝 Queue      → /admin/queue
                                        │   ├── 💬 Feedback   → /admin/feedback
                                        │   ├── ⚙  Skills     → /admin/skills
                                        │   ├── 🗺 Roadmap    → /admin/roadmap
                                        │   └── ↓  Export     → /admin/export
                                        └── AdminErrorBoundary
                                            └── Outlet
                                                ├── (index)   → AdminDashboardView  [lazy]
                                                ├── queue     → AdminQueueView       [lazy]
                                                ├── feedback  → AdminFeedbackView    [lazy]
                                                ├── skills    → AdminSkillsView      [lazy]
                                                ├── roadmap   → AdminRoadmapView     [lazy]
                                                └── export    → AdminExportView      [lazy]
```

---

## Diagram 2 — RequireAdmin guard decision tree

```
User navigates to /admin/*
         │
         ▼
  ┌─────────────────────┐
  │   RequireAdmin       │
  │   reads useAuth()    │
  └─────────────────────┘
         │
         ▼
  user?.is_platform_team
         │
    ┌────┴────┐
   true      false / null
    │              │
    ▼              ▼
 <Outlet />   <Navigate to="/" replace />
 (render           │
  admin            ▼
  routes)     User lands on HomeView
              (history entry replaced —
               back button goes to
               pre-/admin page)
```

---

## Diagram 3 — Pixel layout (viewport at 1280px wide)

```
┌─────────────────────────────────────────────────────────────────┐
│  Nav                                              z-index: 100  │
│  position: fixed  top:0  height: 60px                           │
│  SkillHub ⚡  Discover  Browse  Filtered  Admin    [🌙] [+ Submit] [user ▾]
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────────────────────┐
│  AdminSideNav    │  AdminLayout content area                    │
│                  │                                              │
│  position: fixed │  margin-left: 240px                         │
│  top: 60px       │  padding: 32px 24px                         │
│  width: 240px    │  background: adminBg                        │
│  height:         │                                              │
│  calc(100vh-60px)│  ┌────────────────────────────────────────┐ │
│  background:     │  │  AdminErrorBoundary                    │ │
│  adminSurfaceSide│  │  ┌──────────────────────────────────┐  │ │
│  z-index: 10     │  │  │  <Outlet />                      │  │ │
│                  │  │  │  → AdminDashboardView (or other) │  │ │
│  NAVIGATION      │  │  └──────────────────────────────────┘  │ │
│  ─────────────── │  └────────────────────────────────────────┘ │
│  ▌ 📊 Dashboard  │                                              │
│    📝 Queue      │                                              │
│    💬 Feedback   │                                              │
│    ⚙  Skills     │                                              │
│    🗺 Roadmap    │                                              │
│    ↓  Export     │                                              │
│                  │                                              │
│  (sidebar is     │                                              │
│   scrollable     │                                              │
│   independently) │                                              │
└──────────────────┴──────────────────────────────────────────────┘
  240px                     1040px (at 1280px viewport)
```

---

## Diagram 4 — Z-index stack (cross-section view)

```
Viewport depth axis (higher = rendered on top)
                                             ↑ front
                                             │
  z-index 999  ┌───────────────────────┐    │
               │   Modal overlays      │    │
               └───────────────────────┘    │
                                            │
  z-index 200  ┌───────────────────────┐    │
               │   Nav user dropdown   │    │
               └───────────────────────┘    │
                                            │
  z-index 100  ┌───────────────────────┐    │
               │   Nav bar (fixed)     │    │
               └───────────────────────┘    │
                                            │
  z-index  50  ┌───────────────────────┐    │  (AdminActionBar — future Stage 3)
               │   [reserved]          │    │
               └───────────────────────┘    │
                                            │
  z-index  10  ┌───────────────────────┐    │
               │   AdminSideNav        │    │
               └───────────────────────┘    │
                                            │
  z-index   1  ┌───────────────────────┐    │
               │   AdminLayout content │    │
               └───────────────────────┘    │
                                            ↓ back
```

---

## Diagram 5 — AdminSideNav active vs inactive item states

```
Inactive item:
┌─────────────────────────────────────────┐
│  3px transparent  │ 📝  Queue            │  color: C.muted  fontWeight: 400
│  left border      │                      │  background: transparent
└─────────────────────────────────────────┘

Active item:
┌─────────────────────────────────────────┐
█  3px accent      │ 📊  Dashboard         │  color: C.accent  fontWeight: 600
█  left border     │                      │  background: C.accentDim
└─────────────────────────────────────────┘

Dimensions:
- Item height:  auto (padding 8px top/bottom)
- Item padding: 8px 12px
- Border-radius: 6px (C.control)
- Gap between items: 2px
- Icon font-size: 15px
- Label font-size: 13px
- Section label:  11px, uppercase, letter-spacing 0.8px, color C.dim
```

---

## Diagram 6 — Lazy loading chunk split

```
Initial bundle (loads immediately on any route):
┌──────────────────────────────────────────────────────┐
│  App.tsx                                              │
│  Nav.tsx                                              │
│  HomeView.tsx, BrowseView.tsx, SearchView.tsx         │
│  FilteredView.tsx, SkillDetailView.tsx                │
│  RequireAdmin.tsx  ← guard (tiny, always needed)     │
│  AdminLayout.tsx   ← layout shell (small)            │
│  AdminSideNav.tsx  ← sidebar (small)                 │
│  AdminLoadingSkeleton.tsx ← Suspense fallback (small)│
│  AdminErrorBoundary.tsx   ← boundary (tiny)          │
└──────────────────────────────────────────────────────┘

Lazy chunks (loaded only when /admin/* is first visited):
┌──────────────────────────────────────────────────────┐
│  AdminDashboardView-[hash].js   (stub, tiny now)      │
│  AdminQueueView-[hash].js                             │
│  AdminFeedbackView-[hash].js                          │
│  AdminSkillsView-[hash].js                            │
│  AdminRoadmapView-[hash].js                           │
│  AdminExportView-[hash].js                            │
└──────────────────────────────────────────────────────┘

Note: AdminLayout, AdminSideNav, AdminErrorBoundary, and
AdminLoadingSkeleton are NOT lazy-loaded because they are
needed immediately to render the AdminLoadingSkeleton
fallback frame before the lazy views resolve.
```

---

## Diagram 7 — AdminErrorBoundary render flow

```
Normal path:
AdminLayout renders
    └── AdminErrorBoundary (state: { hasError: false })
            └── <Outlet />
                    └── AdminDashboardView  ✓  renders normally

Error path (child throws during render):
AdminLayout renders
    └── AdminErrorBoundary
            └── <Outlet />
                    └── AdminQueueView  ✗  throws Error("fetch failed")
                            │
                            ▼
                  getDerivedStateFromError()
                  sets: { hasError: true, error: Error }
                            │
                            ▼
                  render() returns error UI:
                  ┌──────────────────────────────┐
                  │   ⚠️                          │
                  │   Something went wrong        │
                  │   fetch failed                │
                  │   [ Retry ]                   │
                  └──────────────────────────────┘
                            │
                  User clicks Retry
                            │
                            ▼
                  handleRetry() sets: { hasError: false }
                            │
                            ▼
                  <Outlet /> re-renders
                  (view may throw again — boundary catches again)
```

---

## Diagram 8 — Theme token map for admin components

```
Theme token           Used by                   Dark value      Light value
─────────────────────────────────────────────────────────────────────────────
C.adminBg             AdminLayout content area  #060e1a         #e8edf5
                      AdminLoadingSkeleton       "               "

C.adminSurfaceSide    AdminLayout sidebar       #0a1522         #f0f4f9
                      AdminLoadingSkeleton       "               "

C.adminSidebarWidth   AdminLayout sidebar width '240px'         '240px'
                      AdminLoadingSkeleton       "               "

C.accent              AdminSideNav active color  #4b7dff        #2a5de8
                      Admin link in Nav          "               "

C.accentDim           AdminSideNav active bg     rgba(75,125,255,0.12)
                                                               rgba(42,93,232,0.09)

C.border              AdminLayout divider        #152030        #dde5ef
                      AdminLoadingSkeleton bars  "               "

C.muted               AdminSideNav inactive      #517898        #5a7a99
                      Admin placeholder text     "               "

C.dim                 AdminSideNav section label #2a4361        #9aaec4

C.text                Admin view headings        #ddeef7        #0e1d30

C.navBg               Nav background             rgba(7,17,31,0.92)
                                                               rgba(240,244,249,0.94)
```

---

## Diagram 9 — Nav modification diff (logical view)

```
BEFORE:
┌─────────────────────────────────────────────────────────────┐
│ [Logo] [Discover] [Browse] [Filtered]  [search]  [🌙] [auth]│
└─────────────────────────────────────────────────────────────┘

AFTER (user.is_platform_team = false):
┌─────────────────────────────────────────────────────────────┐
│ [Logo] [Discover] [Browse] [Filtered]  [search]  [🌙] [auth]│
└─────────────────────────────────────────────────────────────┘
(no visible change)

AFTER (user.is_platform_team = true):
┌───────────────────────────────────────────────────────────────┐
│ [Logo] [Discover] [Browse] [Filtered] [Admin]  [search]  [🌙] [user ▾]│
└───────────────────────────────────────────────────────────────┘
                                          ↑
                                    NavLink to /admin
                                    Conditionally rendered
                                    Active state matches
                                    existing navItem pattern
```

---

## Diagram 10 — Route nesting structure (react-router-dom v6)

```
<Routes>
  │
  ├── <Route path="/"          element={<HomeView />} />
  ├── <Route path="/browse"    element={<BrowseView />} />
  ├── <Route path="/search"    element={<SearchView />} />
  ├── <Route path="/filtered"  element={<FilteredView />} />
  ├── <Route path="/skills/:slug" element={<SkillDetailView />} />
  │
  └── <Route element={<RequireAdmin />}>           ← no path (layout route)
          │
          └── <Route path="/admin" element={       ← Suspense + AdminLayout
                  <Suspense fallback={<AdminLoadingSkeleton />}>
                    <AdminLayout />
                  </Suspense>
                }>
                  │
                  ├── <Route index element={<AdminDashboardView />} />
                  │     matches /admin exactly
                  │
                  ├── <Route path="queue"    element={<AdminQueueView />} />
                  │     matches /admin/queue
                  │
                  ├── <Route path="feedback" element={<AdminFeedbackView />} />
                  ├── <Route path="skills"   element={<AdminSkillsView />} />
                  ├── <Route path="roadmap"  element={<AdminRoadmapView />} />
                  └── <Route path="export"   element={<AdminExportView />} />
```

Key v6 behaviours:
- Child `path="queue"` is relative — resolves to `/admin/queue` automatically
- `<Route index>` matches the parent path exactly (no trailing slash needed)
- `<Route element={<RequireAdmin />}>` with no `path` is a "layout route" —
  it wraps children without adding a URL segment
- `<Suspense>` lives on the layout element, not on individual lazy views,
  so the entire admin shell suspends together on first load

---

## Diagram 11 — AdminLoadingSkeleton layout

```
┌──────────────────┬──────────────────────────────────────────────┐
│  Sidebar skeleton│  Content skeleton                            │
│  width: 240px    │  flex: 1                                     │
│  bg: adminSurface│  bg: adminBg                                 │
│  padding:16px 8px│  padding: 32px 24px                          │
│                  │                                              │
│  ████████████    │  ████████████████████   ← 28px height title  │
│  ████████████    │  ──────────────────────── ← 1px divider      │
│  ████████████    │  ████████████████████████  ← 80px block      │
│  ████████████    │  ████████████████          ← 16px bar        │
│  ████████████    │  ████████████              ← 16px bar        │
│  ████████████    │  ████████████████          ← 16px bar        │
│  (6 rows,        │                                              │
│   staggered      │  All bars animate with adminPulse keyframe:  │
│   animation      │  opacity 0.35 → 0.75 → 0.35 (1.5s)          │
│   delay 0.1s     │                                              │
│   per row)       │                                              │
└──────────────────┴──────────────────────────────────────────────┘
```

---

## Diagram 12 — File dependency graph (Stage 2 additions)

```
apps/web/src/
│
├── lib/theme.ts  ←───────────────────────────────┐ (extended with admin tokens)
│                                                  │
├── context/ThemeContext.tsx (useT)                │
│         │                                        │
├── hooks/useAuth.ts (useAuth)                     │
│         │                                        │
├── components/admin/                              │
│   ├── RequireAdmin.tsx  ←── uses useAuth         │
│   ├── AdminErrorBoundary.tsx  (no theme deps)    │
│   ├── AdminLoadingSkeleton.tsx  ←── uses useT ──►┘
│   ├── AdminSideNav.tsx  ←── uses useT, NavLink   │
│   └── AdminLayout.tsx  ←── uses useT, Outlet     │
│           ├── imports AdminSideNav               │
│           └── imports AdminErrorBoundary         │
│                                                  │
├── views/admin/                                   │
│   ├── AdminDashboardView.tsx  ←── uses useT      │
│   ├── AdminQueueView.tsx      ←── uses useT      │
│   ├── AdminFeedbackView.tsx   ←── uses useT      │
│   ├── AdminSkillsView.tsx     ←── uses useT      │
│   ├── AdminRoadmapView.tsx    ←── uses useT      │
│   └── AdminExportView.tsx     ←── uses useT      │
│                                                  │
├── components/Nav.tsx  (modified — adds NavLink)  │
│                                                  │
└── App.tsx  (modified — adds admin routes + lazy) │
        ├── imports RequireAdmin                   │
        ├── imports AdminLayout                    │
        ├── imports AdminLoadingSkeleton           │
        └── lazy imports 6 AdminXxxView files      │

libs/shared-types/src/index.ts
  └── UserClaims.is_platform_team: boolean  ← consumed by RequireAdmin + Nav
```

Dependency rules enforced (no violations):
- apps/web never imports from apps/api or apps/mcp-server
- libs/shared-types is consumed by apps/web (allowed)
- No circular imports within apps/web/src/components/admin/
