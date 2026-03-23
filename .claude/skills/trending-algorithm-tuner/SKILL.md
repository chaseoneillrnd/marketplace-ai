---
name: trending-algorithm-tuner
description: Use when tuning trending scores, sort signals, or Bayesian rating calculations
---

# Trending Algorithm Tuner

## Trending Score (Install Velocity)

```python
from datetime import datetime, timedelta

def calculate_trending(db, skill_id):
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_installs = db.query(Install)\
        .filter(Install.skill_id == skill_id, Install.installed_at >= week_ago)\
        .count()
    return recent_installs  # Simple velocity; enhance with decay factor
```

## Bayesian Weighted Average

Guards against low-sample inflation (skill with 1 five-star review shouldn't rank #1).

```python
C = 3.0   # Prior mean (global average)
m = 10    # Minimum votes for full weight
R = skill.avg_rating
v = skill.review_count
bayesian = (v / (v + m)) * R + (m / (v + m)) * C
```

## Denormalized Counter Updates

On every install/favorite/fork/review:
```python
skill.install_count = db.query(Install).filter_by(skill_id=skill.id, uninstalled_at=None).count()
skill.avg_rating = db.query(func.avg(Review.rating)).filter_by(skill_id=skill.id).scalar() or 0
```

## Sort Implementation

See `apps/api/skillhub/services/skills.py` — `sort` parameter maps to ORDER BY clauses.

## References

- Skills service: `apps/api/skillhub/services/skills.py`
- Social models: `libs/db/skillhub_db/models/social.py`
