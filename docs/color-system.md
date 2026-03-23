# SkillHub Color System — Design Specification

> **Status:** Proposed
> **Date:** 2026-03-22
> **Stakeholder note:** Division colors are approved by stakeholders — do not change without sign-off.

---

## Problem

All skill cards currently use the same accent color based on author type (official = blue, community = green). There is no visual distinction by **category** or **division**, making it hard for users across engineering, finance, HR, and other teams to quickly scan and find relevant skills.

Additionally, the division colors in the seed database (`seed.py`) and the frontend (`shared-types/index.ts`) have drifted out of sync. This document establishes a single canonical color palette.

---

## Design Principles

1. **Category drives the card color** — the primary visual accent on a skill card should reflect its category (Engineering, Finance, HR, etc.), not just whether it's official or community.
2. **Division colors remain distinct** — division badge chips keep their own palette for organizational identity.
3. **One source of truth** — all colors are defined in `libs/shared-types/src/index.ts` and imported everywhere. The seed script should reference or mirror these values.
4. **Dark + light mode parity** — every color has a dark-mode and light-mode variant that maintain sufficient contrast (WCAG AA on the card surface).
5. **Opacity layering** — backgrounds use the color at low opacity (`12-18%`), borders at medium opacity (`30-40%`), text/icons at full saturation.

---

## 1. Category Colors (NEW)

These colors determine the **skill card accent** (top border gradient, icon background, and card border on hover). Each category gets a distinct hue so users can visually scan the marketplace by domain.

| Category      | Dark Mode   | Light Mode  | Hue Family | Rationale |
|---------------|-------------|-------------|------------|-----------|
| Engineering   | `#4b7dff`   | `#2a5de8`   | Blue       | Matches existing accent — engineering is the core audience |
| Product       | `#a78bfa`   | `#6d4fd4`   | Purple     | Creative/strategic feel; distinct from blue |
| Data          | `#22d3ee`   | `#0891b2`   | Cyan       | Analytics/data-pipeline associations |
| Security      | `#ef5060`   | `#d63040`   | Red        | Alert/protection connotation |
| Finance       | `#1fd49e`   | `#0fa878`   | Teal/Green | Money/growth association |
| General       | `#64748b`   | `#475569`   | Slate      | Neutral — catch-all category |
| HR            | `#f2a020`   | `#c07800`   | Amber      | Warm/people-oriented |
| Research      | `#e879f9`   | `#c026d3`   | Magenta    | Innovation/exploration feel |
| Operations    | `#fb923c`   | `#d97706`   | Orange     | Ops/infrastructure energy |

### Where these apply on a skill card

```
┌─ top border gradient ─────────────────────────┐  ← category color → transparent
│ ┌──────┐                                      │
│ │ ICON │  Skill Name           [official]     │  ← icon bg: color @ 12% opacity
│ │  bg   │  v1.2.3                              │
│ └──────┘                                      │
│  Description text...                          │
│                                                │
│  [Division Chip] [Division Chip]               │  ← division colors (separate palette)
│  #tag1  #tag2  #tag3                           │
│                                                │
│  ★ 4.7 (28)   ↓ 342        [Claude Code]     │  ← install badge keeps its own color
└────────────────────────────────────────────────┘
     └── card border on hover: category color @ 30%
```

### Category filter pills

Category pills in the browse/filter bar should also use these colors when **active**, replacing the current single-accent approach:

- **Active:** `background: categoryColor @ 12%`, `border: categoryColor`, `color: categoryColor`
- **Inactive:** `background: surface`, `border: borderColor`, `color: muted`

---

## 2. Division Colors (EXISTING — Stakeholder Approved)

These colors are used on **division badge chips** only. They identify which org owns or has access to a skill.

| Division           | Canonical Hex | Hue Family |
|--------------------|---------------|------------|
| Engineering Org    | `#4b7dff`     | Blue       |
| Product Org        | `#a78bfa`     | Purple     |
| Finance & Legal    | `#1fd49e`     | Teal       |
| People & HR        | `#f2a020`     | Amber      |
| Operations         | `#22d3ee`     | Cyan       |
| Executive Office   | `#ef5060`     | Red        |
| Sales & Marketing  | `#fb923c`     | Orange     |
| Customer Success   | `#84cc16`     | Lime       |

> **Action required:** Update `seed.py` to use these canonical values instead of the current Tailwind-palette approximations.

### Current seed.py drift (to fix)

| Division          | seed.py (wrong)  | Canonical (correct) |
|-------------------|------------------|---------------------|
| Engineering Org   | `#3B82F6`        | `#4b7dff`           |
| Product Org       | `#8B5CF6`        | `#a78bfa`           |
| Finance & Legal   | `#10B981`        | `#1fd49e`           |
| People & HR       | `#F59E0B`        | `#f2a020`           |
| Operations        | `#EF4444`        | `#22d3ee`           |
| Executive Office  | `#6366F1`        | `#ef5060`           |
| Sales & Marketing | `#EC4899`        | `#fb923c`           |
| Customer Success  | `#14B8A6`        | `#84cc16`           |

---

## 3. Install Method Colors (EXISTING)

Used on the install method badge in the bottom-right of skill cards.

| Method      | Dark Mode   | Light Mode  |
|-------------|-------------|-------------|
| Claude Code | `#4b7dff`   | `#2a5de8`   |
| MCP Server  | `#1fd49e`   | `#0fa878`   |
| Manual      | `#f2a020`   | `#c07800`   |

No changes proposed.

---

## 4. Author Type Badge Colors (EXISTING)

Used on the "official" / "community" / "team" / "individual" badge.

| Type       | Color       | Notes |
|------------|-------------|-------|
| official   | `#4b7dff`   | Blue — platform-endorsed |
| team       | `#1fd49e`   | Green — team-contributed |
| community  | `#a78bfa`   | Purple — community-contributed |
| individual | `#f2a020`   | Amber — single-author |

---

## 5. Semantic / Status Colors (EXISTING)

| Purpose    | Dark Mode   | Light Mode  |
|------------|-------------|-------------|
| Success    | `#1fd49e`   | `#0fa878`   |
| Warning    | `#f2a020`   | `#c07800`   |
| Error      | `#ef5060`   | `#d63040`   |
| Info       | `#4b7dff`   | `#2a5de8`   |

---

## 6. Implementation Plan

### Step 1: Add `CATEGORY_COLORS` to shared-types

```typescript
// libs/shared-types/src/index.ts
export const CATEGORY_COLORS: Record<string, { dark: string; light: string }> = {
  Engineering:  { dark: '#4b7dff', light: '#2a5de8' },
  Product:      { dark: '#a78bfa', light: '#6d4fd4' },
  Data:         { dark: '#22d3ee', light: '#0891b2' },
  Security:     { dark: '#ef5060', light: '#d63040' },
  Finance:      { dark: '#1fd49e', light: '#0fa878' },
  General:      { dark: '#64748b', light: '#475569' },
  HR:           { dark: '#f2a020', light: '#c07800' },
  Research:     { dark: '#e879f9', light: '#c026d3' },
  Operations:   { dark: '#fb923c', light: '#d97706' },
};
```

### Step 2: Update `SkillCard.tsx`

Replace the current author-type-based accent:
```typescript
// BEFORE
const accent = skill.author_type === 'official' ? C.accent : C.green;

// AFTER
const categoryColor = CATEGORY_COLORS[skill.category]?.[C.mode] ?? C.accent;
```

Use `categoryColor` for the top gradient, icon background, and hover border.

### Step 3: Update category filter pills

In `BrowseView.tsx`, `FilteredView.tsx`, and `HomeView.tsx` — when a category pill is active, use its `CATEGORY_COLORS` entry instead of the generic `C.accent`.

### Step 4: Sync seed.py

Update the `DIVISIONS` list in `seed.py` to use the canonical hex values from `DIVISION_COLORS`.

### Step 5: Add color field to categories table (optional)

If we want the DB to be the source of truth for category colors (like divisions already have a `color` column), add a migration to add `color` to the `categories` table and seed the values.

---

## Accessibility Notes

- All colors were selected to meet **WCAG AA contrast** against the dark surface (`#0c1825`) and light surface (`#ffffff`) when used as text.
- Background usage at 12-18% opacity ensures the card content remains readable.
- The `General` category uses slate gray intentionally — it's the neutral fallback and shouldn't compete with domain-specific categories.
- Color is never the **sole** indicator — category names, division labels, and tags provide redundant textual cues.
