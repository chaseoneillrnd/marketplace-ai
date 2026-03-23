---
name: api-test-writer
description: Use when writing API tests in apps/api/tests/
---

# API Test Writer

## Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from skillhub.main import create_app

@pytest.fixture
def client(db_session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)

@pytest.fixture
def auth_headers():
    token = create_test_jwt(user_id="test-uuid", division="engineering-org")
    return {"Authorization": f"Bearer {token}"}
```

## Test Patterns

```python
def test_list_skills(client, auth_headers):
    response = client.get("/api/v1/skills", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_unauthorized_returns_401(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_division_enforcement(client, auth_headers_wrong_division):
    response = client.post("/api/v1/skills/restricted-skill/install",
                          headers=auth_headers_wrong_division)
    assert response.status_code == 403
```

## Coverage Gate

`mise run test:api:coverage` — fails if < 80%.

## References

- Existing tests: `apps/api/tests/`
- Conftest: `apps/api/tests/conftest.py`
- Coverage config: `apps/api/pyproject.toml`
