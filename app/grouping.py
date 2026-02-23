from flask import current_app
from . import db
from .models import Group, Student


def _score(group: Group, student: Student) -> tuple:
    members = group.students

    # 1. Unit overlap — count how many of the incoming student's units
    #    are already represented somewhere in the group.
    student_unit_ids = {u.id for u in student.units}
    group_unit_ids = {u.id for m in members for u in m.units}
    unit_overlap = len(student_unit_ids & group_unit_ids)

    # 2. Gender balance — positive score when the group needs more of
    #    this student's gender, zero when the group is empty.
    male_count = sum(1 for m in members if m.gender == "male")
    female_count = sum(1 for m in members if m.gender == "female")
    if student.gender == "female":
        gender_score = male_count - female_count   # positive → more males, need a female
    elif student.gender == "male":
        gender_score = female_count - male_count   # positive → more females, need a male
    else:
        gender_score = 0

    return (unit_overlap, gender_score)


def assign_group(student: Student) -> Group:
    max_groups = current_app.config["MAX_GROUPS"]
    max_members = current_app.config["MAX_MEMBERS"]

    groups = Group.query.all()
    available = [g for g in groups if g.member_count() < max_members]

    # Only consider joining an existing group if there is at least one unit in common.
    with_overlap = [g for g in available if _score(g, student)[0] > 0]

    if with_overlap:
        # Best existing group that shares at least one unit.
        group = max(with_overlap, key=lambda g: _score(g, student))
    elif len(groups) < max_groups:
        # No overlap anywhere — start a fresh group.
        group = Group(name=f"Group {len(groups) + 1}")
        db.session.add(group)
        db.session.flush()
    elif available:
        # All groups are at max_groups but none have overlap — fall back to
        # best available by gender balance so no one is left without a group.
        group = max(available, key=lambda g: _score(g, student))
    else:
        raise ValueError("Registration is closed — all groups are full.")

    student.group_id = group.id
    return group
