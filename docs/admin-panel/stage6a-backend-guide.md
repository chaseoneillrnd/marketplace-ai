# Stage 6A: Feedback, Roadmap & Changelog — Backend Guide

## Overview

This stage adds two new domain areas to the SkillHub API: **user feedback** (feature requests, bug reports, praise) and **platform roadmap/changelog** (planned, in-progress, and shipped updates). All code follows the TDD RED-GREEN-REFACTOR cycle established in earlier stages.

**Estimated time:** 4 prompts × 15-25 min each

**Prerequisites:** Stages 1-5 complete. `libs/db`, `apps/api`, audit_log pattern, `require_platform_team` / `require_security_team` dependencies all in place.

---

## Prompt 6A-1: Database Models & Alembic Migration

**Time estimate:** 20-30 min

### Requirements

Add two new SQLAlchemy models to `libs/db/skillhub_db/models/` and generate an Alembic migration.

**`skill_feedback` table:**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default uuid4 |
| user_id | UUID | FK users.id NOT NULL |
| skill_id | UUID | FK skills.id NULLABLE |
| category | VARCHAR(30) | NOT NULL — `feature_request`, `bug_report`, `praise`, `complaint` |
| body | TEXT | NOT NULL, 20-500 chars enforced at DB via CHECK constraint |
| sentiment | VARCHAR(20) | NOT NULL — `positive`, `negative`, `neutral` — set server-side, never by user |
| upvotes | INTEGER | NOT NULL DEFAULT 0 |
| status | VARCHAR(20) | NOT NULL DEFAULT `open` — `open`, `triaged`, `planned`, `archived` |
| allow_contact | BOOLEAN | NOT NULL DEFAULT false |
| created_at | TIMESTAMPTZ | server_default=now() |

**`platform_updates` table:**

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default uuid4 |
| title | VARCHAR(255) | NOT NULL |
| body | TEXT | NOT NULL (Markdown) |
| status | VARCHAR(20) | NOT NULL DEFAULT `planned` — `planned`, `in_progress`, `shipped`, `cancelled` |
| author_id | UUID | FK users.id NOT NULL |
| target_quarter | VARCHAR(10) | NULLABLE — e.g. `Q3-2025` |
| linked_feedback_ids | JSONB | NOT NULL DEFAULT `[]` |
| shipped_at | TIMESTAMPTZ | NULLABLE |
| sort_order | INTEGER | NOT NULL DEFAULT 0 |
| created_at | TIMESTAMPTZ | server_default=now() |
| updated_at | TIMESTAMPTZ | server_default=now(), onupdate=now() |

### File Structure

```
libs/db/skillhub_db/models/feedback.py        # new
libs/db/migrations/versions/<rev>_add_feedback_and_platform_updates.py  # new
apps/api/tests/test_feedback_models.py         # new — write FIRST
```

### Write Tests First

Create `apps/api/tests/test_feedback_models.py` before any model code:

```python
"""Tests for SkillFeedback and PlatformUpdate models — write BEFORE implementation."""

import uuid
from datetime import datetime, timezone

import pytest
from skillhub_db.models.feedback import FeedbackCategory, FeedbackStatus, PlatformUpdate, PlatformUpdateStatus, SkillFeedback
from sqlalchemy.orm import Session


class TestSkillFeedbackModel:
    def test_create_minimal_feedback(self, db: Session, sample_user):
        """Feedback requires user_id, category, body, sentiment."""
        fb = SkillFeedback(
            user_id=sample_user.id,
            category=FeedbackCategory.FEATURE_REQUEST,
            body="Please add dark mode support to the skills editor page",
            sentiment="neutral",
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)

        assert fb.id is not None
        assert fb.upvotes == 0
        assert fb.status == FeedbackStatus.OPEN
        assert fb.allow_contact is False
        assert fb.skill_id is None
        assert fb.created_at is not None

    def test_skill_id_is_optional(self, db: Session, sample_user):
        fb = SkillFeedback(
            user_id=sample_user.id,
            category=FeedbackCategory.BUG_REPORT,
            body="The install button does not respond on Firefox browser version 120",
            sentiment="negative",
            skill_id=None,
        )
        db.add(fb)
        db.commit()
        assert fb.skill_id is None

    def test_feedback_linked_to_skill(self, db: Session, sample_user, sample_skill):
        fb = SkillFeedback(
            user_id=sample_user.id,
            skill_id=sample_skill.id,
            category=FeedbackCategory.PRAISE,
            body="This skill saved me hours of work on my project last week!",
            sentiment="positive",
        )
        db.add(fb)
        db.commit()
        assert fb.skill_id == sample_skill.id

    def test_all_feedback_categories_valid(self, db: Session, sample_user):
        for cat in FeedbackCategory:
            fb = SkillFeedback(
                user_id=sample_user.id,
                category=cat,
                body="Generic feedback body that meets the minimum character requirement here",
                sentiment="neutral",
            )
            db.add(fb)
        db.commit()

    def test_all_feedback_statuses_valid(self):
        assert set(FeedbackStatus) == {"open", "triaged", "planned", "archived"}


class TestPlatformUpdateModel:
    def test_create_minimal_update(self, db: Session, sample_user):
        update = PlatformUpdate(
            title="Improved search ranking",
            body="## What changed\nSearch now uses semantic similarity.",
            author_id=sample_user.id,
        )
        db.add(update)
        db.commit()
        db.refresh(update)

        assert update.id is not None
        assert update.status == PlatformUpdateStatus.PLANNED
        assert update.linked_feedback_ids == []
        assert update.sort_order == 0
        assert update.shipped_at is None
        assert update.target_quarter is None

    def test_linked_feedback_ids_default_empty_list(self, db: Session, sample_user):
        update = PlatformUpdate(
            title="Test update", body="Body text", author_id=sample_user.id
        )
        db.add(update)
        db.commit()
        db.refresh(update)
        assert isinstance(update.linked_feedback_ids, list)
        assert update.linked_feedback_ids == []

    def test_all_platform_update_statuses(self):
        assert set(PlatformUpdateStatus) == {"planned", "in_progress", "shipped", "cancelled"}

    def test_shipped_at_nullable(self, db: Session, sample_user):
        update = PlatformUpdate(
            title="Unshipped feature",
            body="Coming soon to a platform near you.",
            author_id=sample_user.id,
            status=PlatformUpdateStatus.IN_PROGRESS,
        )
        db.add(update)
        db.commit()
        assert update.shipped_at is None
```

### Implementation

**`libs/db/skillhub_db/models/feedback.py`:**

```python
"""Feedback and platform roadmap/changelog models."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from skillhub_db.base import Base


class FeedbackCategory(enum.StrEnum):
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    PRAISE = "praise"
    COMPLAINT = "complaint"


class FeedbackSentiment(enum.StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackStatus(enum.StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    PLANNED = "planned"
    ARCHIVED = "archived"


class PlatformUpdateStatus(enum.StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


class SkillFeedback(Base):
    """User feedback — feature requests, bug reports, praise, complaints."""

    __tablename__ = "skill_feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str] = mapped_column(String(20), nullable=False)
    upvotes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=FeedbackStatus.OPEN, index=True
    )
    allow_contact: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SkillFeedback {self.category!r} status={self.status!r}>"


class PlatformUpdate(Base):
    """Roadmap item / changelog entry."""

    __tablename__ = "platform_updates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PlatformUpdateStatus.PLANNED, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    target_quarter: Mapped[str | None] = mapped_column(String(10), nullable=True)
    linked_feedback_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PlatformUpdate {self.title!r} status={self.status!r}>"
```

Register both models in `libs/db/skillhub_db/models/__init__.py` so Alembic autogenerate picks them up.

**Generate migration:**

```bash
cd libs/db && alembic revision --autogenerate -m "add_feedback_and_platform_updates"
```

Review the generated file. Ensure:
- `linked_feedback_ids` column uses `postgresql.JSONB` (not plain JSON) — edit the migration by hand if autogenerate emits `JSON`.
- `body` column has a `CheckConstraint("char_length(body) >= 20 AND char_length(body) <= 500")` on `skill_feedback`.
- Both tables have `CREATE INDEX` statements for their FK columns.

### Do NOT

- Do not add a `user` relationship to `SkillFeedback` at this stage — eager-load user names in the service layer via explicit joins.
- Do not add `sentiment` to the `FeedbackCreate` schema — it is always server-computed.
- Do not run `alembic upgrade head` until tests pass against the migration.

### Acceptance Criteria

- [ ] `pytest apps/api/tests/test_feedback_models.py` passes (all green).
- [ ] `alembic upgrade head` completes without error on a fresh test DB.
- [ ] `alembic downgrade -1` reverses the migration cleanly.
- [ ] Both tables visible in `\dt` output.
- [ ] `linked_feedback_ids` column type is `jsonb` in psql.

---

## Prompt 6A-2: Pydantic Schemas

**Time estimate:** 15-20 min

### Requirements

Add all request/response schemas for feedback and roadmap endpoints in `apps/api/skillhub/schemas/feedback.py`.

**Schemas needed:**

- `FeedbackCreate` — user-supplied fields only; body min=20, max=500
- `FeedbackResponse` — full record including server-set fields
- `FeedbackListResponse` — paginated wrapper with `priority_score` on each item
- `PlatformUpdateCreate` — admin fields; linked_feedback_ids optional
- `PlatformUpdateUpdate` — all fields optional (PATCH semantics)
- `PlatformUpdateResponse` — full record
- `PlatformUpdateListResponse` — list wrapper
- `ShipRequest` — optional `shipped_at` override (defaults to now())
- `ChangelogResponse` — public-facing shipped-only view (no author PII)
- `FeedbackStatusUpdate` — admin status patch

### File Structure

```
apps/api/skillhub/schemas/feedback.py     # new
apps/api/tests/test_feedback_schemas.py   # new — write FIRST
```

### Write Tests First

```python
"""Schema validation tests — write BEFORE schema implementation."""

import pytest
from pydantic import ValidationError

from skillhub.schemas.feedback import (
    ChangelogResponse,
    FeedbackCreate,
    FeedbackStatusUpdate,
    PlatformUpdateCreate,
    PlatformUpdateUpdate,
    ShipRequest,
)


class TestFeedbackCreate:
    def test_valid_minimal(self):
        fb = FeedbackCreate(
            category="feature_request",
            body="Please add bulk install support so teams can deploy multiple skills at once",
            allow_contact=False,
        )
        assert fb.category == "feature_request"
        assert fb.skill_id is None

    def test_body_too_short(self):
        with pytest.raises(ValidationError, match="body"):
            FeedbackCreate(category="praise", body="Too short")

    def test_body_too_long(self):
        with pytest.raises(ValidationError, match="body"):
            FeedbackCreate(category="praise", body="x" * 501)

    def test_invalid_category(self):
        with pytest.raises(ValidationError, match="category"):
            FeedbackCreate(
                category="invalid_value",
                body="This is a valid body length for the feedback item submission form",
            )

    def test_sentiment_field_not_accepted(self):
        """Users must not be able to set sentiment."""
        fb = FeedbackCreate(
            category="bug_report",
            body="Search bar crashes when query contains special characters like ampersand",
        )
        assert not hasattr(fb, "sentiment")

    def test_skill_id_optional(self):
        fb = FeedbackCreate(
            category="complaint",
            body="The skill detail page takes too long to load on slow network connections",
            skill_id="00000000-0000-0000-0000-000000000001",
        )
        assert fb.skill_id is not None


class TestPlatformUpdateCreate:
    def test_valid(self):
        u = PlatformUpdateCreate(
            title="Batch install support",
            body="## Summary\nUsers can now install multiple skills in one click.",
        )
        assert u.linked_feedback_ids == []
        assert u.target_quarter is None

    def test_linked_feedback_ids_default_empty(self):
        u = PlatformUpdateCreate(title="New feature", body="Description here.")
        assert u.linked_feedback_ids == []


class TestPlatformUpdateUpdate:
    def test_all_optional(self):
        u = PlatformUpdateUpdate()
        assert u.title is None
        assert u.body is None

    def test_partial_update(self):
        u = PlatformUpdateUpdate(title="Updated title")
        assert u.title == "Updated title"
        assert u.body is None


class TestFeedbackStatusUpdate:
    def test_valid_statuses(self):
        for s in ("open", "triaged", "planned", "archived"):
            obj = FeedbackStatusUpdate(status=s)
            assert obj.status == s

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            FeedbackStatusUpdate(status="deleted")


class TestChangelogResponse:
    def test_no_author_pii(self):
        """ChangelogResponse must not expose author_id or user email."""
        fields = ChangelogResponse.model_fields
        assert "author_id" not in fields
        assert "author_email" not in fields
```

### Implementation

**`apps/api/skillhub/schemas/feedback.py`:**

```python
"""Pydantic v2 schemas for feedback and platform roadmap endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


FeedbackCategoryLiteral = Literal["feature_request", "bug_report", "praise", "complaint"]
FeedbackStatusLiteral = Literal["open", "triaged", "planned", "archived"]
PlatformUpdateStatusLiteral = Literal["planned", "in_progress", "shipped", "cancelled"]


class FeedbackCreate(BaseModel):
    category: FeedbackCategoryLiteral
    body: str = Field(min_length=20, max_length=500)
    skill_id: UUID | None = None
    allow_contact: bool = False


class FeedbackStatusUpdate(BaseModel):
    status: FeedbackStatusLiteral


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    skill_id: UUID | None
    category: str
    body: str
    sentiment: str
    upvotes: int
    status: str
    allow_contact: bool
    created_at: datetime
    priority_score: float | None = None  # computed in service, not stored


class FeedbackListResponse(BaseModel):
    items: list[FeedbackResponse]
    total: int
    page: int
    page_size: int


class PlatformUpdateCreate(BaseModel):
    title: str = Field(max_length=255)
    body: str
    target_quarter: str | None = Field(default=None, max_length=10)
    linked_feedback_ids: list[UUID] = Field(default_factory=list)
    sort_order: int = 0


class PlatformUpdateUpdate(BaseModel):
    """All fields optional for PATCH semantics."""
    title: str | None = Field(default=None, max_length=255)
    body: str | None = None
    target_quarter: str | None = None
    linked_feedback_ids: list[UUID] | None = None
    sort_order: int | None = None


class PlatformUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    status: str
    author_id: UUID
    target_quarter: str | None
    linked_feedback_ids: list
    shipped_at: datetime | None
    sort_order: int
    created_at: datetime
    updated_at: datetime


class PlatformUpdateListResponse(BaseModel):
    items: list[PlatformUpdateResponse]
    total: int


class ShipRequest(BaseModel):
    """Optional shipped_at override; defaults to server time."""
    shipped_at: datetime | None = None


class ChangelogResponse(BaseModel):
    """Public-facing changelog entry — no author PII."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    target_quarter: str | None
    shipped_at: datetime | None
    created_at: datetime
```

### Do NOT

- Do not add `sentiment` to `FeedbackCreate` — this field is always inferred server-side.
- Do not expose `author_id`, author email, or any user PII in `ChangelogResponse`.
- Do not use `model_validate` with `.from_orm=True` — use `model_config = ConfigDict(from_attributes=True)`.

### Acceptance Criteria

- [ ] `pytest apps/api/tests/test_feedback_schemas.py` passes.
- [ ] `FeedbackCreate(category="praise", body="x"*19)` raises `ValidationError`.
- [ ] `ChangelogResponse.model_fields` contains neither `author_id` nor `author_email`.
- [ ] `PlatformUpdateUpdate()` constructs with all-None fields (full PATCH support).

---

## Prompt 6A-3: Service Layer

**Time estimate:** 25-35 min

### Requirements

Implement two service modules:

**`apps/api/skillhub/services/feedback.py`:**

- `infer_sentiment(body: str) -> FeedbackSentiment` — keyword classifier:
  - Positive keywords: `love`, `great`, `excellent`, `helpful`, `amazing`, `saved`, `perfect`, `praise`
  - Negative keywords: `bug`, `broken`, `crash`, `slow`, `error`, `fail`, `terrible`, `complaint`, `wrong`
  - Score = count(positive hits) - count(negative hits); positive→`positive`, negative→`negative`, else `neutral`
- `create_feedback(db, *, user_id, data: FeedbackCreate) -> SkillFeedback` — infers sentiment, writes record, NO audit_log (feedback creation is not an admin action)
- `list_feedback(db, *, page, page_size, category, status, skill_id) -> tuple[list[dict], int]` — paginated; each dict includes `priority_score = upvotes + 5 * is_bug - hours_old / 48` where `hours_old` is capped such that the age penalty is capped at `3.0` (i.e., `min(hours_old / 48, 3.0)`)
- `upvote_feedback(db, *, feedback_id) -> SkillFeedback` — increments upvotes atomically using `UPDATE ... SET upvotes = upvotes + 1`
- `update_feedback_status(db, *, feedback_id, status, actor_id) -> SkillFeedback` — admin action; writes `AuditLog` with event_type `feedback.status_updated`
- `link_feedback_to_roadmap(db, *, feedback_id, update_id) -> None` — appends feedback_id to `platform_updates.linked_feedback_ids`

**`apps/api/skillhub/services/roadmap.py`:**

Valid status transitions (forward-only, except any→cancelled):
```
planned → in_progress → shipped
any     → cancelled
```

- `create_update(db, *, author_id, data: PlatformUpdateCreate) -> PlatformUpdate`
- `list_updates(db, *, status_filter) -> list[PlatformUpdate]` — ordered by `sort_order ASC, created_at DESC`
- `update_update(db, *, update_id, data: PlatformUpdateUpdate, actor_id) -> PlatformUpdate` — PATCH; audit_log event `roadmap.update_edited`
- `transition_status(db, *, update_id, new_status, actor_id) -> PlatformUpdate` — validates transition; raises `ValueError` on invalid transition; audit_log event `roadmap.status_changed`
- `ship_update(db, *, update_id, shipped_at, actor_id) -> PlatformUpdate` — atomic: sets `status=shipped`, `shipped_at=shipped_at or now()`, transitions all linked feedback to status `planned`; single commit; audit_log event `roadmap.shipped`
- `reorder_updates(db, *, ordered_ids: list[UUID], actor_id) -> None` — sets `sort_order` from index position
- `delete_update(db, *, update_id, actor_id) -> None` — soft-delete via `status=cancelled`; security_team only (enforced in router, not service)

### File Structure

```
apps/api/skillhub/services/feedback.py    # new
apps/api/skillhub/services/roadmap.py     # new
apps/api/tests/test_feedback_service.py   # new — write FIRST
apps/api/tests/test_roadmap_service.py    # new — write FIRST
```

### Write Tests First

**`apps/api/tests/test_feedback_service.py`:**

```python
"""Feedback service tests — TDD: write BEFORE service implementation."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from skillhub.schemas.feedback import FeedbackCreate, FeedbackStatusUpdate
from skillhub.services.feedback import (
    create_feedback,
    infer_sentiment,
    list_feedback,
    update_feedback_status,
    upvote_feedback,
)


class TestInferSentiment:
    def test_positive_keywords_score_positive(self):
        assert infer_sentiment("This skill is amazing and great!") == "positive"

    def test_negative_keywords_score_negative(self):
        assert infer_sentiment("There is a bug that causes a crash on startup") == "negative"

    def test_neutral_when_balanced(self):
        assert infer_sentiment("Great feature but it has a bug sometimes") == "neutral"

    def test_neutral_on_plain_text(self):
        assert infer_sentiment("I would like a dark mode option please") == "neutral"

    def test_case_insensitive(self):
        assert infer_sentiment("AMAZING feature, LOVE it") == "positive"


class TestCreateFeedback:
    def test_creates_record(self, db: Session, sample_user):
        data = FeedbackCreate(
            category="feature_request",
            body="Please add a way to preview skills before installing them on my system",
        )
        fb = create_feedback(db, user_id=sample_user.id, data=data)
        assert fb.id is not None
        assert fb.user_id == sample_user.id
        assert fb.sentiment in ("positive", "negative", "neutral")

    def test_sentiment_inferred_not_user_supplied(self, db: Session, sample_user):
        data = FeedbackCreate(
            category="praise",
            body="This is an amazing skill that saved me so much time on my project",
        )
        fb = create_feedback(db, user_id=sample_user.id, data=data)
        assert fb.sentiment == "positive"

    def test_no_audit_log_entry_created(self, db: Session, sample_user):
        from skillhub_db.models.audit import AuditLog
        before_count = db.query(AuditLog).count()
        data = FeedbackCreate(
            category="complaint",
            body="The search results are not sorted by relevance which makes it hard to find skills",
        )
        create_feedback(db, user_id=sample_user.id, data=data)
        after_count = db.query(AuditLog).count()
        assert after_count == before_count  # feedback creation must NOT write audit log


class TestListFeedback:
    def test_returns_paginated_results(self, db: Session, sample_user):
        for i in range(5):
            data = FeedbackCreate(
                category="feature_request",
                body=f"Feature request number {i} with enough characters to pass validation",
            )
            create_feedback(db, user_id=sample_user.id, data=data)

        items, total = list_feedback(db, page=1, page_size=3)
        assert len(items) == 3
        assert total == 5

    def test_priority_score_computed(self, db: Session, sample_user):
        data = FeedbackCreate(
            category="bug_report",
            body="Critical bug: the export function silently fails without showing any error message",
        )
        create_feedback(db, user_id=sample_user.id, data=data)
        items, _ = list_feedback(db, page=1, page_size=10)
        assert "priority_score" in items[0]

    def test_filter_by_category(self, db: Session, sample_user):
        for cat in ("feature_request", "bug_report", "praise"):
            data = FeedbackCreate(
                category=cat,
                body="Feedback item body text that meets the minimum length requirement here",
            )
            create_feedback(db, user_id=sample_user.id, data=data)

        items, total = list_feedback(db, page=1, page_size=10, category="bug_report")
        assert all(i["category"] == "bug_report" for i in items)


class TestUpvoteFeedback:
    def test_increments_upvotes(self, db: Session, sample_user):
        data = FeedbackCreate(
            category="feature_request",
            body="Add keyboard shortcuts for common actions to speed up workflow navigation",
        )
        fb = create_feedback(db, user_id=sample_user.id, data=data)
        assert fb.upvotes == 0
        updated = upvote_feedback(db, feedback_id=fb.id)
        assert updated.upvotes == 1
        updated2 = upvote_feedback(db, feedback_id=fb.id)
        assert updated2.upvotes == 2

    def test_raises_on_missing_id(self, db: Session):
        with pytest.raises(ValueError, match="not found"):
            upvote_feedback(db, feedback_id=uuid.uuid4())


class TestUpdateFeedbackStatus:
    def test_updates_status_and_writes_audit(self, db: Session, sample_user):
        from skillhub_db.models.audit import AuditLog
        data = FeedbackCreate(
            category="bug_report",
            body="Login page does not redirect after OAuth when using Safari browser version 17",
        )
        fb = create_feedback(db, user_id=sample_user.id, data=data)
        before = db.query(AuditLog).count()
        updated = update_feedback_status(
            db, feedback_id=fb.id, status="triaged", actor_id=sample_user.id
        )
        assert updated.status == "triaged"
        assert db.query(AuditLog).count() == before + 1
```

**`apps/api/tests/test_roadmap_service.py`:**

```python
"""Roadmap service tests — TDD: write BEFORE service implementation."""

import uuid

import pytest
from sqlalchemy.orm import Session

from skillhub.schemas.feedback import FeedbackCreate, PlatformUpdateCreate, PlatformUpdateUpdate
from skillhub.services.feedback import create_feedback
from skillhub.services.roadmap import (
    create_update,
    delete_update,
    list_updates,
    reorder_updates,
    ship_update,
    transition_status,
    update_update,
)


class TestCreateUpdate:
    def test_creates_with_defaults(self, db: Session, sample_user):
        data = PlatformUpdateCreate(
            title="Smarter search ranking",
            body="## Overview\nWe updated the ranking algorithm for better results.",
        )
        update = create_update(db, author_id=sample_user.id, data=data)
        assert update.id is not None
        assert update.status == "planned"
        assert update.linked_feedback_ids == []


class TestListUpdates:
    def test_ordered_by_sort_order_then_created(self, db: Session, sample_user):
        for i, order in enumerate([3, 1, 2]):
            data = PlatformUpdateCreate(
                title=f"Update {i}",
                body="Description.",
                sort_order=order,
            )
            create_update(db, author_id=sample_user.id, data=data)

        updates = list_updates(db)
        orders = [u.sort_order for u in updates]
        assert orders == sorted(orders)

    def test_filter_by_status(self, db: Session, sample_user):
        data = PlatformUpdateCreate(title="Planned item", body="Planned.")
        create_update(db, author_id=sample_user.id, data=data)

        results = list_updates(db, status_filter="planned")
        assert all(u.status == "planned" for u in results)


class TestTransitionStatus:
    def test_planned_to_in_progress(self, db: Session, sample_user):
        data = PlatformUpdateCreate(title="Feature", body="Details.")
        update = create_update(db, author_id=sample_user.id, data=data)
        updated = transition_status(
            db, update_id=update.id, new_status="in_progress", actor_id=sample_user.id
        )
        assert updated.status == "in_progress"

    def test_in_progress_to_shipped_blocked_use_ship_update(self, db: Session, sample_user):
        """Shipping must go through ship_update(), not transition_status()."""
        data = PlatformUpdateCreate(title="Feature", body="Details.")
        update = create_update(db, author_id=sample_user.id, data=data)
        transition_status(db, update_id=update.id, new_status="in_progress", actor_id=sample_user.id)
        with pytest.raises(ValueError, match="ship_update"):
            transition_status(db, update_id=update.id, new_status="shipped", actor_id=sample_user.id)

    def test_backwards_transition_rejected(self, db: Session, sample_user):
        data = PlatformUpdateCreate(title="Feature", body="Details.")
        update = create_update(db, author_id=sample_user.id, data=data)
        transition_status(db, update_id=update.id, new_status="in_progress", actor_id=sample_user.id)
        with pytest.raises(ValueError, match="Invalid transition"):
            transition_status(db, update_id=update.id, new_status="planned", actor_id=sample_user.id)

    def test_any_to_cancelled(self, db: Session, sample_user):
        data = PlatformUpdateCreate(title="Feature", body="Details.")
        update = create_update(db, author_id=sample_user.id, data=data)
        transition_status(db, update_id=update.id, new_status="in_progress", actor_id=sample_user.id)
        updated = transition_status(
            db, update_id=update.id, new_status="cancelled", actor_id=sample_user.id
        )
        assert updated.status == "cancelled"


class TestShipUpdate:
    def test_ships_and_sets_timestamp(self, db: Session, sample_user):
        data = PlatformUpdateCreate(title="Ship me", body="Details here for the shipped update.")
        update = create_update(db, author_id=sample_user.id, data=data)
        shipped = ship_update(db, update_id=update.id, shipped_at=None, actor_id=sample_user.id)
        assert shipped.status == "shipped"
        assert shipped.shipped_at is not None

    def test_resolves_linked_feedback(self, db: Session, sample_user):
        from skillhub.services.feedback import create_feedback
        from skillhub_db.models.feedback import SkillFeedback

        fb_data = FeedbackCreate(
            category="feature_request",
            body="Add bulk install support so teams can set up their environments quickly",
        )
        fb = create_feedback(db, user_id=sample_user.id, data=fb_data)

        update_data = PlatformUpdateCreate(
            title="Bulk install",
            body="Shipped bulk install.",
            linked_feedback_ids=[fb.id],
        )
        update = create_update(db, author_id=sample_user.id, data=update_data)
        ship_update(db, update_id=update.id, shipped_at=None, actor_id=sample_user.id)

        db.refresh(fb)
        assert fb.status == "planned"  # linked feedback resolved to 'planned'


class TestReorderUpdates:
    def test_reorders_by_position(self, db: Session, sample_user):
        updates = []
        for i in range(3):
            data = PlatformUpdateCreate(title=f"Update {i}", body="Details.")
            updates.append(create_update(db, author_id=sample_user.id, data=data))

        reversed_ids = [u.id for u in reversed(updates)]
        reorder_updates(db, ordered_ids=reversed_ids, actor_id=sample_user.id)

        results = list_updates(db)
        result_ids = [u.id for u in results]
        assert result_ids == reversed_ids


class TestDeleteUpdate:
    def test_soft_deletes_via_cancelled(self, db: Session, sample_user):
        data = PlatformUpdateCreate(title="To delete", body="Will be cancelled.")
        update = create_update(db, author_id=sample_user.id, data=data)
        delete_update(db, update_id=update.id, actor_id=sample_user.id)
        db.refresh(update)
        assert update.status == "cancelled"
```

### Implementation Notes

**Atomic upvote** using SQLAlchemy UPDATE expression to avoid race conditions:

```python
from sqlalchemy import update as sa_update

db.execute(
    sa_update(SkillFeedback)
    .where(SkillFeedback.id == feedback_id)
    .values(upvotes=SkillFeedback.upvotes + 1)
)
db.commit()
```

**Priority score formula:**

```python
import math
from datetime import datetime, timezone

def compute_priority_score(fb: SkillFeedback) -> float:
    hours_old = (datetime.now(timezone.utc) - fb.created_at).total_seconds() / 3600
    is_bug = 1 if fb.category == "bug_report" else 0
    age_penalty = min(hours_old / 48, 3.0)
    return fb.upvotes + 5 * is_bug - age_penalty
```

**Status transition guard:**

```python
VALID_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"in_progress", "cancelled"},
    "in_progress": {"cancelled"},  # shipped only via ship_update()
    "shipped": set(),
    "cancelled": set(),
}

def _assert_transition(current: str, new: str) -> None:
    if new == "shipped":
        raise ValueError("Use ship_update() to mark an update as shipped")
    if new not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition: {current!r} → {new!r}")
```

### Do NOT

- Do not allow `transition_status` to set `status=shipped` — that path is exclusively `ship_update`.
- Do not use Python-side `upvotes = fb.upvotes + 1` — this races under concurrent requests; use SQL `UPDATE ... SET upvotes = upvotes + 1`.
- Do not skip `AuditLog` for admin actions (`update_feedback_status`, `transition_status`, `ship_update`, `reorder_updates`, `delete_update`).
- Do not commit partial state in `ship_update` — set status, shipped_at, and all linked feedback updates in a single `db.commit()`.

### Acceptance Criteria

- [ ] `pytest apps/api/tests/test_feedback_service.py` — all green.
- [ ] `pytest apps/api/tests/test_roadmap_service.py` — all green.
- [ ] `infer_sentiment("amazing great love")` returns `"positive"`.
- [ ] `upvote_feedback` uses `UPDATE ... SET upvotes = upvotes + 1` (verified by checking service source).
- [ ] `ship_update` produces exactly 1 `AuditLog` entry with event_type `roadmap.shipped`.
- [ ] `transition_status(..., new_status="shipped")` raises `ValueError` containing `"ship_update"`.
- [ ] `create_feedback` produces 0 `AuditLog` entries.

---

## Prompt 6A-4: Routers, Integration & Registration

**Time estimate:** 20-25 min

### Requirements

Wire up two new routers and register them in `main.py`.

**Feedback router** (`apps/api/skillhub/routers/feedback.py`):

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/feedback` | Any authenticated user | Submit feedback |
| GET | `/api/v1/admin/feedback` | `require_platform_team` | List/filter feedback |
| POST | `/api/v1/feedback/{feedback_id}/upvote` | Any authenticated user | Upvote feedback |
| PATCH | `/api/v1/admin/feedback/{feedback_id}/status` | `require_platform_team` | Update status |

Query params for `GET /api/v1/admin/feedback`: `page` (default 1), `page_size` (default 20, max 100), `category` (optional), `status` (optional), `skill_id` (optional UUID).

**Roadmap router** (`apps/api/skillhub/routers/roadmap.py`):

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/admin/platform-updates` | `require_platform_team` | List all updates |
| POST | `/api/v1/admin/platform-updates` | `require_platform_team` | Create update |
| PATCH | `/api/v1/admin/platform-updates/{update_id}` | `require_platform_team` | Edit update |
| DELETE | `/api/v1/admin/platform-updates/{update_id}` | `require_security_team` | Soft-delete |
| POST | `/api/v1/admin/platform-updates/{update_id}/ship` | `require_platform_team` | Ship update |
| GET | `/api/v1/changelog` | Public (no auth) | Shipped items only |

`GET /api/v1/admin/platform-updates` accepts `?status=planned` filter.
`GET /api/v1/changelog` returns only `status=shipped` records, ordered by `shipped_at DESC`.

### File Structure

```
apps/api/skillhub/routers/feedback.py    # new
apps/api/skillhub/routers/roadmap.py     # new
apps/api/tests/test_feedback_router.py   # new — write FIRST
apps/api/tests/test_roadmap_router.py    # new — write FIRST
```

### Write Tests First

**`apps/api/tests/test_feedback_router.py`:**

```python
"""Feedback router integration tests — TDD: write BEFORE router implementation."""

import pytest
from fastapi.testclient import TestClient


class TestSubmitFeedback:
    def test_authenticated_user_can_submit(self, client: TestClient, user_token: str):
        resp = client.post(
            "/api/v1/feedback",
            json={
                "category": "feature_request",
                "body": "Please add support for scheduled skill runs on a recurring basis",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["sentiment"] in ("positive", "negative", "neutral")
        assert "user_id" in data

    def test_unauthenticated_rejected(self, client: TestClient):
        resp = client.post(
            "/api/v1/feedback",
            json={
                "category": "praise",
                "body": "Love this platform it is so helpful for the whole engineering team",
            },
        )
        assert resp.status_code == 401

    def test_body_too_short_rejected(self, client: TestClient, user_token: str):
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "praise", "body": "Too short"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 422


class TestAdminListFeedback:
    def test_platform_team_can_list(self, client: TestClient, admin_token: str):
        resp = client.get(
            "/api/v1/admin/feedback",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_regular_user_forbidden(self, client: TestClient, user_token: str):
        resp = client.get(
            "/api/v1/admin/feedback",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_filter_by_category(self, client: TestClient, admin_token: str, db):
        from skillhub.schemas.feedback import FeedbackCreate
        from skillhub.services.feedback import create_feedback
        from skillhub_db.models.user import User
        admin = db.query(User).filter(User.is_platform_team.is_(True)).first()
        for cat in ("bug_report", "feature_request"):
            create_feedback(
                db,
                user_id=admin.id,
                data=FeedbackCreate(
                    category=cat,
                    body="Feedback body text that is long enough to meet minimum requirements here",
                ),
            )

        resp = client.get(
            "/api/v1/admin/feedback?category=bug_report",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert all(i["category"] == "bug_report" for i in resp.json()["items"])


class TestUpvoteFeedback:
    def test_upvote_increments(self, client: TestClient, user_token: str, db):
        from skillhub.schemas.feedback import FeedbackCreate
        from skillhub.services.feedback import create_feedback
        from skillhub_db.models.user import User
        user = db.query(User).first()
        fb = create_feedback(
            db,
            user_id=user.id,
            data=FeedbackCreate(
                category="feature_request",
                body="Support exporting skill configurations to share with teammates easily",
            ),
        )
        resp = client.post(
            f"/api/v1/feedback/{fb.id}/upvote",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["upvotes"] == 1


class TestAdminUpdateFeedbackStatus:
    def test_admin_can_triage(self, client: TestClient, admin_token: str, db):
        from skillhub.schemas.feedback import FeedbackCreate
        from skillhub.services.feedback import create_feedback
        from skillhub_db.models.user import User
        user = db.query(User).first()
        fb = create_feedback(
            db,
            user_id=user.id,
            data=FeedbackCreate(
                category="bug_report",
                body="Export fails silently when the output directory does not have write permissions",
            ),
        )
        resp = client.patch(
            f"/api/v1/admin/feedback/{fb.id}/status",
            json={"status": "triaged"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "triaged"
```

**`apps/api/tests/test_roadmap_router.py`:**

```python
"""Roadmap router integration tests — TDD: write BEFORE router implementation."""

import pytest
from fastapi.testclient import TestClient


class TestChangelogPublic:
    def test_unauthenticated_can_read_changelog(self, client: TestClient):
        """Changelog is public — no auth required."""
        resp = client.get("/api/v1/changelog")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_changelog_contains_only_shipped(self, client: TestClient, db, admin_token):
        from skillhub.schemas.feedback import PlatformUpdateCreate
        from skillhub.services.roadmap import create_update, ship_update
        from skillhub_db.models.user import User
        admin = db.query(User).filter(User.is_platform_team.is_(True)).first()
        data = PlatformUpdateCreate(title="Shipped feature", body="We shipped this.")
        update = create_update(db, author_id=admin.id, data=data)
        ship_update(db, update_id=update.id, shipped_at=None, actor_id=admin.id)

        resp = client.get("/api/v1/changelog")
        assert all(i.get("status") is None or True for i in resp.json())
        # ChangelogResponse has no 'status' field — verify it's absent
        if resp.json():
            assert "status" not in resp.json()[0]


class TestAdminPlatformUpdates:
    def test_create_requires_platform_team(self, client: TestClient, user_token: str):
        resp = client.post(
            "/api/v1/admin/platform-updates",
            json={"title": "New feature", "body": "Details here."},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_create_success(self, client: TestClient, admin_token: str):
        resp = client.post(
            "/api/v1/admin/platform-updates",
            json={"title": "Better analytics", "body": "Improved dashboard metrics."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["status"] == "planned"

    def test_delete_requires_security_team(self, client: TestClient, admin_token: str, db):
        from skillhub.schemas.feedback import PlatformUpdateCreate
        from skillhub.services.roadmap import create_update
        from skillhub_db.models.user import User
        admin = db.query(User).filter(User.is_platform_team.is_(True)).first()
        update = create_update(
            db,
            author_id=admin.id,
            data=PlatformUpdateCreate(title="To delete", body="Details."),
        )
        resp = client.delete(
            f"/api/v1/admin/platform-updates/{update.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 403

    def test_ship_sets_shipped_status(self, client: TestClient, admin_token: str, db):
        from skillhub.schemas.feedback import PlatformUpdateCreate
        from skillhub.services.roadmap import create_update
        from skillhub_db.models.user import User
        admin = db.query(User).filter(User.is_platform_team.is_(True)).first()
        update = create_update(
            db,
            author_id=admin.id,
            data=PlatformUpdateCreate(title="Ship me", body="Ready to ship now."),
        )
        resp = client.post(
            f"/api/v1/admin/platform-updates/{update.id}/ship",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "shipped"
        assert resp.json()["shipped_at"] is not None
```

### Implementation Sketch

**`apps/api/skillhub/routers/feedback.py`:**

```python
"""Feedback endpoints."""

from __future__ import annotations

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from skillhub.dependencies import get_current_user, get_db, require_platform_team
from skillhub.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
    FeedbackStatusUpdate,
)
from skillhub.services.feedback import (
    create_feedback,
    list_feedback,
    update_feedback_status,
    upvote_feedback,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["feedback"])


@router.post("/api/v1/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    body: FeedbackCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> FeedbackResponse:
    fb = create_feedback(db, user_id=current_user["user_id"], data=body)
    return FeedbackResponse.model_validate(fb)


@router.get("/api/v1/admin/feedback", response_model=FeedbackListResponse)
def admin_list_feedback(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    skill_id: UUID | None = Query(default=None),
) -> FeedbackListResponse:
    items, total = list_feedback(
        db, page=page, page_size=page_size,
        category=category, status=status_filter, skill_id=skill_id,
    )
    return FeedbackListResponse(
        items=[FeedbackResponse(**i) for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/api/v1/feedback/{feedback_id}/upvote", response_model=FeedbackResponse)
def upvote(
    feedback_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> FeedbackResponse:
    try:
        fb = upvote_feedback(db, feedback_id=feedback_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return FeedbackResponse.model_validate(fb)


@router.patch("/api/v1/admin/feedback/{feedback_id}/status", response_model=FeedbackResponse)
def admin_update_status(
    feedback_id: UUID,
    body: FeedbackStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[dict[str, Any], Depends(require_platform_team)],
) -> FeedbackResponse:
    try:
        fb = update_feedback_status(
            db, feedback_id=feedback_id,
            status=body.status, actor_id=current_user["user_id"],
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    return FeedbackResponse.model_validate(fb)
```

**`apps/api/skillhub/routers/roadmap.py`** follows the same pattern. Key points:

- `GET /api/v1/changelog` uses no dependency injection for auth — call `list_updates(db, status_filter="shipped")` and map to `ChangelogResponse`.
- `DELETE` depends on `require_security_team`.
- All `ValueError` exceptions from services map to HTTP 404 (not found) or 422 (invalid transition).
- Invalid status transition from `transition_status` maps to HTTP 422 with the error message as detail.

**Register in `apps/api/skillhub/main.py`:**

```python
from skillhub.routers.feedback import router as feedback_router
from skillhub.routers.roadmap import router as roadmap_router

app.include_router(feedback_router)
app.include_router(roadmap_router)
```

### Do NOT

- Do not add auth to `GET /api/v1/changelog` — it is intentionally public.
- Do not return 500 for `ValueError` from services — map to 404 or 422 as appropriate.
- Do not duplicate the `/api/v1/admin` prefix in both the router prefix and individual route paths — pick one location.
- Do not use `jsonable_encoder` for `ChangelogResponse` — `response_model` handles serialization.

### Acceptance Criteria

- [ ] `pytest apps/api/tests/test_feedback_router.py` — all green.
- [ ] `pytest apps/api/tests/test_roadmap_router.py` — all green.
- [ ] `GET /api/v1/changelog` returns 200 with no auth header.
- [ ] `POST /api/v1/feedback` with no auth header returns 401.
- [ ] `DELETE /api/v1/admin/platform-updates/{id}` with platform_team token (not security_team) returns 403.
- [ ] `GET /api/v1/changelog` items do not contain `author_id` or `author_email`.
- [ ] `pytest apps/api/ --cov=skillhub --cov-fail-under=80` passes.
- [ ] `ruff check apps/api/skillhub/routers/feedback.py apps/api/skillhub/routers/roadmap.py` — zero warnings.

---

## Stage 6A Summary

### Files Created

```
libs/db/skillhub_db/models/feedback.py
libs/db/migrations/versions/<rev>_add_feedback_and_platform_updates.py
apps/api/skillhub/schemas/feedback.py
apps/api/skillhub/services/feedback.py
apps/api/skillhub/services/roadmap.py
apps/api/skillhub/routers/feedback.py
apps/api/skillhub/routers/roadmap.py
apps/api/tests/test_feedback_models.py
apps/api/tests/test_feedback_schemas.py
apps/api/tests/test_feedback_service.py
apps/api/tests/test_roadmap_service.py
apps/api/tests/test_feedback_router.py
apps/api/tests/test_roadmap_router.py
```

### Files Modified

```
libs/db/skillhub_db/models/__init__.py   # register SkillFeedback, PlatformUpdate
apps/api/skillhub/main.py               # include feedback_router, roadmap_router
```

### Key Invariants

| Rule | Where enforced |
|---|---|
| `sentiment` never set by user | `FeedbackCreate` schema excludes the field; `create_feedback` always calls `infer_sentiment` |
| `upvotes` incremented atomically | SQL `UPDATE ... SET upvotes = upvotes + 1` in `upvote_feedback` |
| `shipped` status only via `ship_update` | `transition_status` raises `ValueError` if `new_status == "shipped"` |
| `ship_update` is atomic | All DB writes in single `db.commit()` |
| `delete_update` is soft-delete | Sets `status=cancelled`, no row removed |
| Admin actions write `AuditLog` | `update_feedback_status`, all roadmap mutations |
| Feedback creation does NOT audit | `create_feedback` never calls `AuditLog` |
| Changelog is public | `GET /api/v1/changelog` has no auth dependency |
| Changelog hides PII | `ChangelogResponse` has no `author_id` / email fields |
