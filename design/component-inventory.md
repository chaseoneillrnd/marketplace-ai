# SkillHub Component Inventory

> Maps every component in `skills-marketplace-v4.jsx` to its purpose, props, and visual behavior.
> Use this as the blueprint when building production React components in `apps/web`.

---

## Foundation Components

### `ThemeToggle`
**Props:** `isDark: boolean`, `onToggle: () => void`
**Behavior:** 38×22px toggle switch with sliding thumb, sun/moon icons. Thumb animates with cubic-bezier easing.

### `Avatar`
**Props:** `username: string`, `size?: number` (default 28)
**Behavior:** Circle with hue-rotated background derived from username hash. Shows user initials.

### `UserChip`
**Props:** `username: string`, `showRole?: boolean`
**Behavior:** Avatar + name inline. Optionally shows role and division below name.

### `Tag`
**Props:** `children: string`
**Behavior:** Monospace pill with `#` prefix. Uses `border` bg, `muted` color.

### `Badge`
**Props:** `color?: string`, `children: ReactNode`
**Behavior:** Rounded pill with tinted background. Used for author type, install method.

### `DivisionChip`
**Props:** `division: string`, `active?: boolean`, `onClick?: () => void`, `small?: boolean`
**Behavior:** Color-coded pill from `DIV_COLOR` map. Active state adds glow ring. Clickable when `onClick` provided.

### `Btn`
**Props:** `onClick`, `primary?: boolean`, `small?: boolean`, `danger?: boolean`, `disabled?: boolean`, `style?: object`, `children`
**Behavior:** Multi-variant button. Primary = blue filled, default = bordered, danger = red tinted.

---

## Composite Components

### `AuthModal`
**States:** `provider` → `callback` → `demo`
**Flow:** Choose OAuth provider → simulated redirect (1.6s) → select demo user identity.
**Visual:** Full-screen overlay with 420px card, rainbow accent bar.

### `SubmitModal`
**States:** Step 1 (Basic Info) → Step 2 (Division Scope) → Step 3 (Review) → Submitted
**Flow:** Multi-step form with stepper indicator, field validation, division checkbox grid.
**Visual:** Full-screen overlay with 520px card, accent→purple gradient bar.

### `UserMenu`
**Behavior:** Click avatar to toggle dropdown. Outside click closes. Shows user info, navigation links, sign out.
**Dropdown width:** 220px, positioned absolute right.

### `Nav`
**Props:** `view`, `setView`, `searchQuery`, `setSearchQuery`, `onSearch`, `authUser`, `onAuthOpen`, `onLogout`, `onSubmitOpen`, `isDark`, `onThemeToggle`
**Behavior:** Fixed top bar with logo, nav items (Discover/Browse/Filtered), search input, theme toggle, auth/submit buttons.

### `SkillCard`
**Props:** `skill: Skill`, `onSelect: (skill) => void`
**Behavior:** Grid card with accent bar, icon, name, description, division chips, tags, stats footer. Hover lifts card.

### `DivisionFilterBar`
**Props:** `divState: { selected, toggle, clear, matches }`
**Behavior:** Horizontal chip bar for multi-select division filtering. "Clear all" appears when any selected.

---

## View Components

### `HomeView`
**Sections:** Hero (title + search + category buttons) → Suggested for You (if authenticated) → Featured Skills
**Props:** `onSelectSkill`, `setView`, `setSearchQuery`, `authUser`

### `BrowseView`
**Sections:** Header → Category tabs → Division filter bar → Card grid
**Props:** `onSelectSkill`, `setView`

### `SearchView`
**Sections:** Back button + results header → Semantic search banner → Division filter → Results grid (or empty state)
**Props:** `query`, `setView`, `onSelectSkill`

### `FilteredView`
**Layout:** Sidebar (230px) + main grid. Sidebar has sticky filters for category, division (multi-select), sort, install method, quality toggle.
**Props:** `onSelectSkill`

### `SkillDetailView`
**Sections:** Back link → Access warning (if restricted) → Skill header card (icon, name, badges, stats, action buttons) → Tab bar → Tab content
**Tabs:** Overview, How to Use, Install, Reviews & Discussion
**Props:** `skill`, `setView`, `authUser`, `onAuthOpen`

### `ReviewsTab`
**Sub-tabs:** Reviews | Discussion
**Features:** Star rating histogram, write review form (5-star selector + textarea), review cards with helpful voting, comment thread with nested replies.
**Props:** `skill`, `authUser`, `onAuthOpen`

---

## Root Component (`App`)

**State:**
- `isDark` — theme toggle
- `view` — current view key (`home`, `browse`, `search`, `filtered`, `detail`)
- `selectedSkill` — skill object for detail view
- `searchQuery` — search input value
- `authUser` — username string or null
- `showAuth` / `showSubmit` — modal visibility

**Routing:** Client-side state-based (no React Router). View switching via `setView()`.
