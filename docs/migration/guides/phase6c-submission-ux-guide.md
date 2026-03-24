# Phase 6C — User Skill Submission UI/UX: Technical Implementation Guide

## For Claude Code — Complete Handoff Document

**Project:** SkillHub Phase 6 Stage C — Submission UI/UX
**Starting Point:** Phase 6 Stages A+B complete. Flask app at `apps/api` with submission pipeline, admin HITL queue with revision tracking, VitePress docs. Existing models in `libs/db/skillhub_db/models/`. Existing submission endpoint `POST /api/v1/submissions` functional.
**Approach:** TDD-first, component-driven development with Vitest (unit) + Playwright (E2E)

---

## Supplementary Materials

```
+-----------------------------------------------------------------------------+
| COMPANION DOCUMENTS                                                         |
+-----------------------------------------------------------------------------+
|                                                                             |
|  phase6-post-migration-diagrams.md                                          |
|    Section 4 — Component hierarchy for submission page                      |
|                                                                             |
|  phase6-post-migration-guide.md                                             |
|    Stage C overview, Open Design Questions #5 (MCP Sync scope)              |
|    Stage A context for submission pipeline, state transitions, gate logic    |
|                                                                             |
|  USAGE: Reference Section 4 diagrams when building component tree.          |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Table of Contents

1. [Global Standards](#global-standards)
2. [Codebase Map](#codebase-map)
3. [Phase C.1 — Shared Components](#phase-c1--shared-components)
4. [Phase C.2 — Submission Modes](#phase-c2--submission-modes)
5. [Phase C.3 — Submission Page Assembly](#phase-c3--submission-page-assembly)
6. [Admin Self-Submission Flow](#admin-self-submission-flow)
7. [Quick Reference: Prompt Sequence](#quick-reference-prompt-sequence)
8. [Dependency Graph](#dependency-graph)

---

## Global Standards

Apply to every prompt. Non-negotiable.

```yaml
Code Quality:
  - Python: ruff (lint + format), mypy --strict, no type: ignore without comment
  - TypeScript: eslint, prettier, tsc --noEmit clean
  - No commented-out code committed
  - No print() / console.log() in production paths — use structured logging

Testing:
  - TDD: write tests FIRST, then implementation
  - Python coverage gate: >=80% (pytest-cov --cov-fail-under=80)
  - TypeScript coverage gate: >=80% (vitest --coverage)
  - Vitest test file lives adjacent to implementation:
    FrontMatterValidator.test.tsx next to FrontMatterValidator.tsx
  - Playwright E2E tests in apps/web/apps/web/e2e/tests/
  - After each major UI component, add entry to docs/features/index.md

Security:
  - No secrets in code — all via Settings (pydantic-settings) or Flask config
  - JWT: decode before trusting, never trust raw claims without verification
  - Division enforcement happens server-side — never client-side
  - File uploads: validate type + size server-side, never trust client headers
  - Sanitize all user-provided markdown before rendering (DOMPurify)

Time Budget:
  - Each prompt: 15-45 minutes
  - If a prompt takes longer, split it — do not exceed 45 minutes
```

### Existing Patterns (All Code Must Follow)

```
File locations:
  - Models: libs/db/skillhub_db/models/
  - Services: apps/fast-api/skillhub/services/ (shared via PYTHONPATH)
  - Schemas: apps/fast-api/skillhub/schemas/ (shared via PYTHONPATH)
  - Flask blueprints: apps/api/skillhub_flask/blueprints/
  - Flask tests: apps/api/tests/
  - React views: apps/web/src/views/
  - React components: apps/web/src/components/
  - React hooks: apps/web/src/hooks/
  - API client: apps/web/src/lib/api.ts (apiFetch<T> helper)
  - Auth helpers: apps/web/src/lib/auth.ts (getToken, clearToken)
  - Shared types: libs/shared-types/src/index.ts
  - E2E tests: apps/web/apps/web/e2e/tests/
  - E2E fixtures: apps/web/apps/web/e2e/fixtures/auth.ts
  - PYTHONPATH: apps/api:apps/fast-api:libs/db:libs/python-common

React patterns:
  - useT() hook for theme colors (via ThemeContext)
  - useAuth() hook for current user
  - useFlag(key) hook for feature flags
  - MemoryRouter + ThemeProvider + AuthProvider + FlagsProvider wrapper in tests
  - vi.stubGlobal('fetch', mockFetch) for API mocking in Vitest
  - Inline styles (no CSS modules in this codebase)
  - Lazy-loaded views with Suspense fallback

Flask patterns:
  - g.current_user — set by before_request hook
  - @require_platform_team — decorator for admin routes
  - get_db() for database session
  - Background threads use SessionLocal() directly
  - PUBLIC_ENDPOINTS — add endpoint names for new public routes

Existing constants (libs/shared-types/src/index.ts):
  - CATEGORIES: ['All', 'Engineering', 'Product', 'Data', 'Security',
    'Finance', 'General', 'HR', 'Research']
  - DIVISIONS: ['Engineering Org', 'Product Org', 'Finance & Legal',
    'People & HR', 'Operations', 'Executive Office',
    'Sales & Marketing', 'Customer Success']
```

### Definition of Done (every prompt)

```
- [ ] Tests written first and passing
- [ ] No type errors (mypy / tsc)
- [ ] No lint warnings (ruff / eslint)
- [ ] Acceptance criteria verified
- [ ] No secrets in committed code
- [ ] Existing tests still pass (no regressions)
- [ ] Entry added to docs/features/index.md (for major UI components)
```

---

## Codebase Map

```
apps/
  api/
    skillhub_flask/
      blueprints/
        submissions.py         # Existing: POST /api/v1/submissions, admin endpoints
      auth.py                  # require_platform_team, g.current_user
      db.py                    # get_db()
    tests/                     # pytest tests for Flask
  fast-api/
    skillhub/
      schemas/
        submission.py          # SubmissionCreateRequest, SubmissionDetail, etc.
      services/
        submissions.py         # create_submission, review_submission, etc.
        llm_judge.py           # LLM judge service (Gate 2)
  web/
    src/
      App.tsx                  # React Router: /, /browse, /search, /skills/:slug, /admin/*
      components/
        SkillCard.tsx           # Browse grid card
        Nav.tsx                 # Top nav bar
        admin/                  # Admin-specific components
        submission/             # NEW: all C.* components go here
      views/
        HomeView.tsx            # Landing page
        SubmitSkillPage.tsx     # NEW: /submit route
        admin/                  # Admin views
      hooks/
        useAuth.ts              # Auth hook
        useSkills.ts            # Skills API hooks
        useJudgeHints.ts        # NEW: LLM judge hints hook
      lib/
        api.ts                  # apiFetch<T>, ApiError, buildUrl
        auth.ts                 # getToken, clearToken
    apps/web/e2e/
      tests/
        submission/             # NEW: E2E tests for submission flow
      fixtures/
        auth.ts                 # loginAs('alice') helper
libs/
  shared-types/src/index.ts    # CATEGORIES, DIVISIONS, SkillSummary, etc.
  db/skillhub_db/models/       # SQLAlchemy models
```

---

## Phase C.1 — Shared Components

> These components are mode-agnostic building blocks consumed by all three submission modes and the page assembly.

---

### Prompt C.1.1 — FrontMatterValidator component

```
Create a mode-agnostic front matter validation component that provides real-time
feedback on SKILL.md structure.

CONTEXT:
- Used by all three submission modes (FormBuilder, FileUpload, MCPSync)
- Validates the YAML front matter block of SKILL.md content
- See Section 4 of phase6-post-migration-diagrams.md for component hierarchy
- Existing categories: CATEGORIES from libs/shared-types/src/index.ts
  ['All', 'Engineering', 'Product', 'Data', 'Security', 'Finance', 'General',
   'HR', 'Research']
- Existing submission schema: apps/fast-api/skillhub/schemas/submission.py
  SubmissionCreateRequest has: name (1-255), short_desc (1-255), category (1-100)

WHAT TO BUILD:

1. Create apps/web/src/components/submission/FrontMatterValidator.tsx:
   - Props:
     * content: string (full SKILL.md text including front matter)
     * onChange: (issues: ValidationIssue[]) => void
   - ValidationIssue type:
     { field: string, severity: 'error' | 'warning' | 'info', message: string }
   - Validates:
     * Front matter delimiters present (--- ... ---)
     * Required fields: name, description, category, version, author,
       install_method, data_sensitivity
     * Field value constraints:
       - name: 1-255 chars
       - description: 1-255 chars
       - version: valid semver (X.Y.Z pattern)
       - category: must be one of CATEGORIES (excluding 'All')
       - install_method: 'claude-code' | 'mcp' | 'manual' | 'all'
       - data_sensitivity: 'low' | 'medium' | 'high' | 'phi'
     * Warnings (non-blocking) for:
       - Missing optional fields (tags, trigger_phrases, changelog)
       - Short description (< 20 chars)
       - No trigger phrases defined
   - Renders: compact vertical list of issues with severity icons
     * Error: red circle-x icon
     * Warning: amber triangle icon
     * Info: blue info-circle icon
   - Green checkmark banner when all required fields are valid
   - Updates on every content change (debounced 300ms via setTimeout)

2. Export the core validation logic as a standalone pure function:
   validateFrontMatter(content: string): ValidationIssue[]
   - Lives in apps/web/src/components/submission/validateFrontMatter.ts
   - Fully testable without React
   - Parses YAML front matter using simple regex + line splitting
     (do NOT add a YAML parsing library — front matter is flat key:value)

3. Export the ValidationIssue type from the same file.

TESTING — Write tests FIRST:

File: apps/web/src/components/submission/validateFrontMatter.test.ts
  - validateFrontMatter: valid content with all required fields returns []
  - validateFrontMatter: missing --- delimiters returns error
  - validateFrontMatter: empty string returns delimiter error
  - validateFrontMatter: missing each required field returns specific error
    (test name, description, category, version, author, install_method,
     data_sensitivity each individually)
  - validateFrontMatter: name > 255 chars returns error
  - validateFrontMatter: description > 255 chars returns error
  - validateFrontMatter: invalid semver (e.g. "1.0", "abc") returns error
  - validateFrontMatter: valid semver "1.0.0" passes
  - validateFrontMatter: invalid category returns error
  - validateFrontMatter: valid category "Engineering" passes
  - validateFrontMatter: invalid install_method returns error
  - validateFrontMatter: invalid data_sensitivity returns error
  - validateFrontMatter: missing optional fields (tags) returns warning
  - validateFrontMatter: description < 20 chars returns warning
  - validateFrontMatter: missing trigger_phrases returns info-level hint

File: apps/web/src/components/submission/FrontMatterValidator.test.tsx
  - Renders issue list when content has errors
  - Shows green checkmark when content is valid
  - Calls onChange with current issues array
  - Debounces: rapid content changes trigger only one validation pass
  - Renders correct severity icons (error=red, warning=amber)
  - Empty content shows delimiter error

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/front-matter-validation.spec.ts
  - Validator shows errors when skill content has missing fields
  - Validator shows green checkmark when all fields are valid
  - Validator updates as user types

DO NOT:
- Add a YAML parsing library (use simple string parsing for flat front matter)
- Create the SkillPreviewPanel (next prompt)
- Wire to any submission mode or page
- Add API calls — validation is 100% client-side
- Use CSS modules or styled-components (inline styles per codebase convention)

Acceptance Criteria:
- [ ] validateFrontMatter pure function handles all field validations
- [ ] FrontMatterValidator component renders issues with severity icons
- [ ] Green checkmark shown when valid
- [ ] 300ms debounce prevents excessive re-renders
- [ ] onChange callback fires with current issues
- [ ] All unit tests pass (>=80% coverage on new files)
- [ ] E2E test passes
- [ ] Accessible: severity communicated via both icon and sr-only text
- [ ] Entry added to docs/features/index.md
```

---

### Prompt C.1.2 — SkillPreviewPanel component

```
Create a live preview panel that renders SKILL.md content as it would appear
to end users browsing the marketplace.

CONTEXT:
- Shared across all three submission modes
- Renders the assembled SKILL.md in a read-only preview card
- Updates live as user edits (debounced)
- Existing SkillCard component: apps/web/src/components/SkillCard.tsx
  uses inline styles, useT() for theme
- Existing theme: apps/web/src/lib/theme.ts
- validateFrontMatter from C.1.1 parses front matter
- See Section 4 of phase6-post-migration-diagrams.md

WHAT TO BUILD:

1. Create apps/web/src/components/submission/SkillPreviewPanel.tsx:
   - Props:
     * content: string (full SKILL.md text including front matter)
     * mode: 'split' | 'preview' (layout hint)
   - Parses front matter to extract metadata fields
   - Renders a preview card with:
     * Header: skill name (h2), category badge, version badge
     * Description paragraph
     * Install method badge (color-coded: claude-code=blue, mcp=purple,
       manual=gray, all=green)
     * Data sensitivity indicator (low=green, medium=amber, high=red, phi=red)
     * Tags as pill chips (use TAG_HUES array pattern from SkillCard.tsx)
     * Trigger phrases as a bullet list under "Trigger Phrases" subheading
     * Content body rendered as markdown
   - Markdown rendering:
     * Install `marked` and `dompurify` as dependencies
     * Code blocks with syntax highlighting via `highlight.js`
     * Tables, lists, headings — standard markdown
     * NO raw HTML allowed (sanitize via DOMPurify)
     * Links open in new tab (target="_blank" rel="noopener noreferrer")
   - Split mode: renders in a fixed-width panel (suitable for side-by-side)
   - Preview mode: full-width rendering
   - States:
     * Empty content: "No content yet — start editing to see a preview" placeholder
     * Malformed front matter: show raw text with amber warning banner
       "Could not parse front matter. Showing raw content."
     * Error: if marked throws, show raw text fallback

2. Reuse the validateFrontMatter parser for extracting field values.
   Create a helper: parseFrontMatter(content: string): Record<string, string>
   in apps/web/src/components/submission/parseFrontMatter.ts

TESTING — Write tests FIRST:

File: apps/web/src/components/submission/parseFrontMatter.test.ts
  - parseFrontMatter: extracts all fields from valid front matter
  - parseFrontMatter: returns empty object for missing delimiters
  - parseFrontMatter: handles multi-word values
  - parseFrontMatter: handles list values (tags, trigger_phrases)

File: apps/web/src/components/submission/SkillPreviewPanel.test.tsx
  - Renders skill name from front matter
  - Renders category badge
  - Renders version badge
  - Renders install method badge with correct color
  - Renders data sensitivity indicator
  - Renders tags as chips
  - Renders markdown content body
  - Handles empty content (shows placeholder)
  - Handles malformed front matter (shows warning + raw text)
  - Sanitizes HTML in content (strips <script> tags)
  - Code blocks rendered (contains <pre><code>)
  - Split mode applies narrower width
  - Preview mode applies full width

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/skill-preview.spec.ts
  - Preview panel shows skill name when valid content entered
  - Preview panel shows placeholder when content is empty
  - Preview panel updates live as content changes

DO NOT:
- Add editing capability (this is read-only preview)
- Wire to API
- Create submission modes yet
- Import SkillCard — this is a separate preview component, not a browse card
- Use react-markdown (use marked + DOMPurify for consistency and bundle size)

Acceptance Criteria:
- [ ] Preview renders accurately from SKILL.md content
- [ ] Front matter metadata displayed as badges/chips
- [ ] Markdown rendered safely (DOMPurify sanitized)
- [ ] Code blocks have syntax highlighting
- [ ] Empty and error states handled gracefully
- [ ] Split vs preview mode layout works
- [ ] All unit tests pass (>=80% coverage)
- [ ] E2E test passes
- [ ] Entry added to docs/features/index.md
```

---

## Phase C.2 — Submission Modes

> Three independent input modes that all produce the same artifact: a `string` containing assembled SKILL.md content. Each mode calls `onContentChange(content: string)` whenever the user's work changes.

---

### Prompt C.2.1 — FormBuilderMode (guided wizard)

```
Create the form-based guided wizard for skill submission — the default mode
for users who want step-by-step guidance.

CONTEXT:
- One of three submission modes in SubmitSkillPage
- Produces assembled SKILL.md string via onContentChange callback
- FrontMatterValidator (C.1.1) and SkillPreviewPanel (C.1.2) are built
- Existing constants: CATEGORIES and DIVISIONS from libs/shared-types/src/index.ts
- See Section 4 of phase6-post-migration-diagrams.md

WHAT TO BUILD:

1. Create apps/web/src/components/submission/FormBuilderMode.tsx:
   - Props:
     * onContentChange: (content: string) => void
     * initialContent?: string (for mode-switching content preservation)
   - 4-step wizard with visual progress indicator (numbered dots + connecting line):

     Step 1 — Basics:
       * name: text input (required, 1-255 chars)
       * short_desc: text input (required, 1-255 chars, labelled "Description")
       * category: <select> dropdown from CATEGORIES (excluding 'All')
       * version: text input (default "1.0.0", validated as semver)

     Step 2 — Configuration:
       * install_method: radio group (claude-code | mcp | manual | all)
       * data_sensitivity: radio group (low | medium | high | phi)
       * divisions: multi-select checkboxes from DIVISIONS
         (at least one required)
       * tags: tag input (type + Enter to add, click X to remove)
       * trigger_phrases: list builder (type + Enter to add, click X to remove)

     Step 3 — Content:
       * Textarea (monospace, min-height 300px) for skill body markdown
       * Simple formatting toolbar: Bold, Italic, Code, Heading, List
         (toolbar inserts markdown syntax at cursor position)
       * "Import from file" button that opens file picker for .md files
         (reads file content into textarea, preserving any existing front matter
          entries from steps 1+2)

     Step 4 — Review:
       * Read-only: SkillPreviewPanel in 'preview' mode with assembled content
       * FrontMatterValidator showing current validation state
       * "Edit" buttons per section that jump back to the relevant step

   - Navigation:
     * "Previous" and "Next" buttons at bottom
     * "Previous" disabled on step 1
     * "Next" disabled until current step's required fields are filled
     * Step indicator dots are clickable (but only to previously completed steps)

   - Content assembly:
     * Builds SKILL.md string from form state:
       ```
       ---
       name: {name}
       description: {short_desc}
       category: {category}
       version: {version}
       author: {current user from context, or "Author"}
       install_method: {install_method}
       data_sensitivity: {data_sensitivity}
       tags: [{tags joined}]
       trigger_phrases: [{trigger_phrases joined}]
       ---

       {content body from step 3}
       ```
     * Calls onContentChange with assembled string (debounced 500ms)

   - If initialContent is provided, reverse-parse it to populate form fields

2. Create apps/web/src/components/submission/StepIndicator.tsx:
   - Props: steps: string[], currentStep: number,
     completedSteps: Set<number>, onStepClick: (step: number) => void
   - Renders numbered dots with labels, connected by a line
   - Current step: filled accent color
   - Completed steps: green check, clickable
   - Future steps: gray outline, not clickable

TESTING — Write tests FIRST:

File: apps/web/src/components/submission/FormBuilderMode.test.tsx
  - Renders step 1 by default with name, description, category, version fields
  - Next button disabled when step 1 fields empty
  - Next button enabled after filling all step 1 required fields
  - Navigates to step 2 on Next click
  - Previous button navigates back to step 1
  - Step 2: division checkboxes from DIVISIONS array
  - Step 2: tag input adds tag on Enter key
  - Step 2: tag input removes tag on X click
  - Step 3: textarea accepts markdown content
  - Step 3: formatting toolbar inserts bold syntax
  - Step 4: renders SkillPreviewPanel with assembled content
  - onContentChange called with assembled SKILL.md string
  - Content assembly includes front matter block with correct fields
  - initialContent reverse-parses to populate form fields
  - Step indicator shows current step highlighted
  - Cannot click ahead to uncompleted steps

File: apps/web/src/components/submission/StepIndicator.test.tsx
  - Renders correct number of step dots
  - Current step has accent styling
  - Completed step shows checkmark and is clickable
  - Future step is grayed out and not clickable
  - Click on completed step fires onStepClick

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/form-builder.spec.ts
  - User can fill out step 1 and advance to step 2
  - User can navigate back and forth between steps
  - Step 4 shows assembled preview of the skill
  - Tag input works (add and remove tags)

DO NOT:
- Create FileUploadMode or MCPSyncMode (separate prompts)
- Add API submission calls (SubmitSkillPage handles that)
- Create SubmitSkillPage wrapper
- Install a rich text editor library (use plain textarea + toolbar)
- Use contentEditable (use textarea)

Acceptance Criteria:
- [ ] 4-step wizard fully navigable
- [ ] Per-step validation prevents advancing with empty required fields
- [ ] Form fields assemble valid SKILL.md string
- [ ] onContentChange fires with correct content (debounced)
- [ ] StepIndicator reflects current/completed/future states
- [ ] initialContent reverse-parsing works
- [ ] All unit tests pass (>=80% coverage)
- [ ] E2E tests pass
- [ ] Accessible: fieldset/legend per step, required indicators,
      step announcements via aria-live
- [ ] Entry added to docs/features/index.md
```

---

### Prompt C.2.2 — FileUploadMode (drag-and-drop)

```
Create the file upload mode for skill submission — the fast path for
experienced authors who already have a SKILL.md file.

CONTEXT:
- Second of three submission modes
- Drag-drop a .md file, parse it client-side, validate, edit, preview
- FrontMatterValidator (C.1.1) and SkillPreviewPanel (C.1.2) are built
- parseFrontMatter helper from C.1.2 extracts metadata
- Existing codebase uses inline styles, useT() for theme

WHAT TO BUILD:

1. Create apps/web/src/components/submission/FileUploadMode.tsx:
   - Props:
     * onContentChange: (content: string) => void
     * initialContent?: string
   - States: 'empty' | 'preview' | 'editing'

   Empty state (drop zone):
     * Dashed border (2px dashed, theme muted color), rounded corners
     * Center-aligned: upload icon + "Drop a .md file here or click to browse"
     * Click triggers hidden <input type="file" accept=".md">
     * Drag-over state: border becomes accent color, bg lightens,
       text changes to "Release to upload"
     * File validation:
       - Must have .md extension (reject with "Only .md files are accepted")
       - Must be <= 500KB (reject with "File too large — maximum 500KB")

   Preview state (after successful file read):
     * File info bar: filename, file size formatted (e.g. "12.4 KB"),
       green checkmark
     * FrontMatterValidator running on file content
     * SkillPreviewPanel showing rendered preview
     * Two buttons: "Edit Content" (enters editing state), "Replace File"
       (resets to empty state)
     * "Clear" button (resets to empty state)

   Editing state:
     * Editable textarea with file content (monospace, full width)
     * FrontMatterValidator updates live
     * SkillPreviewPanel updates live (side-by-side layout)
     * "Back to Preview" button

   - On every content change (drop, edit, replace): call onContentChange
   - If initialContent provided, start in 'preview' state with that content

2. File reading:
   - Use FileReader.readAsText()
   - Assume UTF-8 encoding
   - On read complete: set content, transition to 'preview' state
   - On read error: show error message, stay in 'empty' state

TESTING — Write tests FIRST:

File: apps/web/src/components/submission/FileUploadMode.test.tsx
  - Renders drop zone with correct placeholder text in empty state
  - Drag-over state changes visual feedback (border color)
  - Valid .md file: content read and displayed
  - Non-.md file: rejected with error message
  - File over 500KB: rejected with error message
  - After upload: file info bar shows filename and size
  - After upload: FrontMatterValidator is visible
  - "Edit Content" button transitions to editing state with textarea
  - "Replace File" button resets to empty state
  - "Clear" button resets to empty state
  - Editing textarea calls onContentChange on input
  - onContentChange called with file content after drop
  - initialContent starts in preview state
  - Click on drop zone opens file picker (hidden input click)
  - Drag-leave restores normal border

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/file-upload.spec.ts
  - Drop zone is visible on the upload tab
  - Uploading a valid .md file shows preview
  - User can edit uploaded content
  - User can clear and re-upload

DO NOT:
- Create MCPSyncMode or SubmitSkillPage
- Add server-side upload API calls (the upload endpoint is C.3.3)
- Handle binary files (only .md text)
- Use a drag-and-drop library (use native HTML5 drag events)
- Store files in state (only store the string content)

Acceptance Criteria:
- [ ] Drag-and-drop works with visual feedback
- [ ] File validation enforces .md extension and 500KB limit
- [ ] Content displayed and editable after upload
- [ ] State transitions (empty -> preview -> editing -> preview) work
- [ ] onContentChange fires on all content changes
- [ ] All unit tests pass (>=80% coverage)
- [ ] E2E tests pass
- [ ] Accessible: drop zone has role="button" + aria-label,
      file input is keyboard-accessible, error messages use aria-live
```

---

### Prompt C.2.3 — MCPSyncMode (URL-based introspection)

```
Create the MCP sync mode for skill submission — an advanced mode hidden under
a disclosure for importing skills from an MCP server.

CONTEXT:
- Third submission mode, under "Advanced" disclosure/accordion
- Takes an MCP server URL, introspects tools, generates SKILL.md
- Open Design Question #5 (phase6-post-migration-guide.md):
  DEFAULT: URL + list_tools only (no full protocol)
  Feature flag: SKILLHUB_MCP_FULL_INTROSPECTION (default false)
- Existing apiFetch helper: apps/web/src/lib/api.ts

WHAT TO BUILD:

1. Create apps/web/src/components/submission/MCPSyncMode.tsx:
   - Props:
     * onContentChange: (content: string) => void
   - Initially collapsed behind disclosure:
     * "<details>/<summary>" pattern with "Advanced: Import from MCP Server"
     * Chevron icon that rotates on open

   Workflow (inside disclosure):
     Step 1 — URL Input:
       * Text input for MCP server URL
       * URL validation: must be valid URL format
       * Warning chip if http:// (not https://): "Insecure connection"
       * "Introspect" button (disabled until valid URL)
       * Loading spinner during introspection

     Step 2 — Tool List:
       * Displayed after successful introspection
       * Each tool rendered as a card:
         - Tool name (bold)
         - Description
         - Input schema summary (field names + types)
       * "Select" button per tool card
       * "Back" button to return to URL input

     Step 3 — Generated Content:
       * Auto-generated SKILL.md from selected tool metadata:
         ```
         ---
         name: {tool.name}
         description: {tool.description}
         category: General
         version: 1.0.0
         author: MCP Import
         install_method: mcp
         data_sensitivity: medium
         ---

         ## {tool.name}

         {tool.description}

         ### Parameters

         {for each input_schema field: "- **{name}** ({type}): {description}"}

         ### Usage

         This skill is available via MCP server at `{url}`.
         ```
       * Editable textarea with generated content
       * FrontMatterValidator + SkillPreviewPanel
       * "Select Different Tool" button (back to step 2)

   - Error states:
     * Connection failed: "Could not connect to MCP server. Check the URL."
     * Invalid response: "Server did not return valid MCP tool data."
     * Timeout (10s): "Connection timed out. The server may be unavailable."

   - Calls onContentChange when content is generated or edited

2. New Flask blueprint: apps/api/skillhub_flask/blueprints/mcp.py
   - Blueprint name: "mcp"
   - Register in app factory

   Endpoint: POST /api/v1/mcp/introspect
     - Auth required (g.current_user must exist)
     - Request body (validated via Pydantic):
       MCPIntrospectRequest: { url: str }
     - Processing:
       * Validate URL format (use urllib.parse)
       * Attempt HTTP POST to {url} with MCP initialize + list_tools
         (simplified: just POST to the URL with a tools/list JSON-RPC request)
       * Timeout: 10 seconds (use requests library with timeout=10)
       * Parse response for tools array
     - Response: MCPIntrospectResponse:
       { tools: [{ name: str, description: str, input_schema: dict }] }
     - Error responses:
       * 422: invalid URL format
       * 502: server unreachable or timeout
       * 500: unexpected error
     - Rate limit: 5 requests per user per minute (use simple in-memory
       counter with cleanup, not Redis — keep it simple)

3. New schema: apps/fast-api/skillhub/schemas/mcp.py
   - MCPIntrospectRequest(BaseModel): url: str
   - MCPToolSummary(BaseModel): name: str, description: str, input_schema: dict
   - MCPIntrospectResponse(BaseModel): tools: list[MCPToolSummary]

TESTING — Write tests FIRST:

File: apps/web/src/components/submission/MCPSyncMode.test.tsx
  - Disclosure initially collapsed (content not visible)
  - Disclosure expands on click, shows URL input
  - URL input: empty URL disables Introspect button
  - URL input: valid URL enables Introspect button
  - URL input: http:// URL shows warning chip
  - Introspect click shows loading spinner
  - Successful introspection renders tool cards
  - Tool card shows name, description, schema summary
  - Selecting tool generates SKILL.md content
  - Generated content is editable in textarea
  - onContentChange called with generated/edited content
  - Error state: connection failed message shown
  - Error state: timeout message shown
  - "Back" button returns to URL input
  - "Select Different Tool" returns to tool list

File: apps/api/tests/test_mcp_blueprint.py (pytest)
  - POST /api/v1/mcp/introspect: 401 without auth
  - POST /api/v1/mcp/introspect: 422 for invalid URL
  - POST /api/v1/mcp/introspect: 200 with mocked MCP server response
  - POST /api/v1/mcp/introspect: 502 when server unreachable (mock timeout)
  - POST /api/v1/mcp/introspect: response contains tools array
  - Rate limiting: 6th request within 60s returns 429

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/mcp-sync.spec.ts
  - MCP Sync disclosure expands on click
  - URL input is visible after expanding
  - Introspect button is disabled for empty URL

DO NOT:
- Implement full MCP protocol (just list_tools JSON-RPC is sufficient)
- Store MCP server credentials or URLs in the database
- Create SubmitSkillPage wrapper
- Allow non-authenticated users to introspect
- Use websockets (simple HTTP POST is fine for introspection)
- Install the mcp Python SDK in the Flask app (use raw HTTP requests)

Acceptance Criteria:
- [ ] Disclosure pattern works (collapsed by default)
- [ ] URL validation with http:// warning
- [ ] Introspect flow: URL -> tool list -> generated content
- [ ] Generated SKILL.md has valid front matter
- [ ] Content is editable after generation
- [ ] Flask endpoint works with auth and rate limiting
- [ ] Error handling for all failure modes (422, 502, timeout)
- [ ] All unit tests pass (>=80% coverage)
- [ ] All Flask tests pass (>=80% coverage)
- [ ] E2E tests pass
- [ ] MCP blueprint registered in app factory
```

---

## Phase C.3 — Submission Page Assembly

> Wire everything together into a routable page, add LLM judge live hints, and the server-side upload endpoint.

---

### Prompt C.3.1 — SubmitSkillPage + ModeSelector + SubmissionStatusTracker

```
Assemble the complete skill submission page with mode selector, shared
validation/preview, and post-submit status tracking.

CONTEXT:
- All mode components built: FormBuilderMode (C.2.1), FileUploadMode (C.2.2),
  MCPSyncMode (C.2.3)
- Shared components built: FrontMatterValidator (C.1.1),
  SkillPreviewPanel (C.1.2)
- Existing router: apps/web/src/App.tsx
  Currently has: /, /browse, /search, /filtered, /skills/:slug, /admin/*
- Existing API: POST /api/v1/submissions creates submission
  Body: { name, short_desc, category, content, declared_divisions,
          division_justification }
- Existing auth: useAuth() hook returns { user, isAuthenticated }
- See Section 4 of phase6-post-migration-diagrams.md for full component hierarchy
- Architecture:
  SubmitSkillPage
    -> ModeSelector (tabs)
    -> [active mode component] -> produces { content: string }
    -> FrontMatterValidator (always visible, shared)
    -> SkillPreviewPanel (always visible, shared, split mode)
    -> SubmitButton
    -> SubmissionStatusTracker (after submission)

WHAT TO BUILD:

1. Create apps/web/src/components/submission/ModeSelector.tsx:
   - Props:
     * activeMode: 'form' | 'upload' | 'mcp'
     * onModeChange: (mode: 'form' | 'upload' | 'mcp') => void
   - Three tab buttons in a row:
     * "Form Builder" (icon: clipboard-list)
     * "File Upload" (icon: upload-cloud)
     * "MCP Sync" (icon: link, with "Advanced" sub-label in smaller text)
   - Active tab: accent bottom border + filled background
   - Inactive tabs: muted text, hover effect
   - Accessible: role="tablist", role="tab", aria-selected

2. Create apps/web/src/views/SubmitSkillPage.tsx:
   - Auth gate: if not authenticated, show message + "Sign In" button
     that opens AuthModal (do NOT redirect — the page should still render
     at /submit, just gated)
   - Page layout:
     * Top section: "Submit a New Skill" heading (h1) + subtitle
       "Share your Claude skill with the organization"
     * ModeSelector tabs
     * Main content area (2-column on desktop, stacked on mobile):
       - Left/Top: active mode component
       - Right/Bottom: SkillPreviewPanel in 'split' mode
     * Below mode area: FrontMatterValidator (compact, inline)
     * Division justification: textarea (required, min 10 chars)
       "Explain why this skill belongs to the selected divisions"
     * Submit button row:
       - "Submit for Review" button
       - Disabled when: any validation errors (from FrontMatterValidator),
         or division_justification < 10 chars, or content is empty
       - Shows spinner when submitting
   - State:
     * content: string (lifted, shared across modes)
     * mode: 'form' | 'upload' | 'mcp' (default: 'form')
     * validationIssues: ValidationIssue[]
     * divisionJustification: string
     * isSubmitting: boolean
     * submissionResult: { id: string, displayId: string } | null
   - Mode switching preserves content (content state lives in page, not modes)
   - Submit flow:
     * Extract name, short_desc, category, declared_divisions from
       parsed front matter (use parseFrontMatter from C.1.2)
     * POST /api/v1/submissions via apiFetch with assembled body
     * On 201: set submissionResult, show SubmissionStatusTracker
     * On 422: show validation errors from response
     * On error: show error banner with retry button

3. Create apps/web/src/components/submission/SubmissionStatusTracker.tsx:
   - Props:
     * submissionId: string
     * displayId: string
   - Polls GET /api/v1/submissions/{submissionId} every 5 seconds
   - Renders horizontal progress tracker with stages:
     * "Submitted" (always completed immediately)
     * "Gate 1: Structure" (completed when status != 'submitted')
     * "Gate 2: AI Review" (completed when status has gate2 prefix)
     * "Human Review" (completed when status is 'approved')
   - Current stage: pulsing dot animation
   - Completed stages: green checkmark
   - Failed stages: red X with gate findings summary
   - Below progress: status-specific messages:
     * gate1_passed: "Structure validation passed. AI review in progress..."
     * gate1_failed: "Structure validation failed." + findings list
     * gate2_passed: "AI review passed. Awaiting human review."
     * gate2_flagged: "AI review flagged items. Awaiting human review."
     * gate2_failed: "AI review failed." + findings list
     * approved: "Your skill has been approved!" + link to skill page
     * changes_requested: "Changes requested by reviewer." + notes
   - Stop polling when status is terminal (approved, rejected, gate1_failed,
     gate2_failed)
   - Cleanup: clear interval on unmount

4. Update apps/web/src/App.tsx:
   - Add route: <Route path="/submit" element={<SubmitSkillPage />} />
   - Place OUTSIDE the RequireAdmin gate (any authenticated user can access)
   - Import SubmitSkillPage (can be lazy-loaded like admin views)

5. Update apps/web/src/components/Nav.tsx:
   - Add "Submit Skill" button/link in the nav bar (visible when authenticated)
   - Uses React Router Link to /submit
   - Styled as a secondary action button (not as prominent as primary nav)

TESTING — Write tests FIRST:

File: apps/web/src/components/submission/ModeSelector.test.tsx
  - Renders three tabs with correct labels
  - Active tab has accent styling
  - Clicking tab calls onModeChange with correct mode
  - Tabs have correct ARIA attributes (role="tab", aria-selected)

File: apps/web/src/views/SubmitSkillPage.test.tsx
  - Renders heading "Submit a New Skill"
  - Shows auth gate when not authenticated
  - Shows mode selector when authenticated
  - Mode selector defaults to 'form'
  - Switching mode preserves content
  - Submit button disabled when content is empty
  - Submit button disabled when validation errors exist
  - Submit button disabled when division justification < 10 chars
  - Submit button enabled when valid content + justification present
  - Submitting calls POST /api/v1/submissions with correct payload
  - Successful submission shows SubmissionStatusTracker
  - Failed submission shows error banner

File: apps/web/src/components/submission/SubmissionStatusTracker.test.tsx
  - Renders progress stages
  - Shows "Submitted" as completed immediately
  - Polls API every 5 seconds (mock timers)
  - Updates stage indicators based on status response
  - Shows findings when gate fails
  - Stops polling on terminal status
  - Shows success message + link on approval
  - Cleanup: clearInterval on unmount

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/submit-page.spec.ts
  - /submit route loads the submission page
  - Unauthenticated user sees sign-in prompt
  - Authenticated user sees mode selector with three tabs
  - Switching between tabs works
  - Nav bar shows "Submit Skill" link when logged in
  - Submit button is disabled when form is empty

DO NOT:
- Modify existing views (HomeView, BrowseView, etc.)
- Add admin-specific submission flow (admins use the same page)
- Implement LLM judge live hints yet (next prompt C.3.2)
- Add the upload endpoint (that is C.3.3)
- Change existing API endpoints or schemas

Acceptance Criteria:
- [ ] /submit route accessible and renders full page
- [ ] Auth gate works (unauthenticated users see sign-in prompt)
- [ ] Mode selector switches between all three modes
- [ ] Content preserved when switching modes
- [ ] FrontMatterValidator + SkillPreviewPanel always visible
- [ ] Submit calls API with correct payload
- [ ] SubmissionStatusTracker shows progress and polls
- [ ] Polling stops on terminal status
- [ ] Nav.tsx has "Submit Skill" link (authenticated only)
- [ ] App.tsx route registered
- [ ] All unit tests pass (>=80% coverage)
- [ ] E2E tests pass
- [ ] Responsive: 2-column on desktop, stacked on mobile (test at 768px breakpoint)
- [ ] Entry added to docs/features/index.md
```

---

### Prompt C.3.2 — LLM Judge live hints during editing

```
Add live LLM judge feedback during skill editing — non-blocking hints
that help authors improve content quality before submission.

CONTEXT:
- SubmitSkillPage (C.3.1) is built with all modes and shared components
- Existing LLM judge service: apps/fast-api/skillhub/services/llm_judge.py
- FrontMatterValidator provides structural validation (client-side)
- LLM judge provides content quality feedback (server-side, different concern)
- Must be fully non-blocking — never freeze the editor

> NOTE: The preview-scan endpoint (POST /api/v1/submissions/preview-judge)
> accepts { content, name, category } and returns LLM suggestions
> (category recommendation, quality score, tagging hints) WITHOUT creating
> a submission row. Rate-limited. This is NOT the admin-only scan endpoint.

WHAT TO BUILD:

1. New Flask endpoint: POST /api/v1/submissions/preview-judge
   - Add to apps/api/skillhub_flask/blueprints/submissions.py
   - Auth required (g.current_user)
   - Request body schema (add to apps/fast-api/skillhub/schemas/submission.py):
     PreviewJudgeRequest:
       * content: str (required, min 50 chars)
       * name: str (optional)
       * category: str (optional)
   - Response schema:
     PreviewJudgeResponse:
       * hints: list[JudgeHint]
       * suggested_category: str | None
       * quality_score: int | None (0-100)
     JudgeHint:
       * severity: 'suggestion' | 'warning'
       * message: str
       * category: str (e.g. 'clarity', 'completeness', 'security', 'formatting')
   - Processing:
     * Call a lightweight version of the LLM judge (reuse judge service
       but with a simpler prompt focused on suggestions, not pass/fail)
     * If LLM is unavailable or feature flag 'llm_judge_enabled' is off,
       return empty hints with quality_score=None
     * Timeout: 15 seconds max. If LLM is slow, return partial results
       (whatever was generated before timeout)
   - Rate limiting:
     * Max 1 request per user per 10 seconds
     * Use in-memory dict with (user_id, timestamp) tracking
     * Return 429 Too Many Requests if exceeded
     * Include Retry-After header
   - Add "preview-judge" to PUBLIC_ENDPOINTS if needed, or just ensure
     the auth hook runs (it should since it's under /api/v1/)

2. Create apps/web/src/hooks/useJudgeHints.ts:
   - Custom hook: useJudgeHints(content: string, name?: string, category?: string)
   - Returns: { hints: JudgeHint[], suggestedCategory: string | null,
     qualityScore: number | null, isLoading: boolean }
   - Behavior:
     * Debounce: 3000ms after last content change before firing request
     * Abort: cancel previous in-flight request via AbortController
       when content changes
     * Cache: store results keyed by SHA-256-style hash of content
       (simple hash, e.g. first 16 chars of btoa(content))
       Do not re-fetch if content hash matches cached result
     * Minimum content: do not fire for content < 50 chars
     * Error handling: on any error, return empty hints — never show
       error to user for hints (they are advisory)
     * Rate limit handling: on 429, respect Retry-After and backoff

3. Integrate into SubmitSkillPage:
   - Import useJudgeHints
   - Pass current content to the hook
   - Render hints section below FrontMatterValidator:
     * Section header: "AI Suggestions" with brain icon
     * "Dismiss All" button (right-aligned)
     * Each hint as a dismissable card:
       - severity 'suggestion': light blue-gray background, lightbulb icon
       - severity 'warning': light amber background, warning icon
       - Hint message text
       - Category label (muted, right-aligned)
       - "X" dismiss button per hint
     * Loading state: subtle pulsing placeholder (not a full spinner)
     * Empty state (no hints): "Looking good! No suggestions." with green check
   - Suggested category:
     * If suggestedCategory differs from current category, show:
       "Consider category: {suggestion}" with "Apply" button that updates
       the form state
   - Quality score:
     * If available, show as a small badge: "Quality: {score}/100"
       with color coding (red <40, amber 40-70, green >70)
   - Dismissed hints are stored in component state (reset on content change)
   - Hints NEVER block the Submit button (they are advisory only)

TESTING — Write tests FIRST:

File: apps/web/src/hooks/useJudgeHints.test.tsx
  - Debounces request by 3 seconds
  - Aborts previous request when content changes
  - Caches results for same content (no re-fetch)
  - Does not fire for content < 50 chars
  - Returns empty hints on error (no throw)
  - Handles 429 gracefully (backs off)
  - Returns hints from successful response

File: apps/api/tests/test_preview_judge.py (pytest)
  - POST /api/v1/submissions/preview-judge: 401 without auth
  - POST /api/v1/submissions/preview-judge: 422 for content < 50 chars
  - POST /api/v1/submissions/preview-judge: 200 with valid content
    (mock LLM judge response)
  - POST /api/v1/submissions/preview-judge: returns hints array
  - POST /api/v1/submissions/preview-judge: returns 429 on rate limit
  - POST /api/v1/submissions/preview-judge: returns empty hints when
    LLM judge feature flag is off
  - POST /api/v1/submissions/preview-judge: handles LLM timeout gracefully

File: apps/web/src/views/SubmitSkillPage.test.tsx (add to existing)
  - Hints section renders when hints available
  - Individual hint dismissable via X button
  - "Dismiss All" clears all hints
  - Hints do NOT disable submit button
  - Suggested category shows "Apply" button
  - Quality score badge renders with correct color

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/judge-hints.spec.ts
  - AI Suggestions section appears on submission page
  - Hints are non-blocking (submit button still works)

DO NOT:
- Modify the structural FrontMatterValidator (C.1.1) — these are separate concerns
- Make hints blocking (NEVER disable submit based on hints)
- Change the LLM judge gate logic (Gate 2 is separate from preview-judge)
- Store hint results in the database
- Show errors to the user when hints fail (silent fallback)
- Use WebSockets or SSE (simple polling via debounced fetch is fine)

Acceptance Criteria:
- [ ] Flask endpoint returns hints with rate limiting
- [ ] useJudgeHints hook debounces, aborts, and caches correctly
- [ ] Hints render in SubmitSkillPage as dismissable cards
- [ ] Suggested category "Apply" button works
- [ ] Quality score badge renders
- [ ] Hints are NEVER blocking — submit button unaffected
- [ ] 429 rate limit handled gracefully (backoff, no error shown)
- [ ] LLM unavailability handled (empty hints, no error)
- [ ] All unit tests pass (>=80% coverage)
- [ ] All Flask tests pass (>=80% coverage)
- [ ] E2E tests pass
```

---

### Prompt C.3.3 — Upload endpoint and multipart submission

```
Add the server-side file upload endpoint for direct .md file submission,
and wire the FileUploadMode to optionally use it.

CONTEXT:
- FileUploadMode (C.2.2) currently reads files client-side via FileReader
- We need a server-side upload path for:
  * Files that may need server-side validation beyond client capabilities
  * Direct submission without client-side front matter parsing
- Existing: POST /api/v1/submissions (JSON body) in
  apps/api/skillhub_flask/blueprints/submissions.py
- Existing service: create_submission in
  apps/fast-api/skillhub/services/submissions.py
- parseFrontMatter logic needs a Python equivalent for server-side parsing

WHAT TO BUILD:

1. New Flask endpoint: POST /api/v1/submissions/upload
   - Add to apps/api/skillhub_flask/blueprints/submissions.py
   - Auth required (g.current_user)
   - Content-Type: multipart/form-data
   - Form fields:
     * file: uploaded .md file (required)
     * declared_divisions: JSON string of division array (required)
     * division_justification: string (required)
   - Server-side processing:
     a. Validate file presence and type:
        - No file: 422 "File is required"
        - Wrong extension: 415 "Only .md files are accepted"
        - Too large (> 500KB): 413 "File too large — maximum 500KB"
     b. Read file content as UTF-8 string
     c. Parse front matter from content:
        - Extract name, short_desc (from description), category
        - If front matter missing or incomplete: 422 with specific errors
     d. Parse declared_divisions from form field (JSON.loads)
     e. Call existing create_submission() service with extracted fields
     f. Trigger Gate 1 (reuse existing logic from create_new_submission)
     g. If Gate 1 passes and llm_judge_enabled, trigger Gate 2 in background
   - Returns: SubmissionCreateResponse (same as JSON endpoint)
   - Error responses:
     * 413 Payload Too Large (file > 500KB)
     * 415 Unsupported Media Type (not .md)
     * 422 Unprocessable Entity (missing fields, bad front matter)
     * 401 Unauthorized (no auth)

2. Create server-side front matter parser:
   - Add function parse_skill_front_matter(content: str) -> dict[str, Any]
     in apps/fast-api/skillhub/services/front_matter.py
   - Parses YAML-like front matter between --- delimiters
   - Returns dict of field -> value
   - Raises ValueError if delimiters missing
   - Handles: name, description, category, version, author,
     install_method, data_sensitivity, tags (as list), trigger_phrases (as list)
   - Simple line-by-line parsing (no PyYAML dependency needed for flat
     key:value front matter)

3. Update FileUploadMode (apps/web/src/components/submission/FileUploadMode.tsx):
   - Add "Direct Upload" button alongside existing submit flow
   - "Direct Upload" uses multipart POST to /api/v1/submissions/upload:
     * Constructs FormData with file, declared_divisions, division_justification
     * Uses fetch directly (not apiFetch, since it needs multipart)
     * Adds Authorization header manually from getToken()
   - Both paths (client-side JSON submit via SubmitSkillPage, and direct upload)
     lead to SubmissionStatusTracker
   - "Direct Upload" shows same SubmissionStatusTracker on success

TESTING — Write tests FIRST:

File: apps/fast-api/skillhub/services/test_front_matter.py (or appropriate test location)
  - parse_skill_front_matter: valid content returns all fields
  - parse_skill_front_matter: missing delimiters raises ValueError
  - parse_skill_front_matter: extracts name, description, category
  - parse_skill_front_matter: handles tags as list
  - parse_skill_front_matter: handles trigger_phrases as list
  - parse_skill_front_matter: missing field returns dict without that key

File: apps/api/tests/test_upload_endpoint.py (pytest)
  - POST /api/v1/submissions/upload: 401 without auth
  - POST /api/v1/submissions/upload: 422 when no file provided
  - POST /api/v1/submissions/upload: 415 for non-.md file
  - POST /api/v1/submissions/upload: 413 for file > 500KB
  - POST /api/v1/submissions/upload: 422 for missing front matter
  - POST /api/v1/submissions/upload: 201 with valid .md file
  - POST /api/v1/submissions/upload: creates submission via service
  - POST /api/v1/submissions/upload: Gate 1 runs on uploaded content
  - POST /api/v1/submissions/upload: response matches SubmissionCreateResponse schema
  - POST /api/v1/submissions/upload: declared_divisions parsed from JSON string

File: apps/web/src/components/submission/FileUploadMode.test.tsx (add to existing)
  - "Direct Upload" button is visible after file uploaded
  - "Direct Upload" sends multipart FormData
  - "Direct Upload" success shows SubmissionStatusTracker
  - "Direct Upload" error shows error message

Playwright E2E — File: apps/web/apps/web/e2e/tests/submission/file-upload-direct.spec.ts
  - Direct Upload button visible after uploading a file
  - Direct Upload submits the file to the server

DO NOT:
- Add multipart support to other endpoints (only this one)
- Store uploaded files on disk (content goes into Submission.content column)
- Allow binary file uploads (only .md text)
- Remove the client-side JSON submission path (both paths should work)
- Add a PyYAML dependency (use simple string parsing)
- Change the create_submission service signature

Acceptance Criteria:
- [ ] Upload endpoint accepts multipart .md files
- [ ] File validation: 413 for size, 415 for type, 422 for content
- [ ] Front matter parsed server-side correctly
- [ ] Submission created through existing pipeline (create_submission service)
- [ ] Gate 1 runs on uploaded content
- [ ] Gate 2 triggered in background when applicable
- [ ] FileUploadMode "Direct Upload" button works end-to-end
- [ ] Both submission paths (JSON + multipart) produce same result type
- [ ] All unit tests pass (>=80% coverage)
- [ ] All Flask tests pass (>=80% coverage)
- [ ] E2E tests pass
- [ ] Error codes correct: 413/415/422/401
```

---

## Admin Self-Submission Flow

> This is NOT a separate prompt. It is a design constraint that applies to C.3.1 and should be verified in tests.

```
Admin submissions follow the exact same SubmitSkillPage flow as regular users.
No special UI. The existing pipeline handles the constraint:

1. Admin submits via /submit -> creates Submission with submitted_by = admin user
2. Pipeline runs Gate 1 + Gate 2 as normal
3. Gate 3 (HITL review): self-approval is ALREADY BLOCKED in review_submission()
   service — a different admin must approve
4. In AdminQueueView, admin's own submissions appear with a visual indicator:
   - SubmissionCard (from Stage A.4.1) should show a badge
     "Your submission — another admin must review" when the current user
     is the submitter
   - This badge logic belongs in AdminQueueView integration (Stage A.4.2),
     not in this Stage C

VERIFICATION (add to C.3.1 tests):
- Test that POST /api/v1/submissions works when g.current_user is an admin
- Test that the created submission has the admin's user_id as submitted_by
- No special fields or flags needed — existing self-approval block handles it
```

---

## Quick Reference: Prompt Sequence

```
STAGE C — User Skill Submission UI/UX (8 prompts)

  C.1.1  FrontMatterValidator component + validateFrontMatter pure function
         ~30 min | React component + pure logic | No API calls

  C.1.2  SkillPreviewPanel component + parseFrontMatter helper
         ~30 min | React component + markdown rendering | Add marked + dompurify deps

  C.2.1  FormBuilderMode: 4-step guided wizard + StepIndicator
         ~45 min | React component (largest) | No API calls

  C.2.2  FileUploadMode: drag-and-drop with edit/preview states
         ~30 min | React component | No API calls (upload endpoint is C.3.3)

  C.2.3  MCPSyncMode: URL introspection + Flask blueprint
         ~45 min | React component + Flask blueprint + schema | New API endpoint

  C.3.1  SubmitSkillPage + ModeSelector + SubmissionStatusTracker + route
         ~45 min | React view + components | Wires to existing POST /api/v1/submissions

  C.3.2  LLM Judge live hints + useJudgeHints hook + preview-judge endpoint
         ~45 min | React hook + Flask endpoint | New API endpoint + rate limiting

  C.3.3  Upload endpoint (multipart) + FileUploadMode direct upload
         ~30 min | Flask endpoint + React integration | New API endpoint

TOTAL: 8 prompts, estimated 5-6 hours
```

---

## Dependency Graph

```
C.1.1 (FrontMatterValidator)
  |
  v
C.1.2 (SkillPreviewPanel) ----+
  |                            |
  +----> C.2.1 (FormBuilder)   |
  |                            |
  +----> C.2.2 (FileUpload) ---+----> C.3.1 (SubmitSkillPage)
  |                            |         |
  +----> C.2.3 (MCPSync) -----+         +----> C.3.2 (LLM Judge hints)
                                         |
                                         +----> C.3.3 (Upload endpoint)

Dependency rules:
- C.1.1 must be done before any C.1.2+ prompt
- C.1.2 must be done before any C.2.x prompt
- All C.2.x prompts can run in parallel (they are independent modes)
- All C.2.x must be done before C.3.1
- C.3.1 must be done before C.3.2 or C.3.3
- C.3.2 and C.3.3 can run in parallel
```

---

## New Files Created by This Stage

```
apps/web/src/components/submission/
  FrontMatterValidator.tsx          # C.1.1
  FrontMatterValidator.test.tsx     # C.1.1
  validateFrontMatter.ts            # C.1.1
  validateFrontMatter.test.ts       # C.1.1
  SkillPreviewPanel.tsx             # C.1.2
  SkillPreviewPanel.test.tsx        # C.1.2
  parseFrontMatter.ts               # C.1.2
  parseFrontMatter.test.ts          # C.1.2
  FormBuilderMode.tsx               # C.2.1
  FormBuilderMode.test.tsx          # C.2.1
  StepIndicator.tsx                 # C.2.1
  StepIndicator.test.tsx            # C.2.1
  FileUploadMode.tsx                # C.2.2
  FileUploadMode.test.tsx           # C.2.2
  MCPSyncMode.tsx                   # C.2.3
  MCPSyncMode.test.tsx              # C.2.3
  ModeSelector.tsx                  # C.3.1
  ModeSelector.test.tsx             # C.3.1
  SubmissionStatusTracker.tsx       # C.3.1
  SubmissionStatusTracker.test.tsx  # C.3.1

apps/web/src/views/
  SubmitSkillPage.tsx               # C.3.1
  SubmitSkillPage.test.tsx          # C.3.1

apps/web/src/hooks/
  useJudgeHints.ts                  # C.3.2
  useJudgeHints.test.tsx            # C.3.2

apps/web/apps/web/e2e/tests/submission/
  front-matter-validation.spec.ts   # C.1.1
  skill-preview.spec.ts             # C.1.2
  form-builder.spec.ts              # C.2.1
  file-upload.spec.ts               # C.2.2
  mcp-sync.spec.ts                  # C.2.3
  submit-page.spec.ts               # C.3.1
  judge-hints.spec.ts               # C.3.2
  file-upload-direct.spec.ts        # C.3.3

apps/api/skillhub_flask/blueprints/
  mcp.py                            # C.2.3 (new blueprint)

apps/fast-api/skillhub/schemas/
  mcp.py                            # C.2.3 (new schema file)

apps/fast-api/skillhub/services/
  front_matter.py                   # C.3.3 (server-side parser)

apps/api/tests/
  test_mcp_blueprint.py             # C.2.3
  test_preview_judge.py             # C.3.2
  test_upload_endpoint.py           # C.3.3
```

---

## New API Endpoints Added by This Stage

| Method | Path | Auth | Prompt | Description |
|--------|------|------|--------|-------------|
| POST | /api/v1/mcp/introspect | auth required | C.2.3 | Introspect an MCP server URL for tools |
| POST | /api/v1/submissions/preview-judge | auth required | C.3.2 | LLM judge live hints (non-blocking, rate-limited) |
| POST | /api/v1/submissions/upload | auth required | C.3.3 | Multipart .md file upload submission |

---

## Modified Files by This Stage

```
apps/web/src/App.tsx                 # C.3.1 — add /submit route
apps/web/src/components/Nav.tsx      # C.3.1 — add "Submit Skill" link
apps/web/src/components/submission/
  FileUploadMode.tsx                 # C.3.3 — add "Direct Upload" button
apps/api/skillhub_flask/blueprints/
  submissions.py                     # C.3.2 — add preview-judge endpoint
                                     # C.3.3 — add upload endpoint
apps/api/skillhub_flask/__init__.py  # C.2.3 — register mcp blueprint
  (or app factory file)
apps/fast-api/skillhub/schemas/
  submission.py                      # C.3.2 — add PreviewJudge schemas
libs/shared-types/src/index.ts       # If new shared types needed
docs/features/index.md               # C.1.1, C.1.2, C.2.1, C.3.1 — feature entries
package.json / package-lock.json     # C.1.2 — marked + dompurify + highlight.js deps
```
