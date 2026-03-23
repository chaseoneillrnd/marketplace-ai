---
name: comment-system-builder
description: Use when building or extending the comment/reply system
---

# Comment System Builder

## Structure

- Comments: top-level on skills (`skill_id`)
- Replies: one level deep on comments (`comment_id`)
- No deeper nesting.

## Soft Delete

```python
comment.deleted_at = datetime.utcnow()  # Don't actually delete
```

Display: "This comment has been deleted" if `deleted_at` is set.

## Upvotes

`comment_votes` table (composite PK: `comment_id + user_id`). `upvote_count` denormalized on comments table.

## References

- Social models: `libs/db/skillhub_db/models/social.py`
- Social router: `apps/api/skillhub/routers/social.py`
