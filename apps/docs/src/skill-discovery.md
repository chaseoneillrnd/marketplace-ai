# Skill Discovery

SkillHub provides multiple ways to find the right skill -- browse by category, filter by division, search by keyword, or sort by community signals. The marketplace currently contains 61 skills across 9 categories and 8 organizational divisions.

## Browsing by Category

The marketplace homepage organizes skills into 9 categories that map to organizational functions:

| Category | Slug | Description |
|----------|------|-------------|
| Engineering | `engineering` | Code generation, review, testing, DevOps, CI/CD |
| Product | `product` | Specs, PRDs, user stories, roadmaps |
| Data | `data` | Analytics, SQL, visualization, ML pipelines |
| Security | `security` | Threat modeling, compliance, vulnerability assessment |
| Finance | `finance` | Budgets, forecasting, financial reporting |
| General | `general` | Cross-functional productivity tools |
| HR | `hr` | Hiring, onboarding, people operations |
| Research | `research` | Literature review, synthesis, competitive analysis |
| Operations | `operations` | SOPs, process improvement, incident management |

Click any category pill on the browse page to filter the skill grid. Categories are mutually exclusive -- each skill belongs to exactly one category.

### API Reference

```bash
# List all categories
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/categories

# Browse skills in a category
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?category=engineering"
```

---

## Division Filtering

Skills are scoped to organizational divisions. You can see skills authorized for your division by default, or use multi-select filtering to explore across divisions you have access to.

### The 8 Divisions

| Division | Slug | Focus Area |
|----------|------|------------|
| Engineering Org | `engineering-org` | Software development teams |
| Product Org | `product-org` | Product management and design |
| Data Org | `data-org` | Data science and analytics |
| Security Org | `security-org` | Information security |
| Finance Org | `finance-org` | Financial planning and accounting |
| HR Org | `hr-org` | Human resources and recruiting |
| Research Org | `research-org` | R&D and innovation labs |
| Operations Org | `operations-org` | Business operations and support |

::: info Division Access
Division filtering is **server-enforced**. The API only returns skills your division is authorized to see. If you need access to a skill outside your division, you can submit a cross-division access request from the skill's detail page.
:::

### Multi-Select Filtering

On the web marketplace, division filters appear as a multi-select dropdown. Select multiple divisions to see the union of their skills. The API supports the same:

```bash
# Skills visible to Engineering and Product divisions
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?divisions=engineering-org,product-org"
```

---

## Search

SkillHub provides full-text search across skill names, descriptions, and tags. Results are ranked by relevance with instant response times.

### Web Search

The hero search bar on the homepage accepts any text query. Results appear as you type with category and division facets in the sidebar.

### API Search

```bash
# Search by keyword
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?search=code+review"

# Combine search with category filter
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?search=testing&category=engineering"

# Combine search with division filter
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?search=dashboard&divisions=data-org"
```

### MCP Search

From inside Claude Code, ask naturally:

```
Search SkillHub for skills related to database migrations
```

Claude uses the `search_skills` MCP tool, which supports the same query, category, and division parameters.

---

## Sort Modes

Control how results are ordered using five sort modes:

| Sort Mode | API Value | What It Measures |
|-----------|-----------|------------------|
| **Trending** | `trending` | Install velocity -- skills gaining traction recently |
| **Most Installed** | `installs` | Total lifetime install count |
| **Highest Rated** | `rating` | Bayesian average rating (avoids low-sample-size bias) |
| **Newest** | `newest` | Most recently published skills |
| **Recently Updated** | `updated` | Most recently updated (new versions) |

### Trending Algorithm

The trending score is based on install velocity -- how many installs a skill has received in a recent time window relative to its total. This surfaces skills that are gaining popularity, not just skills that have been around the longest.

### Bayesian Average Rating

Raw average ratings are misleading when sample sizes are small. A skill with 1 review at 5 stars would outrank a skill with 100 reviews at 4.8 stars. SkillHub uses Bayesian averaging to account for this:

```
bayesian_avg = (C * m + sum_of_ratings) / (C + num_ratings)

Where:
  C = confidence threshold (platform-wide average number of ratings)
  m = platform-wide average rating
```

This pulls low-sample skills toward the global average, so a skill needs meaningful review volume to rank at the top.

### API Reference

```bash
# Sort by trending
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?sort=trending"

# Sort by highest rated, filtered to Data category
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?sort=rating&category=data"
```

---

## Featured and Verified Badges

### Featured Skills

The Platform Team curates a **featured** section on the homepage. Featured skills are editorially selected to highlight high-quality, broadly useful skills. They appear in a dedicated carousel above the main skill grid.

Featured skills are marked with a star badge and can have a display order for the carousel layout.

### Verified Skills

A **verified** badge indicates that a skill has passed all three quality gates and has been explicitly vouched for by the Platform Team. While all published skills have passed the gates, verified status is an additional endorsement.

```bash
# Get only featured skills
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?featured=true"

# Get only verified skills
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?verified=true"
```

---

## Pagination

All browse and search results use load-more pagination. The API returns a page of results with metadata for fetching the next page:

```bash
# First page (default: 20 results)
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?page=1&per_page=20"

# Next page
curl -H "Authorization: Bearer $TOKEN" \
  "https://skillhub.yourcompany.com/api/v1/skills?page=2&per_page=20"
```

The web UI shows a **Load More** button that fetches the next page and appends results to the grid.

---

## Skill Detail Page

Clicking a skill card opens its detail page with four tabs:

| Tab | Content |
|-----|---------|
| **Overview** | Full description, trigger phrases, authorized divisions, tags, counters |
| **How to Use** | Usage instructions, best prompts, tips |
| **Install** | Three install method cards (MCP, CLI, Manual) with division access gate |
| **Reviews & Discussion** | Star histogram, written reviews, threaded comments |

```bash
# Get full skill detail
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant
```

## Next Steps

- [Learn about community features -- ratings, reviews, and forks](/social-features)
- [Install a skill you have found](/getting-started)
- [Submit your own skill to the marketplace](/submitting-a-skill)
