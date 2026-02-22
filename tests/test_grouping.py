"""Unit tests for the grouping algorithm (app/grouping.py)."""

import itertools
import pytest
from flask import current_app
from app import db
from app.models import Course, Group, Student, Unit
from app.grouping import _score, assign_group

_counter = itertools.count(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_unit(code="TST 001", name="Test Unit"):
    u = Unit(code=code, name=name)
    db.session.add(u)
    db.session.flush()
    return u


def _make_student(gender="male", units=None, student_id=None, group=None):
    n = next(_counter)
    s = Student(
        name="Test Student",
        student_id=student_id or f"OUK/TST/{n:06d}",
        gender=gender,
        email=f"s{n}@students.ouk.ac.ke",
        phone="0700000000",
    )
    if units:
        s.units = units
    if group:
        s.group_id = group.id
    db.session.add(s)
    db.session.flush()
    return s


def _make_group(name=None, members=None):
    g = Group(name=name or f"Group-{id(object())}")
    db.session.add(g)
    db.session.flush()
    if members:
        for m in members:
            m.group_id = g.id
    db.session.flush()
    return g


# ---------------------------------------------------------------------------
# _score() tests
# ---------------------------------------------------------------------------


class TestScore:
    def test_empty_group_scores_zero(self, app):
        with app.app_context():
            group = _make_group()
            student = _make_student()
            assert _score(group, student) == (0, 0)
            db.session.rollback()

    def test_unit_overlap_counted(self, app):
        with app.app_context():
            u1 = _make_unit("OVL 001", "Overlap Unit 1")
            u2 = _make_unit("OVL 002", "Overlap Unit 2")

            existing = _make_student(units=[u1, u2])
            group = _make_group(members=[existing])

            # Incoming student shares u1 only
            incoming = _make_student(units=[u1])
            overlap, _ = _score(group, incoming)
            assert overlap == 1

            # Incoming student shares both units
            incoming2 = _make_student(units=[u1, u2])
            overlap2, _ = _score(group, incoming2)
            assert overlap2 == 2

            db.session.rollback()

    def test_no_unit_overlap(self, app):
        with app.app_context():
            u1 = _make_unit("NOO 001", "No Overlap 1")
            u2 = _make_unit("NOO 002", "No Overlap 2")

            existing = _make_student(units=[u1])
            group = _make_group(members=[existing])

            incoming = _make_student(units=[u2])
            overlap, _ = _score(group, incoming)
            assert overlap == 0

            db.session.rollback()

    def test_gender_score_female_into_male_heavy_group(self, app):
        with app.app_context():
            m1 = _make_student(gender="male")
            m2 = _make_student(gender="male")
            group = _make_group(members=[m1, m2])

            incoming = _make_student(gender="female")
            _, gender = _score(group, incoming)
            assert gender > 0  # group needs females

            db.session.rollback()

    def test_gender_score_male_into_female_heavy_group(self, app):
        with app.app_context():
            f1 = _make_student(gender="female")
            f2 = _make_student(gender="female")
            group = _make_group(members=[f1, f2])

            incoming = _make_student(gender="male")
            _, gender = _score(group, incoming)
            assert gender > 0  # group needs males

            db.session.rollback()

    def test_gender_score_same_gender_excess_is_negative(self, app):
        with app.app_context():
            f1 = _make_student(gender="female")
            f2 = _make_student(gender="female")
            group = _make_group(members=[f1, f2])

            incoming = _make_student(gender="female")
            _, gender = _score(group, incoming)
            assert gender < 0  # already too many females

            db.session.rollback()

    def test_gender_score_balanced_group_is_zero(self, app):
        with app.app_context():
            m = _make_student(gender="male")
            f = _make_student(gender="female")
            group = _make_group(members=[m, f])

            incoming_f = _make_student(gender="female")
            _, gender_f = _score(group, incoming_f)
            # male_count == female_count → gender_score = 0 - 0? No:
            # male=1, female=1; student is female → score = male - female = 0
            assert gender_f == 0

            db.session.rollback()

    def test_gender_score_other_is_zero(self, app):
        with app.app_context():
            m = _make_student(gender="male")
            group = _make_group(members=[m])

            incoming = _make_student(gender="other")
            _, gender = _score(group, incoming)
            assert gender == 0

            db.session.rollback()


# ---------------------------------------------------------------------------
# assign_group() tests
# ---------------------------------------------------------------------------


class TestAssignGroup:
    def test_creates_first_group(self, app):
        with app.app_context():
            Group.query.delete()
            Student.query.delete()
            db.session.flush()

            student = _make_student()
            group = assign_group(student)

            assert group.id is not None
            assert student.group_id == group.id

            db.session.rollback()

    def test_assigns_to_existing_group(self, app):
        with app.app_context():
            Group.query.delete()
            Student.query.delete()
            db.session.flush()

            existing_group = _make_group(name="Existing Group")
            student = _make_student()
            result = assign_group(student)

            assert result.id == existing_group.id
            assert student.group_id == existing_group.id

            db.session.rollback()

    def test_creates_new_group_when_existing_is_full(self, app):
        with app.app_context():
            Group.query.delete()
            Student.query.delete()
            db.session.flush()

            full_group = _make_group(name="Full Group")
            for i in range(current_app.config["MAX_MEMBERS"]):
                m = _make_student()
                m.group_id = full_group.id
            db.session.flush()

            incoming = _make_student()
            result = assign_group(incoming)

            assert result.id != full_group.id

            db.session.rollback()

    def test_raises_when_all_groups_full(self, app):
        with app.app_context():
            Group.query.delete()
            Student.query.delete()
            db.session.flush()

            for g_idx in range(current_app.config["MAX_GROUPS"]):
                g = _make_group(name=f"FullGroup-{g_idx}")
                for _s_idx in range(current_app.config["MAX_MEMBERS"]):
                    m = _make_student()
                    m.group_id = g.id
            db.session.flush()

            incoming = _make_student()
            with pytest.raises(ValueError, match="closed"):
                assign_group(incoming)

            db.session.rollback()

    def test_prefers_group_with_higher_unit_overlap(self, app):
        with app.app_context():
            Group.query.delete()
            Student.query.delete()
            db.session.flush()

            u1 = _make_unit("PRF 001", "Prefer Unit 1")
            u2 = _make_unit("PRF 002", "Prefer Unit 2")

            # Group A: has u1
            mem_a = _make_student(units=[u1])
            group_a = _make_group(name="Group A", members=[mem_a])

            # Group B: has u2
            mem_b = _make_student(units=[u2])
            group_b = _make_group(name="Group B", members=[mem_b])

            # Incoming has u1 → should go to Group A
            incoming = _make_student(units=[u1])
            result = assign_group(incoming)

            assert result.id == group_a.id

            db.session.rollback()
