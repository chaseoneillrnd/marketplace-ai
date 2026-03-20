# SkillHub Style Guide

> Canonical design reference extracted from `skills-marketplace-v4.jsx`.
> All UI work MUST conform to these tokens, patterns, and conventions.

---

## 1. Color System

SkillHub ships with two themes — **Dark** (default) and **Light**. Every color is referenced through a theme context (`useT()` / `ThemeCtx`) so components never hard-code mode-specific values.

### 1.1 Dark Theme Tokens

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#07111f` | Page background |
| `surface` | `#0c1825` | Card / panel background |
| `surfaceHi` | `#111f30` | Hovered card / elevated surface |
| `border` | `#152030` | Default borders |
| `borderHi` | `#1e3248` | Emphasized borders (hover, focus) |
| `text` | `#ddeaf7` | Primary text |
| `muted` | `#517898` | Secondary / descriptive text |
| `dim` | `#2a4361` | Tertiary / disabled text |
| `accent` | `#4b7dff` | Primary brand blue — buttons, links, active states |
| `accentDim` | `rgba(75,125,255,0.12)` | Accent tint background |
| `green` | `#1fd49e` | Success, community badge |
| `greenDim` | `rgba(31,212,158,0.10)` | Success tint background |
| `amber` | `#f2a020` | Warnings, ratings (★), verified badge |
| `amberDim` | `rgba(242,160,32,0.10)` | Warning tint background |
| `red` | `#ef5060` | Errors, destructive actions, sign-out |
| `redDim` | `rgba(239,80,96,0.10)` | Error tint background |
| `purple` | `#a78bfa` | Secondary accent (gradients, Product Org) |
| `inputBg` | `#060e1a` | Input field backgrounds |
| `codeBg` | `#060e1a` | Code block backgrounds |
| `navBg` | `rgba(7,17,31,0.92)` | Navigation bar (translucent) |
| `cardShadow` | `0 8px 32px rgba(0,0,0,0.5)` | Card elevation shadow |
| `scrollThumb` | `#1e3248` | Scrollbar thumb |

### 1.2 Light Theme Tokens

| Token | Hex | Usage |
|-------|-----|-------|
| `bg` | `#f0f4f9` | Page background |
| `surface` | `#ffffff` | Card / panel background |
| `surfaceHi` | `#f5f8fc` | Hovered card / elevated surface |
| `border` | `#dde5ef` | Default borders |
| `borderHi` | `#c8d5e6` | Emphasized borders |
| `text` | `#0e1d30` | Primary text |
| `muted` | `#5a7a99` | Secondary text |
| `dim` | `#9aaec4` | Tertiary / disabled text |
| `accent` | `#2a5de8` | Primary brand blue |
| `accentDim` | `rgba(42,93,232,0.09)` | Accent tint background |
| `green` | `#0fa878` | Success |
| `greenDim` | `rgba(15,168,120,0.09)` | Success tint |
| `amber` | `#c07800` | Warnings / ratings |
| `amberDim` | `rgba(192,120,0,0.09)` | Warning tint |
| `red` | `#d63040` | Errors / destructive |
| `redDim` | `rgba(214,48,64,0.09)` | Error tint |
| `purple` | `#6d4fd4` | Secondary accent |
| `inputBg` | `#f0f4f9` | Input backgrounds |
| `codeBg` | `#e8edf5` | Code block backgrounds |
| `navBg` | `rgba(240,244,249,0.94)` | Navigation bar |
| `cardShadow` | `0 4px 20px rgba(0,0,0,0.08)` | Card elevation shadow |
| `scrollThumb` | `#c8d5e6` | Scrollbar thumb |

### 1.3 Semantic / Role Colors

| Color | Hex (Dark) | Purpose |
|-------|-----------|---------|
| Install: Claude Code | `#4b7dff` | Install method badge |
| Install: MCP | `#1fd49e` | Install method badge |
| Install: Manual | `#f2a020` | Install method badge |

### 1.4 Division Colors

Each organizational division has a fixed brand color used across chips, filters, and badges:

| Division | Color |
|----------|-------|
| Engineering Org | `#4b7dff` |
| Product Org | `#a78bfa` |
| Finance & Legal | `#1fd49e` |
| People & HR | `#f2a020` |
| Operations | `#22d3ee` |
| Executive Office | `#ef5060` |
| Sales & Marketing | `#fb923c` |
| Customer Success | `#84cc16` |

### 1.5 Tint Pattern

Tinted backgrounds follow a consistent opacity convention:
- **Backgrounds:** `${color}14` (8% opacity) default, `${color}25` (15%) active
- **Borders:** `${color}22` default, `${color}44` active, `${color}66` hover
- **Badges:** `${color}18` bg, `${color}28` border
- **Dim variants:** `rgba(r,g,b,0.09–0.12)` for named tokens

---

## 2. Typography

### 2.1 Font Families

| Family | Usage | Import |
|--------|-------|--------|
| **Outfit** (`'Outfit', sans-serif`) | All UI text — headings, body, labels, buttons | Google Fonts: weights 300–800 |
| **JetBrains Mono** (`'JetBrains Mono', monospace`) | Code blocks, tags, version labels, IDs, monospace badges | Google Fonts: weights 400, 500 |

### 2.2 Type Scale

| Element | Size | Weight | Notes |
|---------|------|--------|-------|
| Hero heading (`h1`) | `40px` | 800 | Gradient text on home page |
| Page heading (`h1`) | `22px` | 700 | Browse, Detail views |
| Section heading (`h2`) | `16px` | 700 | "Featured Skills", "Suggested for You" |
| Section label (`h3`) | `11–12px` | 600 | Uppercase, `letter-spacing: 0.8–1px` |
| Skill card title | `14px` | 600 | |
| Body text | `13–15px` | 400 | `line-height: 1.55–1.75` |
| Small / meta | `11–12px` | 400–500 | Muted color |
| Micro labels | `9–10px` | 600 | Tags, version, counts |
| Button text | `12–13px` | 600 | |

### 2.3 Text Color Hierarchy

1. **Primary** → `text` token — headings, skill names, user names
2. **Secondary** → `muted` token — descriptions, body copy
3. **Tertiary** → `dim` token — timestamps, version numbers, helper text
4. **Accent** → `accent` / semantic color — links, active states, badges

---

## 3. Spacing & Layout

### 3.1 Page Layout

- **Max content width:** `1100px` (general), `1200px` (filtered view with sidebar), `900px` (detail view)
- **Page padding:** `24px` horizontal, `32–40px` vertical
- **Nav height:** `60px` (fixed)
- **Content offset:** `paddingTop: 60px` (below fixed nav)

### 3.2 Grid System

- **Card grid:** `display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px`
- **Filtered view grid:** `minmax(240px, 1fr)` with `230px` fixed sidebar
- **Stats grid:** `repeat(4, 1fr)` with `1px` gap (border effect)

### 3.3 Common Spacing Values

| Use | Value |
|-----|-------|
| Card padding | `16px` |
| Detail panel padding | `24–28px` |
| Modal padding | `28px` |
| Section gap | `40–48px` |
| Element gap (tight) | `4–6px` |
| Element gap (default) | `8–10px` |
| Element gap (loose) | `12–14px` |
| Form field margin-bottom | `14–16px` |

---

## 4. Component Patterns

### 4.1 Cards (`SkillCard`)

```
┌─ gradient accent bar (3px) ──────────────┐
│ [Icon] Name  Verified✓        [Badge]    │
│         v1.2.3                           │
│ Short description text here...           │
│ [Division Chips]                         │
│ [#tag] [#tag] [#tag]                     │
│ ─────────────────────────────────────── │
│ ★ 4.9 (218)    ↓ 1,842    [Claude Code] │
└──────────────────────────────────────────┘
```

- **Border radius:** `12px`
- **Hover:** `translateY(-2px)`, border → `borderHi`, background → `surfaceHi`, accent glow shadow
- **Transition:** `all 0.18s`
- **Accent bar:** `3px` height, `linear-gradient(90deg, accent, accent+44)`

### 4.2 Buttons (`Btn`)

| Variant | Background | Color | Border |
|---------|-----------|-------|--------|
| **Primary** | `accent` (hover: `#1f4fd4`) | `#fff` | none |
| **Default** | `surface` (hover: `surfaceHi`) | `muted` | `1px solid border` |
| **Danger** | `red+14` (hover: `red+28`) | `red` | `1px solid red+44` |
| **Disabled** | Same as variant | Same | `opacity: 0.45`, `cursor: not-allowed` |

- **Padding:** Normal `9px 18px`, Small `5px 12px`
- **Font size:** Normal `13px`, Small `12px`
- **Border radius:** `8px`
- **Font weight:** `600`
- **Transition:** `all 0.15s`

### 4.3 Badges

- **Pill badge:** `border-radius: 99px`, font `10px`, weight `500`
- **Background:** `${color}18`, **border:** `1px solid ${color}28`
- Used for: author type (official/community), install method, filter chips

### 4.4 Tags

- **Background:** `border` token, **color:** `muted` token
- **Font:** JetBrains Mono, `10px`
- **Padding:** `2px 7px`, **border-radius:** `4px`
- **Format:** `#tagname`

### 4.5 Division Chips

- **Border-radius:** `99px` (pill)
- **Font:** JetBrains Mono, `9–10px`, weight `600`
- **Default:** bg `${divColor}14`, border `${divColor}22`
- **Active:** bg `${divColor}25`, border `${divColor}66`, box-shadow `0 0 0 2px ${divColor}22`

### 4.6 Input Fields

- **Background:** `inputBg` token
- **Border:** `1px solid border` (default), `1px solid accent+66` (focused)
- **Border radius:** `8px`
- **Padding:** `9px 12px`
- **Font:** Outfit, `13px`
- **Focus ring:** `box-shadow: 0 0 0 3px accentDim`
- **Error state:** border `1px solid red+66`

### 4.7 Modals / Overlays

- **Overlay:** `rgba(4,8,16,0.85)`, `backdrop-filter: blur(10px)`
- **Box:** `surface` bg, `borderHi` border, `border-radius: 18px`
- **Top accent bar:** `3px` gradient (`accent → purple → green` for auth, `accent → purple` for submit)
- **Max height:** `90vh`, `overflow: auto`

### 4.8 Avatar

- **Shape:** Circle (`border-radius: 50%`)
- **Size:** `24px` (chip), `28px` (default), `32–34px` (large)
- **Color:** HSL generated from username hash — `hsl(hue, 45%, 30%/65%)` bg, `hsl(hue, 45%, 42%/55%)` border
- **Initials:** Centered, bold `700`, `10–13px`

### 4.9 Navigation Bar

- **Position:** `fixed`, top, full width
- **Height:** `60px`
- **Background:** `navBg` (translucent with blur)
- **Backdrop filter:** `blur(14px)`
- **Logo:** `28px` square, `border-radius: 6px`, accent background, ⚡ icon
- **App name:** "SkillHub", weight `700`, `15px`
- **Internal badge:** JetBrains Mono, `10px`, accent color on accentDim bg
- **Nav items:** `13px`, weight `400` (inactive) / `600` (active), `border-radius: 6px`, `4px 10px` padding

### 4.10 Tabs

- **Style:** Underline tabs (not boxed)
- **Active:** `text` color, `border-bottom: 2px solid accent`
- **Inactive:** `muted` color, `border-bottom: 2px solid transparent`
- **Padding:** `7–8px 18px`
- **Font:** `13px`, weight `400` (inactive) / `600` (active)

---

## 5. Interaction Patterns

### 5.1 Hover Effects

| Element | Effect |
|---------|--------|
| Card | `translateY(-2px)`, surface → surfaceHi, border → borderHi, accent glow |
| Button (primary) | bg → `#1f4fd4` |
| Button (default) | bg → surfaceHi |
| Nav item | Follows active/hover bg pattern |
| OAuth provider row | border → `providerColor+66`, bg → `providerColor+09` |
| User select row | border → `accent+55`, bg → `accentDim` |
| Menu item | bg → `surfaceHi` |
| Sign out | bg → `redDim` |

### 5.2 Transitions

| Property | Duration | Easing |
|----------|----------|--------|
| General (`all`) | `0.15s` | default (ease) |
| Background/border (global `*`) | `0.25s` / `0.2s` | default |
| Card hover | `0.18s` | default |
| Theme toggle thumb | `0.25s` | `cubic-bezier(.4,0,.2,1)` |
| Theme toggle background | `0.3s` | default |
| Division chip | `0.12s` | default |
| Pill/button quick | `0.1s` | default |
| Stepper dots | `0.3s` | default |

### 5.3 Animations

- **OAuth loading dots:** `@keyframes pulse { 0%,100%{opacity:.2} 50%{opacity:1} }`, duration `1.2s`, staggered `0.3s` per dot

---

## 6. Iconography

SkillHub uses **text/emoji symbols** — no icon library dependency.

| Symbol | Meaning |
|--------|---------|
| ⚡ | App logo, MCP install method |
| ★ / ☆ | Rating stars (filled/empty) |
| ✓ | Verified, checked, completed |
| ✕ | Close, clear, remove |
| ← / → | Navigation, next/back |
| ↓ | Install count, download |
| ↗ | Fork |
| ♡ | Favorites |
| ↩ | Reply |
| ⎋ | Sign out |
| ↑ | Upvote/helpful |
| ✎ | Write/edit |
| ✦ | AI/semantic, suggested |
| ⌕ | Search |
| ⌨ | CLI install |
| 📦 | Installed skills |
| 📋 | Manual install |
| 📝 | Submissions |
| ⚙ | Advanced filters |
| ⚠ | Warning/caution |
| 🔒 | Restricted access |
| 🔍 | No results |
| 🎉 | Success celebration |
| 🌙 / ☀️ | Dark/light mode |

---

## 7. View Architecture

| View | Route Key | Max Width | Description |
|------|-----------|-----------|-------------|
| Home | `"home"` | `1100px` | Hero + search + suggested + featured |
| Browse | `"browse"` | `1100px` | Category tabs + division filter + grid |
| Search | `"search"` | `1100px` | AI-semantic search results + division filter |
| Filtered | `"filtered"` | `1200px` | Sidebar filters (category, division, sort, method, quality) + grid |
| Detail | `"detail"` | `900px` | Skill header + tabs (Overview, How to Use, Install, Reviews) |

---

## 8. Data Categories & Constants

### 8.1 Categories
`All`, `Engineering`, `Product`, `Data`, `Security`, `Finance`, `General`, `HR`, `Research`

### 8.2 Sort Options
`Trending`, `Most Installed`, `Highest Rated`, `Newest`, `Recently Updated`

### 8.3 Install Methods
- `claude-code` → "Claude Code" (blue `#4b7dff`)
- `mcp` → "MCP Server" (green `#1fd49e`)
- `manual` → "Manual" (amber `#f2a020`)

### 8.4 Author Types
- `official` → accent color badge
- `community` → green color badge

### 8.5 OAuth Providers
Microsoft (`#0078d4`), Google (`#4285f4`), Okta (`#007dc1`), GitHub (`#555`), Generic OIDC (`#a78bfa`)

---

## 9. Scrollbar Styling

```css
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-thumb { background: scrollThumb; border-radius: 2px; }
```

---

## 10. Global CSS Reset

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
input, textarea { transition: background 0.3s, border-color 0.2s; }
input::placeholder, textarea::placeholder { color: dim; }
* { transition: background-color 0.25s, border-color 0.2s, color 0.2s; }
```

---

## 11. Design Principles

1. **Theme-first** — Every color comes from the theme context. Zero hard-coded mode-specific values in components.
2. **Tint convention** — Semantic colors get opacity-based tints for backgrounds (`14`/`25`) and borders (`22`/`44`/`66`).
3. **Consistent radii** — `4px` tags, `6px` small controls, `8px` inputs/buttons, `10–12px` cards/panels, `18px` modals, `99px` pills.
4. **Minimal elevation** — Shadows are subtle; dark mode relies on border contrast, light mode adds soft shadows.
5. **Progressive disclosure** — Cards show minimal info; detail view reveals full content through tabs.
6. **Division-aware** — Organizational divisions are first-class UI citizens with dedicated colors, filters, and access gating.
7. **No icon library** — Emoji/text symbols keep the bundle small and dependencies minimal.
8. **Transition discipline** — All interactive elements have explicit transitions. No jarring state changes.
9. **Font hierarchy** — Outfit for human text, JetBrains Mono for machine/code text. Never mix.
10. **Accessibility baseline** — Sufficient contrast in both themes, focus rings on inputs, keyboard-navigable modals.
