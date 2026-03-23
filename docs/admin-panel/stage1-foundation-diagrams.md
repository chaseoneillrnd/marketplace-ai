# Stage 1: Foundation — Visual Architecture Companion

Mermaid diagrams for `stage1-foundation-guide.md`. Reference these alongside the written guide when reviewing architecture decisions or planning implementation order.

---

## Diagram 1 — Prompt Execution Order & Dependencies

```mermaid
flowchart TD
    P1["Prompt 1\nToken Additions\n~10 min\n\ntokens.json + theme.ts\n(additive only)"]
    P2["Prompt 2\nContrast Fixes\n~8 min\n\nLIGHT.green → #0b7a57\nLIGHT.amber → #8a5400"]
    P3["Prompt 3\nAnnouncerContext\n~12 min\n\nAnnouncerContext.tsx\nuseAnnounce.ts"]
    P4["Prompt 4\nuseFocusTrap\n~12 min\n\nuseFocusTrap.ts"]
    P5["Prompt 5\nAppShell a11y\n~12 min\n\nApp.tsx\nskip link + live regions"]
    P6["Prompt 6\nComponent Fixes\n~21 min\n\nSkillCard, DivisionChip\nAuthModal, Nav, HomeView"]

    P1 --> P2
    P2 --> P3
    P2 --> P4
    P3 --> P5
    P4 --> P5
    P5 --> P6

    style P3 fill:#1e3248,color:#ddeaf7
    style P4 fill:#1e3248,color:#ddeaf7
    style P6 fill:#0b3d2e,color:#ddeaf7
```

**Reading the graph:** P3 and P4 are independent and can be parallelized. All other edges are blocking serial dependencies. P2 must complete before P3/P4 because later tests import `LIGHT` and will fail if contrast values are wrong.

---

## Diagram 2 — New File Tree (Stage 1 output)

```mermaid
graph TD
    root["apps/web/src/"]

    lib["lib/"]
    theme["theme.ts ✏️\n+ adminBg, adminSurfaceSide\n+ purpleDim\n+ WCAG green/amber fix"]
    themeTest["theme.test.ts 🆕\ncontrast + token tests"]

    context["context/"]
    announcerCtx["AnnouncerContext.tsx 🆕\nAnnouncerProvider\naria-live DOM regions"]
    themeCtx["ThemeContext.tsx ✔️\nunchanged"]
    authCtx["AuthContext.tsx ✔️\nunchanged"]

    hooks["hooks/"]
    useAnnounce["useAnnounce.ts 🆕"]
    useAnnounceTest["useAnnounce.test.ts 🆕"]
    useFocusTrap["useFocusTrap.ts 🆕"]
    useFocusTrapTest["useFocusTrap.test.ts 🆕"]

    components["components/"]
    skillCard["SkillCard.tsx ✏️\n+ role=article\n+ tabIndex=0\n+ onKeyDown\n+ focus ring"]
    divChip["DivisionChip.tsx ✏️\n+ tabIndex conditional\n+ onKeyDown conditional"]
    authModal["AuthModal.tsx ✏️\n+ role=dialog\n+ aria-modal\n+ aria-labelledby\n+ useFocusTrap"]
    nav["Nav.tsx ✏️\n+ div→button user menu\n+ aria-expanded\n+ search aria-label"]

    views["views/"]
    homeView["HomeView.tsx ✏️\n+ search aria-label"]

    tests["__tests__/"]
    appShellTest["AppShell.test.tsx 🆕\nskip link + live regions"]
    a11yTest["Accessibility.test.tsx 🆕\ncomponent a11y tests"]

    app["App.tsx ✏️\n+ AnnouncerProvider\n+ skip link\n+ id=main-content"]

    designDir["design/"]
    tokens["tokens.json ✏️\n+ layout.adminSidebarWidth\n+ layout.queueListWidth\n+ borders section\n+ transitions.drag\n+ chart section"]

    root --> lib
    root --> context
    root --> hooks
    root --> components
    root --> views
    root --> tests
    root --> app

    lib --> theme
    lib --> themeTest

    context --> announcerCtx
    context --> themeCtx
    context --> authCtx

    hooks --> useAnnounce
    hooks --> useAnnounceTest
    hooks --> useFocusTrap
    hooks --> useFocusTrapTest

    components --> skillCard
    components --> divChip
    components --> authModal
    components --> nav

    views --> homeView

    tests --> appShellTest
    tests --> a11yTest

    designDir --> tokens
```

---

## Diagram 3 — AnnouncerContext Architecture

```mermaid
graph LR
    appShell["AppShell\n(any component)"]
    useAnnounce["useAnnounce()\nhook"]
    announcerCtx["AnnouncerContext\n.announce(msg, level)"]
    announcerProvider["AnnouncerProvider"]

    politeState["politeMsg\nuseState"]
    assertiveState["assertiveMsg\nuseState"]

    politeDOM["&lt;div role='status'\naria-live='polite'\naria-atomic='true'&gt;\n(visually hidden)"]
    assertiveDOM["&lt;div role='alert'\naria-live='assertive'\naria-atomic='true'&gt;\n(visually hidden)"]

    screenReader(["Screen Reader\nasync read"])

    appShell -- "useAnnounce()" --> useAnnounce
    useAnnounce -- "consumes" --> announcerCtx
    announcerCtx -- "provided by" --> announcerProvider
    announcerProvider -- "manages" --> politeState
    announcerProvider -- "manages" --> assertiveState
    politeState -- "renders text" --> politeDOM
    assertiveState -- "renders text" --> assertiveDOM
    politeDOM -- "polite queue" --> screenReader
    assertiveDOM -- "interrupt" --> screenReader

    style politeDOM fill:#0c3a5e,color:#ddeaf7
    style assertiveDOM fill:#3d1a1a,color:#ddeaf7
    style screenReader fill:#1a3d1a,color:#ddeaf7
```

**Key design decision:** Two separate DOM nodes with two separate React state variables. Never clear and replace a single node — JAWS and NVDA detect text changes on a node; replacing the entire node can miss the mutation event.

**7-second clear:** Prevents stale text from being re-read if the user navigates back to the region with a screen reader virtual cursor.

---

## Diagram 4 — useFocusTrap Lifecycle

```mermaid
sequenceDiagram
    participant Mount as Component Mount
    participant Hook as useFocusTrap
    participant DOM as Container DOM
    participant Prev as previouslyFocused

    Mount->>Hook: enabled=true, containerRef attached
    Hook->>Prev: capture document.activeElement
    Hook->>DOM: querySelectorAll(FOCUSABLE)
    DOM-->>Hook: [btn-A, btn-B, btn-C]
    Hook->>DOM: focusables[0].focus() → btn-A

    Note over DOM: User presses Tab from btn-C
    DOM->>Hook: keydown { key:'Tab', shiftKey:false }
    Hook->>DOM: re-query FOCUSABLE (dynamic DOM)
    Hook->>DOM: activeElement === last? Yes
    Hook->>DOM: preventDefault(); focusables[0].focus() → btn-A

    Note over DOM: User presses Shift+Tab from btn-A
    DOM->>Hook: keydown { key:'Tab', shiftKey:true }
    Hook->>DOM: activeElement === first? Yes
    Hook->>DOM: preventDefault(); last.focus() → btn-C

    Note over DOM: User presses Escape
    DOM->>Hook: keydown { key:'Escape' }
    Hook->>Mount: onEscape?.()

    Note over Mount: Component unmounts
    Mount->>Hook: cleanup runs
    Hook->>Prev: previouslyFocused?.focus()
```

---

## Diagram 5 — WCAG Contrast: Before vs After

```mermaid
graph LR
    subgraph BEFORE["Before (Failing)"]
        b_green["LIGHT.green\n#0fa878\nvs #ffffff\n3.05:1 ✗"]
        b_amber["LIGHT.amber\n#c07800\nvs #ffffff\n3.54:1 ✗"]
        b_threshold["WCAG AA\nbody text\n4.5:1 minimum"]
    end

    subgraph AFTER["After (Passing)"]
        a_green["LIGHT.green\n#0b7a57\nvs #ffffff\n~5.2:1 ✓"]
        a_amber["LIGHT.amber\n#8a5400\nvs #ffffff\n~6.1:1 ✓"]
        a_threshold["WCAG AA\nbody text\n4.5:1 minimum"]
    end

    subgraph UNCHANGED["Dark Mode (Untouched)"]
        d_green["DARK.green\n#1fd49e\nvs #07111f\npasses on dark bg ✓"]
        d_amber["DARK.amber\n#f2a020\nvs #07111f\npasses on dark bg ✓"]
    end

    b_green -.->|"darkened"| a_green
    b_amber -.->|"darkened"| a_amber

    style b_green fill:#3d1a1a,color:#ef9090
    style b_amber fill:#3d1a1a,color:#ef9090
    style a_green fill:#0b3d2e,color:#6affbe
    style a_amber fill:#1a2800,color:#ffe066
    style b_threshold fill:#1a1a2e,color:#9090ef
    style a_threshold fill:#0b1a2e,color:#9090ef
    style d_green fill:#0c1825,color:#1fd49e
    style d_amber fill:#0c1825,color:#f2a020
```

**Why `dim` variants are not fixed:** `greenDim` and `amberDim` are `rgba` values with 9% opacity — they are always decorative (backgrounds, borders). WCAG does not require decorative-only elements to meet contrast thresholds (criterion 1.4.3 exempts "decorative" content). The dim RGB base values are updated to match the new base colors to maintain visual consistency, but this is purely aesthetic.

---

## Diagram 6 — Component ARIA Responsibility Map

```mermaid
graph TD
    subgraph SkillCard["SkillCard.tsx"]
        sc_role["role='article'"]
        sc_tab["tabIndex={0}"]
        sc_label["aria-label={skill.name}"]
        sc_key["onKeyDown\nEnter/Space → onClick"]
        sc_focus["onFocus/onBlur\nfocus ring via boxShadow\n(C.accent, 2px solid)"]
    end

    subgraph DivisionChip["DivisionChip.tsx"]
        dc_tab["tabIndex={0}\n(only when onClick provided)"]
        dc_key["onKeyDown\nEnter/Space → onClick()\n(only when onClick provided)"]
        dc_role["role='button'\n(already present, unchanged)"]
    end

    subgraph AuthModal["AuthModal.tsx"]
        am_dialog["role='dialog'\n(outer backdrop div)"]
        am_modal["aria-modal='true'"]
        am_label["aria-labelledby='auth-modal-title'"]
        am_titleid["id='auth-modal-title'\n(title text div)"]
        am_trap["useFocusTrap(modalRef,\n{ onEscape: onClose })"]
    end

    subgraph Nav["Nav.tsx"]
        nav_btn["div → button\n(user menu trigger)"]
        nav_exp["aria-expanded={menuOpen}"]
        nav_pop["aria-haspopup='true'"]
        nav_userlabel["aria-label=\n'User menu for {name}'"]
        nav_search["aria-label=\n'Search skills'"]
    end

    subgraph HomeView["HomeView.tsx"]
        hv_search["aria-label=\n'Search skills'\n(hero input)"]
    end

    subgraph AppShell["App.tsx AppShell"]
        as_skip["Skip to main content link\n(href='#main-content'\nvisually-hidden-until-focused)"]
        as_main["id='main-content'\n(Routes wrapper div)"]
        as_live["AnnouncerProvider\n(wraps AppShell tree)"]
    end
```

---

## Diagram 7 — Provider Nesting Order (App.tsx after Stage 1)

```mermaid
graph TD
    browser["BrowserRouter"]
    theme["ThemeProvider\n(DARK/LIGHT context)"]
    auth["AuthProvider\n(JWT + user state)"]
    flags["FlagsProvider\n(feature flags)"]
    announce["AnnouncerProvider 🆕\n(aria-live DOM nodes)"]
    appshell["AppShell\n(skip link + Routes)"]

    browser --> theme
    theme --> auth
    auth --> flags
    flags --> announce
    announce --> appshell

    style announce fill:#0c3a5e,color:#ddeaf7
    style appshell fill:#111f30,color:#ddeaf7
```

**Nesting rationale:** `AnnouncerProvider` wraps `AppShell` because any component in the tree (including future admin panel routes) may call `useAnnounce()`. It is placed inside `FlagsProvider` so admin-gated features can use announcements without provider ordering issues.

---

## Diagram 8 — Skip Link Behavior (Focus State Machine)

```mermaid
stateDiagram-v2
    [*] --> Hidden: page load\ntop: -40px

    Hidden --> Visible: :focus (Tab key from browser chrome)
    Visible --> Hidden: :blur (Tab past / click elsewhere)
    Visible --> MainContent: user activates link (Enter / click)

    MainContent --> Hidden: focus moved to #main-content

    note right of Hidden
        position: absolute
        top: -40px
        Not display:none
        (still in tab order)
    end note

    note right of Visible
        top: 0px
        background: C.accent
        color: #fff
        z-index: 9999
        Visible above nav bar
    end note
```

**Why not `display:none`:** A `display:none` element is removed from the tab order entirely. The skip link must be in the tab order as the first focusable element — it is just off-screen by default.

---

## Diagram 9 — Token Taxonomy (tokens.json after Stage 1)

```mermaid
mindmap
  root((tokens.json))
    themes
      dark
        bg, surface, surfaceHi
        border, borderHi
        text, muted, dim
        accent, accentDim
        green, greenDim
        amber, amberDim
        red, redDim
        purple
        inputBg, codeBg
        navBg, cardShadow
        scrollThumb
      light
        [same keys as dark]
    divisionColors
      Engineering Org: #4b7dff
      Product Org: #a78bfa
      [6 others]
    installMethodColors
      claude-code, mcp, manual
    oauthProviderColors
      microsoft, google, okta, github, oidc
    typography
      fontFamilies
      fontWeights
      fontSizes
    radii
      tag 4px / control 6px / input 8px
      card 12px / panel 14px / modal 18px / pill 99px
    spacing
      cardPadding / detailPadding / modalPadding
      pageHorizontal / pageVertical
      gridGap / sectionGap
    layout
      navHeight: 60px
      maxWidthDefault / maxWidthFiltered / maxWidthDetail
      sidebarWidth: 230px
      cardMinWidth / searchMaxWidth
      adminSidebarWidth: 240px ✨NEW
      queueListWidth: 380px ✨NEW
    transitions
      fast / default / card / medium / theme
      drag: 0.2s ✨NEW
    borders ✨NEW
      navActiveIndicator: 3px
      focus: 2px
      input: 1px
    chart ✨NEW
      seriesOrder
      axisText / gridLine / chartBg
```

---

## Diagram 10 — Test File Map

```mermaid
graph LR
    subgraph "Existing tests (must stay passing)"
        t1["useAuth.test.tsx"]
        t2["useFlag.test.tsx"]
        t3["HomeView.test.tsx"]
        t4["FilteredView.test.tsx"]
        t5["api.test.ts"]
        t6["auth.test.ts"]
        t7["BrowseView.test.tsx"]
        t8["SearchView.test.tsx"]
        t9["SkillDetailView.test.tsx"]
        t10["FlagGating.test.tsx"]
    end

    subgraph "New tests (Stage 1)"
        n1["theme.test.ts\n(P1 + P2)"]
        n2["useAnnounce.test.ts\n(P3)"]
        n3["useFocusTrap.test.ts\n(P4)"]
        n4["AppShell.test.tsx\n(P5)"]
        n5["Accessibility.test.tsx\n(P6)"]
    end

    subgraph "Coverage gate"
        cov["≥ 80% overall\nnpx vitest run --coverage"]
    end

    n1 --> cov
    n2 --> cov
    n3 --> cov
    n4 --> cov
    n5 --> cov
    t1 --> cov
    t2 --> cov
    t3 --> cov

    style cov fill:#0b3d2e,color:#6affbe
```

---

## Summary Reference Card

| Prompt | Time | Files Changed | Files Created | Key Test Assertion |
|---|---|---|---|---|
| 1 | 10m | `tokens.json`, `theme.ts` | `theme.test.ts` | `DARK.adminBg === '#060e1a'` |
| 2 | 8m | `theme.ts` | _(appended to theme.test.ts)_ | `contrastRatio(LIGHT.green, '#fff') >= 4.5` |
| 3 | 12m | — | `AnnouncerContext.tsx`, `useAnnounce.ts`, `useAnnounce.test.ts` | `[role="status"]` present; message clears after 7s |
| 4 | 12m | — | `useFocusTrap.ts`, `useFocusTrap.test.ts` | Tab wraps last→first; Escape calls `onEscape` |
| 5 | 12m | `App.tsx` | `AppShell.test.tsx` | skip link href=`#main-content`; live regions present |
| 6 | 21m | `SkillCard.tsx`, `DivisionChip.tsx`, `AuthModal.tsx`, `Nav.tsx`, `HomeView.tsx` | `Accessibility.test.tsx` | `role=article`; `role=dialog`; keyboard Enter/Space |
| **Total** | **~75m** | **7 modified** | **8 created** | |
