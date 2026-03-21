"""Feature flags service."""

from __future__ import annotations

import logging

from skillhub_db.models.flags import FeatureFlag
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_flags(db: Session, *, user_division: str | None = None) -> dict[str, bool]:
    """Return all flags with division overrides applied."""
    flags = db.query(FeatureFlag).all()
    result: dict[str, bool] = {}
    for flag in flags:
        effective = flag.enabled
        if user_division and flag.division_overrides:
            if user_division in flag.division_overrides:
                effective = bool(flag.division_overrides[user_division])
        result[flag.key] = effective
    return result
