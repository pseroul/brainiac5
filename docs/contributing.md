# Contributing Guide

This guide covers everything a new developer needs to get productive on Consensia: setup, workflow, testing, and adding new features.

---

## Development Setup

Follow [installation.md — Option A](installation.md#option-a-local-development-setup) to get the backend and frontend running locally.

After setup you should have:
- Backend at `http://localhost:8000` (`python main.py`)
- Frontend at `http://localhost:5173` (`npm run dev`)
- At least one user account (`python authenticator.py your@email.com`)

---

## Repository Structure

```
consensia/
├── backend/
│   ├── main.py                  # FastAPI app, all REST endpoints
│   ├── data_handler.py          # SQLite CRUD + ChromaDB sync
│   ├── data_similarity.py       # ML pipeline (UMAP, clustering, TOC)
│   ├── chroma_client.py         # ChromaDB wrapper
│   ├── authenticator.py         # TOTP + JWT
│   ├── config.py                # Environment variable setup
│   ├── utils.py                 # format_text / unformat_text
│   ├── requirements.txt         # Python dependencies
│   ├── Makefile                 # audit target (ruff + vulture + pytest)
│   └── tests/
│       ├── test_main.py         # API endpoint unit tests
│       ├── test_data_handler.py # SQLite CRUD unit tests
│       ├── test_data_similarity.py
│       ├── test_authenticator.py
│       ├── test_chroma_client.py
│       ├── test_utils.py
│       ├── test_admin.py
│       └── integration/
│           ├── conftest.py      # fixtures
│           ├── test_auth.py
│           ├── test_idea_lifecycle.py
│           ├── test_tag_cascades.py
│           ├── test_multi_user.py
│           ├── test_toc_pipeline.py
│           ├── test_books.py
│           └── test_voting.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Routes + ProtectedRoute / AdminRoute
│   │   ├── services/api.js      # Axios instance + interceptors
│   │   ├── contexts/
│   │   │   ├── AuthContext.jsx
│   │   │   └── BookContext.jsx
│   │   ├── pages/               # Login, Dashboard, TOC, Tags, Books, Admin
│   │   └── components/          # Navbar, IdeaModal, VoteButtons, BookSelector
│   └── e2e/                     # Playwright E2E tests
├── docs/                        # This documentation
├── Makefile                     # audit-backend / audit-frontend / audit-all
└── .github/workflows/ci.yml     # GitHub Actions CI/CD
```

---

## Quality Protocol

Every change must pass the full audit before being pushed:

```bash
# Backend
make audit-backend          # ruff check --fix + vulture + pytest

# Frontend
make audit-frontend         # ESLint + knip

# Both
make audit-all
```

**Rules (non-negotiable):**

1. **TDD for backend** — write failing tests first, then write the implementation
2. `make audit-backend` must be green before you touch the frontend
3. Write Vitest tests for frontend components before writing the component
4. `make audit-frontend` must be green before pushing
5. `make audit-all` as final validation
6. **No dead code** — if `vulture` (Python) or `knip` (JS) flags something, delete it
7. **Pydantic** for all external data in the backend; **Zod** in the frontend
8. **SOLID** — refactor violations in any file you touch before adding features

---

## Backend Testing

### Unit tests

Unit tests mock all heavy dependencies (ChromaDB, SentenceTransformers, UMAP, HDBSCAN) at the `sys.modules` level at the top of each test file:

```python
# Example: test_main.py
sys.modules["chromadb"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()
```

This keeps unit tests fast and dependency-free.

**Exception:** `tests/test_data_similarity.py::TestEmbeddingAnalyzer` exercises the real UMAP → HDBSCAN pipeline. Do not add `sys.modules` patches that affect it.

### Integration tests

Integration tests use a real temporary SQLite database and a `FakeChromaClient` (in-memory dict):

```
backend/tests/integration/conftest.py
```

Key fixtures:

| Fixture | Scope | Purpose |
|---|---|---|
| `chroma_store` | function | Fresh `{}` dict per test |
| `patch_chroma` | function, autouse | Replaces `ChromaClient` with `FakeChromaClient` |
| `db_path` | function | Temp SQLite path; sets `NAME_DB` env var |
| `client` | function | `TestClient(app)` wired to the test DB |
| `alice` | function | Test user with real TOTP secret + auth headers |
| `bob` | function | Second test user for isolation tests |

Helper imports:

```python
from tests.integration.conftest import create_db_user, make_token, auth_headers
```

### Running tests

```bash
cd backend
source venv/bin/activate

pytest                                   # All tests
pytest tests/integration/               # Integration only
pytest tests/test_main.py               # Single file
pytest -k "test_health"                 # By keyword
pytest --cov=. --cov-report=html        # Coverage + HTML report
```

Coverage threshold: **≥ 80%** (enforced in `pyproject.toml`).

### Known quirks pinned by integration tests

| Quirk | Why it exists |
|---|---|
| `DELETE /ideas/{id}` does not cascade relations | No `PRAGMA foreign_keys = ON` |
| `DELETE /tags/{name}` does not cascade relations | Same |
| Non-existent user email on idea create → `{"id": -1}` | No validation, not a 4xx |
| Empty TOC `[]` is falsy → re-generated every request | `if toc:` check in `main.py` |

Do not "fix" these without updating the pinning tests.

---

## Frontend Testing

### Unit tests (Vitest + React Testing Library)

Unit tests are co-located with source files as `Component.test.jsx`. Global mocks (React Router, axios, Lucide icons) are configured in `src/setupTests.js`.

```bash
cd frontend
npm test                   # Run once
npm run test:watch         # Watch mode
npm run test:coverage      # Coverage report (80% threshold)
```

### E2E tests (Playwright)

E2E tests run against a real Chromium browser with all API calls intercepted via `page.route()` — no real backend is required.

**One-time setup:**

```bash
cd frontend
npx playwright install chromium
```

**Run:**

```bash
npm run test:e2e           # Headless
npm run test:e2e:ui        # Interactive UI
```

E2E spec files:

| File | Coverage |
|---|---|
| `e2e/auth.spec.ts` | Login, logout, 401 interceptor, protected routes |
| `e2e/ideas-crud.spec.ts` | Create/edit/delete ideas, search, similar ideas, tags |
| `e2e/toc.spec.ts` | TOC rendering, collapse/expand, refresh, export |
| `e2e/tags-ideas.spec.ts` | Tag rendering, orphan deletion, modal |

**Delete flows** use `window.confirm`:

```typescript
page.once('dialog', (dialog) => dialog.accept());   // confirm
page.once('dialog', (dialog) => dialog.dismiss());  // cancel
```

---

## Adding a New Backend Endpoint

Follow these steps in order (TDD):

### 1. Define the Pydantic model (if needed)

Add it to `main.py` alongside existing models:

```python
class MyNewItem(BaseModel):
    field_one: str
    field_two: int
```

### 2. Add the data layer function

Add a function to `data_handler.py`:

```python
def add_my_thing(field_one: str, field_two: int) -> int:
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("INSERT INTO ...", (field_one, field_two))
    db.commit()
    return cursor.lastrowid
```

### 3. Write the unit test first

In `tests/test_main.py` (mock the data layer):

```python
def test_create_my_thing(client, auth_headers):
    with patch("main.add_my_thing", return_value=1):
        response = client.post("/my-things", json={"field_one": "x", "field_two": 2}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"id": 1}
```

### 4. Add the route in `main.py`

```python
@app.post("/my-things")
def create_my_thing(item: MyNewItem, current_user=Depends(get_current_user)):
    new_id = add_my_thing(item.field_one, item.field_two)
    return {"id": new_id}
```

### 5. Write an integration test

In `tests/integration/test_my_feature.py`:

```python
def test_create_and_retrieve_my_thing(client, alice):
    r = client.post("/my-things", json={"field_one": "x", "field_two": 2}, headers=alice["headers"])
    assert r.status_code == 200
    assert r.json()["id"] > 0
```

### 6. Run the audit

```bash
make audit-backend
```

Fix any linting or dead-code warnings before moving on.

---

## Adding a New User (CLI)

```bash
cd backend
source venv/bin/activate
python authenticator.py user@example.com
```

For a debug/non-expiring OTP (development only):

```bash
python authenticator.py user@example.com --debug
```

The printed provisioning URI can be opened in a QR code renderer or entered manually in Google Authenticator.

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request:

```
backend job:
  1. Set up Python 3.11
  2. pip install -r requirements.txt
  3. ruff check . (lint)
  4. vulture . (dead code)
  5. pytest --cov=. (≥80% coverage)

frontend job:
  1. Set up Node 20
  2. npm install
  3. ESLint + knip (validate)
  4. Vitest --coverage (≥80% coverage)

deploy job (main branch only, after both jobs pass):
  1. SSH to Raspberry Pi
  2. git pull
  3. Rebuild frontend with VITE_API_URL
  4. Install backend dependencies
  5. sudo systemctl restart consensia
```

**Deployment is automatic on push to `main`.** Ensure `make audit-all` passes locally before merging.
