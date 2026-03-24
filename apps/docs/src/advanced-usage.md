# Advanced Usage

Once you are comfortable installing and using individual skills, you can unlock more powerful patterns: chaining skills together, composing complex workflows, customizing triggers, and managing context window performance.

## Skill Chaining

Skill chaining means using multiple skills in sequence within a single conversation to accomplish a larger task. Each skill handles one step, and you guide Claude through the pipeline.

### Example: Code Review to Test Generation

```
You: Review this pull request using the PR Review skill

Claude: [Uses PR Review Assistant skill]
Here are my findings:
1. Critical: SQL injection in user_search endpoint
2. Warning: Missing error handling in payment_process
3. Suggestion: Extract validation logic into helper function
...

You: Now generate tests for the issues you found using the Pytest Generator skill

Claude: [Uses Pytest Generator skill]
Here are the tests:
- test_user_search_rejects_sql_injection_payload
- test_payment_process_handles_timeout_error
- test_validation_helper_rejects_invalid_input
...
```

### Example: Research to Presentation

```
You: Do a competitive analysis of the top 3 tools in this space

Claude: [Uses Competitive Analysis skill]
...

You: Now create a slide deck presenting these findings to leadership

Claude: [Uses Slide Deck Creator skill]
...
```

### Chaining Best Practices

::: tip
1. **Let each skill complete fully** before invoking the next. Claude produces better output when it finishes one structured task before starting another.
2. **Reference previous output explicitly.** Say "based on the findings above" or "using the analysis you just produced."
3. **Limit chains to 3-4 skills** per conversation. Beyond that, context window pressure can degrade output quality.
:::

---

## Skill Composition

While chaining uses skills in sequence, composition means designing skills that **reference each other** to build layered workflows.

### Building a Composed Workflow

Consider a "Full Feature Lifecycle" workflow that uses multiple skills:

```markdown
---
name: Feature Lifecycle Orchestrator
description: Guide a feature from RFC through implementation to review
triggers:
  - full feature workflow
  - feature lifecycle
category: engineering
---

# Feature Lifecycle Orchestrator

Guide the developer through these phases in order:

## Phase 1: Design
Ask the developer to describe the feature, then:
- Draft an RFC following the RFC Writer pattern
- Include problem statement, proposed solution, and alternatives

## Phase 2: Implementation Plan
Based on the approved RFC:
- Break into tasks with acceptance criteria
- Identify which files need to change
- Flag any migration requirements

## Phase 3: Test-First Development
For each task:
- Write tests FIRST following the Pytest Generator pattern
- Implement until tests pass
- Run the linter before moving on

## Phase 4: Review
Once implementation is complete:
- Self-review using the PR Review Assistant checklist
- Flag any items that need human review attention
```

This skill does not literally invoke other skills, but it encodes the same patterns, creating a coherent multi-phase workflow in a single skill.

### When to Compose vs. Chain

| Approach | Best For | Trade-off |
|----------|----------|-----------|
| **Chaining** | Ad-hoc combinations, exploratory work | Flexible but requires manual orchestration |
| **Composition** | Repeatable workflows, team standards | More effort to create but consistent every time |

---

## Custom Trigger Phrases

Trigger phrases determine when Claude loads a skill into context. Choosing the right triggers is critical for a smooth experience.

### How Triggers Are Matched

Claude Code uses semantic matching against trigger phrases. The matching considers:

1. **Exact overlap** -- "review this PR" matches "review this PR"
2. **Semantic similarity** -- "check my pull request" matches "review this PR"
3. **Keyword presence** -- "PR review" matches "review this PR"

### Designing Effective Triggers

::: tip Trigger Design Guidelines
- **Use 2-4 trigger phrases** per skill. Fewer means the skill may not activate; more creates collision risk.
- **Mix specificity levels.** Include one precise trigger ("python code review") and one general trigger ("review this code").
- **Avoid single-word triggers.** "Review" alone will collide with too many other skills.
- **Test for collisions.** If you have two installed skills with similar triggers, Claude may load the wrong one.
:::

### Trigger Collision Detection

SkillHub's submission pipeline (Gate 1) checks for trigger phrase similarity using Jaccard coefficient. If a new skill's triggers overlap more than 70% with an existing published skill, the submission is flagged:

```
Gate 1 Result: FAIL
Reason: Trigger phrase "review pull request" has Jaccard similarity
of 0.82 with existing skill "pr-review-assistant" trigger
"review this pull request". Consider more specific triggers.
```

### Overriding Triggers Locally

After installing a skill, you can edit the `SKILL.md` file to customize triggers for your workflow:

```bash
# Edit the installed skill
vim .claude/skills/pr-review-assistant/SKILL.md
```

Change the triggers in the front matter:

```yaml
triggers:
  - review this python PR         # more specific to your workflow
  - fastapi endpoint review       # team-specific trigger
```

::: warning
Local edits will be overwritten if you run `update_skill`. Consider forking the skill instead if you want persistent trigger customizations.
:::

---

## Performance Considerations

Skills consume context window space. Understanding how to manage this is important for power users.

### Context Window Basics

Claude's context window has a finite token limit. When a skill is activated:

1. The full skill content (markdown body) is injected into the conversation context
2. This reduces the space available for conversation history and Claude's response
3. Multiple active skills in the same turn compound the cost

### Sizing Guidelines

| Skill Length | Approximate Tokens | Recommendation |
|-------------|-------------------|----------------|
| Short (< 500 words) | ~700 tokens | Ideal for focused, single-task skills |
| Medium (500-1,500 words) | ~2,000 tokens | Good balance of detail and context efficiency |
| Long (1,500-3,000 words) | ~4,000 tokens | Use only when the detail is essential |
| Very long (3,000+ words) | ~5,000+ tokens | Consider splitting into multiple skills |

### Optimization Strategies

::: tip Keep Skills Lean
1. **Remove filler text.** Every word should earn its place in the context window.
2. **Use structured lists** over prose paragraphs. Lists convey the same information in fewer tokens.
3. **Put examples in a separate section.** If the skill works without examples, make them optional context.
4. **Split large skills.** A "Full Code Review" skill should be three skills: Security Review, Performance Review, Readability Review.
:::

### Monitoring Installed Skills

Use the `list_installed` MCP tool to see all your installed skills and their sizes:

```
List my installed SkillHub skills
```

Claude will show each installed skill with its name, version, and a staleness indicator showing whether a newer version is available on the marketplace.

### Uninstalling Unused Skills

Skills that are installed but never triggered still take up disk space and appear in the skill index. Clean up skills you no longer use:

```bash
# Via MCP (natural language)
Uninstall the meeting-summarizer skill

# Via CLI
claude skill uninstall meeting-summarizer

# Via API
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/skills/meeting-summarizer/install
```

---

## Advanced MCP Patterns

### Batch Operations

While the MCP tools operate on one skill at a time, you can ask Claude to perform batch operations conversationally:

```
Search for all engineering skills related to testing, then install the top 3 by rating
```

Claude will call `search_skills`, evaluate the results, then call `install_skill` three times.

### Submission from the Editor

You can write a skill and submit it for review without leaving Claude Code:

```
I just wrote a new skill at .claude/skills/my-new-skill/SKILL.md.
Submit it to SkillHub for review.
```

Claude reads the file, calls `submit_skill` with the content and metadata, and reports back with the submission ID and pipeline status.

### Status Monitoring

Track your submission through the 3-gate pipeline:

```
Check the status of my SkillHub submission SUB-00042
```

Claude calls `check_submission_status` and returns the current gate, result, score, and any reviewer notes.

## Next Steps

- [Submit your own skill](/submitting-a-skill)
- [Learn about the quality gate pipeline](/submitting-a-skill#the-3-gate-pipeline)
- [Browse the FAQ for common questions](/faq)
