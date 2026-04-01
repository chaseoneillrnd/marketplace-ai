---
name: feature-demo-recorder
description: Record browser-based feature demos as GIFs via Playwright and optionally document them in docs/features/index.md. Trigger with "Demo <feature>" or "Demo and Document <feature>".
---

# Feature Demo Recorder

Record a browser-based feature demo as a GIF using Playwright MCP screenshot capture + ffmpeg stitching, and optionally document the feature in `docs/features/index.md`.

## Step 1: Parse the Prompt

- Extract the feature name from the user's message (everything after "Demo" or "Demo and Document").
- Determine mode:
  - If the message contains "Document" (case-insensitive) → **demo+document mode**.
  - Otherwise → **demo-only mode**.
- Generate a kebab-case slug from the feature name. Example: "Admin Analytics Panel" → `admin-analytics-panel`.

## Step 2: Check Prerequisites

Run these checks before proceeding. Stop and inform the user if any fail.

1. **Web dev server running:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
   ```
   Must return `200`. If not, tell the user to run `mise run dev:web`.

2. **API server running:**
   ```bash
   curl -s -o /dev/null -w "%{http_code}" http://localhost:8000
   ```
   Must return `200` (or `404` for root — any non-error is fine). If not, tell the user to run `mise run dev:api`.

3. **Directories exist:**
   ```bash
   mkdir -p docs/features/assets
   mkdir -p /tmp/demo-frames-<slug>
   ```

4. **ImageMagick available:**
   ```bash
   which magick
   ```
   If not found, tell the user to install it (`brew install imagemagick`).

5. **Database is seeded:**
   ```bash
   curl -s http://localhost:8000/api/v1/skills | head -c 100
   ```
   If the response is empty or an empty array `[]`, run `mise run db:seed` and verify again.

## Step 3: Record the Feature Demo via Screenshots

Use the **Playwright MCP tools** (`mcp__plugin_playwright_playwright__*`) to drive the browser. Capture frames by taking screenshots at each meaningful moment.

### Setup

1. **Set viewport size** — Use `browser_resize` to set the viewport to **1440x900**.
2. **Navigate** — Use `browser_navigate` to open `http://localhost:5173`.

### Frame capture pattern

For every meaningful state change during the demo, take a screenshot saved directly to the temp frames directory:

```
browser_take_screenshot → filename: "/tmp/demo-frames-<slug>/frame-001.png"
browser_take_screenshot → filename: "/tmp/demo-frames-<slug>/frame-002.png"
...
```

Use sequential zero-padded filenames (`frame-001.png`, `frame-002.png`, etc.) so ffmpeg can glob them in order.

### Demo interactions

Think carefully about which interactions best showcase the feature:
- Click through relevant UI elements using `browser_click`.
- Fill forms with realistic sample data using `browser_fill_form`.
- Scroll to reveal content as needed.
- Use `browser_snapshot` to read the accessibility tree when you need to find element references.
- Use `browser_wait_for` with 1-2 second pauses between actions for readability.

### Frame capture guidelines

- **Take a screenshot BEFORE and AFTER every meaningful action** (click, type, navigate).
- **Take 2-3 duplicate frames** for states you want the viewer to linger on (e.g., the initial page load, final result). This makes the GIF pause on important states since each frame gets equal duration.
- **Aim for 15-30 total frames.** Fewer than 10 feels too fast; more than 40 produces oversized GIFs.
- **Capture the full happy path** from start to finish.

## Step 4: Stitch Screenshots into GIF

Convert the captured frames into an animated GIF using **ImageMagick** (`magick`). Do NOT use ffmpeg for GIF stitching — its GIF encoder aggressively deduplicates frames and drops content.

### Prerequisites

```bash
which magick
```
If not found, tell the user to install it (`brew install imagemagick`).

### Initial conversion with custom delays

Use `-delay` (in centiseconds) before frame groups to control pacing:
- **150** (1.5s) for transition frames
- **200** (2s) for "linger" frames (important states like search results, filtered views, final state)

```bash
magick -delay 150 /tmp/demo-frames-<slug>/frame-*.png \
  -loop 0 -layers Optimize \
  docs/features/assets/<slug>.gif
```

For more control, specify delays per frame group:

```bash
magick \
  -delay 200 /tmp/demo-frames-<slug>/frame-001.png /tmp/demo-frames-<slug>/frame-002.png \
  -delay 150 /tmp/demo-frames-<slug>/frame-003.png \
  -delay 200 /tmp/demo-frames-<slug>/frame-004.png /tmp/demo-frames-<slug>/frame-005.png \
  ... \
  -loop 0 -layers Optimize \
  docs/features/assets/<slug>.gif
```

### 50MB Hard Limit — Step-Down Fallback

After conversion, check the file size:

```bash
stat -f%z docs/features/assets/<slug>.gif
```

If the file exceeds **50MB** (52428800 bytes), resize:

1. **First retry:** 1024px wide
   ```bash
   magick -delay 150 /tmp/demo-frames-<slug>/frame-*.png \
     -resize 1024x -loop 0 -layers Optimize \
     docs/features/assets/<slug>.gif
   ```

2. **Second retry:** 800px wide
   ```bash
   magick -delay 150 /tmp/demo-frames-<slug>/frame-*.png \
     -resize 800x -loop 0 -layers Optimize \
     docs/features/assets/<slug>.gif
   ```

3. **Still over 50MB:** Warn the user that the demo has too many frames. Suggest reducing the frame count.

### Cleanup temp frames

```bash
rm -rf /tmp/demo-frames-<slug>
```

## Step 5: Update Index (Document Mode Only)

Skip this step entirely if running in demo-only mode.

### Read or create the index file

Read `docs/features/index.md`. If it does not exist, create it with this template:

```markdown
# Features

> Demos of SkillHub features. Generated by the `feature-demo-recorder` skill.
```

### Add or update the feature entry

- If a section with a heading matching the feature name already exists, update its description and GIF reference in place.
- If the feature is new, append a new section at the end of the file:

```markdown
## Feature Name

2-3 sentence description of what the feature does, written based on what was observed during the demo.

![Feature Name](assets/<slug>.gif)
```

### Regenerate the Table of Contents

At the top of the file (after the title and blockquote), regenerate a table of contents as a list of markdown links to each feature heading:

```markdown
- [Feature Name](#feature-name)
- [Another Feature](#another-feature)
```

## Completion

Report to the user:
- The GIF path: `docs/features/assets/<slug>.gif`
- The final file size
- If in document mode: confirm that `docs/features/index.md` was updated
- If any quality step-downs were applied, note the final resolution used
