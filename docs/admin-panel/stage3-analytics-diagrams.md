# Stage 3: Analytics Dashboard & Chart Components
## Visual Architecture Companion

This document is the visual companion to `stage3-analytics-guide.md`. All diagrams are Mermaid unless noted as ASCII.

---

## Diagram 1: Component Dependency Tree

This tree shows which components depend on which. Build order flows from leaves (top) to root (bottom).

```mermaid
graph TD
    %% Utilities — no deps
    CU[chartUtils.ts]
    MD[adminMockData.ts]

    %% Primitive hooks
    UCT[useChartTheme.ts]

    %% Primitive chart components
    EC[EmptyChart.tsx]
    SL[SparkLine.tsx]
    CTTP[CustomTooltip.tsx]

    %% Composite chart components
    ACB[AreaChartBase.tsx]
    DMC[DivisionMiniChart.tsx]
    DCG[DivisionChartGrid.tsx]
    TAC[TrendingAreaChart.tsx]
    SF[SubmissionFunnel.tsx]

    %% Admin UI
    SC[StatCard.tsx]
    ADV[AdminDashboardView.tsx]

    %% Dependencies
    CU --> MD
    CU --> TAC
    UCT --> ACB
    UCT --> SL
    UCT --> DMC
    UCT --> TAC
    UCT --> SC
    UCT --> SF
    UCT --> EC
    EC --> SL
    EC --> ACB
    SL --> SC
    CTTP --> ACB
    CTTP --> TAC
    ACB --> DMC
    DMC --> DCG
    SC --> ADV
    ACB --> ADV
    DCG --> ADV
    TAC --> ADV
    SF --> ADV
    MD --> ADV

    %% Styling
    style CU fill:#1e3248,stroke:#4b7dff,color:#ddeaf7
    style MD fill:#1e3248,stroke:#4b7dff,color:#ddeaf7
    style ECfill:#111f30,stroke:#1fd49e,color:#ddeaf7
    style SL fill:#111f30,stroke:#1fd49e,color:#ddeaf7
    style CTTP fill:#111f30,stroke:#1fd49e,color:#ddeaf7
    style ACB fill:#111f30,stroke:#a78bfa,color:#ddeaf7
    style DMC fill:#111f30,stroke:#a78bfa,color:#ddeaf7
    style DCG fill:#111f30,stroke:#a78bfa,color:#ddeaf7
    style TAC fill:#111f30,stroke:#a78bfa,color:#ddeaf7
    style SF fill:#111f30,stroke:#f2a020,color:#ddeaf7
    style SC fill:#0c1825,stroke:#ef5060,color:#ddeaf7
    style ADV fill:#0c1825,stroke:#ef5060,color:#ddeaf7
    style UCT fill:#060e1a,stroke:#22d3ee,color:#ddeaf7
```

---

## Diagram 2: AdminDashboardView Layout

ASCII layout showing the exact visual arrangement of the dashboard page.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ADMIN PANEL — left sidebar (Stage 2)         [dark/light toggle]           │
├────────────────┬────────────────────────────────────────────────────────────┤
│                │                                                             │
│  Nav Items     │  AdminDashboardView                                         │
│  • Dashboard ← │  ═══════════════════════════════════════════════════════   │
│  • Skills      │                                                             │
│  • Reviews     │  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  • Users       │  │ StatCard   │ │ StatCard   │ │ StatCard   │             │
│  • Flags       │  │ Pending    │ │ Installs   │ │ Active     │             │
│  • Audit Log   │  │ Reviews    │ │ (7d)       │ │ Users      │             │
│                │  │            │ │        ╱╲  │ │        ╱╲  │             │
│                │  │ ▓ 23       │ │ ▓ 1,842│  │ │ ▓ 847  │  │             │
│                │  │ +0%        │ │ +12.4% ╲╱  │ │ +8.2%  ╲╱  │             │
│                │  └────────────┘ └────────────┘ └────────────┘             │
│                │                                                             │
│                │  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│                │  │ StatCard   │ │ StatCard   │ │ StatCard   │             │
│                │  │ Published  │ │ Pass Rate  │ │ Changelog  │             │
│                │  │ Skills     │ │            │ │ Freshness  │             │
│                │  │            │ │            │ │            │             │
│                │  │ ▓ 312      │ │ ▓ 94%      │ │ ▓ 4d median│             │
│                │  │            │ │ +2.1%      │ │ -0.5%      │             │
│                │  └────────────┘ └────────────┘ └────────────┘             │
│                │                               Updated 2 min ago →          │
│                │                                                             │
│                │  Installs — Last 30 Days                                    │
│                │  ┌─────────────────────────────────────────────────────┐   │
│                │  │                          ╭─────╮                    │   │
│                │  │                    ╭─────╯     ╰──╮                 │   │
│                │  │              ╭─────╯              ╰──────╮          │   │
│                │  │        ╭─────╯                           ╰──╮       │   │
│                │  │  ╭─────╯                                    ╰──     │   │
│                │  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░    │   │
│                │  └─────────────────────────────────────────────────────┘   │
│                │  Feb 22    Feb 26    Mar 2    Mar 8    Mar 14   Mar 22      │
│                │                                                             │
│                │  Installs by Division                                       │
│                │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│                │  │ Eng Org  │ │ Prod Org │ │ Finance  │ │ People   │     │
│                │  │ 1.8k     │ │ 942      │ │ 287      │ │ 156      │     │
│                │  │[minichrt]│ │[minichrt]│ │[minichrt]│ │[minichrt]│     │
│                │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│                │  │ Ops      │ │ Executive│ │ Sales    │ │ Customer │     │
│                │  │ 203      │ │ 97       │ │ 412      │ │ 334      │     │
│                │  │[minichrt]│ │[minichrt]│ │[minichrt]│ │[minichrt]│     │
│                │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                │                                                             │
└────────────────┴────────────────────────────────────────────────────────────┘
```

---

## Diagram 3: StatCard Anatomy

```
┌─────────────────────────────────────────────────────────┐
│████████████████████ 3px gradient bar ███████████████████│  ← linear-gradient(90deg, color, color+'44')
│                                                         │
│  LABEL                                                  │  ← 11px/500 Outfit, C.muted
│  (11px/500)                                             │    padding-top: 14px, padding-x: 16px
│                                                         │
│  ┌──────────────────────────┐  ┌───────────────────┐   │
│  │ VALUE                    │  │                   │   │
│  │ 28px/800 Outfit          │  │   SparkLine       │   │  ← 64×32px LineChart
│  │ C.text                   │  │   (no axes,       │   │    bottom-right aligned
│  │                          │  │    no tooltip)    │   │
│  │ ┌──────────────────────┐ │  └───────────────────┘   │
│  │ │ +12.4%               │ │                          │  ← delta badge pill
│  │ │ 11px/600 Outfit      │ │                          │    green18 bg / red18 bg
│  │ │ C.green / C.red      │ │                          │    borderRadius: 99px
│  │ └──────────────────────┘ │                          │
│  │  vs last period          │                          │  ← 10px/400 Outfit, C.dim
│  │  10px/400 Outfit         │                          │    marginTop: 3px
│  └──────────────────────────┘                          │
│                                                         │  ← padding-bottom: 14px
└─────────────────────────────────────────────────────────┘
  border: 1px solid C.border      borderRadius: 12px
  background: C.surface           overflow: hidden
  hover → C.surfaceHi, borderHi, translateY(-1px), cardShadow
```

---

## Diagram 4: AreaChartBase Composition

```
ResponsiveContainer (width="100%", height=props.height)
│
└── AreaChart (data, margin)
    ├── Defs
    │   └── LinearGradient × N (one per series)
    │       ├── Stop (offset="0%", opacity=0.094) ← hex '18' = decimal 24 ÷ 256 ≈ 0.094
    │       └── Stop (offset="100%", opacity=0)
    │
    ├── CartesianGrid
    │   strokeDasharray="3 3"
    │   stroke=C.border          ← very subtle, same as card border
    │   vertical={false}         ← horizontal lines only
    │
    ├── XAxis
    │   dataKey={xKey}           ← default 'date'
    │   tick={ fontSize:9, fontFamily:"JetBrains Mono", fill:C.muted }
    │   axisLine={{ stroke:C.border }}
    │   tickLine={false}
    │   [hidden when compact=true]
    │
    ├── YAxis
    │   tick={ fontSize:9, fontFamily:"JetBrains Mono", fill:C.muted }
    │   axisLine={false}
    │   tickLine={false}
    │   tickFormatter={formatTick}
    │   [hidden when compact=true]
    │
    ├── Tooltip
    │   content={<CustomTooltip />}
    │   cursor={{ stroke:C.borderHi, strokeWidth:1 }}
    │
    └── Area × N (one per series)
        type="monotone"
        dataKey={series.dataKey}
        stroke={series.color}
        strokeWidth={1.5}
        fill="url(#grad-{dataKey})"
        dot={false}
        activeDot={{ r:4, fill:color, stroke:tooltipBg, strokeWidth:2 }}
        isAnimationActive={false}   ← REQUIRED: avoids jsdom animation errors
```

---

## Diagram 5: useChartTheme Token Mapping

```
useT() → Theme                         useChartTheme() → ChartTheme
──────────────────────────             ────────────────────────────────────────

C.border         ──────────────────►  gridStroke       (CartesianGrid stroke)
C.muted          ──────────────────►  axisStroke       (axis tick color)
C.surface        ──────────────────►  tooltipBg        (tooltip background)
C.borderHi       ──────────────────►  tooltipBorder    (tooltip border)
C.text           ──────────────────►  tooltipText      (tooltip label color)
C.accent         ──────────────────►  activeDot        (hover dot fill)

C.accent         ──────────────────►  seriesColors.installs
C.green          ──────────────────►  seriesColors.submissions
C.purple         ──────────────────►  seriesColors.reviews
C.amber          ──────────────────►  seriesColors.flagged
C.red            ──────────────────►  seriesColors.rejected
C.muted          ──────────────────►  seriesColors.views
'#22d3ee'        (constant) ────────►  seriesColors.forks
'#fb923c'        (constant) ────────►  seriesColors.favorites
'#84cc16'        (constant) ────────►  seriesColors.comments

gradientStop(color) returns:
  [ { offset:'0%',   color, opacity: 0.094 },   ← '18' hex suffix parsed to float
    { offset:'100%', color, opacity: 0     } ]
```

---

## Diagram 6: SubmissionFunnel SVG Layout

Pure SVG — no Recharts. Each gate is a trapezoid path.

```
     containerWidth = 100% of parent
     ┌────────────────────────────────────────────────────────┐  ← SVG viewport
     │                                                        │
     │  ████████████████████████████████████████████████████  │  ← Gate 1: Submitted
     │  ████  Submitted                                  120 ██  │    width = 100%
     │  ████████████████████████████████████████████████████  │    fill: ${C.muted}20
     │  ────────────────────────────────────────────────────  │    stroke: C.muted
     │                                                        │
     │    ██████████████████████████████████████████████      │  ← Gate 2: Under Review
     │    ██  Under Review                            80 ████  │    width = 80/120 = 66.7%
     │    ██████████████████████████████████████████████      │    fill: ${C.amber}20
     │    ──────────────────────────────────────────────      │    stroke: C.amber
     │                                                        │
     │         ██████████████████████████████████████         │  ← Gate 3: Approved
     │         ██  Approved                        55 ████    │    width = 55/120 = 45.8%
     │         ██████████████████████████████████████         │    fill: ${C.green}20
     │         ──────────────────────────────────────         │    stroke: C.green
     │                                                        │
     │              ████████████████████████████              │  ← Gate 4: Rejected
     │              ██  Rejected               25 ██          │    width = 25/120 = 20.8%
     │              ████████████████████████████              │    fill: ${C.red}20
     │                                                        │    stroke: C.red
     └────────────────────────────────────────────────────────┘

Trapezoid path formula (for gate i, given top width tw, bottom width bw):
  tlx = (containerWidth - tw) / 2
  trx = tlx + tw
  blx = (containerWidth - bw) / 2
  brx = blx + bw
  d = `M ${tlx} ${topY} L ${trx} ${topY} L ${brx} ${bottomY} L ${blx} ${bottomY} Z`

Width calculation:
  maxCount = gates[0].count  (Submitted is always widest)
  gateWidth(gate) = (gate.count / maxCount) * containerWidth

Gap between gates: 8px
Gate height: (totalHeight - gaps * 3) / 4
```

---

## Diagram 7: TrendingAreaChart Structure

```
TrendingAreaChart
│
├── [Toggle Control Row]
│   ├── <button DAU>   ← active: C.accent bg, white text; inactive: transparent, C.muted
│   ├── <button WAU>      border: 1px solid C.border, borderRadius: 6px (grouped pill)
│   └── <button MAU>
│
├── [Data Transform]
│   selectedData = { DAU: props.dau, WAU: props.wau, MAU: props.mau }[period]
│   rawValues    = selectedData.map(d => d.v)
│   avgValues    = rollingAverage(rawValues, 7)
│   chartData    = selectedData.map((d,i) => ({
│                    date: d.date,
│                    value: d.v,
│                    avg: avgValues[i] ?? undefined
│                  }))
│
└── [Recharts Composition]
    ResponsiveContainer (width="100%", height=props.height ?? 240)
    └── AreaChart (data=chartData)
        ├── Defs
        │   ├── LinearGradient#grad-value  (accent blue, opacity 0.094 → 0)
        │   └── LinearGradient#grad-avg    (no fill — fillOpacity=0)
        ├── CartesianGrid (dashed, C.border)
        ├── XAxis (date, JetBrains Mono 9px)
        ├── YAxis (JetBrains Mono 9px, formatTick)
        ├── Tooltip (content=<CustomTooltip />)
        ├── Area (dataKey="value", stroke=C.accent, fill="url(#grad-value)")
        └── Area (dataKey="avg", stroke=C.green, strokeDasharray="4 2",
                  fillOpacity=0, strokeWidth=1, dot=false)
                  ← 7-day rolling average overlay — dashed green, no area fill
```

---

## Diagram 8: DivisionChartGrid Responsive Breakpoints

```
Width > 640px:    4 columns
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ Eng  │ │ Prod │ │ Fin  │ │ HR   │
└──────┘ └──────┘ └──────┘ └──────┘
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ Ops  │ │ Exec │ │ Sales│ │ CS   │
└──────┘ └──────┘ └──────┘ └──────┘


Width 380px–640px: 2 columns
┌──────┐ ┌──────┐
│ Eng  │ │ Prod │
└──────┘ └──────┘
┌──────┐ ┌──────┐
│ Fin  │ │ HR   │
└──────┘ └──────┘
┌──────┐ ┌──────┐
│ Ops  │ │ Exec │
└──────┘ └──────┘
┌──────┐ ┌──────┐
│ Sales│ │ CS   │
└──────┘ └──────┘


Width < 380px: 1 column
┌──────┐
│ Eng  │
└──────┘
┌──────┐
│ Prod │
└──────┘
  ...
```

Media query implementation via scoped `<style>` tag (inline CSS cannot express breakpoints):
```css
.division-chart-grid { grid-template-columns: repeat(4,1fr); }
@media (max-width: 640px) { .division-chart-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 380px) { .division-chart-grid { grid-template-columns: 1fr; } }
```

---

## Diagram 9: Division Color Reference

Used in `DivisionMiniChart`, `DivisionChartGrid`, mock data, and `SubmissionFunnel` (for any division-filtered funnel views).

| Division (display name) | Slug key | Hex color | Sample |
|-------------------------|----------|-----------|--------|
| Engineering Org | `engineering-org` | `#4b7dff` | ■ blue |
| Product Org | `product-org` | `#a78bfa` | ■ violet |
| Finance & Legal | `finance-legal` | `#1fd49e` | ■ teal |
| People & HR | `people-hr` | `#f2a020` | ■ amber |
| Operations | `operations` | `#22d3ee` | ■ cyan |
| Executive Office | `executive-office` | `#ef5060` | ■ red |
| Sales & Marketing | `sales-marketing` | `#fb923c` | ■ orange |
| Customer Success | `customer-success` | `#84cc16` | ■ lime |

These are imported from `DIVISION_COLORS` in `@skillhub/shared-types`. Do not hardcode them in chart components — always reference `DIVISION_COLORS[division]` to stay in sync.

---

## Diagram 10: Mock Data Shape → Component Mapping

```
AdminAnalyticsSummary (adminMockData.ts)
│
├── stats
│   ├── pendingReviews ─────────────────► StatCard #1 (label: "Pending Reviews")
│   ├── installs7d ─────────────────────► StatCard #2 (label: "Installs (7d)")
│   ├── installs7dDelta ─────────────────► StatCard #2 delta badge
│   ├── dau ─────────────────────────────► StatCard #3 (label: "Active Users (DAU)")
│   ├── dauDelta ────────────────────────► StatCard #3 delta badge
│   ├── publishedSkills ─────────────────► StatCard #4 (label: "Published Skills")
│   ├── submissionPassRate ──────────────► StatCard #5 (label: "Pass Rate")
│   ├── submissionPassRateDelta ─────────► StatCard #5 delta badge
│   ├── changelogFreshnessDays ──────────► StatCard #6 (label: "Changelog Freshness")
│   └── changelogFreshnessDelta ─────────► StatCard #6 delta badge
│
├── installs30d ─────────────────────────► AreaChartBase (section: "Installs — Last 30 Days")
│   └── [last 7 items].map(v) ───────────► StatCard #2 sparkData
│
├── divisionInstalls[8] ─────────────────► DivisionChartGrid
│   ├── [0].installs7d ──────────────────► DivisionMiniChart (Engineering Org)
│   └── ... (×8)
│
├── trending
│   ├── dau ─────────────────────────────► TrendingAreaChart (DAU series)
│   │   └── [last 7 items].map(v) ───────► StatCard #3 sparkData
│   ├── wau ─────────────────────────────► TrendingAreaChart (WAU series)
│   └── mau ─────────────────────────────► TrendingAreaChart (MAU series)
│
├── funnel[4] ───────────────────────────► SubmissionFunnel
│   ├── [0] Submitted (muted)
│   ├── [1] Under Review (amber)
│   ├── [2] Approved (green)
│   └── [3] Rejected (red)
│
└── updatedAt ───────────────────────────► "Updated N min ago" label
```

---

## Diagram 11: Recharts Mock Strategy

```
Test Environment                         Production Environment
─────────────────────────────            ────────────────────────────────────

vi.mock('recharts')                      Real recharts module
         │                                          │
         ▼                                          ▼
src/__mocks__/recharts.ts               recharts npm package (~240KB)
         │
         ├── AreaChart → <div data-testid="recharts-areachart">
         ├── LineChart → <div data-testid="recharts-linechart">
         ├── Area      → <div data-testid="recharts-area">
         ├── Line      → <div data-testid="recharts-line">
         ├── XAxis     → <div data-testid="recharts-xaxis">
         ├── YAxis     → <div data-testid="recharts-yaxis">
         ├── CartesianGrid → <div data-testid="recharts-cartesiangrid">
         ├── Tooltip   → <div data-testid="recharts-tooltip">
         ├── ResponsiveContainer → passthrough div (no testid)
         ├── Defs      → passthrough div
         ├── Stop      → passthrough div
         └── LinearGradient → passthrough div

Test assertions use data-testid:
  expect(screen.getByTestId('recharts-areachart')).toBeInTheDocument()
  expect(screen.getAllByTestId('recharts-area').length).toBe(2)

SubmissionFunnel uses NO Recharts — test via:
  expect(container.querySelector('svg')).toBeInTheDocument()
  expect(container.querySelectorAll('path').length).toBe(4)
```

---

## Diagram 12: Bundle Split — Before and After Stage 3

```
Before Stage 3 (Stage 2 output):
─────────────────────────────────
dist/assets/
  index-[hash].js          ~180KB   ← React + React Router + main app
  AdminDashboardView-[hash].js  ~4KB  ← Stage 2 stub view (nearly empty)

After Stage 3:
─────────────────────────────────
dist/assets/
  index-[hash].js          ~180KB   ← UNCHANGED (recharts not in main chunk)
  AdminDashboardView-[hash].js  ~244KB  ← recharts + all chart components

Load behavior:
  User visits /              → loads index chunk only
  User visits /admin         → lazy-loads admin chunk on demand
  Admin chunk is cached after first visit

CRITICAL: If index chunk grows after this stage, recharts was
accidentally imported outside the lazy boundary. Check:
  1. Is recharts imported in App.tsx or any non-admin file?
  2. Is AdminDashboardView imported statically anywhere?
  3. Does any shared lib (lib/theme.ts, etc.) import recharts?
```

---

## Diagram 13: GradientStop Opacity Convention

The `0.094` opacity value is not arbitrary. It matches the existing `${color}18` alpha convention used throughout the codebase (SkillCard, DivisionChip, StatCard badges).

```
Hex alpha suffix '18' in CSS:
  '18' hexadecimal = 24 decimal
  24 / 255 = 0.094... (≈ 9.4%)

Examples in existing code:
  background: `${accent}18`      → ~9.4% opacity
  background: `${color}14`       → 14/255 = 5.5% opacity (lighter, used in tags)
  background: `${accent}25`      → 25/255 = 14.5% opacity (stronger, active states)

Chart gradient:
  Stop at 0%:   opacity 0.094 → area fill has ~9.4% opacity at top
  Stop at 100%: opacity 0     → fades to transparent at baseline

This creates a subtle fill that is visible in dark mode and
readable in light mode without overwhelming the chart lines.
```

---

## Diagram 14: CustomTooltip Layout

```
┌─────────────────────────────────────────┐
│  Jan 5, 2026                            │  ← JetBrains Mono, 10px, C.muted
│                                         │    margin-bottom: 6px
│  Installs              1,842            │  ← name: Outfit 12px/600, C.text
│                                         │    value: JetBrains Mono 13px/600, entry.color
│  Avg (7d)              1,654            │  ← repeat per payload entry
│                                         │
└─────────────────────────────────────────┘
  background: C.surface          border-radius: 8px
  border: 1px solid C.borderHi   padding: 8px 12px
  box-shadow: C.cardShadow

Row layout: display:flex, justifyContent:space-between, gap:16px, marginBottom:2px
Only rendered when active={true} — returns null otherwise
```

---

## Diagram 15: Theme Responsiveness Flow

```
User clicks dark/light toggle
          │
          ▼
ThemeContext updates → new Theme object (DARK or LIGHT)
          │
          ├──► useT() in all components re-runs
          │         │
          │         └──► useChartTheme() re-derives all chart tokens
          │                   │
          │                   ├──► gridStroke changes (C.border)
          │                   ├──► axisStroke changes (C.muted)
          │                   ├──► tooltipBg changes (C.surface)
          │                   └──► seriesColors.installs changes (C.accent)
          │
          └──► React re-renders all chart components
                    │
                    ├──► CartesianGrid gets new stroke color
                    ├──► Axis ticks get new fill color
                    ├──► Tooltip gets new background
                    └──► LinearGradient stops use new series color
                              (gradient is re-rendered with new color hex)

Fixed series colors (forks='#22d3ee', etc.) do NOT change with theme.
These are semantic data colors, not UI chrome colors.
```

---

## Cross-Reference: Stage 2 Contracts

These are the Stage 2 outputs that Stage 3 depends on. If Stage 2 used different names or paths, adapt accordingly.

| Stage 2 Output | Stage 3 Usage |
|----------------|---------------|
| `AdminLayout` component with `adminBg`, `adminSurfaceSide` tokens | `AdminDashboardView` renders inside this layout |
| Lazy-loaded `AdminDashboardView` at `/admin` route | Stage 3 replaces the stub implementation |
| `Suspense` boundary wrapping admin routes | Ensures recharts chunk loads asynchronously |
| `ThemeProvider` and `useT()` hook | Used by all chart components via `useChartTheme()` |
| `C.surface`, `C.surfaceHi`, `C.border`, `C.borderHi` tokens | Used in StatCard, EmptyChart, DivisionMiniChart |
| `C.accent`, `C.green`, `C.amber`, `C.red`, `C.purple` | Used in StatCard accent bars, delta badges |
| `C.muted`, `C.dim` | Used in chart axis labels, empty state text |
| `DIVISION_COLORS` from `@skillhub/shared-types` | Used in DivisionMiniChart, DivisionChartGrid |
| `api.get<T>()` from `lib/api.ts` | Used in `AdminDashboardView` data fetching |
