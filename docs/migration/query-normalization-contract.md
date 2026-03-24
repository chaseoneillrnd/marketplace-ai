# Query Parameter Normalization Contract

**Date:** 2026-03-23
**Status:** Accepted
**Purpose:** Define exactly how Flask's `MultiDict` is converted to Python types before Pydantic validation, ensuring behavioral parity with FastAPI's parameter pipeline.

## Problem

FastAPI coerces query string parameters automatically before Pydantic sees them:
- `"42"` → `int(42)`
- `"true"` → `bool(True)`
- `?divisions=a&divisions=b` → `list["a", "b"]`
- `?verified=1` → `bool(True)`

Flask gives raw strings via `request.args` (a Werkzeug `MultiDict`). Without explicit normalization, Pydantic v2 in strict mode rejects string-typed integers, and in lax mode may coerce differently than FastAPI.

## Contract

### Rule 1: Use Pydantic v2 in lax mode (default) for query params

Do NOT set `model_config = ConfigDict(strict=True)` on query param models. Lax mode handles `"42"` → `int` and `"true"` → `bool` coercion that matches FastAPI behavior.

### Rule 2: Use `request.args.to_dict(flat=False)` as the input

`flat=False` returns `{"key": ["value1", "value2"]}` for repeated keys. Pydantic v2 coerces `["42"]` to `42` for `int` fields and keeps `["a", "b"]` for `list[str]` fields.

```python
raw = request.args.to_dict(flat=False)
# {"page": ["1"], "divisions": ["eng", "product"], "verified": ["true"]}
```

### Rule 3: Single-value fields receive a list; Pydantic handles unwrapping

For a field typed as `int`, Pydantic v2 lax mode coerces `["1"]` → `1`. This is correct behavior.

For a field typed as `str | None` with default `None`, if the key is absent from the dict, Pydantic uses the default. If present as `[""]`, Pydantic coerces to `""`. To treat empty string as None:

```python
@field_validator("q", mode="before")
@classmethod
def empty_string_to_none(cls, v):
    if isinstance(v, list) and len(v) == 1 and v[0] == "":
        return None
    if isinstance(v, list) and len(v) == 1:
        return v[0]
    return v
```

### Rule 4: Boolean coercion must match FastAPI exactly

FastAPI accepts these as `True`: `"true"`, `"True"`, `"1"`, `"on"`, `"yes"`
FastAPI accepts these as `False`: `"false"`, `"False"`, `"0"`, `"off"`, `"no"`

Pydantic v2 lax mode accepts: `"true"`, `"True"`, `"1"`, `"false"`, `"False"`, `"0"`
Pydantic v2 rejects: `"on"`, `"off"`, `"yes"`, `"no"`

**Gap:** FastAPI accepts `"yes"`, `"on"` — Pydantic v2 does not.

**Decision:** Accept the Pydantic v2 behavior. The current frontend sends `"true"`/`"false"` only. Document that `"yes"`/`"on"` are not supported. If parity is strictly required, add a `@field_validator` for bool fields.

### Rule 5: List fields use `list[str]` typing

For `divisions: list[str] = []`, `request.args.to_dict(flat=False)` correctly returns `{"divisions": ["a", "b"]}` which Pydantic validates as `list[str]`.

If the key is absent, Pydantic uses the default `[]`.

### Rule 6: Enum fields receive string values

For `sort: SortOption = SortOption.TRENDING`, the raw value is `["trending"]`. Pydantic coerces `["trending"]` to the enum value. Invalid values raise `ValidationError` → 422.

### Rule 7: ge/le/gt/lt constraints via Field()

```python
page: int = Field(default=1, ge=1)
per_page: int = Field(default=20, ge=1, le=100)
days: int = Field(default=30, ge=1, le=365)
limit: int = Field(default=10, ge=1, le=50)
```

Pydantic enforces these after coercion. ValidationError → 422.

### Rule 8: datetime fields use ISO 8601 parsing

For `date_from: datetime | None = None`, the raw string `"2026-01-01T00:00:00Z"` is coerced by Pydantic's datetime validator. Invalid formats raise ValidationError → 422.

## Implementation

### The `validated_query()` decorator

```python
from functools import wraps
from flask import request
from pydantic import BaseModel, ValidationError

def validated_query(model_cls: type[BaseModel]):
    """Validate query parameters using a Pydantic model.

    Normalizes Flask's MultiDict to a dict suitable for Pydantic v2 lax mode.
    Returns 422 with FastAPI-compatible error format on validation failure.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            raw = request.args.to_dict(flat=False)
            # Unwrap single-element lists for non-list fields
            hints = model_cls.model_fields
            normalized = {}
            for key, values in raw.items():
                if key in hints:
                    field = hints[key]
                    # If the field annotation is list-like, keep as list
                    origin = getattr(field.annotation, "__origin__", None)
                    if origin is list:
                        normalized[key] = values
                    elif len(values) == 1:
                        normalized[key] = values[0]
                    else:
                        normalized[key] = values[0]  # Take first for non-list
                else:
                    normalized[key] = values[0] if len(values) == 1 else values
            try:
                params = model_cls.model_validate(normalized)
            except ValidationError as exc:
                return {"detail": exc.errors(include_url=False)}, 422
            return fn(*args, query=params, **kwargs)
        return wrapper
    return decorator
```

### The `validated_body()` decorator

```python
def validated_body(model_cls: type[BaseModel]):
    """Validate JSON request body using a Pydantic model.

    Returns 422 with FastAPI-compatible error format on validation failure.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                body = model_cls.model_validate(request.get_json(force=True) or {})
            except ValidationError as exc:
                return {"detail": exc.errors(include_url=False)}, 422
            return fn(*args, body=body, **kwargs)
        return wrapper
    return decorator
```

## Parity Test Matrix

These tests must pass against BOTH FastAPI and Flask to confirm behavioral equivalence:

```python
@pytest.mark.parametrize("param,value,expected_status", [
    # Int coercion
    ("page", "1", 200),
    ("page", "0", 422),      # ge=1
    ("page", "abc", 422),
    ("per_page", "101", 422), # le=100

    # Bool coercion
    ("verified", "true", 200),
    ("verified", "false", 200),
    ("verified", "1", 200),
    ("verified", "0", 200),
    ("verified", "True", 200),
    ("verified", "yes", 422),  # Divergence: FastAPI accepts, Flask/Pydantic rejects

    # Enum coercion
    ("sort", "trending", 200),
    ("sort", "invalid", 422),

    # Missing/empty
    ("q", "", 200),           # Empty string → None
    ("q", None, 200),         # Absent → None
])
```
