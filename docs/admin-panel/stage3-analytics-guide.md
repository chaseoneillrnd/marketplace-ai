# Stage 3: Analytics Dashboard & Chart Components
## SkillHub Admin Panel — Technical Implementation Guide

**Prerequisites:** Stage 1 (foundation — theme tokens, adminBg, adminSurfaceSide, AdminLayout) and Stage 2 (admin shell — routing, nav, lazy loading, stub views) must be complete.

**Estimated implementation time:** 90–120 minutes (agent-driven, TDD)

**New dependency:** `recharts` (~240KB gzipped) — admin chunk only, zero impact on main bundle because Stage 2 established lazy loading.

---

## Overview

This stage replaces the AdminDashboardView stub from Stage 2 with a fully functional analytics landing page. It introduces all chart primitives, a StatCard component, mock data scaffolding, and the `useChartTheme` hook that drives theme-responsive chart styling.

Everything in this stage lives in the admin code path. No public-facing files are modified. The recharts import is bounded by the lazy boundary already in place.

---

## 0. Dependency Installation

Add `recharts` and its type declarations to `apps/web/package.json` **before writing any implementation code**. The type package is a devDependency.

```json
// apps/web/package.json — add to "dependencies"
"recharts": "^2.12.7"

// add to "devDependencies"
"@types/recharts": "^1.8.29"
```

Run `npm install` (or the project's package manager) from `apps/web/`.

Recharts ships its own types since v2.6, so `@types/recharts` may resolve to an empty shim — that is expected. If the package manager warns about it being unnecessary, omit the devDependency entry.

**Verify after install:**
```
tsc --noEmit   # must pass clean
vite build     # check that admin chunk grows ~240KB, main chunk unchanged
```

---

## 1. File Tree for This Stage

```
apps/web/src/
├── hooks/
│   └── useChartTheme.ts               ← new
├── components/charts/
│   ├── EmptyChart.tsx                 ← new
│   ├── SparkLine.tsx                  ← new
│   ├── AreaChartBase.tsx              ← new
│   ├── CustomTooltip.tsx              ← new
│   ├── DivisionMiniChart.tsx          ← new
│   ├── DivisionChartGrid.tsx          ← new
│   ├── TrendingAreaChart.tsx          ← new
│   ├── SubmissionFunnel.tsx           ← new
│   └── chartUtils.ts                  ← new
├── components/admin/
│   └── StatCard.tsx                   ← new
├── views/admin/
│   └── AdminDashboardView.tsx         ← replaces Stage 2 stub
└── lib/
    └── adminMockData.ts               ← new
```

Test files mirror this tree under `src/__tests__/admin/` or co-located `.test.tsx` files — agent chooses, but must be consistent.

---

## 2. TDD Mandate

**RED first.** For every file below, write the test file first and confirm it fails before writing the implementation. The implementation is only allowed to do what makes the tests pass — no extra surface area.

Recharts must be mocked in the test environment. Add this mock once, at the top level in `src/test-setup.ts` or via a dedicated `src/__mocks__/recharts.ts` file:

```typescript
// src/__mocks__/recharts.ts
// Recharts renders SVG via canvas-dependent internals that break in jsdom.
// All chart components are replaced with identifiable data-testid stubs.
import { vi } from 'vitest';
const stub = (name: string) => {
  const C = ({ children, 'data-testid': dt }: React.PropsWithChildren<{ 'data-testid'?: string }>) => (
    <div data-testid={dt ?? `recharts-${name.toLowerCase()}`}>{children}</div>
  );
  C.displayName = name;
  return C;
};
export const AreaChart = stub('AreaChart');
export const LineChart = stub('LineChart');
export const Area = stub('Area');
export const Line = stub('Line');
export const XAxis = stub('XAxis');
export const YAxis = stub('YAxis');
export const CartesianGrid = stub('CartesianGrid');
export const Tooltip = stub('Tooltip');
export const ResponsiveContainer = ({ children }: React.PropsWithChildren<object>) => <div>{children}</div>;
export const LinearGradient = stub('LinearGradient');
export const Defs = stub('Defs');
export const Stop = stub('Stop');
export const ReferenceLine = stub('ReferenceLine');
```

Add `vi.mock('recharts')` at the top of any test file that imports chart components, or configure `moduleNameMapper` in `vite.config.ts` to auto-apply the mock in test mode:

```typescript
// vite.config.ts — inside test: {}
moduleNameMapper: {
  '^recharts$': path.resolve(__dirname, 'src/__mocks__/recharts.ts'),
},
```

Using the mapper approach means individual test files do not need a manual `vi.mock('recharts')` call.

---

## 3. `hooks/useChartTheme.ts`

### What it does

Derives chart-specific color tokens from the current theme. All chart components call this hook — they never reach into `useT()` directly for visual values. This centralizes theme changes to one place.

### Interface

```typescript
export interface ChartTheme {
  gridStroke: string;       // C.border
  axisStroke: string;       // C.muted
  tooltipBg: string;        // C.surface
  tooltipBorder: string;    // C.borderHi
  tooltipText: string;      // C.text
  activeDot: string;        // C.accent
  seriesColors: SeriesColors;
  gradientStop: (color: string) => GradientStop[];
}

export interface SeriesColors {
  installs: string;      // C.accent
  submissions: string;   // C.green
  reviews: string;       // C.purple
  flagged: string;       // C.amber
  rejected: string;      // C.red
  forks: string;         // '#22d3ee'
  favorites: string;     // '#fb923c'
  views: string;         // C.muted
  comments: string;      // '#84cc16'
}

export interface GradientStop {
  offset: string;
  color: string;
  opacity: number;
}
```

### Implementation notes

- Call `useT()` once at the top of the hook; derive all values from that single `C` reference.
- `gradientStop(color)` returns a two-element array: `[{offset:'0%', color, opacity:0.094}, {offset:'100%', color, opacity:0}]`. The opacity value 0.094 is the parsed numeric equivalent of the hex suffix `18` (24/256 ≈ 0.094) — this matches the `${accent}18` convention used throughout the existing SkillCard and DivisionChip components.
- Fixed colors (`forks`, `favorites`, `comments`) are hardcoded constants, not theme tokens, because they are semantic data series colors that do not invert with dark/light mode.

### Tests

```typescript
// useChartTheme.test.ts
describe('useChartTheme', () => {
  it('returns gridStroke equal to theme border', () => { ... })
  it('returns seriesColors.installs equal to theme accent', () => { ... })
  it('gradientStop returns two stops with correct offsets', () => { ... })
  it('gradientStop top stop has opacity 0.094', () => { ... })
  it('gradientStop bottom stop has opacity 0', () => { ... })
  it('responds to theme change — dark vs light returns different gridStroke', () => { ... })
})
```

Test with `renderHook` from `@testing-library/react`, wrapping with `ThemeProvider`.

---

## 4. `components/charts/chartUtils.ts`

Pure utility functions — no React, no Recharts. These are the highest-priority tests because they are pure functions with deterministic output.

### Functions

#### `formatTick(value: number): string`

Abbreviates large numbers for axis labels:
- `value < 1000` → `String(value)`
- `value < 1_000_000` → one decimal place, trailing zero stripped, `k` suffix. `1200` → `'1.2k'`, `1000` → `'1k'`, `1500` → `'1.5k'`
- `value >= 1_000_000` → `m` suffix, same rule

#### `abbreviateCount(value: number): string`

Same rounding logic as `formatTick` but used for display badges (StatCard delta, DivisionMiniChart count). The implementations may share a private helper.

#### `rollingAverage(data: number[], window: number): (number | null)[]`

Computes a trailing rolling average over `data` with the given `window` size.
- Returns an array of the same length as `data`.
- The first `window - 1` values return `null` (not enough history to compute).
- Window size 1 returns the data unchanged (each value is its own average).
- Empty array input returns empty array.
- If `window` exceeds data length, all values return `null`.

#### `generateDateLabels(days: number, endDate?: Date): string[]`

Returns an array of `days` strings in `'MMM D'` format (e.g., `'Jan 5'`), ending at `endDate` (defaults to today). Used to populate mock data and axis labels consistently.

### Tests (write these first)

```typescript
describe('formatTick', () => {
  it('returns string for values under 1000', () => expect(formatTick(500)).toBe('500'))
  it('abbreviates 1200 to 1.2k', () => expect(formatTick(1200)).toBe('1.2k'))
  it('abbreviates 1000 to 1k (no trailing decimal)', () => expect(formatTick(1000)).toBe('1k'))
  it('abbreviates 1500 to 1.5k', () => expect(formatTick(1500)).toBe('1.5k'))
  it('abbreviates 1_200_000 to 1.2m', () => expect(formatTick(1_200_000)).toBe('1.2m'))
})

describe('rollingAverage', () => {
  it('returns null for first window-1 entries', () => {
    const result = rollingAverage([1,2,3,4,5], 3);
    expect(result[0]).toBeNull();
    expect(result[1]).toBeNull();
    expect(result[2]).toBeCloseTo(2);
  })
  it('window 1 returns data unchanged', () => {
    expect(rollingAverage([10,20,30], 1)).toEqual([10,20,30]);
  })
  it('handles empty input', () => expect(rollingAverage([], 3)).toEqual([]))
  it('window exceeds length — all null', () => {
    expect(rollingAverage([1,2], 5)).toEqual([null, null]);
  })
})
```

---

## 5. `components/charts/EmptyChart.tsx`

### Purpose

Renders whenever a chart component receives an empty or null data array. Used as the default empty state for all chart components.

### Visual spec

- Container: full width, height defaults to 120px (overridable via `height` prop)
- Background: `C.surfaceHi`
- Border: `1px dashed ${C.border}`
- Border radius: `8px`
- Content: centered flex column
  - Icon: `'◌'` (U+25CC) or a simple SVG circle, 24px, `C.dim` color
  - Text: `'No data yet'`, 12px, 400 weight, `C.dim`, Outfit font

### Props

```typescript
interface EmptyChartProps {
  height?: number;
  label?: string;  // overrides "No data yet"
}
```

### Tests

```typescript
describe('EmptyChart', () => {
  it('renders with default label', () => {
    render(<EmptyChart />, { wrapper })
    expect(screen.getByText('No data yet')).toBeInTheDocument()
  })
  it('renders with custom label', () => {
    render(<EmptyChart label="Loading..." />, { wrapper })
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })
  it('applies height prop', () => {
    const { container } = render(<EmptyChart height={80} />, { wrapper })
    expect(container.firstChild).toHaveStyle({ height: '80px' })
  })
})
```

---

## 6. `components/charts/SparkLine.tsx`

### Purpose

A minimal 64×32 line chart used inside StatCard to show 7-day trend. No axes, no tooltip, no animation, no interaction. Purely visual.

### Recharts composition

```
LineChart (width, height, margin all 0)
  └── Line
        dataKey="v"
        stroke={color}
        strokeWidth={1.5}
        dot={false}
        isAnimationActive={false}
```

### Props

```typescript
interface SparkLineProps {
  data: Array<{ v: number }>;
  color: string;
  width?: number;   // default 64
  height?: number;  // default 32
}
```

### Empty state

If `data.length < 2`, render `<EmptyChart height={height ?? 32} label="" />` — a blank placeholder, no text.

### Tests

```typescript
describe('SparkLine', () => {
  it('renders recharts LineChart when data provided', () => {
    const data = Array.from({length:7}, (_,i) => ({v: i*10}))
    render(<SparkLine data={data} color="#4b7dff" />, { wrapper })
    // recharts mock renders a div with data-testid="recharts-linechart"
    expect(screen.getByTestId('recharts-linechart')).toBeInTheDocument()
  })
  it('renders empty state when data has fewer than 2 points', () => {
    render(<SparkLine data={[{v:1}]} color="#4b7dff" />, { wrapper })
    // EmptyChart renders — recharts LineChart absent
    expect(screen.queryByTestId('recharts-linechart')).not.toBeInTheDocument()
  })
  it('defaults to 64×32', () => {
    // verify props forwarded correctly — check via mock inspection
  })
})
```

---

## 7. `components/charts/CustomTooltip.tsx`

### Purpose

Replaces Recharts' default tooltip content. Used by both `AreaChartBase` and `TrendingAreaChart`.

### Props

Recharts passes `active`, `payload`, and `label` to custom tooltip components. Accept the standard Recharts `TooltipProps<number, string>` type.

```typescript
import type { TooltipProps } from 'recharts';

export function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) { ... }
```

### Visual spec

- Outer container: inline styles, no className
  - Background: `C.surface`
  - Border: `1px solid ${C.borderHi}`
  - Border radius: `8px`
  - Padding: `8px 12px`
  - Box shadow: `C.cardShadow`
- Date/label row: JetBrains Mono, 10px, `C.muted`, margin-bottom 6px
- For each entry in `payload`:
  - Series name: Outfit, 12px, 600 weight, `C.text`
  - Value: JetBrains Mono, 13px, 600 weight, colored with `entry.color` (the series color passed by Recharts)
  - Layout: name left, value right, flex row with space-between

### Tests

```typescript
describe('CustomTooltip', () => {
  it('renders nothing when active is false', () => {
    const { container } = render(
      <CustomTooltip active={false} payload={[]} label="Jan 1" />,
      { wrapper }
    )
    expect(container.firstChild).toBeNull()
  })
  it('renders label and value when active', () => {
    const payload = [{ name: 'Installs', value: 42, color: '#4b7dff' }]
    render(<CustomTooltip active={true} payload={payload as never} label="Jan 5" />, { wrapper })
    expect(screen.getByText('Jan 5')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('Installs')).toBeInTheDocument()
  })
  it('renders multiple payload entries', () => {
    const payload = [
      { name: 'Installs', value: 42, color: '#4b7dff' },
      { name: 'Avg', value: 38, color: '#1fd49e' },
    ]
    render(<CustomTooltip active={true} payload={payload as never} label="Jan 5" />, { wrapper })
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('38')).toBeInTheDocument()
  })
})
```

---

## 8. `components/charts/AreaChartBase.tsx`

### Purpose

The canonical reusable area chart. Used directly in `AdminDashboardView` for the 30-day installs chart, and composed into `DivisionMiniChart`. `TrendingAreaChart` has its own composition but may import `AreaChartBase` to stay DRY.

### Props

```typescript
export interface AreaSeries {
  dataKey: string;
  color: string;
  name?: string;
  gradientId?: string;  // auto-generated if omitted: "grad-{dataKey}"
}

interface AreaChartBaseProps {
  data: Record<string, unknown>[];
  series: AreaSeries[];
  xKey?: string;        // default 'date'
  height?: number;      // default 220
  compact?: boolean;    // removes Y axis, reduces padding, used in mini charts
  showLegend?: boolean; // default false
}
```

### Recharts composition

```
ResponsiveContainer (width="100%", height=props.height)
  AreaChart (data, margin={top:4, right:4, bottom:0, left: compact?0:-8})
    Defs
      LinearGradient (id="grad-{dataKey}", x1=0, y1=0, x2=0, y2=1) for each series
        Stop (offset="0%", stopColor=color, stopOpacity=0.094)
        Stop (offset="100%", stopColor=color, stopOpacity=0)
    CartesianGrid (strokeDasharray="3 3", stroke=chartTheme.gridStroke, vertical=false)
    XAxis (dataKey=xKey, tick={fontSize:9, fontFamily:"JetBrains Mono", fill:chartTheme.axisStroke})
    YAxis (hidden when compact, tick={fontSize:9, ...same as XAxis})
    Tooltip (content=<CustomTooltip />, cursor={{stroke:chartTheme.borderHi}})
    Area (for each series)
      type="monotone"
      dataKey={series.dataKey}
      stroke={series.color}
      strokeWidth={1.5}
      fill={`url(#grad-${series.dataKey})`}
      dot={false}
      activeDot={{r:4, fill:series.color, stroke:chartTheme.tooltipBg, strokeWidth:2}}
      isAnimationActive={false}
```

### Key implementation notes

- Generate gradient IDs deterministically from `dataKey` to avoid React key collisions when multiple series use the same chart.
- When `compact=true`, hide both axes entirely (pass `hide={true}` to XAxis and YAxis) and set `margin` to `{top:0, right:0, bottom:0, left:0}`.
- When `data` is empty or has fewer than 2 points, render `<EmptyChart height={height} />` instead of the chart.
- The `cartesianGrid` stroke is `chartTheme.gridStroke` (`C.border`), not `C.dim` — the grid should be very subtle.

### Tests

```typescript
describe('AreaChartBase', () => {
  const mockData = Array.from({length:7}, (_,i) => ({ date:`Jan ${i+1}`, installs: i*10 }))
  const series = [{ dataKey: 'installs', color: '#4b7dff', name: 'Installs' }]

  it('renders AreaChart when data is provided', () => {
    render(<AreaChartBase data={mockData} series={series} />, { wrapper })
    expect(screen.getByTestId('recharts-areachart')).toBeInTheDocument()
  })
  it('renders EmptyChart when data is empty', () => {
    render(<AreaChartBase data={[]} series={series} />, { wrapper })
    expect(screen.getByText('No data yet')).toBeInTheDocument()
    expect(screen.queryByTestId('recharts-areachart')).not.toBeInTheDocument()
  })
  it('renders EmptyChart when data has 1 point', () => {
    render(<AreaChartBase data={[{date:'Jan 1', installs:10}]} series={series} />, { wrapper })
    expect(screen.getByText('No data yet')).toBeInTheDocument()
  })
  it('renders one Area element per series', () => {
    const twoSeries = [
      { dataKey: 'installs', color: '#4b7dff' },
      { dataKey: 'submissions', color: '#1fd49e' },
    ]
    const twoData = Array.from({length:7}, (_,i) => ({ date:`Jan ${i+1}`, installs:i, submissions:i*2 }))
    render(<AreaChartBase data={twoData} series={twoSeries} />, { wrapper })
    expect(screen.getAllByTestId('recharts-area').length).toBe(2)
  })
})
```

---

## 9. `components/charts/DivisionMiniChart.tsx`

### Purpose

A small self-contained chart card for a single division. Composed into `DivisionChartGrid`.

### Props

```typescript
interface DivisionMiniChartProps {
  division: string;         // slug key, e.g. 'engineering-org'
  displayName: string;      // e.g. 'Engineering Org'
  color: string;            // division color hex
  installData: Array<{ date: string; v: number }>;
  totalInstalls: number;    // integer, shown in badge
}
```

### Visual spec

- Container: `C.surface` bg, `1px solid ${C.border}` border, `8px` radius, padding `12px 12px 8px`
- Header row (flex, space-between, align center, margin-bottom 8px):
  - Left: division name, 12px/600, Outfit, `C.text`
  - Right: count badge — `abbreviateCount(totalInstalls)`, 10px/600, JetBrains Mono, division `color`, background `${color}14`, border `1px solid ${color}22`, padding `1px 7px`, radius `99px`
- Chart: `<AreaChartBase data={installData.map(d => ({date:d.date, v:d.v}))} series={[{dataKey:'v', color}]} height={80} compact={true} />`

### Tests

```typescript
describe('DivisionMiniChart', () => {
  const props = {
    division: 'engineering-org',
    displayName: 'Engineering Org',
    color: '#4b7dff',
    installData: Array.from({length:7}, (_,i) => ({date:`Jan ${i+1}`, v:i*5})),
    totalInstalls: 1842,
  }

  it('renders division name', () => {
    render(<DivisionMiniChart {...props} />, { wrapper })
    expect(screen.getByText('Engineering Org')).toBeInTheDocument()
  })
  it('renders abbreviated install count', () => {
    render(<DivisionMiniChart {...props} />, { wrapper })
    expect(screen.getByText('1.8k')).toBeInTheDocument()
  })
  it('renders AreaChartBase', () => {
    render(<DivisionMiniChart {...props} />, { wrapper })
    expect(screen.getByTestId('recharts-areachart')).toBeInTheDocument()
  })
  it('shows empty chart when no data', () => {
    render(<DivisionMiniChart {...props} installData={[]} />, { wrapper })
    expect(screen.getByText('No data yet')).toBeInTheDocument()
  })
})
```

---

## 10. `components/charts/DivisionChartGrid.tsx`

### Purpose

Renders eight `DivisionMiniChart` cards in a 4×2 responsive grid.

### Props

```typescript
interface DivisionChartGridProps {
  divisions: DivisionMiniChartProps[];  // must be 8 items (one per division)
  loading?: boolean;
}
```

### Responsive layout via inline style

```typescript
const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: '12px',
  // Responsive overrides applied via a <style> tag injected once into the component
};
```

Because this stage uses inline styles throughout (no CSS modules, no className), implement responsiveness with a scoped `<style>` tag:

```tsx
// Inside the component return, before the grid div:
<style>{`
  .division-chart-grid { grid-template-columns: repeat(4,1fr); }
  @media (max-width: 640px) { .division-chart-grid { grid-template-columns: repeat(2,1fr); } }
  @media (max-width: 380px) { .division-chart-grid { grid-template-columns: 1fr; } }
`}</style>
```

Then apply `className="division-chart-grid"` to the grid container **in addition to** the inline `display:grid` and `gap` styles. This is the only use of className in this stage — it is justified by the requirement to use CSS media queries, which cannot be expressed as inline styles.

### Loading state

When `loading={true}`, render 8 skeleton placeholder divs at the same size as a DivisionMiniChart (`height: 130px`), with `C.surfaceHi` background and `8px` radius. Use `data-testid="division-skeleton"`.

### Tests

```typescript
describe('DivisionChartGrid', () => {
  const makeDivision = (slug: string, name: string, color: string) => ({
    division: slug, displayName: name, color,
    installData: Array.from({length:7}, (_,i) => ({date:`Jan ${i+1}`, v:i*3})),
    totalInstalls: 500,
  })
  const divisions = [
    makeDivision('engineering-org','Engineering Org','#4b7dff'),
    makeDivision('product-org','Product Org','#a78bfa'),
    makeDivision('finance-legal','Finance & Legal','#1fd49e'),
    makeDivision('people-hr','People & HR','#f2a020'),
    makeDivision('operations','Operations','#22d3ee'),
    makeDivision('executive-office','Executive Office','#ef5060'),
    makeDivision('sales-marketing','Sales & Marketing','#fb923c'),
    makeDivision('customer-success','Customer Success','#84cc16'),
  ]

  it('renders 8 DivisionMiniChart components', () => {
    render(<DivisionChartGrid divisions={divisions} />, { wrapper })
    expect(screen.getAllByText(/Org|Legal|HR|Operations|Office|Marketing|Success/).length).toBeGreaterThanOrEqual(8)
  })
  it('renders 8 skeletons when loading', () => {
    render(<DivisionChartGrid divisions={divisions} loading={true} />, { wrapper })
    expect(screen.getAllByTestId('division-skeleton').length).toBe(8)
  })
})
```

---

## 11. `components/charts/TrendingAreaChart.tsx`

### Purpose

Shows platform engagement trends with DAU / WAU / MAU toggle and a 7-day rolling average overlay.

### Props

```typescript
type TrendPeriod = 'DAU' | 'WAU' | 'MAU';

interface TrendingAreaChartProps {
  dau: Array<{ date: string; v: number }>;
  wau: Array<{ date: string; v: number }>;
  mau: Array<{ date: string; v: number }>;
  height?: number;  // default 240
}
```

### State

```typescript
const [period, setPeriod] = useState<TrendPeriod>('DAU');
```

### Data transformation

Before rendering, derive the selected series and compute its rolling average:

```typescript
const selectedData = { DAU: dau, WAU: wau, MAU: mau }[period];
const rawValues = selectedData.map(d => d.v);
const avgValues = rollingAverage(rawValues, 7);

const chartData = selectedData.map((d, i) => ({
  date: d.date,
  value: d.v,
  avg: avgValues[i] ?? undefined,  // null → undefined so Recharts skips the point
}));
```

### Recharts composition

Two series on one chart:
1. `value` — primary, `chartTheme.seriesColors.installs` (accent blue)
2. `avg` — secondary overlay, `chartTheme.seriesColors.submissions` (green), `strokeDasharray="4 2"` (dashed), `strokeWidth={1}`, no fill (fill="none" or `fillOpacity={0}`)

Use `<AreaChartBase>` with `series` prop if it can express all of the above, OR compose the Recharts primitives directly here. Composing directly is recommended for the dashed overlay — `AreaChartBase` does not currently accept `strokeDasharray` per series.

### Toggle control

Three-button segmented control above the chart:

```tsx
{(['DAU','WAU','MAU'] as TrendPeriod[]).map(p => (
  <button
    key={p}
    onClick={() => setPeriod(p)}
    style={{
      padding: '3px 12px',
      fontSize: '11px',
      fontWeight: 600,
      fontFamily: "'JetBrains Mono',monospace",
      border: 'none',
      cursor: 'pointer',
      background: period === p ? C.accent : 'transparent',
      color: period === p ? '#fff' : C.muted,
      borderRadius: p === 'DAU' ? '6px 0 0 6px' : p === 'MAU' ? '0 6px 6px 0' : '0',
      transition: 'background 0.15s, color 0.15s',
    }}
  >
    {p}
  </button>
))}
```

Wrap all three in a flex container with `border: 1px solid ${C.border}` and `borderRadius: 6px`.

### Tests

```typescript
describe('TrendingAreaChart', () => {
  const makeData = (n: number) => Array.from({length:n}, (_,i) => ({date:`Jan ${i+1}`, v:i*5+10}))
  const props = { dau: makeData(30), wau: makeData(12), mau: makeData(12) }

  it('renders DAU by default', () => {
    render(<TrendingAreaChart {...props} />, { wrapper })
    // toggle shows DAU as active
    const dauBtn = screen.getByText('DAU')
    expect(dauBtn).toBeInTheDocument()
  })
  it('switches to WAU on click', async () => {
    const { user } = setup()  // @testing-library/user-event setup
    render(<TrendingAreaChart {...props} />, { wrapper })
    await user.click(screen.getByText('WAU'))
    // chart re-renders — no crash, WAU button styled as active
    expect(screen.getByText('WAU')).toBeInTheDocument()
  })
  it('renders chart elements', () => {
    render(<TrendingAreaChart {...props} />, { wrapper })
    expect(screen.getByTestId('recharts-areachart')).toBeInTheDocument()
  })
  it('shows empty chart when dau data is empty', () => {
    render(<TrendingAreaChart {...props} dau={[]} />, { wrapper })
    expect(screen.getByText('No data yet')).toBeInTheDocument()
  })
})
```

---

## 12. `components/charts/SubmissionFunnel.tsx`

### Purpose

A pure SVG funnel visualization showing the 4-gate submission pipeline. Does **not** use Recharts. This is the only chart in this stage that has zero Recharts dependency.

### Why pure SVG

The funnel shape (trapezoids narrowing downward) cannot be expressed cleanly with Recharts bar charts without substantial customization. Pure SVG is simpler, more precise, and has no bundle cost.

### Props

```typescript
interface FunnelGate {
  label: string;
  count: number;
  color: string;
}

interface SubmissionFunnelProps {
  gates?: FunnelGate[];  // defaults to 4 standard gates from mock data
  height?: number;       // default 200
}
```

### Default gate colors (semantic)

| Gate | Color token |
|------|-------------|
| Submitted | `C.muted` |
| Under Review | `C.amber` |
| Approved | `C.green` |
| Rejected | `C.red` |

### SVG layout

The funnel is drawn as 4 trapezoid paths, stacked vertically. The widest (Submitted) is at the top; each subsequent gate is proportionally narrower based on `count / maxCount`. Each trapezoid is:
- Height: `(totalHeight - gaps) / 4` (equal height per gate)
- Width: proportional to `count / maxCount * containerWidth`
- Centered horizontally
- Fill: `${gate.color}20` (alpha 0.125 — hex `20`)
- Stroke: `gate.color`
- Stroke width: `1.5`

Text labels overlay each trapezoid:
- Gate name: 11px, Outfit, 600, `C.text`, centered
- Count: 10px, JetBrains Mono, 400, `gate.color`, centered below name

### Implementation note on SVG path

Each trapezoid path: given top-left x (`tlx`), top-right x (`trx`), bottom-left x (`blx`), bottom-right x (`brx`), and y coordinates for top/bottom edges:

```
d={`M ${tlx} ${topY} L ${trx} ${topY} L ${brx} ${bottomY} L ${blx} ${bottomY} Z`}
```

### Tests

```typescript
describe('SubmissionFunnel', () => {
  const gates: FunnelGate[] = [
    { label: 'Submitted', count: 120, color: '#517898' },
    { label: 'Under Review', count: 80, color: '#f2a020' },
    { label: 'Approved', count: 55, color: '#1fd49e' },
    { label: 'Rejected', count: 25, color: '#ef5060' },
  ]

  it('renders an SVG element', () => {
    const { container } = render(<SubmissionFunnel gates={gates} />, { wrapper })
    expect(container.querySelector('svg')).toBeInTheDocument()
  })
  it('renders 4 gate labels', () => {
    render(<SubmissionFunnel gates={gates} />, { wrapper })
    expect(screen.getByText('Submitted')).toBeInTheDocument()
    expect(screen.getByText('Under Review')).toBeInTheDocument()
    expect(screen.getByText('Approved')).toBeInTheDocument()
    expect(screen.getByText('Rejected')).toBeInTheDocument()
  })
  it('renders gate counts', () => {
    render(<SubmissionFunnel gates={gates} />, { wrapper })
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()
  })
  it('renders 4 path elements for trapezoids', () => {
    const { container } = render(<SubmissionFunnel gates={gates} />, { wrapper })
    expect(container.querySelectorAll('path').length).toBe(4)
  })
  it('does not render Recharts', () => {
    render(<SubmissionFunnel gates={gates} />, { wrapper })
    expect(screen.queryByTestId('recharts-areachart')).not.toBeInTheDocument()
  })
})
```

---

## 13. `components/admin/StatCard.tsx`

### Purpose

The primary KPI display unit. Used in a 3×2 grid at the top of `AdminDashboardView`. Each card shows a metric, a label, a delta badge, and an optional sparkline.

### Props

```typescript
interface StatCardProps {
  label: string;
  value: string | number;      // pre-formatted by caller (e.g. "1,842" or "94%")
  delta?: number;              // signed float, e.g. +12.4 or -3.1; omit for no badge
  deltaLabel?: string;         // e.g. "vs last week"; defaults to "vs last period"
  sparkData?: Array<{v:number}>; // 7 points for SparkLine; omit for no sparkline
  sparkColor?: string;         // defaults to accent
  accentColor?: string;        // top gradient bar color; defaults to C.accent
  onClick?: () => void;
  'data-testid'?: string;
}
```

### Visual spec — exact measurements

```
┌─────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓  3px accent gradient bar  ▓▓│ ← linear-gradient(90deg, color, color+'44')
├─────────────────────────────────────────┤
│ LABEL (11px/500 Outfit, muted)          │ ← padding-top: 14px, padding-x: 16px
│                                         │
│ VALUE                     [sparkline]   │ ← 28px/800 Outfit, text color
│ (±DELTA% vs last period)  [64×32 chart] │ ← delta badge: 11px pill
│                                         │
└─────────────────────────────────────────┘ ← padding-bottom: 14px, padding-x: 16px
```

Container styles:
- `background: C.surface`
- `border: 1px solid ${C.border}`
- `borderRadius: 12px`
- `overflow: hidden`
- `cursor: onClick ? 'pointer' : 'default'`
- `transition: 'all 0.18s'`
- On hover: `background: C.surfaceHi`, `border-color: C.borderHi`, `transform: translateY(-1px)`, `boxShadow: C.cardShadow`

Content layout (below the gradient bar):
- `padding: '14px 16px'`
- Label row: `marginBottom: 6px`
- Value row: `display: flex, justifyContent: space-between, alignItems: flex-end`
  - Left column: value div + delta badge below it
  - Right column: SparkLine (if sparkData provided), aligned to bottom-right

Delta badge:
- Positive delta: background `${C.green}18`, color `C.green`, text `+{delta}%`
- Negative delta: background `${C.red}18`, color `C.red`, text `{delta}%` (already negative)
- Zero or undefined: no badge rendered
- Style: `padding: '2px 8px'`, `borderRadius: '99px'`, `fontSize: '11px'`, `fontWeight: 600`, `fontFamily: Outfit`
- Delta label: 10px/400, Outfit, `C.dim`, shown below the badge with `marginTop: 3px`

### Tests

```typescript
describe('StatCard', () => {
  it('renders label and value', () => {
    render(<StatCard label="Installs (7d)" value="1,842" />, { wrapper })
    expect(screen.getByText('Installs (7d)')).toBeInTheDocument()
    expect(screen.getByText('1,842')).toBeInTheDocument()
  })
  it('renders positive delta badge', () => {
    render(<StatCard label="Test" value="100" delta={12.4} />, { wrapper })
    expect(screen.getByText('+12.4%')).toBeInTheDocument()
  })
  it('renders negative delta badge', () => {
    render(<StatCard label="Test" value="100" delta={-3.1} />, { wrapper })
    expect(screen.getByText('-3.1%')).toBeInTheDocument()
  })
  it('does not render delta when omitted', () => {
    render(<StatCard label="Test" value="100" />, { wrapper })
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })
  it('renders sparkline when sparkData provided', () => {
    const sparkData = Array.from({length:7}, (_,i) => ({v:i*10}))
    render(<StatCard label="Test" value="100" sparkData={sparkData} sparkColor="#4b7dff" />, { wrapper })
    expect(screen.getByTestId('recharts-linechart')).toBeInTheDocument()
  })
  it('does not render sparkline when sparkData omitted', () => {
    render(<StatCard label="Test" value="100" />, { wrapper })
    expect(screen.queryByTestId('recharts-linechart')).not.toBeInTheDocument()
  })
  it('calls onClick when clicked', async () => {
    const fn = vi.fn()
    const { user } = setup()
    render(<StatCard label="Test" value="100" onClick={fn} />, { wrapper })
    await user.click(screen.getByText('100'))
    expect(fn).toHaveBeenCalledOnce()
  })
})
```

---

## 14. `lib/adminMockData.ts`

### Purpose

Provides realistic mock data for all dashboard components. This module is used while the backend analytics endpoints are not yet built. When the real API returns real data, callers swap the mock for an API response — the shape is identical.

### Shape contract

This mock data must exactly match the shape that `GET /api/v1/admin/analytics/summary` will return. By defining the types here first, the backend team has a typed contract to implement against.

### Types and data

```typescript
// Matches API response shape for /api/v1/admin/analytics/summary
export interface AdminAnalyticsSummary {
  stats: {
    pendingReviews: number;
    installs7d: number;
    installs7dDelta: number;        // percentage change vs prior 7d
    dau: number;
    dauDelta: number;
    publishedSkills: number;
    submissionPassRate: number;     // 0–100
    submissionPassRateDelta: number;
    changelogFreshnessDays: number; // median days since last changelog update
    changelogFreshnessDelta: number;
  };
  installs30d: Array<{ date: string; installs: number }>;   // 30 data points
  divisionInstalls: Array<{
    division: string;       // slug
    displayName: string;
    color: string;
    installs7d: Array<{ date: string; v: number }>;
    totalInstalls: number;
  }>;
  trending: {
    dau: Array<{ date: string; v: number }>;   // 30 points
    wau: Array<{ date: string; v: number }>;   // 12 points (weekly)
    mau: Array<{ date: string; v: number }>;   // 12 points (monthly)
  };
  funnel: Array<{
    label: string;
    count: number;
    color: string;  // semantic color hex
  }>;
  updatedAt: string;  // ISO datetime string
}
```

### Data generation

Use `generateDateLabels` from `chartUtils.ts` to generate consistent date arrays. Do not hardcode specific dates — derive from a fixed `referenceDate` constant at the top of the file so tests are deterministic:

```typescript
const REF_DATE = new Date('2026-03-23T00:00:00Z');
```

The 8 `divisionInstalls` entries must cover all 8 divisions using the exact slug keys from `DIVISION_COLORS` in `@skillhub/shared-types`.

The `funnel.color` values must use the actual theme tokens (not hardcoded hex) — but since this is a `.ts` file without React context access, pass the semantic intent as a string key and let the component resolve the actual color. **OR** hardcode the DARK theme colors as the mock default and accept that light mode won't recolor the funnel mock. The light mode color difference in a mock is acceptable.

Recommended approach: export the mock as a plain object with DARK-mode colors hardcoded, since mock data is temporary. Add a `// TODO: replace with api.get('/api/v1/admin/analytics/summary')` comment above the export.

### Tests

```typescript
describe('adminMockData', () => {
  it('has stats with all required keys', () => {
    const keys = ['pendingReviews','installs7d','dau','publishedSkills','submissionPassRate','changelogFreshnessDays']
    keys.forEach(k => expect(MOCK_ANALYTICS).toHaveProperty(`stats.${k}`))
  })
  it('has 30 installs30d data points', () => {
    expect(MOCK_ANALYTICS.installs30d.length).toBe(30)
  })
  it('has 8 division entries', () => {
    expect(MOCK_ANALYTICS.divisionInstalls.length).toBe(8)
  })
  it('has 4 funnel gates', () => {
    expect(MOCK_ANALYTICS.funnel.length).toBe(4)
  })
  it('trending.dau has 30 points', () => {
    expect(MOCK_ANALYTICS.trending.dau.length).toBe(30)
  })
  it('all division slugs are valid DIVISION_COLORS keys', () => {
    MOCK_ANALYTICS.divisionInstalls.forEach(d => {
      expect(DIVISION_COLORS).toHaveProperty(d.division)
    })
  })
})
```

---

## 15. `views/admin/AdminDashboardView.tsx`

### Purpose

The landing page of the admin panel. Replaces the Stage 2 stub view. Fetches analytics data, renders 6 stat cards, the 30-day installs chart, and the division chart grid.

### Data fetching

```typescript
const [data, setData] = useState<AdminAnalyticsSummary | null>(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [lastFetched, setLastFetched] = useState<Date | null>(null);

useEffect(() => {
  let cancelled = false;
  setLoading(true);
  api.get<AdminAnalyticsSummary>('/api/v1/admin/analytics/summary')
    .then(d => {
      if (!cancelled) {
        setData(d);
        setLastFetched(new Date());
      }
    })
    .catch(() => {
      if (!cancelled) {
        // Fall back to mock data so the dashboard is always usable
        setData(MOCK_ANALYTICS);
        setLastFetched(new Date());
      }
    })
    .finally(() => { if (!cancelled) setLoading(false); });
  return () => { cancelled = true; };
}, []);
```

**Important:** on API failure, fall back to mock data rather than showing an error state. The admin panel should always show useful information. An `error` state for analytics is a degraded experience — mock data is better than a blank page.

### "Updated N min ago" label

```typescript
function minutesAgo(date: Date): string {
  const mins = Math.floor((Date.now() - date.getTime()) / 60000);
  if (mins < 1) return 'just now';
  if (mins === 1) return '1 min ago';
  return `${mins} min ago`;
}
```

Rendered below the stat card grid: 11px/400 Outfit, `C.dim` color, `marginTop: 6px`, `textAlign: 'right'`.

### Stat card grid

Six cards in a `display:grid` with `gridTemplateColumns: 'repeat(3,1fr)'` and `gap: '14px'`. Responsive collapse handled by the same scoped `<style>` approach used in `DivisionChartGrid`:

```css
.stat-card-grid { grid-template-columns: repeat(3,1fr); }
@media (max-width: 800px) { .stat-card-grid { grid-template-columns: repeat(2,1fr); } }
@media (max-width: 500px) { .stat-card-grid { grid-template-columns: 1fr; } }
```

The six cards:

| Position | Label | Value source | Delta source | Spark series | Accent |
|----------|-------|-------------|-------------|-------------|--------|
| 1 | Pending Reviews | `stats.pendingReviews` | none | none | `C.amber` |
| 2 | Installs (7d) | `stats.installs7d` (formatted with toLocaleString) | `stats.installs7dDelta` | last 7 of `installs30d` mapped to `{v}` | `C.accent` |
| 3 | Active Users (DAU) | `stats.dau` | `stats.dauDelta` | last 7 of `trending.dau` mapped to `{v}` | `C.green` |
| 4 | Published Skills | `stats.publishedSkills` | none | none | `C.purple` |
| 5 | Pass Rate | `${stats.submissionPassRate}%` | `stats.submissionPassRateDelta` | none | `C.green` |
| 6 | Changelog Freshness | `${stats.changelogFreshnessDays}d median` | `stats.changelogFreshnessDelta` | none | `C.amber` |

### Layout below stat cards

```
[stat card grid]
[updated N min ago — right-aligned]
[16px gap]
[section header: "Installs — Last 30 Days", 13px/600 Outfit, C.text]
[4px gap]
[AreaChartBase, data=installs30d, series=[{dataKey:'installs', color:C.accent}], height=220]
[24px gap]
[section header: "Installs by Division"]
[4px gap]
[DivisionChartGrid, divisions=divisionInstalls, loading=loading]
```

### Loading state

When `loading=true` and `data=null`, render a minimal skeleton: 6 placeholder divs at `height:100px` with `C.surfaceHi` background and `12px` radius, in the stat card grid layout. Use `data-testid="stat-skeleton"`.

### Tests

```typescript
describe('AdminDashboardView', () => {
  // Mock fetch globally (same pattern as HomeView tests)
  // Must mock /api/v1/admin/analytics/summary

  it('renders skeleton during load', () => {
    mockFetch.mockReturnValue(new Promise(() => {}))
    render(<AdminDashboardView />, { wrapper })
    expect(screen.getAllByTestId('stat-skeleton').length).toBe(6)
  })

  it('renders stat cards after successful fetch', async () => {
    mockFetch.mockResolvedValue({
      ok: true, status: 200,
      json: () => Promise.resolve(MOCK_ANALYTICS),
    })
    render(<AdminDashboardView />, { wrapper })
    await waitFor(() => {
      expect(screen.getByText('Pending Reviews')).toBeInTheDocument()
    })
    expect(screen.getByText('Installs (7d)')).toBeInTheDocument()
    expect(screen.getByText('Pass Rate')).toBeInTheDocument()
  })

  it('falls back to mock data on API error', async () => {
    mockFetch.mockResolvedValue({ ok: false, status: 500, statusText: 'Error', json: () => Promise.resolve({}) })
    render(<AdminDashboardView />, { wrapper })
    await waitFor(() => {
      // Mock data renders — Pending Reviews label is present
      expect(screen.getByText('Pending Reviews')).toBeInTheDocument()
    })
    // No error state visible
    expect(screen.queryByTestId('error-state')).not.toBeInTheDocument()
  })

  it('renders installs chart section', async () => {
    mockFetch.mockResolvedValue({
      ok: true, status: 200,
      json: () => Promise.resolve(MOCK_ANALYTICS),
    })
    render(<AdminDashboardView />, { wrapper })
    await waitFor(() => screen.getByText('Installs — Last 30 Days'))
    expect(screen.getByTestId('recharts-areachart')).toBeInTheDocument()
  })

  it('renders division chart section header', async () => {
    mockFetch.mockResolvedValue({
      ok: true, status: 200,
      json: () => Promise.resolve(MOCK_ANALYTICS),
    })
    render(<AdminDashboardView />, { wrapper })
    await waitFor(() => screen.getByText('Installs by Division'))
  })
})
```

---

## 16. Integration with Stage 2 Admin Shell

Stage 2 established lazy loading for all admin views. `AdminDashboardView` is already wired as the default admin route. This stage replaces the stub content — the route, the lazy import, and the `Suspense` boundary are **not changed**.

Verify by checking the Stage 2 router file. The import should look like:

```typescript
const AdminDashboardView = lazy(() =>
  import('./views/admin/AdminDashboardView').then(m => ({ default: m.AdminDashboardView }))
);
```

If Stage 2 used a different export convention (e.g., default export), match it. Do not change the lazy boundary.

---

## 17. TypeScript Requirements

- All component props must be typed with explicit interfaces (no `any`, no implicit `object`).
- `useChartTheme` return type must be explicitly annotated as `ChartTheme`.
- `chartUtils.ts` functions must have explicit parameter and return types.
- Recharts component props (e.g., `TooltipProps`) should be imported from recharts directly.
- Run `tsc --noEmit` from `apps/web/` after each file — fix all errors before moving on.

Common Recharts TypeScript pitfall: `ResponsiveContainer` requires an explicit `height` or `aspect` prop, not `height="100%"` as a string (this is a number prop in v2.12). Use `height={props.height}` always.

---

## 18. Bundle Verification

After `vite build`:

1. Inspect the build output. Look for the admin chunk (named `AdminDashboardView` or similar by the lazy boundary). It should be significantly larger than before this stage (~240KB addition).
2. The main entry chunk (`index-[hash].js`) should **not** grow. If it does, recharts is being imported outside the lazy boundary — trace the import chain.
3. Acceptable outcome: a new `.js` chunk in `dist/assets/` that is approximately 240–260KB (pre-gzip) and is only loaded when the admin route is visited.

---

## 19. Implementation Order (Enforced)

Execute in this exact order. Each step depends on the previous.

1. Install `recharts` in `package.json` → run install → verify `tsc --noEmit` passes
2. Write and confirm `src/__mocks__/recharts.ts` (or test-setup mock)
3. `chartUtils.ts` — tests first, then implementation
4. `useChartTheme.ts` — tests first, then implementation
5. `EmptyChart.tsx` — tests first, then implementation
6. `SparkLine.tsx` — tests first, then implementation (depends on EmptyChart)
7. `CustomTooltip.tsx` — tests first, then implementation
8. `AreaChartBase.tsx` — tests first, then implementation (depends on EmptyChart, CustomTooltip)
9. `adminMockData.ts` — tests first, then implementation (depends on chartUtils)
10. `StatCard.tsx` — tests first, then implementation (depends on SparkLine)
11. `DivisionMiniChart.tsx` — tests first, then implementation (depends on AreaChartBase)
12. `DivisionChartGrid.tsx` — tests first, then implementation (depends on DivisionMiniChart)
13. `TrendingAreaChart.tsx` — tests first, then implementation (depends on AreaChartBase, chartUtils)
14. `SubmissionFunnel.tsx` — tests first, then implementation (pure SVG, no Recharts dep)
15. `AdminDashboardView.tsx` — tests first, then implementation (depends on everything above)
16. Run full test suite: `vitest run --coverage` — must pass ≥80% coverage
17. `tsc --noEmit` — must be clean
18. `vite build` — verify bundle split

---

## 20. Definition of Done

- [ ] `vitest run --coverage` passes with ≥80% coverage for all new files
- [ ] `tsc --noEmit` exits 0 with no errors
- [ ] `vite build` succeeds; admin chunk present; main chunk unchanged
- [ ] Dark/light theme toggle visually changes chart colors (manual verification)
- [ ] DAU/WAU/MAU toggle switches the series in TrendingAreaChart without error
- [ ] `DivisionChartGrid` renders 8 division charts in a 4×2 grid
- [ ] `StatCard` positive delta shows green badge, negative shows red badge
- [ ] `SubmissionFunnel` renders 4 SVG paths (no Recharts)
- [ ] `AdminDashboardView` falls back to mock data on API error (no blank page)
- [ ] No `console.log` or `console.error` in production paths
- [ ] No `type: ignore` comments without an explanatory note
- [ ] All chart components show `EmptyChart` when data is empty (not a crash)
