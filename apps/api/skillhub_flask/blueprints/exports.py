"""Export endpoints — admin only.

Bug fixes applied during Flask migration:
- Bug #1: Accept JSON body {scope, format, start_date?, end_date?} NOT query params
- Bug #2: Return "download_url" NOT "file_path" in GET response
- Bug #3: Return status "pending" NOT "queued" in responses
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from flask import Blueprint, g, jsonify, request
from pydantic import BaseModel

from skillhub_flask.db import get_db

from skillhub.services.exports import get_export_status, request_export, run_export_sync

logger = logging.getLogger(__name__)

bp = Blueprint("exports", __name__)


class ExportRequestBody(BaseModel):
    """Request body for creating an export job.

    Bug #1 fix: This is accepted as JSON body, not query params.
    """

    scope: str = "installs"
    format: str = "csv"
    start_date: str | None = None
    end_date: str | None = None


@bp.before_request
def _enforce_platform_team() -> Any:
    """All export routes require platform_team."""
    user = getattr(g, "current_user", None)
    if not user or not user.get("is_platform_team"):
        return jsonify({"detail": "Platform team access required"}), 403
    return None


def _fix_status(data: dict[str, Any]) -> dict[str, Any]:
    """Bug #3 fix: Normalize status 'queued' to 'pending'."""
    if data.get("status") == "queued":
        data["status"] = "pending"
    return data


def _fix_download_url(data: dict[str, Any]) -> dict[str, Any]:
    """Bug #2 fix: Rename 'file_path' to 'download_url' in response."""
    if "file_path" in data:
        data["download_url"] = data.pop("file_path")
    return data


@bp.route("/api/v1/admin/exports", methods=["POST"])
def create_export() -> tuple:
    """Request a new data export job.

    Bug #1: Accepts JSON body with {scope, format, start_date?, end_date?}.
    Bug #3: Returns status 'pending' instead of 'queued'.
    """
    db = get_db()
    body = ExportRequestBody.model_validate(request.get_json(force=True))

    try:
        result = request_export(
            db,
            user_id=UUID(g.current_user["user_id"]),
            scope=body.scope,
            format=body.format,
            filters={
                k: v
                for k, v in {
                    "start_date": body.start_date,
                    "end_date": body.end_date,
                }.items()
                if v is not None
            },
        )
    except ValueError as e:
        return jsonify({"detail": str(e)}), 429

    # Run synchronously so the job is complete before we respond.
    run_export_sync(db, UUID(result["id"]))

    # Re-fetch updated status so response reflects completed state.
    updated = get_export_status(db, UUID(result["id"]))
    if updated:
        result = updated

    result = _fix_status(result)
    result = _fix_download_url(result)
    return jsonify(result), 201


@bp.route("/api/v1/admin/exports/<job_id>", methods=["GET"])
def export_status(job_id: str) -> tuple:
    """Get the status of an export job.

    Bug #2: Returns 'download_url' instead of 'file_path'.
    Bug #3: Returns status 'pending' instead of 'queued'.
    """
    db = get_db()
    result = get_export_status(db, UUID(job_id))
    if not result:
        return jsonify({"detail": "Export job not found"}), 404

    result = _fix_status(result)
    result = _fix_download_url(result)
    return jsonify(result), 200
