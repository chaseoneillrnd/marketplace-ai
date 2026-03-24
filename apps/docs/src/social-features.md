# Social Features

SkillHub is more than a download catalog -- it is a community-driven marketplace where ratings, reviews, comments, and forks create organic quality signals that help everyone find the best skills.

## Star Ratings

Every authenticated user can rate any skill from 1 to 5 stars. Ratings are one-per-user-per-skill; submitting a new rating replaces your previous one.

### How Ratings Are Displayed

- **Skill cards** show the average rating and total review count
- **Skill detail pages** show a star histogram (5-star breakdown)
- **Sort by rating** uses the Bayesian average, not the raw mean

### Bayesian Average

To prevent gaming and low-sample bias, SkillHub calculates ratings using a Bayesian average:

```
bayesian_avg = (C * m + sum_of_ratings) / (C + num_ratings)

C = platform average number of ratings per skill
m = platform average rating across all skills
```

This means a skill with 2 ratings at 5.0 stars will not outrank a skill with 50 ratings at 4.7 stars. Skills need meaningful engagement to reach the top of the leaderboard.

### API Reference

```bash
# Rate a skill (1-5)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": 5, "body": "Excellent skill, saved me hours on PR reviews."}' \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant/reviews

# Update your existing review
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": 4, "body": "Updated: still great, but could use more edge case coverage."}' \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant/reviews
```

---

## Written Reviews

Beyond star ratings, users can write detailed text reviews. Reviews help skill authors understand what works and what needs improvement.

### Review Features

| Feature | Description |
|---------|-------------|
| **One review per user per skill** | Enforced by unique constraint on `(skill_id, user_id)` |
| **Edit capability** | Update your review text and rating at any time |
| **Helpful / Unhelpful voting** | Other users can vote on whether a review is useful |
| **Sorted by helpfulness** | Reviews with more "helpful" votes appear first |

### Writing a Good Review

::: tip Review Guidelines
- **Be specific.** "Great skill" is less useful than "The security checklist caught a SQL injection I would have missed."
- **Mention your use case.** Help others decide if the skill fits their needs.
- **Suggest improvements.** Authors appreciate actionable feedback.
- **Rate honestly.** Inflated ratings hurt everyone; 3 stars is a perfectly good rating.
:::

### Helpful / Unhelpful Voting

Every review has a vote mechanism. Users can mark a review as **helpful** or **unhelpful**. Each user gets one vote per review (you can change your vote). The vote tally helps surface the most useful reviews at the top.

```bash
# Vote a review as helpful
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vote": "helpful"}' \
  https://skillhub.yourcompany.com/api/v1/reviews/{review_id}/votes
```

---

## Comments and Threaded Replies

The **Reviews & Discussion** tab on each skill detail page includes a threaded comment system for open-ended conversation.

### How Comments Work

- Any authenticated user can post a comment on any skill they can access
- Comments support **threaded replies** -- click "Reply" on any comment to start a sub-thread
- Comments can be **upvoted** by other users to surface the most valuable discussions
- Authors can **soft-delete** their own comments (content is removed, thread structure preserved)

### Comment vs. Review

| | Review | Comment |
|--|--------|---------|
| **Includes a rating** | Yes (1-5 stars) | No |
| **One per user per skill** | Yes | No limit |
| **Threaded replies** | No | Yes |
| **Use case** | Overall skill evaluation | Questions, tips, discussion |

### API Reference

```bash
# Post a comment
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": "Has anyone tried using this with Python 3.12 match statements?"}' \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant/comments

# Reply to a comment
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": "Yes, it handles match/case patterns correctly since v2.1."}' \
  https://skillhub.yourcompany.com/api/v1/comments/{comment_id}/replies

# Upvote a comment
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/comments/{comment_id}/votes
```

---

## Favorites Collection

Save skills you use frequently or want to revisit later to your **Favorites** collection.

### How Favorites Work

- Click the heart icon on any skill card or detail page to toggle a favorite
- Your favorites list is accessible from your profile
- Favorites are private -- other users cannot see your collection
- There is no limit on the number of favorites

### API Reference

```bash
# Add a skill to favorites
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant/favorite

# Remove from favorites
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/skills/pr-review-assistant/favorite

# List your favorites
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/users/me/favorites
```

---

## Following Skill Authors

Follow prolific skill authors to stay informed when they publish new skills or update existing ones.

### How Following Works

- Click **Follow** on a skill author's profile
- You follow the **author**, not an individual skill
- Following is visible to the author (they can see their follower count)
- Notification support for new skill publications is planned for Phase 2

### API Reference

```bash
# Follow an author
curl -X POST -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/users/{user_id}/follow

# Unfollow
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/users/{user_id}/follow

# List who you follow
curl -H "Authorization: Bearer $TOKEN" \
  https://skillhub.yourcompany.com/api/v1/users/me/following
```

---

## Forking Skills

Forking lets you create a **division-specific variant** of an existing skill while preserving lineage back to the original. This is one of SkillHub's most powerful collaboration features.

### When to Fork

- You want to adapt a general skill for your division's specific conventions
- You need to add domain-specific examples (e.g., your team's SQL style guide)
- You want to tighten constraints for a regulated context (e.g., finance compliance)

### How Forking Works

1. Navigate to a skill's detail page and click **Fork**
2. SkillHub creates a new skill under your authorship
3. The fork records the **original skill ID** and **version at fork time**
4. You can edit the forked skill's content, name, and metadata
5. The original author can see how many forks their skill has

### Fork via MCP

From inside Claude Code:

```
Fork the sql-query-builder skill for my division
```

Claude calls the `fork_skill` MCP tool, which creates the fork and writes the new `SKILL.md` locally.

### API Reference

```bash
# Fork a skill
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"division": "finance-org"}' \
  https://skillhub.yourcompany.com/api/v1/skills/sql-query-builder/fork
```

### Fork Lineage

Forks maintain a reference to their upstream skill:

```json
{
  "id": "fork-uuid",
  "name": "SQL Query Builder (Finance)",
  "fork_of": {
    "skill_id": "original-uuid",
    "skill_slug": "sql-query-builder",
    "version_at_fork": "1.2.0"
  }
}
```

This makes it easy to see which skills are variants of a common ancestor, and to pull updates from upstream when the original improves.

---

## Community Signals at a Glance

Every skill card displays key engagement metrics:

| Signal | Icon | Source |
|--------|------|--------|
| Install count | Download arrow | Tracked via API on every install |
| Average rating | Stars | Bayesian average of all reviews |
| Review count | Chat bubble | Number of written reviews |
| Fork count | Branch icon | Number of forks created |
| Favorite count | Heart | Number of users who favorited |

These signals, combined with the trending algorithm, create **organic quality curation** -- the best skills rise to the top without requiring central editorial oversight.

## Next Steps

- [Discover skills in the marketplace](/skill-discovery)
- [Learn about advanced skill usage](/advanced-usage)
- [Submit your own skill](/submitting-a-skill)
