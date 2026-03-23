# Feature Demo Recorder — Design Spec

**Date:** 2026-03-23
**Status:** Approved

## Overview

A Claude Code skill that records browser-based feature demos as GIFs and optionally documents them in a central features index. Triggered via natural language prompts describing the feature to demo.

## Trigger Patterns

- **"Demo \<feature\>"** — Record GIF only, save to `docs/features/assets/<feature-slug>.gif`
- **"Demo and Document \<feature\>"** — Record GIF + create/update entry in `docs/features/index.md`

## Workflow

1. **Parse prompt** — Extract feature name, determine mode (demo-only vs demo+document)
2. **Ensure seed data** — Check if DB is seeded, run `mise run db:seed` if not
3. **Launch Playwright** — Open browser at `http://localhost:5173` with video recording enabled (1920px viewport, 24fps)
4. **AI-driven navigation** — Claude uses Playwright MCP tools to navigate the UI based on the feature description. No scripted recipes — Claude interprets the feature and performs the appropriate interactions.
5. **Stop recording** — End Playwright video capture, producing a `.webm` file
6. **Convert to GIF** — Use ffmpeg two-pass palette method: `fps=24, scale=1920:-1, lanczos, palettegen stats_mode=full, paletteuse dither=floyd_steinberg`
7. **Save GIF** — Write to `docs/features/assets/<feature-slug>.gif`
8. **Update index (Document mode only):**
   - Read existing `docs/features/index.md` (or create if missing)
   - If feature section exists, update the GIF and description
   - If feature section doesn't exist, append new section
   - Regenerate ToC at top of file

## Output Format

### docs/features/index.md

```markdown
# Features

- [Feature Name](#feature-name)
- [Feature 2](#feature-2)

# Feature Name
Description of what this feature does.
![Feature Name](assets/feature-name.gif)

# Feature 2
Description of feature 2.
![Feature 2](assets/feature-2.gif)
```

### File Structure

```
docs/features/
  index.md              # Central feature index with ToC
  assets/
    browse-skills.gif
    install-skill.gif
    admin-analytics.gif
    ...
```

## Technical Details

### Dependencies
- **Playwright MCP tools** — Already available in the environment for browser control
- **ffmpeg** — Already installed at `/opt/homebrew/bin/ffmpeg`

### Auth
- No authentication required — stub accounts work without login
- Seed data ensured before recording via `mise run db:seed`

### GIF Settings
- Resolution: 1920px wide (height auto-scaled to maintain aspect ratio)
- Framerate: 24fps
- Palette: Two-pass with `stats_mode=full` for optimal 256-color selection
- Dithering: Floyd-Steinberg

### Slug Generation
Feature name converted to kebab-case slug for filenames:
- "Browse Skills" → `browse-skills`
- "Admin Analytics Panel" → `admin-analytics-panel`

### Dev Server
- Web app must be running at `http://localhost:5173`
- API must be running at `http://localhost:8000`

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Recording approach | AI-driven | Adapts to UI changes, no script maintenance |
| Capture method | Playwright video recording | Native, smooth, reliable |
| Output format | Single flat index + assets dir | Simple, scannable |
| GIF quality | 1920px/24fps | High quality, acceptable size for short clips |
| Auth | None needed | Stub accounts from seed data |
