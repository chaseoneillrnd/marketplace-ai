"""Request validation helpers for Flask using Pydantic v2.

Provides validated_query() and validated_body() decorators that normalize
Flask's request data for Pydantic validation and return 422 errors in
a format compatible with the frontend.
"""

from __future__ import annotations

import functools
from typing import Any

from flask import jsonify, request
from pydantic import BaseModel, ValidationError


class DivisionRestrictedError(Exception):
    """Raised when a user's division does not have access to a resource."""

    pass


def validated_body(model_cls: type[BaseModel]) -> Any:
    """Decorator that validates JSON request body using a Pydantic model.

    Returns 422 with structured error format on validation failure.
    """

    def decorator(fn: Any) -> Any:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                body = model_cls.model_validate(request.get_json(force=True) or {})
            except ValidationError as exc:
                return jsonify({"detail": exc.errors(include_url=False)}), 422
            return fn(*args, body=body, **kwargs)

        return wrapper

    return decorator


def validated_query(model_cls: type[BaseModel]) -> Any:
    """Decorator that validates query parameters using a Pydantic model.

    Normalizes Flask's MultiDict to a dict suitable for Pydantic v2 lax mode.
    Returns 422 with structured error format on validation failure.
    """

    def decorator(fn: Any) -> Any:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            raw = request.args.to_dict(flat=False)
            hints = model_cls.model_fields
            normalized: dict[str, Any] = {}

            for key, values in raw.items():
                if key in hints:
                    field_info = hints[key]
                    origin = getattr(field_info.annotation, "__origin__", None)
                    if origin is list:
                        normalized[key] = values
                    elif len(values) == 1:
                        normalized[key] = values[0]
                    else:
                        normalized[key] = values[0]
                else:
                    normalized[key] = values[0] if len(values) == 1 else values

            try:
                params = model_cls.model_validate(normalized)
            except ValidationError as exc:
                return jsonify({"detail": exc.errors(include_url=False)}), 422

            return fn(*args, query=params, **kwargs)

        return wrapper

    return decorator


def json_response(data: Any, status: int = 200) -> tuple[Any, int]:
    """Serialize a Pydantic model or dict to a JSON response.

    Uses model_dump(mode="json") for Pydantic models to handle
    Decimal, UUID, datetime serialization correctly.
    """
    if isinstance(data, BaseModel):
        return jsonify(data.model_dump(mode="json")), status
    if isinstance(data, list) and data and isinstance(data[0], BaseModel):
        return jsonify([item.model_dump(mode="json") for item in data]), status
    return jsonify(data), status
