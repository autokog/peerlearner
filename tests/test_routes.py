"""Tests for /api/* endpoints (app/routes.py)."""

import pytest
from flask import current_app
from app import db
from app.models import Course, Group, Student, Unit, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_login(client, email="coord@ouk.ac.ke", password="pass1234"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _logout(client):
    client.post("/api/auth/logout")


def _cleanup_user(app, email):
    with app.app_context():
        u = User.query.filter_by(email=email).first()
        if u:
            if u.student_id:
                u.student_id = None
                db.session.flush()
            db.session.delete(u)
            db.session.commit()


def _cleanup_student(app, student_id_str):
    with app.app_context():
        s = Student.query.filter_by(student_id=student_id_str).first()
        if s:
            # unlink any user
            u = User.query.filter_by(student_id=s.id).first()
            if u:
                u.student_id = None
                db.session.flush()
            db.session.delete(s)
            db.session.commit()


def _valid_enroll_payload(app, student_id="OUK/RT/001"):
    """Return a minimal valid enroll payload using real DB IDs."""
    with app.app_context():
        course = Course.query.first()
        unit = Unit.query.first()
        return {
            "name": "Route Test Student",
            "student_id": student_id,
            "gender": "male",
            "email": f"{student_id.replace('/', '')}@students.ouk.ac.ke",
            "phone": "0700000099",
            "course_id": course.id,
            "unit_ids": [unit.id],
        }


# ---------------------------------------------------------------------------
# GET /api/courses
# ---------------------------------------------------------------------------


class TestGetCourses:
    def test_returns_courses_when_logged_in(self, client, app):
        _register_and_login(client)
        r = client.get("/api/courses")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_requires_authentication(self, client):
        r = client.get("/api/courses")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/units
# ---------------------------------------------------------------------------


class TestGetUnits:
    def test_returns_units_when_logged_in(self, client, app):
        _register_and_login(client)
        r = client.get("/api/units")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "code" in data[0]
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_requires_authentication(self, client):
        r = client.get("/api/units")
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/register  (student enrolment)
# ---------------------------------------------------------------------------


class TestStudentEnroll:
    def test_success(self, client, app):
        _register_and_login(client)
        payload = _valid_enroll_payload(app)
        r = client.post("/api/register", json=payload)
        assert r.status_code == 201
        data = r.get_json()
        assert "student" in data
        assert "group" in data
        assert data["student"]["student_id"] == payload["student_id"]
        assert data["group"]["id"] is not None
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")
        _cleanup_student(app, payload["student_id"])

    def test_missing_required_fields(self, client, app):
        _register_and_login(client)
        r = client.post("/api/register", json={"name": "Incomplete"})
        assert r.status_code == 400
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_invalid_email_domain(self, client, app):
        _register_and_login(client)
        with app.app_context():
            course = Course.query.first()
        payload = {
            "name": "Bad Email",
            "student_id": "OUK/RT/BAD",
            "gender": "male",
            "email": "student@gmail.com",
            "phone": "0700000000",
            "course_id": course.id,
        }
        r = client.post("/api/register", json=payload)
        assert r.status_code == 400
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_invalid_course_id(self, client, app):
        _register_and_login(client)
        payload = _valid_enroll_payload(app, student_id="OUK/RT/IC1")
        payload["course_id"] = 999999
        r = client.post("/api/register", json=payload)
        assert r.status_code == 400
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_invalid_unit_ids(self, client, app):
        _register_and_login(client)
        payload = _valid_enroll_payload(app, student_id="OUK/RT/IU1")
        payload["unit_ids"] = [999999]
        r = client.post("/api/register", json=payload)
        assert r.status_code == 400
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_duplicate_student_id(self, client, app):
        _register_and_login(client)
        payload = _valid_enroll_payload(app, student_id="OUK/RT/DUP")
        client.post("/api/register", json=payload)
        r = client.post("/api/register", json=payload)
        assert r.status_code == 409
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")
        _cleanup_student(app, payload["student_id"])

    def test_requires_authentication(self, client, app):
        payload = _valid_enroll_payload(app, student_id="OUK/RT/NOAUTH")
        r = client.post("/api/register", json=payload)
        assert r.status_code == 401

    def test_all_groups_full_returns_403(self, client, app):
        _register_and_login(client)

        with app.app_context():
            # Fill every group to capacity
            Group.query.delete()
            db.session.flush()
            course = Course.query.first()
            for g_i in range(current_app.config["MAX_GROUPS"]):
                g = Group(name=f"TestFull-{g_i}")
                db.session.add(g)
                db.session.flush()
                for s_i in range(current_app.config["MAX_MEMBERS"]):
                    s = Student(
                        name="Filler",
                        student_id=f"OUK/FL/{g_i}{s_i:02d}",
                        gender="male",
                        email=f"fl{g_i}{s_i}@students.ouk.ac.ke",
                        phone="0700000000",
                        group_id=g.id,
                        course_id=course.id if course else None,
                    )
                    db.session.add(s)
            db.session.commit()

        payload = _valid_enroll_payload(app, student_id="OUK/RT/OVER")
        r = client.post("/api/register", json=payload)
        assert r.status_code == 403

        # Cleanup
        with app.app_context():
            for g_i in range(current_app.config["MAX_GROUPS"]):
                for s_i in range(current_app.config["MAX_MEMBERS"]):
                    s = Student.query.filter_by(student_id=f"OUK/FL/{g_i}{s_i:02d}").first()
                    if s:
                        db.session.delete(s)
            Group.query.filter(Group.name.like("TestFull-%")).delete()
            db.session.commit()

        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_links_student_to_existing_user(self, client, app):
        """Enrolling a student whose email matches an existing user should link them."""
        student_email = "OUK99999".lower() + "@students.ouk.ac.ke"
        user_email = student_email

        # Create user first
        client.post(
            "/api/auth/register",
            json={"email": user_email, "password": "pass1234"},
        )

        with app.app_context():
            course = Course.query.first()
            unit = Unit.query.first()

        payload = {
            "name": "Link Test",
            "student_id": "OUK/LK/001",
            "gender": "female",
            "email": student_email,
            "phone": "0700000088",
            "course_id": course.id,
            "unit_ids": [unit.id],
        }
        r = client.post("/api/register", json=payload)
        assert r.status_code == 201

        with app.app_context():
            u = User.query.filter_by(email=user_email).first()
            assert u is not None
            assert u.student_id is not None

        _logout(client)
        _cleanup_student(app, "OUK/LK/001")
        _cleanup_user(app, user_email)


# ---------------------------------------------------------------------------
# GET /api/groups
# ---------------------------------------------------------------------------


class TestGetGroups:
    def test_returns_list_when_authenticated(self, client, app):
        _register_and_login(client)
        r = client.get("/api/groups")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_requires_authentication(self, client):
        r = client.get("/api/groups")
        assert r.status_code == 401

    def test_group_contains_member_list(self, client, app):
        _register_and_login(client)
        payload = _valid_enroll_payload(app, student_id="OUK/GRP/001")
        client.post("/api/register", json=payload)

        r = client.get("/api/groups")
        assert r.status_code == 200
        groups = r.get_json()
        assert any("members" in g for g in groups)

        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")
        _cleanup_student(app, "OUK/GRP/001")


# ---------------------------------------------------------------------------
# GET /api/student/<student_id>
# ---------------------------------------------------------------------------


class TestGetStudent:
    def test_returns_student_when_found(self, client, app):
        _register_and_login(client)
        payload = _valid_enroll_payload(app, student_id="OUK/GS/001")
        client.post("/api/register", json=payload)

        r = client.get(f"/api/student/{payload['student_id']}")
        assert r.status_code == 200
        data = r.get_json()
        assert data["student"]["student_id"] == payload["student_id"]
        assert "group" in data

        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")
        _cleanup_student(app, "OUK/GS/001")

    def test_returns_404_for_unknown_id(self, client, app):
        _register_and_login(client)
        r = client.get("/api/student/DOESNOTEXIST")
        assert r.status_code == 404
        _logout(client)
        _cleanup_user(app, "coord@ouk.ac.ke")

    def test_requires_authentication(self, client):
        r = client.get("/api/student/OUK/00/001")
        assert r.status_code == 401
