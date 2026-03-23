---
name: social-feature-builder
description: Use when adding social features like favorites, follows, installs, or forks
---

# Social Feature Builder

## Pattern: Toggle Endpoint

```python
@router.post("/api/v1/skills/{slug}/favorite")
def add_favorite(slug, db=Depends(get_db), user=Depends(get_current_user)):
    skill = get_skill_or_404(db, slug)
    existing = db.query(Favorite).filter_by(user_id=user["user_id"], skill_id=skill.id).first()
    if existing:
        raise HTTPException(409, "Already favorited")
    db.add(Favorite(user_id=user["user_id"], skill_id=skill.id))
    skill.favorite_count += 1  # Denormalized counter
    audit_log(db, "skill.favorited", user["user_id"], "skill", skill.id)

@router.delete("/api/v1/skills/{slug}/favorite")
def remove_favorite(slug, db=Depends(get_db), user=Depends(get_current_user)):
    fav = db.query(Favorite).filter_by(...).first()
    if not fav: raise HTTPException(404)
    db.delete(fav)
    skill.favorite_count -= 1
    audit_log(db, "skill.unfavorited", ...)
```

## Denormalized Counters

Update on skills table: `install_count`, `fork_count`, `favorite_count`. Source of truth remains the join table (installs, forks, favorites).

## Composite PK for Join Tables

```python
class Favorite(Base):
    __tablename__ = "favorites"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
```

## References

- Social router: `apps/api/skillhub/routers/social.py`
- Social service: `apps/api/skillhub/services/social.py`
- Social models: `libs/db/skillhub_db/models/social.py`
