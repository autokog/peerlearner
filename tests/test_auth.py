"""Tests for /api/auth/* endpoints (app/auth.py)."""

import pytest
from app import db
from app.models import Student, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register(client, email="user@ouk.ac.ke", password="pass1234"):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def _login(client, email="user@ouk.ac.ke", password="pass1234"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _me(client):
    return client.get("/api/auth/me")


def _logout(client):
    return client.post("/api/auth/logout")


def _cleanup_user(app, email):
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if u:
            db.session.delete(u)
            db.session.commit()


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_success(self, client, app):
        email = "newreg@ouk.ac.ke"
        r = _register(client, email)
        assert r.status_code == 201
        data = r.get_json()
        assert data["user"]["email"] == email
        assert "gravatar_url" in data["user"]
        _cleanup_user(app, email)

    def test_missing_email(self, client):
        r = client.post("/api/auth/register", json={"password": "pass1234"})
        assert r.status_code == 400

    def test_missing_password(self, client):
        r = client.post("/api/auth/register", json={"email": "x@ouk.ac.ke"})
        assert r.status_code == 400

    def test_invalid_domain(self, client):
        r = _register(client, email="user@gmail.com")
        assert r.status_code == 400
        assert "OUK" in r.get_json()["error"]

    def test_duplicate_email(self, client, app):
        email = "dup@ouk.ac.ke"
        _register(client, email)
        r = _register(client, email)
        assert r.status_code == 409
        _cleanup_user(app, email)

    def test_short_password(self, client):
        r = _register(client, email="short@ouk.ac.ke", password="abc")
        assert r.status_code == 400

    def test_sets_session(self, client, app):
        email = "sess@ouk.ac.ke"
        _register(client, email)
        r = _me(client)
        assert r.status_code == 200
        _logout(client)
        _cleanup_user(app, email)

    def test_auto_links_existing_student(self, client, app):
        """Registering with an email that matches a Student should auto-link."""
        email = "autolink@students.ouk.ac.ke"

        with app.app_context():
            from app.models import Course
            course = Course.query.first()
            s = Student(
                name="Auto Link",
                student_id="OUK/AL/001",
                gender="male",
                email=email,
                phone="0700000001",
                course_id=course.id if course else None,
            )
            db.session.add(s)
            db.session.commit()
            student_id = s.id

        r = _register(client, email=email)
        assert r.status_code == 201
        data = r.get_json()
        assert data["user"]["student"] is not None
        assert data["user"]["student"]["email"] == email

        _logout(client)

        with app.app_context():
            u = User.query.filter_by(email=email).first()
            assert u is not None
            assert u.student_id == student_id
            db.session.delete(u)
            s = Student.query.get(student_id)
            if s:
                db.session.delete(s)
            db.session.commit()


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    def test_success(self, client, app):
        email = "logintest@ouk.ac.ke"
        _register(client, email)
        _logout(client)

        r = _login(client, email)
        assert r.status_code == 200
        assert r.get_json()["user"]["email"] == email
        _logout(client)
        _cleanup_user(app, email)

    def test_wrong_password(self, client, app):
        email = "wrongpw@ouk.ac.ke"
        _register(client, email)
        _logout(client)
        r = _login(client, email, password="wrongpassword")
        assert r.status_code == 401
        _cleanup_user(app, email)

    def test_unknown_user(self, client):
        r = _login(client, email="nobody@ouk.ac.ke")
        assert r.status_code == 401

    def test_missing_credentials(self, client):
        r = client.post("/api/auth/login", json={})
        assert r.status_code == 400

    def test_invalid_domain(self, client):
        r = _login(client, email="user@hotmail.com")
        assert r.status_code == 400

    def test_auto_links_student_on_login(self, client, app):
        """Logging in after a student record is created should auto-link."""
        email = "latelink@students.ouk.ac.ke"
        _register(client, email)
        _logout(client)

        # Create student after user exists
        with app.app_context():
            from app.models import Course
            course = Course.query.first()
            s = Student(
                name="Late Link",
                student_id="OUK/LL/001",
                gender="female",
                email=email,
                phone="0700000002",
                course_id=course.id if course else None,
            )
            db.session.add(s)
            db.session.commit()
            student_id = s.id

        r = _login(client, email)
        assert r.status_code == 200
        data = r.get_json()
        assert data["user"]["student"] is not None

        _logout(client)
        with app.app_context():
            u = User.query.filter_by(email=email).first()
            if u:
                db.session.delete(u)
            s = Student.query.get(student_id)
            if s:
                db.session.delete(s)
            db.session.commit()


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------


class TestLogout:
    def test_logout_clears_session(self, client, app):
        email = "logoutme@ouk.ac.ke"
        _register(client, email)
        assert _me(client).status_code == 200
        _logout(client)
        assert _me(client).status_code == 401
        _cleanup_user(app, email)

    def test_logout_without_login_is_harmless(self, client):
        r = _logout(client)
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------


class TestMe:
    def test_returns_user_when_authenticated(self, client, app):
        email = "metest@ouk.ac.ke"
        _register(client, email)
        r = _me(client)
        assert r.status_code == 200
        assert r.get_json()["user"]["email"] == email
        _logout(client)
        _cleanup_user(app, email)

    def test_returns_401_when_not_authenticated(self, client):
        r = _me(client)
        assert r.status_code == 401
