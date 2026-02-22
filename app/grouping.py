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

    if available:
        # Pick the group with the best (unit overlap, gender balance) score.
        group = max(available, key=lambda g: _score(g, student))
    elif len(groups) < max_groups:
        group = Group(name=f"Group {len(groups) + 1}")
        db.session.add(group)
        db.session.flush()
    else:
        raise ValueError("Registration is closed — all groups are full.")

    student.group_id = group.id
    return group
