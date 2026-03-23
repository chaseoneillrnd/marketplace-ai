---
name: review-system-builder
description: Use when building or extending the review and discussion system
---

# Review System Builder

## One-Review-Per-User Constraint

`UNIQUE(skill_id, user_id)` on reviews table. Second review → 409 Conflict.

## Rating Histogram

```python
histogram = db.query(Review.rating, func.count())\
    .filter_by(skill_id=skill.id)\
    .group_by(Review.rating)\
    .all()
# Returns: [(5, 12), (4, 8), (3, 3), (2, 1), (1, 0)]
```

## Helpful/Unhelpful Votes

```python
class ReviewVote(Base):
    review_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reviews.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    vote: Mapped[str]  # "helpful" | "unhelpful"
```

## avg_rating Recalculation

Trigger on review create/update/delete:
```python
skill.avg_rating = db.query(func.avg(Review.rating)).filter_by(skill_id=skill.id).scalar() or 0
skill.review_count = db.query(Review).filter_by(skill_id=skill.id).count()
```

## References

- Reviews router: `apps/api/skillhub/routers/reviews.py` (if separate) or `social.py`
- Reviews service: `apps/api/skillhub/services/reviews.py`
- Models: `libs/db/skillhub_db/models/social.py`
