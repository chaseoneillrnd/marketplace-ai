# Stage 6B: Feedback, Roadmap & Export — Frontend Views

**Admin Panel Technical Implementation Guide**
Date: 2026-03-23
Prerequisites: Stages 1–5 + Stage 6A (feedback/roadmap/export backend) complete

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Decisions](#2-architecture-decisions)
3. [File Map](#3-file-map)
4. [Task Breakdown](#4-task-breakdown)
5. [Shared Types Extension](#5-shared-types-extension)
6. [Hooks](#6-hooks)
7. [AdminFeedbackView](#7-adminfeedbackview)
8. [AdminRoadmapView (Kanban + DnD)](#8-adminroadmapview-kanban--dnd)
9. [AdminExportView](#9-adminexportview)
10. [Public ChangelogView](#10-public-changelogview)
11. [FeedbackNewView (User-facing)](#11-feedbacknewview-user-facing)
12. [SkillDetailView Feedback Entry Point](#12-skilldetailview-feedback-entry-point)
13. [App.tsx Route Registration](#13-apptsx-route-registration)
14. [Testing: Frontend (TDD)](#14-testing-frontend-tdd)
15. [Acceptance Criteria](#15-acceptance-criteria)
16. [Accessibility Contract](#16-accessibility-contract)

---

## 1. Overview

Stage 6B wires the 6A backend surfaces into the React frontend. There are five new surfaces:

| Surface | Path | Auth |
|---|---|---|
| Admin Feedback | `/admin/feedback` | admin required |
| Admin Roadmap (Kanban) | `/admin/roadmap` | admin required |
| Admin Export | `/admin/exports` | admin required |
| Public Changelog | `/changelog` | none |
| New Platform Feedback | `/feedback/new` | optional |

A "Give feedback" ghost button is added to `SkillDetailView` footer to funnel users to the skill-scoped feedback form.

All styles use `useT()` inline tokens — no CSS classes, no external stylesheets. Emoji are the sole icon system (no icon library imports).

---

## 2. Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Drag-and-drop | HTML Drag and Drop API (no library) | Zero bundle cost; already covered by full keyboard alternative |
| Keyboard DnD alternative | Space pick-up, Arrow move, Enter confirm, Escape cancel | WCAG 2.5.3; aria-live announces each move |
| Export polling | `useInterval` inside `useAdminExport`, 2s while pending | Avoids websocket complexity; export jobs complete in < 60s |
| Kanban column state | `useState` + optimistic local reorder + PATCH to backend | Optimistic keeps UI snappy; rollback on API error |
| Feedback filter state | URL search params via `useSearchParams` | Shareable links; browser Back navigates filter history |
| Changelog route | Outside `AppShell` — no Nav overhead | Public, unauthenticated; share-friendly meta tags |
| Feedback skill link | `?skill_id=<uuid>` query param on `/feedback/new` | Keeps form generic; pre-fills skill chip in UI |

---

## 3. File Map

### New files

```
apps/web/src/
├── hooks/
│   ├── useAdminFeedback.ts
│   ├── useAdminRoadmap.ts
│   └── useAdminExport.ts
├── views/admin/
│   ├── AdminFeedbackView.tsx
│   ├── AdminRoadmapView.tsx
│   └── AdminExportView.tsx
├── views/
│   ├── ChangelogView.tsx
│   └── FeedbackNewView.tsx
└── __tests__/
    ├── AdminFeedbackView.test.tsx
    ├── AdminRoadmapView.test.tsx
    ├── AdminExportView.test.tsx
    ├── ChangelogView.test.tsx
    └── FeedbackNewView.test.tsx
```

### Modified files

```
apps/web/src/App.tsx                      — add 5 routes
apps/web/src/views/SkillDetailView.tsx    — add feedback ghost button in footer
libs/shared-types/src/index.ts            — add Feedback, RoadmapItem, ExportJob types
```

---

## 4. Task Breakdown

Each task is designed for 2–5 minute RED-GREEN-REFACTOR execution.

| # | Task | TDD Phase |
|---|---|---|
| 6B.1 | Extend `libs/shared-types` with Feedback, RoadmapItem, ExportJob types | Types before hooks |
| 6B.2 | Write `AdminFeedbackView.test.tsx` (RED) | All assertions fail |
| 6B.3 | Implement `useAdminFeedback.ts` (GREEN) | Hook unit passes |
| 6B.4 | Implement `AdminFeedbackView.tsx` (GREEN) | View tests pass |
| 6B.5 | Write `AdminRoadmapView.test.tsx` (RED) | All assertions fail |
| 6B.6 | Implement `useAdminRoadmap.ts` (GREEN) | Hook unit passes |
| 6B.7 | Implement `AdminRoadmapView.tsx` (GREEN) | View tests pass |
| 6B.8 | Write `AdminExportView.test.tsx` (RED) | All assertions fail |
| 6B.9 | Implement `useAdminExport.ts` (GREEN) | Hook unit passes |
| 6B.10 | Implement `AdminExportView.tsx` (GREEN) | View tests pass |
| 6B.11 | Write `ChangelogView.test.tsx` + implement (GREEN) | Public route passes |
| 6B.12 | Write `FeedbackNewView.test.tsx` + implement (GREEN) | User form passes |
| 6B.13 | Modify `SkillDetailView.tsx` — feedback ghost button | Smoke test |
| 6B.14 | Register routes in `App.tsx` | Integration smoke |

---

## 5. Shared Types Extension

**File:** `libs/shared-types/src/index.ts`

Append the following exports. Do NOT modify existing exports.

```typescript
// --- Feedback ---

export type FeedbackType = 'feature_request' | 'bug_report' | 'praise' | 'complaint';
export type FeedbackSentiment = 'positive' | 'neutral' | 'critical';

export interface FeedbackItem {
  id: string;
  type: FeedbackType;
  sentiment: FeedbackSentiment;
  content: string;
  skill_id: string | null;
  skill_name: string | null;
  skill_slug: string | null;
  division: string | null;
  author_id: string | null;
  created_at: string;
  archived: boolean;
  roadmap_item_id: string | null;
}

export interface FeedbackListResponse {
  items: FeedbackItem[];
  total: number;
  page: number;
  per_page: number;
}

// --- Roadmap ---

export type RoadmapStatus = 'planned' | 'in_progress' | 'shipped' | 'cancelled';

export interface RoadmapItem {
  id: string;
  title: string;
  description: string | null;
  status: RoadmapStatus;
  position: number;
  feedback_count: number;
  version_tag: string | null;
  changelog_body: string | null;
  shipped_at: string | null;
  created_at: string;
}

export interface RoadmapListResponse {
  items: RoadmapItem[];
}

// --- Export Jobs ---

export type ExportScope = 'installs' | 'submissions' | 'users' | 'analytics';
export type ExportFormat = 'csv' | 'json';
export type ExportStatus = 'pending' | 'processing' | 'complete' | 'failed';

export interface ExportJob {
  id: string;
  scope: ExportScope;
  format: ExportFormat;
  status: ExportStatus;
  download_url: string | null;
  expires_at: string | null;
  created_at: string;
  error: string | null;
}

export interface ExportQuota {
  used: number;
  limit: number;
  remaining: number;
  resets_at: string;
}

// --- Changelog (public) ---

export interface ChangelogEntry {
  id: string;
  version_tag: string;
  changelog_body: string;
  shipped_at: string;
  title: string;
}
```

---

## 6. Hooks

### 6.1 `useAdminFeedback`

**File:** `apps/web/src/hooks/useAdminFeedback.ts`

```typescript
import { useState, useCallback, useEffect } from 'react';
import type { FeedbackItem, FeedbackListResponse, FeedbackType, FeedbackSentiment } from '@skillhub/shared-types';
import { api } from '../lib/api';

export interface FeedbackFilters {
  type?: FeedbackType;
  sentiment?: FeedbackSentiment;
  date_from?: string;
  date_to?: string;
  page?: number;
  per_page?: number;
}

export function useAdminFeedback(filters: FeedbackFilters = {}) {
  const [data, setData] = useState<FeedbackListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<FeedbackListResponse>(
        '/api/v1/admin/feedback',
        { ...filters, page: filters.page ?? 1, per_page: filters.per_page ?? 25 },
      );
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feedback');
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(filters)]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { fetch(); }, [fetch]);

  const archive = useCallback(async (id: string) => {
    await api.patch(`/api/v1/admin/feedback/${id}/archive`);
    setData((prev) =>
      prev
        ? { ...prev, items: prev.items.map((f) => (f.id === id ? { ...f, archived: true } : f)) }
        : prev,
    );
  }, []);

  const linkToRoadmap = useCallback(async (feedbackId: string, roadmapItemId: string) => {
    await api.patch(`/api/v1/admin/feedback/${feedbackId}/roadmap`, { roadmap_item_id: roadmapItemId });
    setData((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((f) =>
              f.id === feedbackId ? { ...f, roadmap_item_id: roadmapItemId } : f,
            ),
          }
        : prev,
    );
  }, []);

  return { data, loading, error, refetch: fetch, archive, linkToRoadmap };
}
```

### 6.2 `useAdminRoadmap`

**File:** `apps/web/src/hooks/useAdminRoadmap.ts`

```typescript
import { useState, useCallback, useEffect } from 'react';
import type { RoadmapItem, RoadmapStatus, RoadmapListResponse } from '@skillhub/shared-types';
import { api } from '../lib/api';

export function useAdminRoadmap() {
  const [items, setItems] = useState<RoadmapItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.get<RoadmapListResponse>('/api/v1/admin/roadmap');
      setItems(result.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load roadmap');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  // Optimistic move: update local state immediately, rollback on error
  const moveItem = useCallback(
    async (id: string, toStatus: RoadmapStatus, toPosition: number) => {
      const previous = items;
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, status: toStatus, position: toPosition } : item,
        ),
      );
      try {
        await api.patch<RoadmapItem>(`/api/v1/admin/roadmap/${id}`, {
          status: toStatus,
          position: toPosition,
        });
      } catch {
        setItems(previous); // rollback
      }
    },
    [items],
  );

  const createItem = useCallback(async (title: string) => {
    const item = await api.post<RoadmapItem>('/api/v1/admin/roadmap', { title, status: 'planned' });
    setItems((prev) => [item, ...prev]);
  }, []);

  const shipItem = useCallback(
    async (id: string, version_tag: string, changelog_body: string) => {
      const updated = await api.patch<RoadmapItem>(`/api/v1/admin/roadmap/${id}/ship`, {
        version_tag,
        changelog_body,
      });
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
    },
    [],
  );

  return { items, loading, error, refetch: fetch, moveItem, createItem, shipItem };
}
```

### 6.3 `useAdminExport`

**File:** `apps/web/src/hooks/useAdminExport.ts`

```typescript
import { useState, useCallback, useEffect, useRef } from 'react';
import type { ExportJob, ExportQuota, ExportScope, ExportFormat } from '@skillhub/shared-types';
import { api } from '../lib/api';

const POLL_INTERVAL_MS = 2000;

export function useAdminExport() {
  const [job, setJob] = useState<ExportJob | null>(null);
  const [quota, setQuota] = useState<ExportQuota | null>(null);
  const [requesting, setRequesting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const startPoll = useCallback(
    (id: string) => {
      stopPoll();
      pollRef.current = setInterval(async () => {
        try {
          const updated = await api.get<ExportJob>(`/api/v1/admin/exports/${id}`);
          setJob(updated);
          if (updated.status === 'complete' || updated.status === 'failed') {
            stopPoll();
          }
        } catch {
          stopPoll();
        }
      }, POLL_INTERVAL_MS);
    },
    [stopPoll],
  );

  useEffect(() => () => stopPoll(), [stopPoll]);

  const fetchQuota = useCallback(async () => {
    try {
      const q = await api.get<ExportQuota>('/api/v1/admin/exports/quota');
      setQuota(q);
    } catch {
      // quota is informational; suppress errors
    }
  }, []);

  useEffect(() => { fetchQuota(); }, [fetchQuota]);

  const requestExport = useCallback(
    async (scope: ExportScope, format: ExportFormat, dateFrom?: string, dateTo?: string, division?: string) => {
      setRequesting(true);
      setError(null);
      setJob(null);
      try {
        const created = await api.post<ExportJob>('/api/v1/admin/exports', {
          scope,
          format,
          date_from: dateFrom,
          date_to: dateTo,
          division,
        });
        setJob(created);
        await fetchQuota();
        if (created.status !== 'complete') {
          startPoll(created.id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Export request failed');
      } finally {
        setRequesting(false);
      }
    },
    [fetchQuota, startPoll],
  );

  const reset = useCallback(() => {
    stopPoll();
    setJob(null);
    setError(null);
  }, [stopPoll]);

  return { job, quota, requesting, error, requestExport, reset };
}
```

---

## 7. AdminFeedbackView

**File:** `apps/web/src/views/admin/AdminFeedbackView.tsx`

### Requirements

- Filter chips row: All | Feature Request | Bug Report | Praise | Complaint
- Sentiment filter row: All | Positive | Neutral | Critical
- Date range: two `input[type="date"]` using `C.inputBg` / `C.border` tokens
- Feedback rows in a table-like list; each row contains:
  - Sentiment label with semantic background (green14 / muted / red14)
  - Type chip (pill shape, `C.surface` bg, `C.border` border)
  - Skill chip — navigable link to `/skills/:slug`
  - Division badge
  - Content excerpt in `C.codeBg` block (max 2 lines, overflow: hidden)
  - "Link to Roadmap" dropdown — fetches roadmap items, selects one
  - "Archive" button (only visible when `archived === false`)
- Pagination: Previous / Next buttons, page X of Y label
- Empty state when `items.length === 0`
- Archived items displayed with 40% opacity and "Archived" badge

### Token reference

| Purpose | Token |
|---|---|
| Positive sentiment bg | `C.greenDim` |
| Positive sentiment text | `C.green` |
| Critical sentiment bg | `C.redDim` |
| Critical sentiment text | `C.red` |
| Neutral sentiment bg | `C.accentDim` |
| Neutral sentiment text | `C.muted` |
| Active filter chip | `C.accent` bg, white text |
| Inactive filter chip | `C.surface` bg, `C.muted` text, `C.border` border |
| Content block | `background: C.codeBg`, `borderRadius: 6px`, `padding: 8px 12px` |

### Implementation skeleton

```tsx
// apps/web/src/views/admin/AdminFeedbackView.tsx
import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { FeedbackType, FeedbackSentiment } from '@skillhub/shared-types';
import { useT } from '../../context/ThemeContext';
import { useAdminFeedback } from '../../hooks/useAdminFeedback';
import { useAdminRoadmap } from '../../hooks/useAdminRoadmap';

const TYPE_LABELS: Record<string, string> = {
  feature_request: '✨ Feature Request',
  bug_report: '🐛 Bug Report',
  praise: '🙌 Praise',
  complaint: '⚠️ Complaint',
};

const SENTIMENT_CONFIG = {
  positive: { label: '😊 Positive', emoji: '😊' },
  neutral:  { label: '😐 Neutral',  emoji: '😐' },
  critical: { label: '😤 Critical', emoji: '😤' },
} as const;

export function AdminFeedbackView() {
  const C = useT();
  const [params, setParams] = useSearchParams();

  const type = (params.get('type') as FeedbackType | null) ?? undefined;
  const sentiment = (params.get('sentiment') as FeedbackSentiment | null) ?? undefined;
  const dateFrom = params.get('date_from') ?? undefined;
  const dateTo = params.get('date_to') ?? undefined;
  const page = Number(params.get('page') ?? 1);

  const { data, loading, error, archive, linkToRoadmap } = useAdminFeedback({
    type, sentiment, date_from: dateFrom, date_to: dateTo, page,
  });

  const { items: roadmapItems } = useAdminRoadmap();

  // Track which feedback row has the roadmap dropdown open
  const [linkingId, setLinkingId] = useState<string | null>(null);

  const setParam = (key: string, value: string | undefined) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    next.delete('page');
    setParams(next, { replace: true });
  };

  const filterChipStyle = (active: boolean) => ({
    padding: '5px 14px',
    borderRadius: '99px',
    border: `1px solid ${active ? C.accent : C.border}`,
    background: active ? C.accent : C.surface,
    color: active ? '#fff' : C.muted,
    fontSize: '12px',
    fontWeight: active ? 600 : 400,
    cursor: 'pointer',
  });

  const sentimentStyle = (s: FeedbackSentiment) => ({
    positive: { background: C.greenDim, color: C.green },
    neutral:  { background: C.accentDim, color: C.muted },
    critical: { background: C.redDim,   color: C.red },
  }[s]);

  const totalPages = data ? Math.ceil(data.total / data.per_page) : 1;

  return (
    <div style={{ padding: '28px 32px', maxWidth: '1100px' }}>
      <h1 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '24px', color: C.text }}>
        💬 Feedback
      </h1>

      {/* Type filter chips */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
        {(['', 'feature_request', 'bug_report', 'praise', 'complaint'] as const).map((t) => (
          <button
            key={t || 'all'}
            style={filterChipStyle(type === (t || undefined))}
            onClick={() => setParam('type', t || undefined)}
          >
            {t ? TYPE_LABELS[t] : 'All'}
          </button>
        ))}
      </div>

      {/* Sentiment filter chips */}
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
        {(['', 'positive', 'neutral', 'critical'] as const).map((s) => (
          <button
            key={s || 'all'}
            style={filterChipStyle(sentiment === (s || undefined))}
            onClick={() => setParam('sentiment', s || undefined)}
          >
            {s ? SENTIMENT_CONFIG[s].label : '🔮 All Sentiments'}
          </button>
        ))}
      </div>

      {/* Date range */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px', alignItems: 'center' }}>
        <span style={{ fontSize: '12px', color: C.muted }}>From</span>
        <input
          type="date"
          value={dateFrom ?? ''}
          onChange={(e) => setParam('date_from', e.target.value || undefined)}
          style={{
            background: C.inputBg, border: `1px solid ${C.border}`, color: C.text,
            padding: '6px 10px', borderRadius: '8px', fontSize: '13px',
          }}
        />
        <span style={{ fontSize: '12px', color: C.muted }}>To</span>
        <input
          type="date"
          value={dateTo ?? ''}
          onChange={(e) => setParam('date_to', e.target.value || undefined)}
          style={{
            background: C.inputBg, border: `1px solid ${C.border}`, color: C.text,
            padding: '6px 10px', borderRadius: '8px', fontSize: '13px',
          }}
        />
      </div>

      {/* Error state */}
      {error && (
        <div style={{ color: C.red, padding: '12px', background: C.redDim, borderRadius: '8px', marginBottom: '16px' }}>
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div style={{ color: C.muted, fontSize: '14px' }}>Loading feedback…</div>
      )}

      {/* Feedback list */}
      {!loading && data && (
        <>
          {data.items.length === 0 ? (
            <div style={{
              textAlign: 'center', padding: '48px', color: C.dim,
              border: `1px dashed ${C.border}`, borderRadius: '12px',
            }}>
              <div style={{ fontSize: '32px', marginBottom: '8px' }}>🗂️</div>
              <div>No feedback matches the current filters.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {data.items.map((item) => (
                <div
                  key={item.id}
                  style={{
                    background: C.surface, border: `1px solid ${C.border}`,
                    borderRadius: '12px', padding: '16px',
                    opacity: item.archived ? 0.4 : 1,
                    transition: 'opacity 0.2s',
                  }}
                >
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', flexWrap: 'wrap', marginBottom: '10px' }}>
                    {/* Sentiment badge */}
                    <span style={{
                      ...sentimentStyle(item.sentiment),
                      padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: 600,
                    }}>
                      {SENTIMENT_CONFIG[item.sentiment].label}
                    </span>

                    {/* Type chip */}
                    <span style={{
                      background: C.surface, border: `1px solid ${C.border}`,
                      color: C.muted, padding: '3px 10px', borderRadius: '99px', fontSize: '11px',
                    }}>
                      {TYPE_LABELS[item.type]}
                    </span>

                    {/* Skill link */}
                    {item.skill_slug && (
                      <Link
                        to={`/skills/${item.skill_slug}`}
                        style={{
                          background: C.accentDim, color: C.accent,
                          padding: '3px 10px', borderRadius: '99px', fontSize: '11px',
                          textDecoration: 'none', fontWeight: 500,
                        }}
                      >
                        🔧 {item.skill_name}
                      </Link>
                    )}

                    {/* Division badge */}
                    {item.division && (
                      <span style={{
                        background: C.surfaceHi, border: `1px solid ${C.border}`,
                        color: C.dim, padding: '3px 10px', borderRadius: '99px', fontSize: '11px',
                      }}>
                        🏢 {item.division}
                      </span>
                    )}

                    {item.archived && (
                      <span style={{
                        background: C.amberDim, color: C.amber,
                        padding: '3px 10px', borderRadius: '99px', fontSize: '11px', fontWeight: 600,
                      }}>
                        Archived
                      </span>
                    )}

                    {/* Spacer */}
                    <div style={{ flex: 1 }} />

                    {/* Actions */}
                    {!item.archived && (
                      <>
                        {/* Link to Roadmap dropdown */}
                        <div style={{ position: 'relative' }}>
                          <button
                            onClick={() => setLinkingId(linkingId === item.id ? null : item.id)}
                            style={{
                              background: C.accentDim, color: C.accent, border: 'none',
                              padding: '5px 12px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer',
                            }}
                          >
                            🗺️ Link to Roadmap
                          </button>
                          {linkingId === item.id && (
                            <div style={{
                              position: 'absolute', right: 0, top: '34px', zIndex: 50,
                              background: C.surface, border: `1px solid ${C.borderHi}`,
                              borderRadius: '10px', minWidth: '220px', boxShadow: C.cardShadow,
                              padding: '6px',
                            }}>
                              {roadmapItems
                                .filter((r) => r.status !== 'cancelled' && r.status !== 'shipped')
                                .map((r) => (
                                  <button
                                    key={r.id}
                                    onClick={async () => {
                                      await linkToRoadmap(item.id, r.id);
                                      setLinkingId(null);
                                    }}
                                    style={{
                                      display: 'block', width: '100%', textAlign: 'left',
                                      padding: '8px 12px', background: 'none', border: 'none',
                                      color: C.text, fontSize: '13px', cursor: 'pointer',
                                      borderRadius: '6px',
                                    }}
                                  >
                                    {r.title}
                                  </button>
                                ))}
                              {roadmapItems.filter((r) => r.status !== 'cancelled' && r.status !== 'shipped').length === 0 && (
                                <div style={{ padding: '8px 12px', color: C.dim, fontSize: '12px' }}>
                                  No active roadmap items
                                </div>
                              )}
                            </div>
                          )}
                        </div>

                        <button
                          onClick={() => archive(item.id)}
                          style={{
                            background: 'none', border: `1px solid ${C.border}`, color: C.muted,
                            padding: '5px 12px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer',
                          }}
                        >
                          🗄️ Archive
                        </button>
                      </>
                    )}
                  </div>

                  {/* Content block */}
                  <div style={{
                    background: C.codeBg, borderRadius: '6px', padding: '8px 12px',
                    fontSize: '13px', color: C.text, lineHeight: '1.5',
                    display: '-webkit-box', WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical', overflow: 'hidden',
                    fontFamily: "'JetBrains Mono', monospace",
                  }}>
                    {item.content}
                  </div>

                  <div style={{ marginTop: '8px', fontSize: '11px', color: C.dim }}>
                    {new Date(item.created_at).toLocaleDateString('en-US', {
                      year: 'numeric', month: 'short', day: 'numeric',
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', justifyContent: 'center', marginTop: '24px' }}>
              <button
                disabled={page <= 1}
                onClick={() => setParam('page', String(page - 1))}
                style={{
                  padding: '7px 16px', borderRadius: '8px', border: `1px solid ${C.border}`,
                  background: C.surface, color: page <= 1 ? C.dim : C.text, cursor: page <= 1 ? 'default' : 'pointer',
                  fontSize: '13px',
                }}
              >
                ← Previous
              </button>
              <span style={{ fontSize: '13px', color: C.muted }}>
                Page {page} of {totalPages}
              </span>
              <button
                disabled={page >= totalPages}
                onClick={() => setParam('page', String(page + 1))}
                style={{
                  padding: '7px 16px', borderRadius: '8px', border: `1px solid ${C.border}`,
                  background: C.surface, color: page >= totalPages ? C.dim : C.text,
                  cursor: page >= totalPages ? 'default' : 'pointer', fontSize: '13px',
                }}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

---

## 8. AdminRoadmapView (Kanban + DnD)

**File:** `apps/web/src/views/admin/AdminRoadmapView.tsx`

### Requirements

- Four columns rendered side-by-side: Planned | In Progress | Shipped | Cancelled
- Column header: 11px / weight 600 / Outfit / uppercase / letter-spacing 0.8px
- Cards: `borderRadius: 12px`, `background: C.surface`, `border: 1px solid C.border`, `padding: 16px`
- Vertical gap between cards: 10px; horizontal gap between columns: 14px
- HTML Drag and Drop API for card repositioning (no external library)
- Full keyboard alternative (Space/Enter to pick up, Arrow keys to move columns, Enter to confirm, Escape to cancel)
- `aria-live="polite"` region announces column moves
- "New Item" inline form at top of Planned column
- "Mark as Shipped" side panel slides in from right — collects `version_tag` + `changelog_body`

### Column configuration

```typescript
const COLUMNS: { status: RoadmapStatus; label: string; emoji: string; color: string }[] = [
  { status: 'planned',     label: 'PLANNED',     emoji: '📋', color: C.muted  },
  { status: 'in_progress', label: 'IN PROGRESS', emoji: '🔄', color: C.accent },
  { status: 'shipped',     label: 'SHIPPED',     emoji: '✅', color: C.green  },
  { status: 'cancelled',   label: 'CANCELLED',   emoji: '🚫', color: C.dim    },
];
```

### Implementation skeleton

```tsx
// apps/web/src/views/admin/AdminRoadmapView.tsx
import { useState, useRef } from 'react';
import type { RoadmapItem, RoadmapStatus } from '@skillhub/shared-types';
import { useT } from '../../context/ThemeContext';
import { useAdminRoadmap } from '../../hooks/useAdminRoadmap';

// DnD state shape
interface DragState {
  itemId: string;
  sourceStatus: RoadmapStatus;
}

// Keyboard DnD state shape
interface KbPickup {
  itemId: string;
  currentStatus: RoadmapStatus;
}

export function AdminRoadmapView() {
  const C = useT();
  const { items, loading, error, moveItem, createItem, shipItem } = useAdminRoadmap();

  // Drag state
  const [drag, setDrag] = useState<DragState | null>(null);
  const [dragOverCol, setDragOverCol] = useState<RoadmapStatus | null>(null);

  // Keyboard pickup state
  const [kbPickup, setKbPickup] = useState<KbPickup | null>(null);
  const announceRef = useRef<HTMLDivElement>(null);

  // New item form
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [creating, setCreating] = useState(false);

  // Ship side panel
  const [shipTarget, setShipTarget] = useState<RoadmapItem | null>(null);
  const [shipVersion, setShipVersion] = useState('');
  const [shipChangelog, setShipChangelog] = useState('');
  const [shipping, setShipping] = useState(false);

  const STATUSES: RoadmapStatus[] = ['planned', 'in_progress', 'shipped', 'cancelled'];

  const COLUMN_META: Record<RoadmapStatus, { label: string; emoji: string; headerColor: string }> = {
    planned:     { label: 'PLANNED',     emoji: '📋', headerColor: C.muted  },
    in_progress: { label: 'IN PROGRESS', emoji: '🔄', headerColor: C.accent },
    shipped:     { label: 'SHIPPED',     emoji: '✅', headerColor: C.green  },
    cancelled:   { label: 'CANCELLED',   emoji: '🚫', headerColor: C.dim    },
  };

  const itemsByStatus = (status: RoadmapStatus) =>
    items
      .filter((i) => i.status === status)
      .sort((a, b) => a.position - b.position);

  const announce = (msg: string) => {
    if (announceRef.current) announceRef.current.textContent = msg;
  };

  // --- Drag handlers ---
  const handleDragStart = (itemId: string, sourceStatus: RoadmapStatus) => {
    setDrag({ itemId, sourceStatus });
  };

  const handleDrop = async (toStatus: RoadmapStatus) => {
    if (!drag) return;
    const targetItems = itemsByStatus(toStatus);
    const toPosition = targetItems.length;
    await moveItem(drag.itemId, toStatus, toPosition);
    setDrag(null);
    setDragOverCol(null);
  };

  // --- Keyboard handlers ---
  const handleCardKeyDown = (e: React.KeyboardEvent, item: RoadmapItem) => {
    if (e.key === ' ' || e.key === 'Enter') {
      if (!kbPickup) {
        e.preventDefault();
        setKbPickup({ itemId: item.id, currentStatus: item.status });
        announce(`Picked up "${item.title}". Use arrow keys to move between columns, Enter to place, Escape to cancel.`);
      }
    }
    if (kbPickup?.itemId === item.id) {
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        const idx = STATUSES.indexOf(kbPickup.currentStatus);
        if (idx < STATUSES.length - 1) {
          const next = STATUSES[idx + 1];
          setKbPickup({ ...kbPickup, currentStatus: next });
          announce(`Moved to ${COLUMN_META[next].label} column.`);
        }
      }
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        const idx = STATUSES.indexOf(kbPickup.currentStatus);
        if (idx > 0) {
          const prev = STATUSES[idx - 1];
          setKbPickup({ ...kbPickup, currentStatus: prev });
          announce(`Moved to ${COLUMN_META[prev].label} column.`);
        }
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        const targetItems = itemsByStatus(kbPickup.currentStatus);
        moveItem(kbPickup.itemId, kbPickup.currentStatus, targetItems.length);
        announce(`Placed "${item.title}" in ${COLUMN_META[kbPickup.currentStatus].label}.`);
        setKbPickup(null);
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        announce(`Cancelled. "${item.title}" remains in ${COLUMN_META[item.status].label}.`);
        setKbPickup(null);
      }
    }
  };

  const handleCreateItem = async () => {
    if (!newTitle.trim()) return;
    setCreating(true);
    try {
      await createItem(newTitle.trim());
      setNewTitle('');
      setShowNewForm(false);
    } finally {
      setCreating(false);
    }
  };

  const handleShip = async () => {
    if (!shipTarget || !shipVersion.trim()) return;
    setShipping(true);
    try {
      await shipItem(shipTarget.id, shipVersion.trim(), shipChangelog);
      setShipTarget(null);
      setShipVersion('');
      setShipChangelog('');
    } finally {
      setShipping(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '32px', color: C.muted }}>Loading roadmap…</div>;
  }

  if (error) {
    return (
      <div style={{ padding: '32px', color: C.red, background: C.redDim, borderRadius: '12px', margin: '32px' }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{ padding: '28px 32px' }}>
      {/* aria-live region (visually hidden) */}
      <div
        ref={announceRef}
        aria-live="polite"
        aria-atomic="true"
        style={{ position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clip: 'rect(0,0,0,0)' }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 700, color: C.text }}>🗺️ Roadmap</h1>
      </div>

      {/* Kanban board */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '14px' }}>
        {STATUSES.map((status) => {
          const meta = COLUMN_META[status];
          const colItems = itemsByStatus(status);
          const isDragTarget = dragOverCol === status;

          return (
            <div
              key={status}
              onDragOver={(e) => { e.preventDefault(); setDragOverCol(status); }}
              onDragLeave={() => setDragOverCol(null)}
              onDrop={() => handleDrop(status)}
              style={{
                background: isDragTarget ? C.surfaceHi : C.bg,
                border: `1px solid ${isDragTarget ? C.accent : C.border}`,
                borderRadius: '12px',
                padding: '12px',
                minHeight: '200px',
                transition: 'background 0.15s, border-color 0.15s',
              }}
            >
              {/* Column header */}
              <div style={{
                fontSize: '11px', fontWeight: 600,
                color: meta.headerColor,
                letterSpacing: '0.8px', marginBottom: '12px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span>{meta.emoji} {meta.label}</span>
                <span style={{ fontWeight: 400, color: C.dim }}>{colItems.length}</span>
              </div>

              {/* New item form (Planned column only) */}
              {status === 'planned' && (
                <div style={{ marginBottom: '10px' }}>
                  {showNewForm ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <input
                        autoFocus
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleCreateItem();
                          if (e.key === 'Escape') { setShowNewForm(false); setNewTitle(''); }
                        }}
                        placeholder="Item title…"
                        style={{
                          background: C.inputBg, border: `1px solid ${C.borderHi}`, color: C.text,
                          padding: '7px 10px', borderRadius: '8px', fontSize: '13px', outline: 'none',
                        }}
                      />
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          onClick={handleCreateItem}
                          disabled={creating || !newTitle.trim()}
                          style={{
                            flex: 1, background: C.accent, color: '#fff', border: 'none',
                            borderRadius: '8px', padding: '6px', fontSize: '12px', cursor: 'pointer',
                          }}
                        >
                          {creating ? '…' : 'Add'}
                        </button>
                        <button
                          onClick={() => { setShowNewForm(false); setNewTitle(''); }}
                          style={{
                            background: 'none', border: `1px solid ${C.border}`, color: C.muted,
                            borderRadius: '8px', padding: '6px 10px', fontSize: '12px', cursor: 'pointer',
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowNewForm(true)}
                      style={{
                        width: '100%', background: 'none', border: `1px dashed ${C.border}`,
                        color: C.dim, borderRadius: '8px', padding: '8px', fontSize: '12px', cursor: 'pointer',
                      }}
                    >
                      + New Item
                    </button>
                  )}
                </div>
              )}

              {/* Cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {colItems.map((item) => {
                  const isPickedUp = kbPickup?.itemId === item.id;
                  return (
                    <div
                      key={item.id}
                      draggable
                      tabIndex={0}
                      role="button"
                      aria-label={`${item.title}. Press Space or Enter to pick up and move.`}
                      aria-grabbed={isPickedUp}
                      onDragStart={() => handleDragStart(item.id, status)}
                      onDragEnd={() => { setDrag(null); setDragOverCol(null); }}
                      onKeyDown={(e) => handleCardKeyDown(e, item)}
                      style={{
                        background: C.surface,
                        border: `1px solid ${isPickedUp ? C.accent : C.border}`,
                        borderRadius: '12px',
                        padding: '16px',
                        cursor: drag ? 'grabbing' : 'grab',
                        outline: isPickedUp ? `2px solid ${C.accent}` : 'none',
                        outlineOffset: '2px',
                        opacity: drag?.itemId === item.id ? 0.5 : 1,
                        transition: 'opacity 0.15s, border-color 0.15s',
                      }}
                    >
                      <div style={{ fontSize: '13px', fontWeight: 600, color: C.text, marginBottom: '6px' }}>
                        {item.title}
                      </div>
                      {item.description && (
                        <div style={{ fontSize: '12px', color: C.muted, marginBottom: '8px', lineHeight: '1.4' }}>
                          {item.description}
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        {item.feedback_count > 0 && (
                          <span style={{ fontSize: '11px', color: C.dim }}>
                            💬 {item.feedback_count}
                          </span>
                        )}
                        {/* Ship button for in_progress items */}
                        {status === 'in_progress' && (
                          <button
                            onClick={(e) => { e.stopPropagation(); setShipTarget(item); }}
                            style={{
                              background: C.greenDim, color: C.green, border: 'none',
                              padding: '3px 10px', borderRadius: '99px', fontSize: '11px', cursor: 'pointer',
                            }}
                          >
                            ✅ Ship
                          </button>
                        )}
                        {item.version_tag && (
                          <span style={{
                            background: C.accentDim, color: C.accent,
                            padding: '2px 8px', borderRadius: '99px', fontSize: '11px',
                          }}>
                            {item.version_tag}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* "Mark as Shipped" side panel */}
      {shipTarget && (
        <>
          {/* Overlay */}
          <div
            onClick={() => setShipTarget(null)}
            style={{
              position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100,
            }}
          />
          <div style={{
            position: 'fixed', right: 0, top: 0, bottom: 0, width: '400px',
            background: C.surface, borderLeft: `1px solid ${C.borderHi}`,
            zIndex: 101, padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px',
            overflowY: 'auto',
          }}>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: C.text }}>
              ✅ Mark as Shipped
            </h2>
            <p style={{ fontSize: '13px', color: C.muted }}>{shipTarget.title}</p>

            <div>
              <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '6px' }}>
                Version Tag *
              </label>
              <input
                value={shipVersion}
                onChange={(e) => setShipVersion(e.target.value)}
                placeholder="e.g. v1.4.0"
                style={{
                  width: '100%', background: C.inputBg, border: `1px solid ${C.border}`,
                  color: C.text, padding: '8px 12px', borderRadius: '8px', fontSize: '13px',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '6px' }}>
                Changelog
              </label>
              <textarea
                value={shipChangelog}
                onChange={(e) => setShipChangelog(e.target.value)}
                placeholder="What changed in this release…"
                rows={6}
                style={{
                  width: '100%', background: C.inputBg, border: `1px solid ${C.border}`,
                  color: C.text, padding: '8px 12px', borderRadius: '8px', fontSize: '13px',
                  resize: 'vertical', fontFamily: 'inherit',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: 'auto' }}>
              <button
                onClick={handleShip}
                disabled={shipping || !shipVersion.trim()}
                style={{
                  flex: 1, background: C.green, color: '#fff', border: 'none',
                  borderRadius: '10px', padding: '10px', fontSize: '14px', fontWeight: 600,
                  cursor: shipping || !shipVersion.trim() ? 'default' : 'pointer',
                  opacity: shipping || !shipVersion.trim() ? 0.6 : 1,
                }}
              >
                {shipping ? 'Shipping…' : '🚀 Ship It'}
              </button>
              <button
                onClick={() => setShipTarget(null)}
                style={{
                  background: 'none', border: `1px solid ${C.border}`, color: C.muted,
                  borderRadius: '10px', padding: '10px 16px', fontSize: '14px', cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
```

---

## 9. AdminExportView

**File:** `apps/web/src/views/admin/AdminExportView.tsx`

### Requirements

- **Stage 1 (configuration):** scope selector, format selector, optional date range, optional division filter
- **Stage 2 (confirmation):** green "Request Export" button with quota display
- **Polling state:** spinner with "Preparing your export…" message
- **Complete state:** green download link, "Ready — expires in 24 hours"
- **Failed state:** red error message, Reset button
- **Quota display:** "N of 5 exports remaining today" (amber when ≤ 1 remaining)
- Reset button returns to Stage 1

### Implementation skeleton

```tsx
// apps/web/src/views/admin/AdminExportView.tsx
import { useState } from 'react';
import type { ExportScope, ExportFormat } from '@skillhub/shared-types';
import { useT } from '../../context/ThemeContext';
import { useAdminExport } from '../../hooks/useAdminExport';

const SCOPE_OPTIONS: { value: ExportScope; label: string }[] = [
  { value: 'installs',    label: '📦 Installs' },
  { value: 'submissions', label: '📝 Submissions' },
  { value: 'users',       label: '👥 Users' },
  { value: 'analytics',   label: '📊 Analytics' },
];

const FORMAT_OPTIONS: { value: ExportFormat; label: string }[] = [
  { value: 'csv',  label: 'CSV' },
  { value: 'json', label: 'JSON' },
];

export function AdminExportView() {
  const C = useT();
  const { job, quota, requesting, error, requestExport, reset } = useAdminExport();

  const [scope, setScope] = useState<ExportScope>('installs');
  const [format, setFormat] = useState<ExportFormat>('csv');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [division, setDivision] = useState('');

  const quotaLow = quota ? quota.remaining <= 1 : false;

  const selectStyle = {
    background: C.inputBg, border: `1px solid ${C.border}`, color: C.text,
    padding: '8px 12px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
  };

  return (
    <div style={{ padding: '28px 32px', maxWidth: '600px' }}>
      <h1 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '24px', color: C.text }}>
        📤 Export Data
      </h1>

      {/* Quota banner */}
      {quota && (
        <div style={{
          padding: '10px 16px', borderRadius: '10px', marginBottom: '20px',
          background: quotaLow ? C.amberDim : C.accentDim,
          border: `1px solid ${quotaLow ? C.amber : C.accent}33`,
          color: quotaLow ? C.amber : C.accent,
          fontSize: '13px',
        }}>
          {quota.remaining === 0
            ? `⛔ Export limit reached. Resets ${new Date(quota.resets_at).toLocaleTimeString()}.`
            : `📊 ${quota.remaining} of ${quota.limit} exports remaining today`}
        </div>
      )}

      {/* Complete state */}
      {job?.status === 'complete' && job.download_url && (
        <div style={{
          padding: '24px', background: C.greenDim, border: `1px solid ${C.green}44`,
          borderRadius: '12px', marginBottom: '24px', textAlign: 'center',
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>✅</div>
          <div style={{ fontSize: '15px', fontWeight: 600, color: C.green, marginBottom: '6px' }}>
            Export Ready
          </div>
          <div style={{ fontSize: '12px', color: C.muted, marginBottom: '16px' }}>
            Ready — expires in 24 hours
          </div>
          <a
            href={job.download_url}
            download
            style={{
              display: 'inline-block', background: C.green, color: '#fff',
              padding: '10px 24px', borderRadius: '10px', textDecoration: 'none',
              fontWeight: 600, fontSize: '14px', marginBottom: '12px',
            }}
          >
            ⬇️ Download {format.toUpperCase()}
          </a>
          <div>
            <button
              onClick={reset}
              style={{
                background: 'none', border: `1px solid ${C.border}`, color: C.muted,
                padding: '7px 16px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer',
              }}
            >
              New Export
            </button>
          </div>
        </div>
      )}

      {/* Failed state */}
      {(job?.status === 'failed' || error) && (
        <div style={{
          padding: '16px', background: C.redDim, border: `1px solid ${C.red}44`,
          borderRadius: '12px', marginBottom: '24px',
        }}>
          <div style={{ color: C.red, fontSize: '14px', marginBottom: '10px' }}>
            ❌ {job?.error ?? error ?? 'Export failed'}
          </div>
          <button
            onClick={reset}
            style={{
              background: C.red, color: '#fff', border: 'none',
              padding: '7px 16px', borderRadius: '8px', fontSize: '12px', cursor: 'pointer',
            }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Pending / processing state */}
      {(job?.status === 'pending' || job?.status === 'processing') && (
        <div style={{
          padding: '24px', background: C.accentDim, border: `1px solid ${C.accent}33`,
          borderRadius: '12px', marginBottom: '24px', textAlign: 'center',
        }}>
          <div style={{ fontSize: '24px', marginBottom: '8px', animation: 'spin 1s linear infinite' }}>⏳</div>
          <div style={{ fontSize: '14px', color: C.muted }}>Preparing your export…</div>
          <div style={{ fontSize: '11px', color: C.dim, marginTop: '6px' }}>This usually takes less than 30 seconds.</div>
        </div>
      )}

      {/* Configuration form (hidden while job in progress) */}
      {!job && (
        <div style={{
          background: C.surface, border: `1px solid ${C.border}`,
          borderRadius: '12px', padding: '24px',
          display: 'flex', flexDirection: 'column', gap: '18px',
        }}>
          {/* Scope */}
          <div>
            <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '8px', fontWeight: 500 }}>
              Data Scope
            </label>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {SCOPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setScope(opt.value)}
                  style={{
                    padding: '7px 14px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
                    background: scope === opt.value ? C.accent : C.surface,
                    color: scope === opt.value ? '#fff' : C.muted,
                    border: `1px solid ${scope === opt.value ? C.accent : C.border}`,
                    fontWeight: scope === opt.value ? 600 : 400,
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Format */}
          <div>
            <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '8px', fontWeight: 500 }}>
              Format
            </label>
            <div style={{ display: 'flex', gap: '8px' }}>
              {FORMAT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setFormat(opt.value)}
                  style={{
                    padding: '7px 18px', borderRadius: '8px', fontSize: '13px', cursor: 'pointer',
                    background: format === opt.value ? C.accent : C.surface,
                    color: format === opt.value ? '#fff' : C.muted,
                    border: `1px solid ${format === opt.value ? C.accent : C.border}`,
                    fontWeight: format === opt.value ? 600 : 400,
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Date range */}
          <div>
            <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '8px', fontWeight: 500 }}>
              Date Range (optional)
            </label>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} style={selectStyle} />
              <span style={{ color: C.dim, fontSize: '12px' }}>to</span>
              <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} style={selectStyle} />
            </div>
          </div>

          {/* Division filter */}
          <div>
            <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '8px', fontWeight: 500 }}>
              Division Filter (optional)
            </label>
            <input
              value={division}
              onChange={(e) => setDivision(e.target.value)}
              placeholder="Leave blank for all divisions"
              style={{ ...selectStyle, width: '100%' }}
            />
          </div>

          {/* Request button */}
          <button
            onClick={() =>
              requestExport(scope, format, dateFrom || undefined, dateTo || undefined, division || undefined)
            }
            disabled={requesting || quota?.remaining === 0}
            style={{
              background: C.green, color: '#fff', border: 'none',
              borderRadius: '10px', padding: '12px', fontSize: '14px', fontWeight: 600,
              cursor: requesting || quota?.remaining === 0 ? 'default' : 'pointer',
              opacity: requesting || quota?.remaining === 0 ? 0.6 : 1,
              marginTop: '4px',
            }}
          >
            {requesting ? '⏳ Requesting…' : '📤 Request Export'}
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## 10. Public ChangelogView

**File:** `apps/web/src/views/ChangelogView.tsx`

### Requirements

- Unauthenticated — placed outside `AppShell` as a standalone route
- Fetches `GET /api/v1/changelog` (public endpoint, no auth header needed)
- Groups entries by `version_tag`, sorted by `shipped_at` descending
- Minimal chrome: no Nav, simple centered layout, back link to `/`

```tsx
// apps/web/src/views/ChangelogView.tsx
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { ChangelogEntry } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { api } from '../lib/api';

export function ChangelogView() {
  const C = useT();
  const [entries, setEntries] = useState<ChangelogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ChangelogEntry[]>('/api/v1/changelog')
      .then((data) => setEntries(data))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load changelog'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div
      style={{
        background: C.bg, minHeight: '100vh', color: C.text,
        fontFamily: "'Outfit',sans-serif",
      }}
    >
      <div style={{ maxWidth: '720px', margin: '0 auto', padding: '48px 24px' }}>
        <Link
          to="/"
          style={{ color: C.accent, textDecoration: 'none', fontSize: '13px', display: 'inline-block', marginBottom: '32px' }}
        >
          ← Back to SkillHub
        </Link>

        <h1 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '8px' }}>
          📋 Changelog
        </h1>
        <p style={{ color: C.muted, fontSize: '15px', marginBottom: '40px' }}>
          Platform updates and shipped features.
        </p>

        {loading && <div style={{ color: C.muted }}>Loading…</div>}
        {error && <div style={{ color: C.red }}>{error}</div>}

        {!loading && entries.length === 0 && (
          <div style={{ color: C.dim, textAlign: 'center', padding: '48px' }}>
            No changelog entries yet.
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {entries.map((entry) => (
            <div key={entry.id}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                <span style={{
                  background: C.accentDim, color: C.accent, padding: '4px 12px',
                  borderRadius: '99px', fontSize: '12px', fontWeight: 700,
                  fontFamily: "'JetBrains Mono',monospace",
                }}>
                  {entry.version_tag}
                </span>
                <span style={{ fontSize: '12px', color: C.dim }}>
                  {new Date(entry.shipped_at).toLocaleDateString('en-US', {
                    year: 'numeric', month: 'long', day: 'numeric',
                  })}
                </span>
              </div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '10px', color: C.text }}>
                {entry.title}
              </h2>
              <div style={{
                fontSize: '14px', color: C.muted, lineHeight: '1.7',
                whiteSpace: 'pre-wrap',
                borderLeft: `3px solid ${C.border}`,
                paddingLeft: '16px',
              }}>
                {entry.changelog_body}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 11. FeedbackNewView (User-facing)

**File:** `apps/web/src/views/FeedbackNewView.tsx`

### Requirements

- Accessible from `/feedback/new`
- Accepts optional `?skill_id=<uuid>` query param; if present, pre-fills skill chip display
- Fields: type radio group, content textarea (required, min 20 chars), optional contact checkbox
- Submit calls `POST /api/v1/feedback`
- Success: inline thank-you message, return link

```tsx
// apps/web/src/views/FeedbackNewView.tsx
import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import type { FeedbackType } from '@skillhub/shared-types';
import { useT } from '../context/ThemeContext';
import { api } from '../lib/api';

const TYPE_OPTIONS: { value: FeedbackType; label: string; desc: string }[] = [
  { value: 'feature_request', label: '✨ Feature Request', desc: 'Suggest a new capability' },
  { value: 'bug_report',      label: '🐛 Bug Report',      desc: 'Something is broken' },
  { value: 'praise',          label: '🙌 Praise',          desc: 'What is working well' },
  { value: 'complaint',       label: '⚠️ Complaint',       desc: 'Something that frustrates you' },
];

export function FeedbackNewView() {
  const C = useT();
  const [searchParams] = useSearchParams();
  const skillId = searchParams.get('skill_id');

  const [type, setType] = useState<FeedbackType>('feature_request');
  const [content, setContent] = useState('');
  const [allowContact, setAllowContact] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isValid = content.trim().length >= 20;

  const handleSubmit = async () => {
    if (!isValid || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post('/api/v1/feedback', {
        type,
        content: content.trim(),
        skill_id: skillId ?? undefined,
        allow_contact: allowContact,
      });
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div style={{ maxWidth: '560px', margin: '0 auto', padding: '80px 24px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🙏</div>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: C.text, marginBottom: '10px' }}>
          Thank you!
        </h1>
        <p style={{ color: C.muted, fontSize: '15px', marginBottom: '28px' }}>
          Your feedback has been received. We read every submission.
        </p>
        <Link
          to={skillId ? `/skills` : '/'}
          style={{
            display: 'inline-block', background: C.accent, color: '#fff',
            padding: '10px 24px', borderRadius: '10px', textDecoration: 'none', fontWeight: 600,
          }}
        >
          ← Back to SkillHub
        </Link>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '560px', margin: '0 auto', padding: '48px 24px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '6px', color: C.text }}>
        Give Feedback
      </h1>
      <p style={{ color: C.muted, fontSize: '14px', marginBottom: '28px' }}>
        Help us improve SkillHub. All feedback is read by the platform team.
      </p>

      {/* Skill context chip */}
      {skillId && (
        <div style={{
          background: C.accentDim, border: `1px solid ${C.accent}44`,
          borderRadius: '8px', padding: '8px 14px', fontSize: '12px', color: C.accent,
          marginBottom: '20px', display: 'inline-block',
        }}>
          🔧 Feedback for a specific skill
        </div>
      )}

      {/* Type selector */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '10px', fontWeight: 500 }}>
          Type
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          {TYPE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setType(opt.value)}
              style={{
                padding: '10px 12px', borderRadius: '10px', textAlign: 'left', cursor: 'pointer',
                background: type === opt.value ? C.accentDim : C.surface,
                border: `1px solid ${type === opt.value ? C.accent : C.border}`,
                color: type === opt.value ? C.accent : C.text,
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{opt.label}</div>
              <div style={{ fontSize: '11px', color: C.muted, marginTop: '2px' }}>{opt.desc}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div style={{ marginBottom: '16px' }}>
        <label style={{ fontSize: '12px', color: C.muted, display: 'block', marginBottom: '8px', fontWeight: 500 }}>
          Feedback *
        </label>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Describe your experience, idea, or issue in detail…"
          rows={6}
          style={{
            width: '100%', background: C.inputBg, border: `1px solid ${C.border}`,
            color: C.text, padding: '10px 14px', borderRadius: '10px', fontSize: '14px',
            resize: 'vertical', fontFamily: 'inherit', outline: 'none',
          }}
        />
        <div style={{
          fontSize: '11px', marginTop: '4px',
          color: content.length < 20 ? C.dim : C.green,
        }}>
          {content.trim().length} / 20 minimum characters
        </div>
      </div>

      {/* Allow contact */}
      <label style={{
        display: 'flex', gap: '10px', alignItems: 'center', cursor: 'pointer',
        marginBottom: '24px', fontSize: '13px', color: C.muted,
      }}>
        <input
          type="checkbox"
          checked={allowContact}
          onChange={(e) => setAllowContact(e.target.checked)}
          style={{ accentColor: C.accent, width: '16px', height: '16px' }}
        />
        The platform team may follow up with me about this feedback
      </label>

      {error && (
        <div style={{
          color: C.red, background: C.redDim, borderRadius: '8px',
          padding: '10px 14px', marginBottom: '16px', fontSize: '13px',
        }}>
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!isValid || submitting}
        style={{
          width: '100%', background: C.accent, color: '#fff', border: 'none',
          borderRadius: '10px', padding: '13px', fontSize: '15px', fontWeight: 600,
          cursor: !isValid || submitting ? 'default' : 'pointer',
          opacity: !isValid || submitting ? 0.6 : 1,
        }}
      >
        {submitting ? 'Submitting…' : 'Submit Feedback'}
      </button>
    </div>
  );
}
```

---

## 12. SkillDetailView Feedback Entry Point

**File:** `apps/web/src/views/SkillDetailView.tsx`

Add a ghost "Give feedback" button in the skill footer section. This requires only a small modification — do NOT refactor the existing view.

Find the section that renders the skill footer (after the reviews section), and add:

```tsx
{/* Feedback entry point — add at bottom of skill detail footer */}
<div style={{ marginTop: '24px', paddingTop: '20px', borderTop: `1px solid ${C.border}` }}>
  <button
    onClick={() => navigate(`/feedback/new?skill_id=${skill.id}`)}
    style={{
      background: 'none',
      border: `1px solid ${C.border}`,
      color: C.muted,
      padding: '8px 16px',
      borderRadius: '8px',
      fontSize: '13px',
      cursor: 'pointer',
    }}
  >
    💬 Give feedback on this skill
  </button>
</div>
```

The `navigate` function is already imported in `SkillDetailView.tsx`. Verify `skill.id` is accessible in scope (it is, from the `skill` variable returned by `useSkillDetail`).

---

## 13. App.tsx Route Registration

**File:** `apps/web/src/App.tsx`

### Changes required

1. Add imports for the three new admin views and two public/user views.
2. Register `/changelog` as a standalone route **outside** `AppShell` (no Nav wrapper).
3. Register `/feedback/new` inside `AppShell`.
4. Register the three admin routes inside `AppShell` (admin layout is assumed to be handled by the admin shell from Stage 2).

```tsx
// New imports to add
import { AdminFeedbackView } from './views/admin/AdminFeedbackView';
import { AdminRoadmapView }  from './views/admin/AdminRoadmapView';
import { AdminExportView }   from './views/admin/AdminExportView';
import { ChangelogView }     from './views/ChangelogView';
import { FeedbackNewView }   from './views/FeedbackNewView';
```

Inside `AppShell`'s `<Routes>`, add:

```tsx
<Route path="/admin/feedback" element={<AdminFeedbackView />} />
<Route path="/admin/roadmap"  element={<AdminRoadmapView />} />
<Route path="/admin/exports"  element={<AdminExportView />} />
<Route path="/feedback/new"   element={<FeedbackNewView />} />
```

Outside `AppShell`, as a sibling `<Route>` in the top-level `<Routes>` wrapping `AppShell`:

```tsx
// In App() — modify the BrowserRouter children:
<Routes>
  <Route path="/changelog" element={<ChangelogView />} />
  <Route path="/*" element={<AppShell />} />
</Routes>
```

This requires restructuring `App.tsx` so that the top-level `BrowserRouter` renders a `Routes` with `/changelog` outside the shell, and `/*` matching the shell. The providers stay wrapping everything.

Full updated `App.tsx`:

```tsx
import { useState } from 'react';
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
import { AdminFeedbackView } from './views/admin/AdminFeedbackView';
import { AdminRoadmapView }  from './views/admin/AdminRoadmapView';
import { AdminExportView }   from './views/admin/AdminExportView';
import { ChangelogView }     from './views/ChangelogView';
import { FeedbackNewView }   from './views/FeedbackNewView';

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
          <Route path="/"                element={<HomeView />} />
          <Route path="/browse"          element={<BrowseView />} />
          <Route path="/search"          element={<SearchView />} />
          <Route path="/filtered"        element={<FilteredView />} />
          <Route path="/skills/:slug"    element={<SkillDetailView />} />
          <Route path="/feedback/new"    element={<FeedbackNewView />} />
          <Route path="/admin/feedback"  element={<AdminFeedbackView />} />
          <Route path="/admin/roadmap"   element={<AdminRoadmapView />} />
          <Route path="/admin/exports"   element={<AdminExportView />} />
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
            <Routes>
              <Route path="/changelog" element={<ChangelogView />} />
              <Route path="/*" element={<AppShell />} />
            </Routes>
          </FlagsProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
```

---

## 14. Testing: Frontend (TDD)

Write ALL tests before any implementation. Run with `npm test` from `apps/web/`.

### 14.1 `AdminFeedbackView.test.tsx`

**File:** `apps/web/src/__tests__/AdminFeedbackView.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { AdminFeedbackView } from '../views/admin/AdminFeedbackView';

// Mock hooks
vi.mock('../hooks/useAdminFeedback', () => ({
  useAdminFeedback: vi.fn(),
}));
vi.mock('../hooks/useAdminRoadmap', () => ({
  useAdminRoadmap: vi.fn(),
}));

import { useAdminFeedback } from '../hooks/useAdminFeedback';
import { useAdminRoadmap } from '../hooks/useAdminRoadmap';

const mockFeedback = [
  {
    id: 'fb-1',
    type: 'feature_request',
    sentiment: 'positive',
    content: 'This skill saves me so much time every day working on things.',
    skill_id: 'skill-1',
    skill_name: 'Code Review',
    skill_slug: 'code-review',
    division: 'Engineering',
    author_id: 'user-1',
    created_at: '2026-03-01T10:00:00Z',
    archived: false,
    roadmap_item_id: null,
  },
  {
    id: 'fb-2',
    type: 'bug_report',
    sentiment: 'critical',
    content: 'The install command fails silently on macOS when dependencies are missing.',
    skill_id: null,
    skill_name: null,
    skill_slug: null,
    division: 'Design',
    author_id: 'user-2',
    created_at: '2026-03-02T14:00:00Z',
    archived: true,
    roadmap_item_id: null,
  },
];

const renderView = () =>
  render(
    <MemoryRouter>
      <ThemeProvider>
        <AdminFeedbackView />
      </ThemeProvider>
    </MemoryRouter>,
  );

describe('AdminFeedbackView', () => {
  beforeEach(() => {
    vi.mocked(useAdminRoadmap).mockReturnValue({
      items: [], loading: false, error: null,
      refetch: vi.fn(), moveItem: vi.fn(), createItem: vi.fn(), shipItem: vi.fn(),
    });
  });

  it('renders loading state', () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: null, loading: true, error: null,
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/loading feedback/i)).toBeInTheDocument();
  });

  it('renders feedback items', async () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: { items: mockFeedback, total: 2, page: 1, per_page: 25 },
      loading: false, error: null,
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/saves me so much time/i)).toBeInTheDocument();
    expect(screen.getByText(/install command fails/i)).toBeInTheDocument();
  });

  it('renders empty state when no items', () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: { items: [], total: 0, page: 1, per_page: 25 },
      loading: false, error: null,
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/no feedback matches/i)).toBeInTheDocument();
  });

  it('shows Archived badge for archived items', () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: { items: mockFeedback, total: 2, page: 1, per_page: 25 },
      loading: false, error: null,
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    expect(screen.getByText('Archived')).toBeInTheDocument();
  });

  it('calls archive when Archive button is clicked', async () => {
    const archive = vi.fn();
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: { items: [mockFeedback[0]], total: 1, page: 1, per_page: 25 },
      loading: false, error: null,
      refetch: vi.fn(), archive, linkToRoadmap: vi.fn(),
    });
    renderView();
    fireEvent.click(screen.getByText(/archive/i));
    expect(archive).toHaveBeenCalledWith('fb-1');
  });

  it('renders skill chip link for feedback with skill', () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: { items: [mockFeedback[0]], total: 1, page: 1, per_page: 25 },
      loading: false, error: null,
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    const link = screen.getByRole('link', { name: /code review/i });
    expect(link).toHaveAttribute('href', '/skills/code-review');
  });

  it('renders error state', () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: null, loading: false, error: 'Network error',
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });

  it('renders pagination when total > per_page', () => {
    vi.mocked(useAdminFeedback).mockReturnValue({
      data: { items: mockFeedback, total: 60, page: 1, per_page: 25 },
      loading: false, error: null,
      refetch: vi.fn(), archive: vi.fn(), linkToRoadmap: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/page 1 of 3/i)).toBeInTheDocument();
  });
});
```

### 14.2 `AdminRoadmapView.test.tsx`

**File:** `apps/web/src/__tests__/AdminRoadmapView.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { AdminRoadmapView } from '../views/admin/AdminRoadmapView';

vi.mock('../hooks/useAdminRoadmap', () => ({
  useAdminRoadmap: vi.fn(),
}));

import { useAdminRoadmap } from '../hooks/useAdminRoadmap';

const mockItems = [
  { id: 'ri-1', title: 'Skill versioning', status: 'planned', position: 0,
    description: 'Allow skills to have versions', feedback_count: 3,
    version_tag: null, changelog_body: null, shipped_at: null, created_at: '2026-01-01T00:00:00Z' },
  { id: 'ri-2', title: 'MCP install improvements', status: 'in_progress', position: 0,
    description: null, feedback_count: 7,
    version_tag: null, changelog_body: null, shipped_at: null, created_at: '2026-01-02T00:00:00Z' },
  { id: 'ri-3', title: 'Analytics export v2', status: 'shipped', position: 0,
    description: null, feedback_count: 2,
    version_tag: 'v1.3.0', changelog_body: 'Added CSV exports', shipped_at: '2026-02-01T00:00:00Z',
    created_at: '2026-01-03T00:00:00Z' },
];

const renderView = () =>
  render(
    <MemoryRouter>
      <ThemeProvider>
        <AdminRoadmapView />
      </ThemeProvider>
    </MemoryRouter>,
  );

describe('AdminRoadmapView', () => {
  beforeEach(() => {
    vi.mocked(useAdminRoadmap).mockReturnValue({
      items: mockItems, loading: false, error: null,
      refetch: vi.fn(), moveItem: vi.fn(), createItem: vi.fn(), shipItem: vi.fn(),
    });
  });

  it('renders four column headers', () => {
    renderView();
    expect(screen.getByText(/planned/i)).toBeInTheDocument();
    expect(screen.getByText(/in progress/i)).toBeInTheDocument();
    expect(screen.getByText(/shipped/i)).toBeInTheDocument();
    expect(screen.getByText(/cancelled/i)).toBeInTheDocument();
  });

  it('renders roadmap items in correct columns', () => {
    renderView();
    expect(screen.getByText('Skill versioning')).toBeInTheDocument();
    expect(screen.getByText('MCP install improvements')).toBeInTheDocument();
    expect(screen.getByText('Analytics export v2')).toBeInTheDocument();
  });

  it('shows "New Item" button in Planned column', () => {
    renderView();
    expect(screen.getByText('+ New Item')).toBeInTheDocument();
  });

  it('shows inline form when "New Item" clicked', () => {
    renderView();
    fireEvent.click(screen.getByText('+ New Item'));
    expect(screen.getByPlaceholderText(/item title/i)).toBeInTheDocument();
  });

  it('calls createItem on form submit', async () => {
    const createItem = vi.fn();
    vi.mocked(useAdminRoadmap).mockReturnValue({
      items: [], loading: false, error: null,
      refetch: vi.fn(), moveItem: vi.fn(), createItem, shipItem: vi.fn(),
    });
    renderView();
    fireEvent.click(screen.getByText('+ New Item'));
    fireEvent.change(screen.getByPlaceholderText(/item title/i), {
      target: { value: 'New feature title' },
    });
    fireEvent.click(screen.getByText('Add'));
    expect(createItem).toHaveBeenCalledWith('New feature title');
  });

  it('renders loading state', () => {
    vi.mocked(useAdminRoadmap).mockReturnValue({
      items: [], loading: true, error: null,
      refetch: vi.fn(), moveItem: vi.fn(), createItem: vi.fn(), shipItem: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/loading roadmap/i)).toBeInTheDocument();
  });

  it('renders Ship button for in_progress items', () => {
    renderView();
    expect(screen.getByText(/ship/i)).toBeInTheDocument();
  });

  it('opens ship panel when Ship button is clicked', () => {
    renderView();
    fireEvent.click(screen.getByText(/✅ Ship/));
    expect(screen.getByText(/mark as shipped/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/v1\.4\.0/i)).toBeInTheDocument();
  });

  it('cards have draggable attribute', () => {
    renderView();
    const cards = screen.getAllByRole('button', { name: /press space or enter to pick up/i });
    expect(cards.length).toBeGreaterThan(0);
  });

  it('has aria-live region for keyboard DnD announcements', () => {
    renderView();
    const liveRegion = document.querySelector('[aria-live="polite"]');
    expect(liveRegion).toBeInTheDocument();
  });
});
```

### 14.3 `AdminExportView.test.tsx`

**File:** `apps/web/src/__tests__/AdminExportView.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { AdminExportView } from '../views/admin/AdminExportView';

vi.mock('../hooks/useAdminExport', () => ({
  useAdminExport: vi.fn(),
}));

import { useAdminExport } from '../hooks/useAdminExport';

const mockQuota = { used: 2, limit: 5, remaining: 3, resets_at: '2026-03-24T00:00:00Z' };

const renderView = () =>
  render(
    <MemoryRouter>
      <ThemeProvider>
        <AdminExportView />
      </ThemeProvider>
    </MemoryRouter>,
  );

describe('AdminExportView', () => {
  beforeEach(() => {
    vi.mocked(useAdminExport).mockReturnValue({
      job: null, quota: mockQuota, requesting: false, error: null,
      requestExport: vi.fn(), reset: vi.fn(),
    });
  });

  it('renders scope selector buttons', () => {
    renderView();
    expect(screen.getByText(/installs/i)).toBeInTheDocument();
    expect(screen.getByText(/submissions/i)).toBeInTheDocument();
    expect(screen.getByText(/users/i)).toBeInTheDocument();
    expect(screen.getByText(/analytics/i)).toBeInTheDocument();
  });

  it('renders format selector', () => {
    renderView();
    expect(screen.getByText('CSV')).toBeInTheDocument();
    expect(screen.getByText('JSON')).toBeInTheDocument();
  });

  it('renders quota banner', () => {
    renderView();
    expect(screen.getByText(/3 of 5 exports remaining/i)).toBeInTheDocument();
  });

  it('calls requestExport on button click', () => {
    const requestExport = vi.fn();
    vi.mocked(useAdminExport).mockReturnValue({
      job: null, quota: mockQuota, requesting: false, error: null,
      requestExport, reset: vi.fn(),
    });
    renderView();
    fireEvent.click(screen.getByText(/request export/i));
    expect(requestExport).toHaveBeenCalledWith('installs', 'csv', undefined, undefined, undefined);
  });

  it('shows pending state when job is pending', () => {
    vi.mocked(useAdminExport).mockReturnValue({
      job: { id: 'ex-1', scope: 'installs', format: 'csv', status: 'pending',
             download_url: null, expires_at: null, created_at: '2026-03-23T10:00:00Z', error: null },
      quota: mockQuota, requesting: false, error: null,
      requestExport: vi.fn(), reset: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/preparing your export/i)).toBeInTheDocument();
  });

  it('shows download link when job is complete', () => {
    vi.mocked(useAdminExport).mockReturnValue({
      job: { id: 'ex-1', scope: 'installs', format: 'csv', status: 'complete',
             download_url: 'https://example.com/exports/ex-1.csv',
             expires_at: '2026-03-24T10:00:00Z', created_at: '2026-03-23T10:00:00Z', error: null },
      quota: mockQuota, requesting: false, error: null,
      requestExport: vi.fn(), reset: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/export ready/i)).toBeInTheDocument();
    expect(screen.getByText(/expires in 24 hours/i)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /download/i });
    expect(link).toHaveAttribute('href', 'https://example.com/exports/ex-1.csv');
  });

  it('shows error state when job fails', () => {
    vi.mocked(useAdminExport).mockReturnValue({
      job: { id: 'ex-1', scope: 'installs', format: 'csv', status: 'failed',
             download_url: null, expires_at: null, created_at: '2026-03-23T10:00:00Z',
             error: 'Database timeout' },
      quota: mockQuota, requesting: false, error: null,
      requestExport: vi.fn(), reset: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/database timeout/i)).toBeInTheDocument();
  });

  it('disables request button when quota is 0', () => {
    vi.mocked(useAdminExport).mockReturnValue({
      job: null,
      quota: { used: 5, limit: 5, remaining: 0, resets_at: '2026-03-24T00:00:00Z' },
      requesting: false, error: null,
      requestExport: vi.fn(), reset: vi.fn(),
    });
    renderView();
    expect(screen.getByText(/export limit reached/i)).toBeInTheDocument();
    const btn = screen.getByText(/request export/i).closest('button');
    expect(btn).toBeDisabled();
  });
});
```

### 14.4 `ChangelogView.test.tsx`

**File:** `apps/web/src/__tests__/ChangelogView.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { ChangelogView } from '../views/ChangelogView';

vi.mock('../lib/api', () => ({
  api: { get: vi.fn() },
}));

import { api } from '../lib/api';

const mockEntries = [
  { id: 'ce-1', version_tag: 'v1.3.0', title: 'Analytics Export',
    changelog_body: 'Added CSV and JSON export capabilities.',
    shipped_at: '2026-02-01T00:00:00Z' },
  { id: 'ce-2', version_tag: 'v1.2.0', title: 'Social Features',
    changelog_body: 'Likes, comments, and follows are now live.',
    shipped_at: '2026-01-15T00:00:00Z' },
];

describe('ChangelogView', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockResolvedValue(mockEntries);
  });

  it('renders changelog heading', async () => {
    render(<MemoryRouter><ThemeProvider><ChangelogView /></ThemeProvider></MemoryRouter>);
    await waitFor(() => expect(screen.getByText(/changelog/i)).toBeInTheDocument());
  });

  it('renders version tags', async () => {
    render(<MemoryRouter><ThemeProvider><ChangelogView /></ThemeProvider></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText('v1.3.0')).toBeInTheDocument();
      expect(screen.getByText('v1.2.0')).toBeInTheDocument();
    });
  });

  it('renders changelog body text', async () => {
    render(<MemoryRouter><ThemeProvider><ChangelogView /></ThemeProvider></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/csv and json export/i)).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(<MemoryRouter><ThemeProvider><ChangelogView /></ThemeProvider></MemoryRouter>);
    await waitFor(() => {
      const link = screen.getByRole('link', { name: /back to skillhub/i });
      expect(link).toHaveAttribute('href', '/');
    });
  });

  it('shows empty state when no entries', async () => {
    vi.mocked(api.get).mockResolvedValue([]);
    render(<MemoryRouter><ThemeProvider><ChangelogView /></ThemeProvider></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText(/no changelog entries yet/i)).toBeInTheDocument();
    });
  });
});
```

### 14.5 `FeedbackNewView.test.tsx`

**File:** `apps/web/src/__tests__/FeedbackNewView.test.tsx`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { FeedbackNewView } from '../views/FeedbackNewView';

vi.mock('../lib/api', () => ({
  api: { post: vi.fn() },
}));

import { api } from '../lib/api';

const renderView = (search = '') =>
  render(
    <MemoryRouter initialEntries={[`/feedback/new${search}`]}>
      <ThemeProvider>
        <FeedbackNewView />
      </ThemeProvider>
    </MemoryRouter>,
  );

describe('FeedbackNewView', () => {
  beforeEach(() => {
    vi.mocked(api.post).mockResolvedValue({});
  });

  it('renders type options', () => {
    renderView();
    expect(screen.getByText(/feature request/i)).toBeInTheDocument();
    expect(screen.getByText(/bug report/i)).toBeInTheDocument();
    expect(screen.getByText(/praise/i)).toBeInTheDocument();
    expect(screen.getByText(/complaint/i)).toBeInTheDocument();
  });

  it('submit button is disabled when content < 20 chars', () => {
    renderView();
    const btn = screen.getByRole('button', { name: /submit feedback/i });
    expect(btn).toBeDisabled();
  });

  it('submit button is enabled when content >= 20 chars', () => {
    renderView();
    fireEvent.change(screen.getByPlaceholderText(/describe your experience/i), {
      target: { value: 'This is a detailed enough feedback entry to pass validation.' },
    });
    const btn = screen.getByRole('button', { name: /submit feedback/i });
    expect(btn).not.toBeDisabled();
  });

  it('calls api.post with correct payload on submit', async () => {
    renderView();
    fireEvent.change(screen.getByPlaceholderText(/describe your experience/i), {
      target: { value: 'This is a detailed enough feedback entry to pass validation.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }));
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/v1/feedback', expect.objectContaining({
        type: 'feature_request',
        content: 'This is a detailed enough feedback entry to pass validation.',
      }));
    });
  });

  it('shows success state after submission', async () => {
    renderView();
    fireEvent.change(screen.getByPlaceholderText(/describe your experience/i), {
      target: { value: 'This is a detailed enough feedback entry to pass validation.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }));
    await waitFor(() => {
      expect(screen.getByText(/thank you/i)).toBeInTheDocument();
    });
  });

  it('shows skill context chip when skill_id in query', () => {
    renderView('?skill_id=skill-123');
    expect(screen.getByText(/feedback for a specific skill/i)).toBeInTheDocument();
  });

  it('shows error state on API failure', async () => {
    vi.mocked(api.post).mockRejectedValue(new Error('Server error'));
    renderView();
    fireEvent.change(screen.getByPlaceholderText(/describe your experience/i), {
      target: { value: 'This is a detailed enough feedback entry to pass validation.' },
    });
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }));
    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });
  });
});
```

---

## 15. Acceptance Criteria

| # | Criterion | Verification |
|---|---|---|
| AC-1 | `AdminFeedbackView` renders with all filter chips; selecting a type updates URL params | Manual + test |
| AC-2 | Sentiment filter applies correct semantic colors (green/muted/red) | Visual + test |
| AC-3 | Archive button calls PATCH and sets item opacity to 40% | Test `archive` mock called |
| AC-4 | "Link to Roadmap" dropdown lists active roadmap items | Test with roadmap items mock |
| AC-5 | `AdminRoadmapView` renders four kanban columns | Test column headers |
| AC-6 | Cards draggable via HTML DnD; `moveItem` called on drop | DnD event simulation |
| AC-7 | Keyboard DnD: Space picks up, ArrowRight/Left moves columns, Enter confirms, Escape cancels | Keyboard event test |
| AC-8 | `aria-live` region announces every keyboard column move | Check announceRef content |
| AC-9 | "New Item" inline form in Planned column; Enter submits, Escape cancels | Form interaction test |
| AC-10 | "Mark as Shipped" panel requires version_tag; calls `shipItem` | Panel interaction test |
| AC-11 | `AdminExportView` scope/format selectors toggle correctly | Button state test |
| AC-12 | Export request calls `requestExport` with correct args | Mock call assertion |
| AC-13 | Polling state shows spinner; complete state shows download link | Job status tests |
| AC-14 | Quota banner turns amber when remaining ≤ 1; button disabled at 0 | Quota mock tests |
| AC-15 | `ChangelogView` renders outside Nav at `/changelog` | Route structure in App.tsx |
| AC-16 | Changelog entries display version_tag, date, title, body | Entries render test |
| AC-17 | `FeedbackNewView` submit disabled until content ≥ 20 chars | Character count test |
| AC-18 | Skill context chip shown when `?skill_id` present | Query param test |
| AC-19 | `SkillDetailView` footer has "Give feedback" ghost button linking to `/feedback/new?skill_id=` | DOM + href test |
| AC-20 | TypeScript: `tsc --noEmit` passes clean on all new files | CI gate |
| AC-21 | Vitest coverage ≥ 80% on all new files | `vitest --coverage` |

---

## 16. Accessibility Contract

| Element | Requirement |
|---|---|
| Kanban cards | `role="button"`, `tabIndex={0}`, `aria-label` includes title and move instruction |
| Kanban pickup | `aria-grabbed={true}` during keyboard pickup |
| Column drop zone | `aria-dropeffect="move"` on column during drag |
| Move announcement | `aria-live="polite"` `aria-atomic="true"` — announces column name on each move |
| "Link to Roadmap" dropdown | Closes on Escape; focus returns to trigger button |
| Date inputs | Explicit `<label>` or `aria-label` on each date input |
| Export "Request Export" | `aria-busy="true"` on button while requesting |
| Feedback textarea | `aria-describedby` pointing to character count element |
| Ship panel overlay | Focus trapped within panel; Escape closes panel |
| Pagination buttons | `aria-disabled="true"` (not `disabled`) on Previous at page 1 and Next at last page |

---

## Do NOT

- Do NOT import any drag-and-drop library (react-beautiful-dnd, @dnd-kit, etc.) — use HTML Drag and Drop API only
- Do NOT add CSS class names or import any stylesheet files — all styles must be inline via `useT()`
- Do NOT use the `disabled` attribute on pagination buttons — use `aria-disabled` to keep them keyboard-reachable
- Do NOT use `console.log` or `console.error` in production paths — use structured error state instead
- Do NOT modify existing hook or view logic beyond the specific additions described in section 12
- Do NOT render the `<Nav>` component inside `ChangelogView` — it is a standalone public page
- Do NOT trust `skill_id` from query params without validating UUID format before sending to API
- Do NOT skip the `aria-live` region in `AdminRoadmapView` — it is required for keyboard DnD accessibility
- Do NOT commit type annotations that require `// @ts-ignore` — fix the underlying type issue instead
