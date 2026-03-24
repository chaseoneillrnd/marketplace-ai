# Phase 6 Stage B — User Documentation via VitePress: Technical Implementation Guide

## For Claude Code — Complete Handoff Document

**Project:** SkillHub User Documentation Portal (VitePress)
**Starting Point:** Phase 6 Stage A complete. Flask app at `apps/api` with HITL queue enhancements. NX monorepo with `apps/web`, `apps/api`, `apps/mcp-server`.
**Approach:** TDD-first, VitePress documentation app in `apps/docs/`

---

## Supplementary Materials

```
+-----------------------------------------------------------------------------+
| COMPANION DOCUMENT                                                          |
+-----------------------------------------------------------------------------+
|                                                                             |
|  phase6-post-migration-diagrams.md                                          |
|                                                                             |
|  Visual architecture companion — reference Section 3 for:                   |
|  - VitePress architecture overview                                          |
|  - Nginx configuration layout                                               |
|  - Docker multi-stage build                                                 |
|  - Documentation site map                                                   |
|                                                                             |
|  USAGE: Reference by section when executing prompts.                        |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

## Table of Contents

1. [Global Standards](#global-standards)
2. [Phase B.1 — VitePress Scaffold](#phase-b1--vitepress-scaffold)
   - [B.1.1 — Initialize VitePress app in NX monorepo](#prompt-b11--initialize-vitepress-app-in-nx-monorepo)
3. [Phase B.2 — Documentation Content](#phase-b2--documentation-content)
   - [B.2.1 — Getting Started + Introduction to Skills](#prompt-b21--getting-started--introduction-to-skills)
   - [B.2.2 — Discovery, Social Features, and Advanced Usage](#prompt-b22--discovery-social-features-and-advanced-usage)
   - [B.2.3 — Submission Guide, FAQ, Feature Requests, and Resources](#prompt-b23--submission-guide-faq-feature-requests-and-resources)
4. [Phase B.3 — Integration and Finalization](#phase-b3--integration-and-finalization)
   - [B.3.1 — Feature index entry and final validation](#prompt-b31--feature-index-entry-and-final-validation)
5. [Quick Reference: Prompt Sequence](#quick-reference-prompt-sequence)

---

## Global Standards

Apply to every prompt. Non-negotiable.

```yaml
Code Quality:
  - TypeScript: eslint, prettier, tsc --noEmit clean
  - Markdown: frontmatter on every page, single H1, valid internal links
  - No commented-out code committed
  - No console.log() in production paths — use structured logging

Testing:
  - TDD: write tests FIRST, then implementation
  - VitePress build must exit 0 (docs compile without errors)
  - All internal links must resolve (no dead links)
  - TypeScript coverage gate: >=80% (vitest --coverage) for any .ts config files

Security:
  - No secrets in documentation examples — use placeholders
  - No real internal URLs — use placeholder domains
  - No real API keys in code snippets

Existing Patterns:
  - NX projects live in apps/ or libs/
  - NX project config: project.json per app
  - Root package.json workspaces: ["apps/*", "libs/*"]
  - Mise tasks defined in mise.toml at project root
  - React components live in apps/web/src/components/
  - Color tokens: match the React app palette (dark theme, blue-purple-green gradients)

Definition of Done (every prompt):
  - [ ] Tests written first and passing
  - [ ] No type errors (tsc)
  - [ ] No lint warnings (eslint)
  - [ ] VitePress build succeeds (npx vitepress build apps/docs)
  - [ ] Acceptance criteria verified
  - [ ] No secrets in committed code
  - [ ] Existing tests still pass (no regressions)
```

### File Locations

```
New files (this stage):
  - VitePress app:           apps/docs/
  - VitePress config:        apps/docs/.vitepress/config.ts
  - VitePress theme:         apps/docs/.vitepress/theme/
  - Documentation pages:     apps/docs/src/
  - NX project config:       apps/docs/project.json
  - Package manifest:        apps/docs/package.json
  - Public assets:           apps/docs/public/

Existing files modified:
  - NX config:               nx.json (no change needed — auto-detected via project.json)
  - Mise tasks:              mise.toml
  - Feature index:           docs/features/index.md
```

---

## Phase B.1 — VitePress Scaffold

> See Section 3 of phase6-post-migration-diagrams.md for VitePress architecture diagram.

**Goal:** Create a fully functional VitePress documentation app at `apps/docs/`, integrated into the NX monorepo with mise tasks, building and serving successfully.

**Time estimate:** 30-45 minutes

---

### Prompt B.1.1 — Initialize VitePress app in NX monorepo

```
Create a new VitePress documentation app at apps/docs/ in the NX monorepo.

CONTEXT:
- NX monorepo at /Users/chase/wk/marketplace-ai
- Existing apps: apps/web (React+Vite), apps/api (Flask), apps/mcp-server (Python MCP)
- Root package.json has workspaces: ["apps/*", "libs/*"] — apps/docs is auto-included
- nx.json uses project.json detection — no manual registration needed
- VitePress will be served at /docs via nginx location block (Docker setup is out of scope)
- See Section 3 of phase6-post-migration-diagrams.md for architecture overview

Requirements:

1. Create apps/docs/package.json:
   - name: "@skillhub/docs"
   - version: "1.0.0"
   - private: true
   - scripts:
     * dev: "vitepress dev src --port 5174"
     * build: "vitepress build src"
     * preview: "vitepress preview src --port 5174"
   - dependencies:
     * vitepress: "^1.5.0"
   - devDependencies:
     * vue: "^3.5.0" (peer dependency for VitePress)

2. Create apps/docs/.vitepress/config.ts:
   - Import defineConfig from 'vitepress'
   - base: '/docs/'
   - title: 'SkillHub Docs'
   - description: 'User documentation for the SkillHub AI Skills Marketplace'
   - head: favicon link to /docs/logo.svg
   - themeConfig:
     * logo: '/logo.svg'
     * nav: [
         { text: 'Home', link: '/' },
         { text: 'Getting Started', link: '/getting-started' },
         { text: 'Back to SkillHub', link: 'https://skillhub.internal/' }
       ]
     * sidebar: [
         {
           text: 'Getting Started',
           items: [
             { text: 'Getting Started', link: '/getting-started' },
             { text: 'Introduction to Skills', link: '/introduction-to-skills' }
           ]
         },
         {
           text: 'Using Skills',
           items: [
             { text: 'Uses for Skills', link: '/uses-for-skills' },
             { text: 'Skill Discovery', link: '/skill-discovery' },
             { text: 'Social Features', link: '/social-features' },
             { text: 'Advanced Usage', link: '/advanced-usage' }
           ]
         },
         {
           text: 'Contributing',
           items: [
             { text: 'Submitting a Skill', link: '/submitting-a-skill' },
             { text: 'Feature Requests', link: '/feature-requests' }
           ]
         },
         {
           text: 'Reference',
           items: [
             { text: 'FAQ', link: '/faq' },
             { text: 'Resources', link: '/resources' }
           ]
         }
       ]
     * socialLinks: [
         { icon: 'github', link: 'https://gitlab.internal/skillhub' }
       ]
     * footer:
         message: 'Internal documentation for SkillHub'
         copyright: 'SkillHub Team'
     * search: { provider: 'local' }

3. Create apps/docs/.vitepress/theme/index.ts:
   - Import default theme from 'vitepress/theme'
   - Import './custom.css'
   - Export default theme (extend later as needed)

4. Create apps/docs/.vitepress/theme/custom.css:
   - Override VitePress CSS variables to match SkillHub dark theme:
     * --vp-c-brand-1: #6366f1 (indigo — primary brand)
     * --vp-c-brand-2: #818cf8 (indigo lighter)
     * --vp-c-brand-3: #4f46e5 (indigo darker)
     * --vp-c-brand-soft: rgba(99, 102, 241, 0.14)
     * --vp-home-hero-name-color: transparent (with gradient background)
     * --vp-home-hero-name-background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #10b981 100%)
     * --vp-home-hero-image-background-image: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #10b981 100%)
     * --vp-home-hero-image-filter: blur(40px) saturate(150%)
   - Add dark mode overrides in .dark selector
   - Set default color scheme to dark: html.dark as default

5. Create apps/docs/src/index.md (landing page):
   ---
   layout: home
   hero:
     name: "SkillHub"
     text: "AI Skills Marketplace"
     tagline: "Discover, share, and install AI skills across your organization"
     image:
       src: /logo.svg
       alt: SkillHub
     actions:
       - theme: brand
         text: Get Started
         link: /getting-started
       - theme: alt
         text: Browse Skills
         link: https://skillhub.internal/
       - theme: alt
         text: Submit a Skill
         link: /submitting-a-skill
   features:
     - icon: "🔍"
       title: Discover Skills
       details: Browse and search skills by category, division, tags, and popularity.
       link: /skill-discovery
     - icon: "⚡"
       title: One-Click Install
       details: Install skills directly via Claude Code CLI, Cline, or MCP server.
       link: /getting-started
     - icon: "📝"
       title: Submit Your Own
       details: Share your AI skills with the organization through a guided submission process.
       link: /submitting-a-skill
     - icon: "⭐"
       title: Rate and Review
       details: Help the community by rating skills and leaving reviews.
       link: /social-features
   ---

6. Create apps/docs/src/public/logo.svg:
   - Simple placeholder SVG: a rounded square with "SH" text
   - Colors: indigo (#6366f1) background, white text
   - Size: 128x128 viewBox

7. Create apps/docs/project.json (NX project config):
   {
     "name": "docs",
     "projectType": "application",
     "sourceRoot": "apps/docs/src",
     "targets": {
       "dev": {
         "command": "npx vitepress dev src --port 5174",
         "options": { "cwd": "apps/docs" }
       },
       "build": {
         "command": "npx vitepress build src",
         "options": { "cwd": "apps/docs" }
       },
       "preview": {
         "command": "npx vitepress preview src --port 5174",
         "options": { "cwd": "apps/docs" }
       }
     }
   }

8. Add mise tasks to mise.toml (in the Docs section):
   [tasks."dev:docs"]
   description = "Start docs dev server"
   run = "npx nx run docs:dev"

   [tasks."build:docs"]
   description = "Build documentation site"
   run = "npx nx run docs:build"

9. Create stub markdown pages (empty content, frontmatter only) for all 10 pages
   so the sidebar links do not break during build:
   - apps/docs/src/getting-started.md
   - apps/docs/src/introduction-to-skills.md
   - apps/docs/src/uses-for-skills.md
   - apps/docs/src/skill-discovery.md
   - apps/docs/src/social-features.md
   - apps/docs/src/advanced-usage.md
   - apps/docs/src/submitting-a-skill.md
   - apps/docs/src/feature-requests.md
   - apps/docs/src/faq.md
   - apps/docs/src/resources.md

   Each stub should have:
   ---
   title: <Page Title>
   description: <One-line description>
   ---
   # <Page Title>
   Content coming soon.

Write tests FIRST:
1. VitePress build test (shell test or vitest):
   - Run "npx vitepress build src" from apps/docs/ and assert exit code 0
   - Assert .vitepress/dist/ directory exists after build
   - Assert .vitepress/dist/index.html exists
2. NX integration test:
   - Run "npx nx show projects" and assert "docs" is listed
3. Config validation test (can be a simple Node.js script or vitest):
   - Import config.ts and assert base === '/docs/'
   - Assert sidebar has 4 groups
   - Assert sidebar total items count === 10
4. Stub page validation:
   - Assert all 10 stub .md files exist in apps/docs/src/
   - Assert each has frontmatter with title field

Do NOT:
- Write full documentation content yet (stubs only in this prompt)
- Configure nginx or Docker (out of scope for this guide)
- Add Algolia or external search
- Install VitePress globally — use workspace dependency

Acceptance Criteria:
- [ ] apps/docs/ exists with the complete directory structure
- [ ] npm install from root succeeds (workspace resolution)
- [ ] npx nx run docs:dev starts dev server on port 5174
- [ ] npx nx run docs:build produces .vitepress/dist/ output with index.html
- [ ] VitePress config has base: '/docs/'
- [ ] "Back to SkillHub" link in nav
- [ ] Sidebar has 4 groups with 10 total page entries
- [ ] Local search enabled
- [ ] Custom theme CSS applied with SkillHub brand colors
- [ ] Landing page renders hero + 4 feature cards
- [ ] All 10 stub pages exist and build without errors
- [ ] mise run dev:docs works
- [ ] mise run build:docs works
- [ ] All tests pass
```

---

## Phase B.2 — Documentation Content

**Goal:** Write comprehensive user-facing documentation across 10 pages covering getting started, skill usage, discovery, social features, submission, and reference material.

---

### Prompt B.2.1 — Getting Started + Introduction to Skills

**Time estimate:** 30-45 minutes

```
Write the first two documentation pages: Getting Started and Introduction to Skills.
Replace the stubs created in B.1.1 with full content.

CONTEXT:
- VitePress app at apps/docs/ (from Prompt B.1.1)
- Sidebar already configured for these pages
- Target audience: end users of SkillHub — NOT developers
- SkillHub is an internal AI skills marketplace
- Skills are installed into Claude Code, Cline, or via MCP server
- The API base URL is https://skillhub.internal/api/v1
- Key API endpoints for user reference:
  * GET /api/v1/skills — list/search skills
  * GET /api/v1/skills/{slug} — skill detail
  * GET /api/v1/skills/{slug}/install — get install instructions
  * POST /api/v1/submissions — submit a new skill
  * GET /api/v1/categories — list categories

Requirements:

1. Replace apps/docs/src/getting-started.md with full content:

   Frontmatter:
   ---
   title: Getting Started
   description: Install your first AI skill from SkillHub in under 5 minutes.
   ---

   Sections:
   a) "Welcome to SkillHub" — brief intro (2-3 paragraphs)
      - What SkillHub is
      - What you can do with it
      - Screenshot placeholder: ![SkillHub Homepage](./assets/screenshots/homepage.png)

   b) "Prerequisites" — what you need before starting
      - An org SSO account
      - One of: Claude Code CLI, Cline VS Code extension, or MCP-compatible client

   c) "Installation Methods" — use VitePress code-group tabs for each method:

      ::: code-group
      ```bash [Claude Code CLI]
      # Install a skill by slug
      claude skill install <skill-slug>

      # Or install by URL
      claude skill install https://skillhub.internal/api/v1/skills/<slug>/install
      ```

      ```text [Cline Extension]
      1. Open VS Code
      2. Open Command Palette (Cmd+Shift+P)
      3. Type "Cline: Install Skill"
      4. Paste the skill URL from SkillHub
      5. Click Install
      ```

      ```json [MCP Server]
      // Add to your MCP client configuration:
      {
        "mcpServers": {
          "skillhub": {
            "url": "https://skillhub.internal/mcp",
            "transport": "sse"
          }
        }
      }
      ```

      ```text [Manual Install]
      1. Navigate to the skill page on SkillHub
      2. Click "Download SKILL.md"
      3. Place the file in your project's .claude/skills/ directory
      4. Restart your Claude Code session
      ```
      :::

   d) "Your First Skill" — step-by-step walkthrough
      - Step 1: Browse to SkillHub
      - Step 2: Search for a skill (e.g., "code-review")
      - Step 3: Click "Install" and choose your method
      - Step 4: Verify installation
      - Step 5: Use the skill
      - Screenshot placeholder: ![Install Flow](./assets/screenshots/install-flow.png)

   e) "What's Next" — links to other pages:
      - Introduction to Skills — understand how skills work
      - Skill Discovery — find the right skill
      - Submitting a Skill — share your own

2. Replace apps/docs/src/introduction-to-skills.md with full content:

   Frontmatter:
   ---
   title: Introduction to Skills
   description: Learn what AI skills are, how they work, and how they extend your AI assistant.
   ---

   Sections:
   a) "What is an AI Skill?" — non-technical explanation
      - A skill is a reusable instruction set that teaches your AI assistant new capabilities
      - Analogy: skills are like browser extensions for your AI
      - Skills are written in Markdown with structured front matter

   b) "How Skills Work"
      - When a skill is installed, it becomes available in your AI context window
      - The AI reads the skill instructions and follows them when relevant
      - Skills can be triggered explicitly or matched automatically
      - Diagram placeholder: ![Skill Architecture](./assets/diagrams/skill-flow.png)

   c) "Anatomy of a Skill" — explain the structure:
      Use a VitePress custom container:

      ::: details Example Skill File (SKILL.md)
      ```yaml
      ---
      name: Code Review Assistant
      description: Performs thorough code reviews with security focus
      version: 1.2.0
      category: coding
      author: jsmith
      install_method: claude-code
      data_sensitivity: low
      tags: [code-review, security, best-practices]
      trigger_phrases:
        - "review this code"
        - "check for issues"
      ---
      ```
      :::

      Explain each field:
      - name / description — identity
      - version — semver, updated on changes
      - category — one of: coding, analysis, documentation, automation, communication, other
      - install_method — how the skill is delivered
      - data_sensitivity — low / medium / high / phi
      - tags — for search and discovery
      - trigger_phrases — what activates the skill

   d) "Skill Types" — organized by category:

      | Category        | Description                         | Example Skills                     |
      |----------------|-------------------------------------|-------------------------------------|
      | Coding          | Code generation, review, refactoring | Code Review, Test Writer           |
      | Analysis        | Data analysis, reporting             | CSV Analyzer, Metrics Dashboard    |
      | Documentation   | Docs generation, formatting          | API Doc Generator, Changelog Writer|
      | Automation       | Workflow automation, scripting       | PR Template, Deploy Checklist      |
      | Communication   | Email, presentations, summaries      | Email Drafter, Meeting Notes       |

   e) "The Context Window"
      - Skills work within the AI context window
      - More skills = less room for conversation context
      - Recommendation: install 3-5 skills at a time
      - How to manage active skills

   f) "Common Workflows"
      - Code review workflow
      - Documentation workflow
      - Analysis workflow
      - Each with 3-4 step description

3. Create placeholder directories and files for screenshot/diagram references:
   - apps/docs/src/assets/screenshots/.gitkeep
   - apps/docs/src/assets/diagrams/.gitkeep
   - apps/docs/src/assets/screenshots/homepage.png (placeholder: 800x450 gray image
     with "Homepage Screenshot" text — or just create the directory and add a note
     in the markdown that screenshots are TODO)

   ALTERNATIVE (preferred): Use VitePress tip containers instead of broken image refs:
   ::: tip Screenshot
   [Homepage screenshot will be added after UI is finalized]
   :::

Write tests FIRST:
1. Both .md files have frontmatter with title and description fields
2. VitePress build succeeds with the new content (exit code 0)
3. Each page has exactly one H1 heading
4. No broken internal links between pages (all link targets exist)
5. getting-started.md contains a code-group block
6. introduction-to-skills.md contains a details block
7. introduction-to-skills.md contains a table

Do NOT:
- Add custom Vue components
- Write pages not in this prompt's scope
- Include real API keys or internal hostnames (use skillhub.internal placeholder)
- Modify .vitepress/config.ts

Acceptance Criteria:
- [ ] apps/docs/src/getting-started.md has full content (not a stub)
- [ ] apps/docs/src/introduction-to-skills.md has full content (not a stub)
- [ ] Both files have correct frontmatter (title, description)
- [ ] getting-started.md covers 4 installation methods in code-group tabs
- [ ] introduction-to-skills.md covers skill anatomy, types table, context window
- [ ] Internal links between pages resolve
- [ ] VitePress build succeeds
- [ ] Content is user-focused (not developer/API documentation)
- [ ] All tests pass
```

---

### Prompt B.2.2 — Discovery, Social Features, and Advanced Usage

**Time estimate:** 30-45 minutes

```
Write the second batch of documentation pages: Uses for Skills, Skill Discovery,
Social Features, and Advanced Usage. Replace the stubs from B.1.1.

CONTEXT:
- VitePress app at apps/docs/
- Existing completed pages: getting-started.md, introduction-to-skills.md
- Target audience: end users (not developers)
- SkillHub API endpoints relevant to this batch:
  * GET /api/v1/skills?category=coding&sort=popular — filtered search
  * GET /api/v1/skills?q=search-term — text search
  * GET /api/v1/skills?division=engineering — division filter
  * GET /api/v1/skills?tags=python,automation — tag filter
  * POST /api/v1/skills/{slug}/reviews — submit a review
  * GET /api/v1/skills/{slug}/reviews — list reviews
  * POST /api/v1/skills/{slug}/favorite — toggle favorite
  * POST /api/v1/feedback — submit feature request feedback

Requirements:

1. Replace apps/docs/src/uses-for-skills.md:

   Frontmatter:
   ---
   title: Uses for Skills
   description: Explore real-world use cases for AI skills across roles and workflows.
   ---

   Sections:
   a) "Skills for Every Role" — organized by persona:

      ::: tip For Developers
      - **Code Review Assistant** — automated review with security and style checks
      - **Test Writer** — generates unit tests from function signatures
      - **Refactoring Guide** — suggests and applies refactoring patterns
      - **Git Commit Crafter** — writes conventional commit messages
      :::

      ::: tip For Product Managers
      - **PRD Generator** — creates product requirement documents from notes
      - **User Story Writer** — converts requirements into user stories
      - **Competitive Analysis** — structures competitive research
      :::

      ::: tip For Analysts
      - **CSV Analyzer** — explores and visualizes CSV data
      - **SQL Query Builder** — generates SQL from natural language
      - **Metrics Dashboard** — creates dashboard definitions from KPIs
      :::

      ::: tip For Everyone
      - **Email Drafter** — composes professional emails from bullet points
      - **Meeting Notes** — summarizes meeting transcripts
      - **Presentation Builder** — creates slide outlines from topics
      - **Mermaid Chart Generator** — creates diagrams from descriptions
      :::

   b) "Most Popular Skills" — list top 10 (fictional but realistic examples):
      Use a numbered list with category badges

   c) "Choosing the Right Skill"
      - Match skill category to your task
      - Check data sensitivity level
      - Read reviews and ratings
      - Try before committing: use preview mode

   d) "Combining Skills"
      - Brief intro to using multiple skills together
      - Link to Advanced Usage page for details

2. Replace apps/docs/src/skill-discovery.md:

   Frontmatter:
   ---
   title: Skill Discovery
   description: Find the perfect skill using search, filters, tags, and categories.
   ---

   Sections:
   a) "Browsing the Catalog"
      - Category-based browsing
      - Screenshot placeholder (use tip container)
      - Featured skills section on homepage

   b) "Search and Filters"
      - Text search: searches name, description, tags
      - Category filter: coding, analysis, documentation, automation, communication
      - Division filter: see skills shared with your division
      - Tag filter: narrow results with specific tags
      - Sort options: popular, recent, highest-rated, most-installed

      Example search URLs (informational, not clickable):
      ::: code-group
      ```text [By Category]
      skillhub.internal/skills?category=coding
      ```
      ```text [By Search Term]
      skillhub.internal/skills?q=code+review
      ```
      ```text [By Division]
      skillhub.internal/skills?division=engineering
      ```
      :::

   c) "Division-Based Visibility"
      - Skills can be shared with specific divisions or all-org
      - Your division filter shows skills available to you
      - Cross-division skills: approved for multiple teams
      - How division tagging works during submission

   d) "Featured and Trending"
      - How skills get featured (staff picks, high ratings)
      - Trending algorithm: installs + reviews in last 30 days
      - New arrivals section

   e) "Sorting Options"
      - Popular: most installs all-time
      - Recent: newest published first
      - Highest Rated: average rating descending
      - Most Installed: install count descending

3. Replace apps/docs/src/social-features.md:

   Frontmatter:
   ---
   title: Social Features
   description: Rate, review, and engage with the SkillHub community.
   ---

   Sections:
   a) "Reviews and Ratings"
      - Star rating system (1-5 stars)
      - Written reviews
      - How to leave a review
      - Review guidelines: be constructive, specific, honest
      - Screenshot placeholder

   b) "Comments and Discussions"
      - Commenting on skill pages
      - Asking questions to skill authors
      - Reporting issues with a skill
      - Community guidelines

   c) "Favorites and Collections"
      - Adding skills to favorites
      - Organizing favorites (planned feature)
      - Quick access from your profile

   d) "Following Skill Authors"
      - Getting notified when authors publish new skills
      - Author profiles and their skill catalog

   e) "Community Guidelines"
      Use a VitePress warning container:
      ::: warning Community Guidelines
      - Be respectful and constructive in reviews
      - Report security issues via the dedicated channel, not in reviews
      - Do not share sensitive data in comments
      - Skill authors: respond to feedback professionally
      :::

4. Replace apps/docs/src/advanced-usage.md:

   Frontmatter:
   ---
   title: Advanced Usage
   description: Skill chaining, MCP integration, custom triggers, and power-user tips.
   ---

   Sections:
   a) "Skill Chaining and Composition"
      - Running multiple skills in sequence
      - Example workflow: Code Review -> Test Writer -> Git Commit
      - How context passes between skills
      - Tips for effective chaining

   b) "MCP Server Integration"
      - What the MCP server provides beyond basic install
      - Available MCP tools: search_skills, get_skill, install_skill
      - Connecting from different MCP clients
      - Configuration example:
        ```json
        {
          "mcpServers": {
            "skillhub": {
              "url": "https://skillhub.internal/mcp",
              "transport": "sse",
              "headers": {
                "Authorization": "Bearer ${SKILLHUB_TOKEN}"
              }
            }
          }
        }
        ```

   c) "Custom Trigger Phrases"
      - How trigger phrases work
      - Defining effective triggers
      - Avoiding conflicts with other skills
      - Example trigger configurations

   d) "Skill Configuration via Front Matter"
      - Optional front matter fields for power users
      - Environment-specific variants
      - Controlling data sensitivity
      - Version pinning

   e) "Performance Tips"
      - Context window management
      - When to uninstall unused skills
      - Skill loading order
      - Debugging skill issues:
        ::: details Troubleshooting Checklist
        1. Is the skill installed? Check with `claude skill list`
        2. Is the skill file valid? Check front matter syntax
        3. Is there a version conflict? Check `claude skill info <slug>`
        4. Clear cache: `claude skill cache clear`
        5. Reinstall: `claude skill install <slug> --force`
        :::

Write tests FIRST:
1. All 4 .md files have frontmatter with title and description
2. VitePress build succeeds (exit code 0)
3. Each page has exactly one H1
4. No broken internal links
5. uses-for-skills.md contains VitePress tip containers
6. skill-discovery.md contains a code-group block
7. social-features.md contains a warning container
8. advanced-usage.md contains a details block and a JSON code block

Do NOT:
- Modify existing completed pages (getting-started, introduction-to-skills)
- Add custom Vue components
- Modify .vitepress/config.ts
- Include real internal URLs

Acceptance Criteria:
- [ ] All 4 pages replaced with full content (not stubs)
- [ ] Correct frontmatter on all pages
- [ ] uses-for-skills.md covers 4+ persona categories with skill examples
- [ ] skill-discovery.md covers search, filters, divisions, sorting
- [ ] social-features.md covers reviews, comments, favorites, guidelines
- [ ] advanced-usage.md covers chaining, MCP, triggers, performance
- [ ] VitePress build succeeds
- [ ] All internal cross-links resolve
- [ ] All tests pass
```

---

### Prompt B.2.3 — Submission Guide, FAQ, Feature Requests, and Resources

**Time estimate:** 30-45 minutes

```
Write the final batch of documentation pages: Submitting a Skill, Feature Requests,
FAQ, and Resources. Replace the stubs from B.1.1. This completes the full 10-page
documentation set.

CONTEXT:
- VitePress app at apps/docs/
- Existing completed pages: getting-started, introduction-to-skills, uses-for-skills,
  skill-discovery, social-features, advanced-usage
- Target audience: end users
- Submission pipeline: Gate 1 (automated frontmatter validation) -> Gate 2 (LLM quality
  check) -> Gate 3 (human-in-the-loop review by platform team)
- Submission statuses: submitted, gate1_passed, gate1_failed, gate2_passed, gate2_flagged,
  gate2_failed, changes_requested, revision_pending, approved, rejected, published
- Submission API endpoints:
  * POST /api/v1/submissions — create submission
  * GET /api/v1/submissions/{display_id} — check status
  * POST /api/v1/submissions/{display_id}/resubmit — resubmit after changes requested
- Feedback endpoint: POST /api/v1/feedback

Requirements:

1. Replace apps/docs/src/submitting-a-skill.md:

   Frontmatter:
   ---
   title: Submitting a Skill
   description: How to submit, review, and publish your AI skills on SkillHub.
   ---

   Sections:
   a) "Before You Submit"
      - Prerequisites: org SSO account, skill file ready
      - Front matter requirements (link to Introduction to Skills)
      - Data sensitivity classification guide:

        | Level   | Description                                | Examples                        |
        |---------|--------------------------------------------|---------------------------------|
        | low     | No sensitive data processed                | Code formatting, git helpers    |
        | medium  | May process business data                  | Report generators, email tools  |
        | high    | Processes confidential data                | HR tools, financial analysis    |
        | phi     | Processes protected health information     | Clinical note tools             |

   b) "Submission Methods" — use code-group tabs:

      ::: code-group
      ```text [Web Form]
      1. Navigate to skillhub.internal/submit
      2. Fill in the required fields:
         - Skill name and description
         - Category and tags
         - Division visibility
         - Data sensitivity level
      3. Paste or type your skill content
      4. Click "Submit for Review"
      ```

      ```text [File Upload]
      1. Navigate to skillhub.internal/submit
      2. Click "Upload SKILL.md"
      3. Select your prepared SKILL.md file
      4. Review the parsed front matter
      5. Adjust division visibility if needed
      6. Click "Submit for Review"
      ```

      ```text [MCP Sync]
      1. Connect to the SkillHub MCP server
      2. Use the submit_skill tool:
         submit_skill(file_path="./SKILL.md")
      3. The tool validates and submits automatically
      4. Check status: get_submission_status(id="SUB-xxxx")
      ```
      :::

   c) "The Review Pipeline" — explain the 3-gate process simply:

      ::: info How Review Works
      Your submission goes through three review stages:

      **Stage 1 — Automated Checks** (instant)
      Validates front matter format, required fields, and slug availability.

      **Stage 2 — Quality Review** (1-2 minutes)
      AI-assisted quality and safety check. Evaluates content clarity,
      usefulness, and potential risks.

      **Stage 3 — Human Review** (1-3 business days)
      A platform team member reviews your skill, checking for policy
      compliance and quality standards.
      :::

   d) "Tracking Your Submission"
      - Status page: skillhub.internal/submissions/{display_id}
      - Status meanings explained in plain language
      - Email notifications at each stage

   e) "Responding to Change Requests"
      - What a change request looks like
      - Common change request flags:
        * Missing or incomplete front matter
        * Security concern identified
        * Scope too broad
        * Quality does not meet standards
        * Division assignment incorrect
        * Changelog required
      - How to resubmit:
        1. Review the feedback and flags
        2. Make the requested changes
        3. Click "Resubmit" or use the API
        4. Your revision enters the pipeline again
      - Revision tracking: each resubmission increments the revision number

   f) "After Approval"
      - Publishing process
      - Version updates for published skills
      - Updating metadata vs. content changes
      - Deprecating a skill

   g) "Tips for Faster Approval"
      ::: tip Tips for Faster Approval
      - Complete all front matter fields (including optional ones)
      - Write a clear, specific description
      - Set the correct data sensitivity level
      - Include trigger phrases
      - Add a changelog entry for version updates
      - Test your skill before submitting
      :::

2. Replace apps/docs/src/feature-requests.md:

   Frontmatter:
   ---
   title: Feature Requests
   description: How to submit ideas and vote on features for SkillHub.
   ---

   Sections:
   a) "Submitting Feature Requests"
      - Via the feedback form: skillhub.internal/feedback
      - What to include: description, use case, expected behavior
      - Categories: UI/UX, new feature, integration, performance, other

   b) "What Makes a Good Feature Request"
      ::: tip Writing a Good Feature Request
      1. **Be specific** — describe exactly what you want
      2. **Explain why** — what problem does this solve?
      3. **Give examples** — show a before/after scenario
      4. **Consider scope** — is this a small tweak or a major feature?
      :::

   c) "Voting on Features"
      - Upvote existing requests
      - Most-voted features get prioritized
      - Roadmap visibility

   d) "Roadmap"
      - Where to see the current roadmap
      - How priorities are determined
      - Release cadence

3. Replace apps/docs/src/faq.md:

   Frontmatter:
   ---
   title: Frequently Asked Questions
   description: Common questions about SkillHub, skill installation, submission, and more.
   ---

   Use VitePress details containers for collapsible Q&A. Minimum 15 questions.
   Organize into sections:

   a) "Account and Access" (3+ questions):
      ::: details How do I log in to SkillHub?
      SkillHub uses your organization's SSO. Visit skillhub.internal and click
      "Sign in with SSO." No separate registration needed.
      :::

      ::: details What divisions can I see skills from?
      You can see skills from your own division plus any skills marked as
      "all-org." Division visibility is set by the skill author during submission.
      :::

      ::: details How do I change my division?
      Your division is synced from the org directory. Contact your IT admin
      if your division assignment is incorrect.
      :::

   b) "Skill Installation" (4+ questions):
      - How do I install a skill?
      - Can I install skills on multiple machines?
      - How do I uninstall a skill?
      - What if a skill doesn't work after installation?

   c) "Submission Process" (4+ questions):
      - How long does the review process take?
      - Why was my submission rejected?
      - Can I resubmit after rejection?
      - How do I update a published skill?

   d) "Reviews and Social" (2+ questions):
      - Can I edit my review?
      - How are skill ratings calculated?

   e) "Technical Questions" (3+ questions):
      - What is the MCP server?
      - How many skills can I install at once?
      - Are skills sandboxed?

4. Replace apps/docs/src/resources.md:

   Frontmatter:
   ---
   title: Resources
   description: Reference links, glossary, and support information for SkillHub.
   ---

   Sections:
   a) "Glossary"
      | Term               | Definition                                               |
      |--------------------|----------------------------------------------------------|
      | Skill              | A reusable AI instruction set in SKILL.md format         |
      | Front Matter       | YAML metadata block at the top of a skill file           |
      | MCP                | Model Context Protocol — standard for AI tool integration |
      | HITL               | Human-in-the-loop — manual review by platform team       |
      | Gate               | An automated or manual review stage in the pipeline      |
      | Division           | Organizational unit that controls skill visibility       |
      | Slug               | URL-friendly unique identifier for a skill               |
      | Context Window     | The amount of text an AI can process at once             |
      | Trigger Phrase     | A phrase that activates a specific skill                 |
      | Semver             | Semantic versioning (MAJOR.MINOR.PATCH)                  |

   b) "Useful Links"
      - SkillHub App: `skillhub.internal`
      - API Documentation: `skillhub.internal/api/docs`
      - MCP Server: `skillhub.internal/mcp`
      - GitLab Repository: `gitlab.internal/skillhub`
      - Status Page: `status.internal/skillhub`

   c) "Support"
      - Slack channel: #skillhub-support
      - Email: skillhub-team@org.internal
      - Office hours: Tuesdays 2-3pm

   d) "Changelog"
      - Link to changelog (placeholder)
      - How to subscribe to updates

Write tests FIRST:
1. All 4 .md files have frontmatter with title and description
2. VitePress build succeeds (exit code 0)
3. Each page has exactly one H1
4. No broken internal links across the full 10-page doc set
5. submitting-a-skill.md contains a code-group block and a table
6. faq.md contains at least 15 details blocks (count ::: details occurrences)
7. resources.md contains a glossary table with at least 10 rows
8. Complete sidebar coverage: every sidebar entry in config.ts has a corresponding .md file
   (parse config, extract all link paths, verify files exist)

Do NOT:
- Modify existing completed pages
- Add custom Vue components
- Modify .vitepress/config.ts
- Include real internal URLs (use .internal placeholder domain)

Acceptance Criteria:
- [ ] All 4 pages created with full content
- [ ] Full documentation set complete: 10 content pages + index = 11 pages total
- [ ] VitePress build succeeds
- [ ] All sidebar entries resolve to existing pages
- [ ] FAQ has 15+ questions in collapsible details containers
- [ ] submitting-a-skill.md covers 3 submission methods, 3-gate pipeline, change requests
- [ ] resources.md has glossary with 10+ terms
- [ ] feature-requests.md covers submission, voting, roadmap
- [ ] All internal cross-links resolve
- [ ] All tests pass
```

---

## Phase B.3 — Integration and Finalization

**Goal:** Register the documentation portal in the feature index and run final validation across the entire doc set.

---

### Prompt B.3.1 — Feature index entry and final validation

**Time estimate:** 15-20 minutes

```
Add the User Documentation Portal entry to docs/features/index.md and run
comprehensive validation of the entire VitePress documentation site.

CONTEXT:
- VitePress app at apps/docs/ with 10 content pages + index (11 total)
- Feature index at docs/features/index.md (currently has a heading and one-liner)
- All documentation content is complete from B.2.1, B.2.2, B.2.3
- Need to add a feature entry and do final quality checks

Requirements:

1. Append to docs/features/index.md:

   ## User Documentation Portal
   ![Documentation Portal](assets/docs-portal.gif)
   Comprehensive user documentation built with VitePress, covering getting started,
   skill discovery, submission workflows, and advanced usage.

2. Create placeholder asset:
   - docs/features/assets/docs-portal.gif — create a placeholder (can be a tiny
     1x1 gif or a .gitkeep file renamed). Document that a real recording should
     replace this.
   - OR: if no asset system exists, use a text note instead:
     <!-- Screenshot: docs-portal.gif — record with feature-demo-recorder skill -->

3. Run and verify comprehensive VitePress validation:
   a) Build test: npx vitepress build src (from apps/docs/) exits 0
   b) Link audit: every internal link in every .md file resolves to an existing page
   c) Frontmatter audit: every .md file in apps/docs/src/ has title and description
   d) Heading audit: every .md file has exactly one H1
   e) Sidebar completeness: every sidebar link in config.ts maps to an existing .md file
   f) Content length: no page is a stub (each .md file > 50 lines)
   g) NX integration: "docs" appears in nx show projects output
   h) Mise tasks: mise run dev:docs and mise run build:docs execute without error

4. Fix any issues found during validation (broken links, missing frontmatter, etc.)

Write tests FIRST:
1. docs/features/index.md contains "User Documentation Portal" heading
2. docs/features/index.md contains "docs-portal.gif" reference
3. VitePress full build succeeds
4. All .md files in apps/docs/src/ have frontmatter with title
5. All .md files in apps/docs/src/ have > 50 lines (not stubs)
6. Sidebar link count matches file count in apps/docs/src/ (excluding index.md)
7. NX recognizes docs project

Do NOT:
- Modify any documentation content (only fix validation issues)
- Add new pages
- Change VitePress config (only fix if broken)

Acceptance Criteria:
- [ ] docs/features/index.md updated with User Documentation Portal entry
- [ ] Placeholder asset created or documented
- [ ] VitePress build succeeds
- [ ] All 10 content pages have frontmatter with title and description
- [ ] All 10 content pages have > 50 lines (no stubs remaining)
- [ ] All sidebar entries resolve to existing files
- [ ] All internal links resolve
- [ ] NX recognizes the docs project
- [ ] mise tasks work (dev:docs, build:docs)
- [ ] All tests pass
- [ ] No regressions in existing tests
```

---

## Quick Reference: Prompt Sequence

```
PHASE B.1 — VitePress Scaffold (1 prompt)
  B.1.1  Initialize VitePress app in NX monorepo           30-45 min
         Creates: apps/docs/ structure, config, theme, stubs, NX + mise integration

PHASE B.2 — Documentation Content (3 prompts)
  B.2.1  Getting Started + Introduction to Skills           30-45 min
         Creates: 2 full content pages (install methods, skill anatomy)
  B.2.2  Discovery, Social, Advanced Usage                  30-45 min
         Creates: 4 full content pages (uses, discovery, social, advanced)
  B.2.3  Submission Guide, FAQ, Feature Requests, Resources 30-45 min
         Creates: 4 full content pages (submission pipeline, 15+ FAQ, glossary)

PHASE B.3 — Integration and Finalization (1 prompt)
  B.3.1  Feature index entry + final validation             15-20 min
         Updates: docs/features/index.md, runs full quality audit

TOTAL: 5 prompts, ~2.5-3.5 hours estimated
PAGES: 11 (10 content + 1 index/landing)
```

### Dependency Graph

```
B.1.1 (scaffold)
  ├── B.2.1 (getting-started, introduction)
  ├── B.2.2 (uses, discovery, social, advanced)
  └── B.2.3 (submission, faq, feature-requests, resources)
       └── B.3.1 (feature index + validation)
```

B.2.1, B.2.2, and B.2.3 can run in parallel after B.1.1 (they only depend on the scaffold). B.3.1 must run last as it validates the complete set.

### Files Created (Complete List)

```
apps/docs/
├── package.json
├── project.json
├── .vitepress/
│   ├── config.ts
│   └── theme/
│       ├── index.ts
│       └── custom.css
├── src/
│   ├── index.md
│   ├── getting-started.md
│   ├── introduction-to-skills.md
│   ├── uses-for-skills.md
│   ├── skill-discovery.md
│   ├── social-features.md
│   ├── advanced-usage.md
│   ├── submitting-a-skill.md
│   ├── feature-requests.md
│   ├── faq.md
│   ├── resources.md
│   ├── assets/
│   │   ├── screenshots/.gitkeep
│   │   └── diagrams/.gitkeep
│   └── public/
│       └── logo.svg
└── (generated) .vitepress/dist/   (build output, gitignored)

Files Modified:
├── mise.toml                      (add dev:docs, build:docs tasks)
└── docs/features/index.md         (add User Documentation Portal entry)
```
