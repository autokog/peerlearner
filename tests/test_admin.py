"""Tests for /api/admin/* endpoints (app/admin.py)."""

import pytest
from app import db
from app.models import AuditLog, Group, Student, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _register(client, email, password="pass1234"):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def _login(client, email, password="pass1234"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _make_admin(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        user.role = "admin"
        db.session.commit()


def _cleanup_user(app, email):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            if user.student_id:
                user.student_id = None
                db.session.flush()
            db.session.delete(user)
            db.session.commit()


# ---------------------------------------------------------------------------
# GET /api/admin/groups
# ---------------------------------------------------------------------------

class TestAdminGetGroups:
    EMAIL = "admin-groups@ouk.ac.ke"

    def setup_method(self):
        pass

    def test_requires_authentication(self, client):
        res = client.get("/api/admin/groups")
        assert res.status_code == 401

    def test_requires_admin(self, client, app):
        _register(client, self.EMAIL)
        _login(client, self.EMAIL)
        res = client.get("/api/admin/groups")
        assert res.status_code == 403
        _cleanup_user(app, self.EMAIL)

    def test_admin_can_get_groups(self, client, app):
        _register(client, self.EMAIL)
        _make_admin(app, self.EMAIL)
        _login(client, self.EMAIL)
        res = client.get("/api/admin/groups")
        assert res.status_code == 200
        assert isinstance(res.get_json(), list)
        _cleanup_user(app, self.EMAIL)


# ---------------------------------------------------------------------------
# GET /api/admin/audit-log
# ---------------------------------------------------------------------------

class TestAdminAuditLog:
    EMAIL = "admin-audit@ouk.ac.ke"

    def test_requires_authentication(self, client):
        res = client.get("/api/admin/audit-log")
        assert res.status_code == 401

    def test_requires_admin(self, client, app):
        _register(client, self.EMAIL)
        _login(client, self.EMAIL)
        res = client.get("/api/admin/audit-log")
        assert res.status_code == 403
        _cleanup_user(app, self.EMAIL)

    def test_returns_paginated_entries(self, client, app):
        _register(client, self.EMAIL)
        _make_admin(app, self.EMAIL)
        _login(client, self.EMAIL)
        res = client.get("/api/admin/audit-log")
        assert res.status_code == 200
        data = res.get_json()
        assert "entries" in data
        assert "total" in data
        assert "pages" in data
        assert isinstance(data["entries"], list)
        _cleanup_user(app, self.EMAIL)

    def test_register_creates_audit_entry(self, client, app):
        _register(client, self.EMAIL)
        _make_admin(app, self.EMAIL)
        _login(client, self.EMAIL)
        res = client.get("/api/admin/audit-log")
        data = res.get_json()
        actions = [e["action"] for e in data["entries"]]
        assert "user.register" in actions
        assert "user.login" in actions
        _cleanup_user(app, self.EMAIL)


# ---------------------------------------------------------------------------
# POST /api/admin/students/<id>/move
# ---------------------------------------------------------------------------

class TestAdminMoveStudent:
    ADMIN_EMAIL = "admin-move@ouk.ac.ke"

    def _get_student_and_groups(self, app):
        """Return (student_db_id, other_group_id) from the DB, or None if not enough data."""
        with app.app_context():
            student = Student.query.first()
            if not student or student.group_id is None:
                return None, None
            other_group = Group.query.filter(Group.id != student.group_id).first()
            if not other_group:
                return None, None
            return student.id, other_group.id

    def test_requires_authentication(self, client, app):
        student_id, group_id = self._get_student_and_groups(app)
        if student_id is None:
            pytest.skip("Need at least 2 groups and 1 student")
        res = client.post(
            f"/api/admin/students/{student_id}/move",
            json={"group_id": group_id},
        )
        assert res.status_code == 401

    def test_requires_admin(self, client, app):
        student_id, group_id = self._get_student_and_groups(app)
        if student_id is None:
            pytest.skip("Need at least 2 groups and 1 student")
        _register(client, self.ADMIN_EMAIL)
        _login(client, self.ADMIN_EMAIL)
        res = client.post(
            f"/api/admin/students/{student_id}/move",
            json={"group_id": group_id},
        )
        assert res.status_code == 403
        _cleanup_user(app, self.ADMIN_EMAIL)

    def test_move_student(self, client, app):
        student_id, group_id = self._get_student_and_groups(app)
        if student_id is None:
            pytest.skip("Need at least 2 groups and 1 student")
        _register(client, self.ADMIN_EMAIL)
        _make_admin(app, self.ADMIN_EMAIL)
        _login(client, self.ADMIN_EMAIL)
        res = client.post(
            f"/api/admin/students/{student_id}/move",
            json={"group_id": group_id},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert data["student"]["group_id"] == group_id
        assert data["group"]["id"] == group_id
        _cleanup_user(app, self.ADMIN_EMAIL)

    def test_move_creates_audit_entry(self, client, app):
        student_id, group_id = self._get_student_and_groups(app)
        if student_id is None:
            pytest.skip("Need at least 2 groups and 1 student")
        _register(client, self.ADMIN_EMAIL)
        _make_admin(app, self.ADMIN_EMAIL)
        _login(client, self.ADMIN_EMAIL)
        client.post(
            f"/api/admin/students/{student_id}/move",
            json={"group_id": group_id},
        )
        res = client.get("/api/admin/audit-log")
        actions = [e["action"] for e in res.get_json()["entries"]]
        assert "admin.move_student" in actions
        _cleanup_user(app, self.ADMIN_EMAIL)

    def test_returns_404_for_missing_student(self, client, app):
        _register(client, self.ADMIN_EMAIL)
        _make_admin(app, self.ADMIN_EMAIL)
        _login(client, self.ADMIN_EMAIL)
        res = client.post("/api/admin/students/99999/move", json={"group_id": 1})
        assert res.status_code == 404
        _cleanup_user(app, self.ADMIN_EMAIL)

    def test_returns_404_for_missing_group(self, client, app):
        student_id, _ = self._get_student_and_groups(app)
        if student_id is None:
            pytest.skip("Need at least 1 student")
        _register(client, self.ADMIN_EMAIL)
        _make_admin(app, self.ADMIN_EMAIL)
        _login(client, self.ADMIN_EMAIL)
        res = client.post(
            f"/api/admin/students/{student_id}/move",
            json={"group_id": 99999},
        )
        assert res.status_code == 404
        _cleanup_user(app, self.ADMIN_EMAIL)

    def test_returns_400_when_group_id_missing(self, client, app):
        student_id, _ = self._get_student_and_groups(app)
        if student_id is None:
            pytest.skip("Need at least 1 student")
        _register(client, self.ADMIN_EMAIL)
        _make_admin(app, self.ADMIN_EMAIL)
        _login(client, self.ADMIN_EMAIL)
        res = client.post(f"/api/admin/students/{student_id}/move", json={})
        assert res.status_code == 400
        _cleanup_user(app, self.ADMIN_EMAIL)


# ---------------------------------------------------------------------------
# is_admin in /api/auth/me
# ---------------------------------------------------------------------------

class TestIsAdminField:
    EMAIL = "admin-me@ouk.ac.ke"

    def test_is_admin_false_by_default(self, client, app):
        _register(client, self.EMAIL)
        res = client.get("/api/auth/me")
        assert res.get_json()["user"]["is_admin"] is False
        _cleanup_user(app, self.EMAIL)

    def test_is_admin_true_after_promotion(self, client, app):
        _register(client, self.EMAIL)
        _make_admin(app, self.EMAIL)
        res = client.get("/api/auth/me")
        assert res.get_json()["user"]["is_admin"] is True
        _cleanup_user(app, self.EMAIL)
