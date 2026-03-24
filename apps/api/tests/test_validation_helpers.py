"""Tests for the validation module — validated_body, validated_query, json_response, DivisionRestrictedError."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Flask, jsonify
from pydantic import BaseModel, Field

from skillhub_flask.validation import (
    DivisionRestrictedError,
    json_response,
    validated_body,
    validated_query,
)


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class SampleBody(BaseModel):
    name: str = Field(..., min_length=1)
    age: int


class SampleQuery(BaseModel):
    page: int = 1
    per_page: int = 20
    active: bool = True
    tags: list[str] = []


class SampleResponse(BaseModel):
    id: str
    value: float


# ---------------------------------------------------------------------------
# Helper: mini Flask app for testing decorators
# ---------------------------------------------------------------------------


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/test-body", methods=["POST"])
    @validated_body(SampleBody)
    def body_endpoint(body: SampleBody) -> tuple:
        return jsonify({"name": body.name, "age": body.age}), 200

    @app.route("/test-query", methods=["GET"])
    @validated_query(SampleQuery)
    def query_endpoint(query: SampleQuery) -> tuple:
        return jsonify({
            "page": query.page,
            "per_page": query.per_page,
            "active": query.active,
            "tags": query.tags,
        }), 200

    return app


# ---------------------------------------------------------------------------
# validated_body
# ---------------------------------------------------------------------------


class TestValidatedBody:
    """Test the validated_body decorator."""

    def test_valid_json_passes(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.post("/test-body", json={"name": "Alice", "age": 30})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["name"] == "Alice"
            assert data["age"] == 30

    def test_invalid_json_returns_422_with_detail_array(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.post("/test-body", json={"name": "", "age": "not-a-number"})
            assert resp.status_code == 422
            data = resp.get_json()
            assert "detail" in data
            assert isinstance(data["detail"], list)
            assert len(data["detail"]) > 0

    def test_missing_required_fields_returns_422(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.post("/test-body", json={})
            assert resp.status_code == 422
            data = resp.get_json()
            assert isinstance(data["detail"], list)

    def test_empty_body_returns_422(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.post(
                "/test-body",
                data="{}",
                content_type="application/json",
            )
            assert resp.status_code == 422


# ---------------------------------------------------------------------------
# validated_query
# ---------------------------------------------------------------------------


class TestValidatedQuery:
    """Test the validated_query decorator."""

    def test_defaults_used_when_no_params(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.get("/test-query")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["page"] == 1
            assert data["per_page"] == 20
            assert data["active"] is True
            assert data["tags"] == []

    def test_int_coercion_from_string(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.get("/test-query?page=3&per_page=50")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["page"] == 3
            assert data["per_page"] == 50

    def test_bool_coercion_from_string(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.get("/test-query?active=false")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["active"] is False

    def test_list_handling_multiple_values(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.get("/test-query?tags=python&tags=flask")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["tags"] == ["python", "flask"]

    def test_list_handling_single_value(self) -> None:
        app = _make_app()
        with app.test_client() as client:
            resp = client.get("/test-query?tags=python")
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["tags"] == ["python"]


# ---------------------------------------------------------------------------
# DivisionRestrictedError
# ---------------------------------------------------------------------------


class TestDivisionRestrictedError:
    """Verify DivisionRestrictedError is a proper exception class."""

    def test_is_exception_subclass(self) -> None:
        assert issubclass(DivisionRestrictedError, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(DivisionRestrictedError, match="no access"):
            raise DivisionRestrictedError("no access")

    def test_message_preserved(self) -> None:
        err = DivisionRestrictedError("Division X restricted")
        assert str(err) == "Division X restricted"

    def test_inherits_from_exception_not_base(self) -> None:
        """Verify it can be caught as a generic Exception."""
        try:
            raise DivisionRestrictedError("test")
        except Exception as e:
            assert isinstance(e, DivisionRestrictedError)


# ---------------------------------------------------------------------------
# json_response
# ---------------------------------------------------------------------------


class TestJsonResponse:
    """Test the json_response helper for serialization."""

    def test_pydantic_model_serialization(self) -> None:
        app = Flask(__name__)
        with app.app_context():
            model = SampleResponse(id="abc-123", value=3.14)
            resp, status = json_response(model, status=200)
            assert status == 200
            data = resp.get_json()
            assert data["id"] == "abc-123"
            assert data["value"] == 3.14

    def test_list_of_pydantic_models(self) -> None:
        app = Flask(__name__)
        with app.app_context():
            models = [
                SampleResponse(id="a", value=1.0),
                SampleResponse(id="b", value=2.0),
            ]
            resp, status = json_response(models, status=200)
            assert status == 200
            data = resp.get_json()
            assert isinstance(data, list)
            assert len(data) == 2
            assert data[0]["id"] == "a"

    def test_dict_passthrough(self) -> None:
        app = Flask(__name__)
        with app.app_context():
            raw = {"key": "value", "count": 42}
            resp, status = json_response(raw, status=201)
            assert status == 201
            data = resp.get_json()
            assert data["key"] == "value"
            assert data["count"] == 42

    def test_custom_status_code(self) -> None:
        app = Flask(__name__)
        with app.app_context():
            resp, status = json_response({"ok": True}, status=404)
            assert status == 404

    def test_empty_list_passthrough(self) -> None:
        """An empty list should pass through as dict (falls to last branch)."""
        app = Flask(__name__)
        with app.app_context():
            resp, status = json_response([], status=200)
            assert status == 200
            data = resp.get_json()
            assert data == []
