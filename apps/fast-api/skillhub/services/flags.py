"""Feature flags service."""

from __future__ import annotations

import logging
from typing import Any

from opentelemetry import trace
from skillhub_db.models.flags import FeatureFlag
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
tracer = trace.get_tracer("skillhub.services.flags")


def get_flags(db: Session, *, user_division: str | None = None) -> dict[str, bool]:
    """Return all flags with division overrides applied."""
    with tracer.start_as_current_span("service.flags.get_flags") as span:
        span.set_attribute("flags.user_division", user_division or "")

        flags = db.query(FeatureFlag).all()
        result: dict[str, bool] = {}
        for flag in flags:
            effective = flag.enabled
            if user_division and flag.division_overrides:
                if user_division in flag.division_overrides:
                    effective = bool(flag.division_overrides[user_division])
            result[flag.key] = effective

        span.set_attribute("flags.count", len(result))
        return result


def create_flag(
    db: Session,
    key: str,
    *,
    enabled: bool = True,
    description: str | None = None,
    division_overrides: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Create a new feature flag. Raises ValueError if key already exists."""
    existing = db.query(FeatureFlag).filter(FeatureFlag.key == key).first()
    if existing:
        raise ValueError(f"Flag '{key}' already exists")

    flag = FeatureFlag(
        key=key,
        enabled=enabled,
        description=description,
        division_overrides=division_overrides,
    )
    db.add(flag)
    db.commit()
    db.refresh(flag)

    return _flag_to_dict(flag)


def update_flag(
    db: Session,
    key: str,
    *,
    enabled: bool | None = None,
    description: str | None = None,
    division_overrides: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Update an existing feature flag. Raises ValueError if not found."""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == key).first()
    if not flag:
        raise ValueError(f"Flag '{key}' not found")

    if enabled is not None:
        flag.enabled = enabled
    if description is not None:
        flag.description = description
    if division_overrides is not None:
        flag.division_overrides = division_overrides

    db.commit()
    db.refresh(flag)

    return _flag_to_dict(flag)


def delete_flag(db: Session, key: str) -> None:
    """Delete a feature flag. Raises ValueError if not found."""
    flag = db.query(FeatureFlag).filter(FeatureFlag.key == key).first()
    if not flag:
        raise ValueError(f"Flag '{key}' not found")

    db.delete(flag)
    db.commit()


def _flag_to_dict(flag: FeatureFlag) -> dict[str, Any]:
    """Convert FeatureFlag ORM object to dict."""
    return {
        "key": flag.key,
        "enabled": flag.enabled,
        "description": flag.description,
        "division_overrides": flag.division_overrides,
    }
