# Stage 6B: Frontend Diagrams Companion

**Stage 6B: Feedback, Roadmap & Export — Frontend Views**
Date: 2026-03-23

---

## 1. Component Tree

```mermaid
graph TD
    App["App()"]
    Providers["ThemeProvider > AuthProvider > FlagsProvider"]
    Routes["BrowserRouter > Routes"]
    Changelog["Route /changelog → ChangelogView"]
    AppShell["Route /* → AppShell"]
    Nav["Nav"]
    ShellRoutes["Shell Routes"]

    App --> Providers
    Providers --> Routes
    Routes --> Changelog
    Routes --> AppShell
    AppShell --> Nav
    AppShell --> ShellRoutes

    ShellRoutes --> FeedbackNew["Route /feedback/new → FeedbackNewView"]
    ShellRoutes --> AdminFeedback["Route /admin/feedback → AdminFeedbackView"]
    ShellRoutes --> AdminRoadmap["Route /admin/roadmap → AdminRoadmapView"]
    ShellRoutes --> AdminExports["Route /admin/exports → AdminExportView"]

    AdminFeedback --> hookFeedback["useAdminFeedback(filters)"]
    AdminFeedback --> hookRoadmap1["useAdminRoadmap() — for Link dropdown"]
    AdminRoadmap --> hookRoadmap2["useAdminRoadmap()"]
    AdminExports --> hookExport["useAdminExport()"]
    ChangelogView["ChangelogView"] --> apiGet["api.get('/api/v1/changelog')"]
    FeedbackNew --> apiPost["api.post('/api/v1/feedback')"]

    subgraph "SkillDetailView modification"
        SkillDetail["SkillDetailView"] --> FeedbackBtn["Ghost button → /feedback/new?skill_id=..."]
    end
```

---

## 2. AdminFeedbackView Layout

```mermaid
graph TD
    FV["AdminFeedbackView"]
    FV --> TypeChips["Type filter chips row\n[All | Feature Request | Bug Report | Praise | Complaint]"]
    FV --> SentimentChips["Sentiment filter chips\n[All Sentiments | Positive | Neutral | Critical]"]
    FV --> DateRange["Date range row\n[From: input[date]] [To: input[date]]"]
    FV --> FeedbackList["Feedback item list"]
    FV --> Pagination["Pagination: ← Prev | Page X of Y | Next →"]

    FeedbackList --> FeedbackRow["FeedbackRow (per item)"]
    FeedbackRow --> SentimentBadge["Sentiment badge (color-coded pill)"]
    FeedbackRow --> TypeChip["Type chip (pill)"]
    FeedbackRow --> SkillLink["Skill chip → /skills/:slug (if skill_slug)"]
    FeedbackRow --> DivisionBadge["Division badge"]
    FeedbackRow --> ArchivedBadge["'Archived' badge (if archived)"]
    FeedbackRow --> ContentBlock["Content excerpt (codeBg, 2-line clamp)"]
    FeedbackRow --> Actions["Actions (only if !archived)"]
    Actions --> LinkDropdown["'Link to Roadmap' dropdown"]
    Actions --> ArchiveBtn["'Archive' button"]
    LinkDropdown --> RoadmapOptions["Roadmap item options (active only)"]
```

---

## 3. Sentiment Color Mapping

```mermaid
graph LR
    positive["sentiment: positive"] -->|bg| greenDim["C.greenDim"]
    positive -->|color| green["C.green"]
    neutral["sentiment: neutral"] -->|bg| accentDim["C.accentDim"]
    neutral -->|color| muted["C.muted"]
    critical["sentiment: critical"] -->|bg| redDim["C.redDim"]
    critical -->|color| red["C.red"]
```

---

## 4. AdminRoadmapView — Kanban Layout

```mermaid
graph LR
    subgraph "Kanban Board (4-column CSS grid, gap: 14px)"
        subgraph "PLANNED (C.muted header)"
            P1["[+ New Item button / inline form]"]
            P2["Card: title, description, feedback_count"]
            P3["Card: title, feedback_count"]
        end
        subgraph "IN PROGRESS (C.accent header)"
            IP1["Card: title + [✅ Ship] button"]
            IP2["Card: title"]
        end
        subgraph "SHIPPED (C.green header)"
            S1["Card: title + version_tag chip"]
        end
        subgraph "CANCELLED (C.dim header)"
            C1["(empty)"]
        end
    end
```

---

## 5. Kanban Card Anatomy

```mermaid
graph TD
    Card["RoadmapCard\n(borderRadius:12px, surface bg, border, padding:16px)"]
    Card --> Title["Title (13px/600, C.text)"]
    Card --> Desc["Description (12px, C.muted) — optional"]
    Card --> Footer["Footer row"]
    Footer --> FeedbackCount["💬 N (if feedback_count > 0)"]
    Footer --> ShipBtn["✅ Ship button (in_progress only)"]
    Footer --> VersionTag["version_tag chip (shipped only)"]

    Card --> DragAttr["draggable=true"]
    Card --> A11y["role=button, tabIndex=0\naria-label='[title]. Press Space or Enter to pick up and move.'\naria-grabbed={isPickedUp}"]
```

---

## 6. Drag-and-Drop State Machine

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Dragging : onDragStart(itemId, sourceStatus)
    Dragging --> DragOver : onDragOver(targetColumn)
    DragOver --> Dragging : onDragLeave
    DragOver --> Idle : onDrop → moveItem(id, toStatus, toPosition)
    Dragging --> Idle : onDragEnd (drop outside column)
```

---

## 7. Keyboard Drag-and-Drop State Machine

```mermaid
stateDiagram-v2
    [*] --> Rest
    Rest --> PickedUp : Space / Enter on card\nannounce: "Picked up [title]. Use arrow keys..."
    PickedUp --> PickedUp_ColRight : ArrowRight\nannounce: "Moved to [COLUMN]"
    PickedUp --> PickedUp_ColLeft : ArrowLeft\nannounce: "Moved to [COLUMN]"
    PickedUp_ColRight --> PickedUp : (same state, new currentStatus)
    PickedUp_ColLeft --> PickedUp : (same state, new currentStatus)
    PickedUp --> Rest : Enter → moveItem(id, currentStatus, position)\nannounce: "Placed [title] in [COLUMN]"
    PickedUp --> Rest : Escape\nannounce: "Cancelled. [title] remains in [COLUMN]"
```

---

## 8. "Mark as Shipped" Side Panel Flow

```mermaid
sequenceDiagram
    participant User
    participant AdminRoadmapView
    participant SidePanel
    participant API

    User->>AdminRoadmapView: Click "✅ Ship" on in_progress card
    AdminRoadmapView->>SidePanel: setShipTarget(item) — panel slides in
    User->>SidePanel: Fill version_tag (required) + changelog_body
    User->>SidePanel: Click "🚀 Ship It"
    SidePanel->>API: PATCH /api/v1/admin/roadmap/{id}/ship
    API-->>SidePanel: Updated RoadmapItem (status: shipped)
    SidePanel->>AdminRoadmapView: setItems (item updated)
    SidePanel->>AdminRoadmapView: setShipTarget(null) — panel closes
```

---

## 9. AdminExportView — State Machine

```mermaid
stateDiagram-v2
    [*] --> Configuration : initial load (job = null)
    Configuration --> Requesting : Click "Request Export"
    Requesting --> Polling : POST /admin/exports → job created (pending/processing)
    Requesting --> Configuration : API error → show error + Try Again
    Polling --> Polling : GET /admin/exports/{id} every 2s (status: pending/processing)
    Polling --> Complete : status = complete
    Polling --> Failed : status = failed
    Complete --> Configuration : Click "New Export" → reset()
    Failed --> Configuration : Click "Try Again" → reset()
```

---

## 10. AdminExportView — Component Layout

```mermaid
graph TD
    EV["AdminExportView"]
    EV --> QuotaBanner["Quota banner\n(accent when N>1, amber when N≤1, hidden when loading)"]
    EV --> JobState{job status?}

    JobState -->|null| ConfigForm["Configuration Form\n(surface bg, border, 12px radius, 24px padding)"]
    JobState -->|pending/processing| Spinner["⏳ Preparing your export…\n(accentDim bg)"]
    JobState -->|complete| DownloadBlock["✅ Export Ready\n[⬇️ Download CSV/JSON link]\n'expires in 24 hours'\n[New Export button]"]
    JobState -->|failed| ErrorBlock["❌ Error message\n[Try Again button]"]

    ConfigForm --> ScopeRow["Scope toggle buttons\n[Installs | Submissions | Users | Analytics]"]
    ConfigForm --> FormatRow["Format toggle buttons\n[CSV | JSON]"]
    ConfigForm --> DateRow["Date range\n[From date] [To date]"]
    ConfigForm --> DivisionInput["Division filter input (optional)"]
    ConfigForm --> RequestBtn["📤 Request Export (C.green bg)\n(disabled when quota.remaining = 0)"]
```

---

## 11. Feedback Form Flow (User-facing)

```mermaid
flowchart TD
    Start(["User on SkillDetailView"]) --> FeedbackBtn["Click '💬 Give feedback on this skill'"]
    FeedbackBtn --> Navigate["navigate('/feedback/new?skill_id=' + skill.id)"]
    Navigate --> FeedbackNewView["FeedbackNewView renders\n(skill context chip shown)"]

    StartDirect(["User types /feedback/new directly"]) --> FeedbackNewView2["FeedbackNewView renders\n(no skill context chip)"]

    FeedbackNewView --> SelectType["Select type\n(Feature Request / Bug Report / Praise / Complaint)"]
    FeedbackNewView2 --> SelectType

    SelectType --> WriteContent["Write content (≥20 chars required)"]
    WriteContent --> CharCount{"content.trim().length ≥ 20?"}
    CharCount -->|No| DisabledBtn["Submit button disabled\ncharacter count shown in C.dim"]
    CharCount -->|Yes| EnabledBtn["Submit button enabled\ncharacter count shown in C.green"]
    EnabledBtn --> Submit["Click 'Submit Feedback'"]
    Submit --> PostAPI["POST /api/v1/feedback"]
    PostAPI -->|Success| ThankYou["🙏 Thank you! screen\n← Back to SkillHub link"]
    PostAPI -->|Error| ErrorMsg["Error message shown\nForm remains editable"]
```

---

## 12. Public Changelog Route Isolation

```mermaid
graph TD
    BrowserRouter["BrowserRouter"]
    BrowserRouter --> TopRoutes["Top-level Routes"]
    TopRoutes --> ChangelogRoute["Route path='/changelog'\n→ ChangelogView (standalone, no Nav)"]
    TopRoutes --> AppShellRoute["Route path='/*'\n→ AppShell (with Nav, Auth, theme shell)"]

    subgraph "ChangelogView (no Nav)"
        CL["← Back to SkillHub link"]
        CL2["📋 Changelog heading"]
        CL3["Entry list: version_tag + date + title + body"]
    end

    ChangelogRoute --> CL
```

---

## 13. Hook Data Flow

```mermaid
graph LR
    subgraph "useAdminFeedback"
        AF_params["FeedbackFilters (type, sentiment, dates, page)"]
        AF_params -->|GET /api/v1/admin/feedback| AF_state["{ data, loading, error }"]
        AF_archive["archive(id)"] -->|PATCH .../archive| AF_state
        AF_link["linkToRoadmap(fbId, rmId)"] -->|PATCH .../roadmap| AF_state
    end

    subgraph "useAdminRoadmap"
        AR_fetch["fetch()"] -->|GET /api/v1/admin/roadmap| AR_items["items: RoadmapItem[]"]
        AR_move["moveItem(id, status, pos)"] -->|optimistic update + PATCH| AR_items
        AR_create["createItem(title)"] -->|POST /api/v1/admin/roadmap| AR_items
        AR_ship["shipItem(id, ver, log)"] -->|PATCH .../ship| AR_items
    end

    subgraph "useAdminExport"
        AE_req["requestExport(scope, format, ...)"] -->|POST /api/v1/admin/exports| AE_job["job: ExportJob | null"]
        AE_poll["setInterval 2000ms"] -->|GET /api/v1/admin/exports/{id}| AE_job
        AE_quota["fetchQuota()"] -->|GET .../quota| AE_quota_state["quota: ExportQuota"]
        AE_job -->|status complete/failed| AE_stopPoll["stopPoll()"]
    end
```

---

## 14. Token Reference by View

```mermaid
graph TD
    subgraph "AdminFeedbackView tokens"
        T1["Active chip: C.accent bg, #fff text"]
        T2["Inactive chip: C.surface bg, C.muted text, C.border border"]
        T3["Content block: C.codeBg bg, 6px radius"]
        T4["Positive: C.greenDim / C.green"]
        T5["Neutral: C.accentDim / C.muted"]
        T6["Critical: C.redDim / C.red"]
    end

    subgraph "AdminRoadmapView tokens"
        R1["Column bg: C.bg (idle), C.surfaceHi (drag target)"]
        R2["Column border: C.border (idle), C.accent (drag target)"]
        R3["Card: C.surface bg, C.border border, 12px radius, 16px padding"]
        R4["Planned header: C.muted"]
        R5["In Progress header: C.accent"]
        R6["Shipped header: C.green"]
        R7["Cancelled header: C.dim"]
        R8["Column header: 11px/600/uppercase/0.8px letter-spacing"]
    end

    subgraph "AdminExportView tokens"
        E1["Scope/Format active: C.accent bg, #fff text"]
        E2["Request btn: C.green bg, #fff text"]
        E3["Complete block: C.greenDim bg, C.green border"]
        E4["Pending block: C.accentDim bg, C.accent border"]
        E5["Failed block: C.redDim bg, C.red border"]
        E6["Quota normal: C.accentDim / C.accent"]
        E7["Quota low (≤1): C.amberDim / C.amber"]
    end
```
