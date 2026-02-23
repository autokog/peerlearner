import uuid
from flask import Blueprint, current_app, request, jsonify, session
from . import db
from .models import Course, Group, Student, Unit, User
from .grouping import assign_group
from .auth import login_required, _audit, _session_user_id

api = Blueprint("api", __name__, url_prefix="/api")


def _to_uuid(value):
    """Convert a string or UUID to a UUID object, returning None on failure."""
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return None


@api.route("/config", methods=["GET"])
def get_config():
    return jsonify({
        "max_groups": current_app.config["MAX_GROUPS"],
        "max_members": current_app.config["MAX_MEMBERS"],
    })


@api.route("/courses", methods=["GET"])
@login_required
def get_courses():
    courses = Course.query.order_by(Course.name).all()
    return jsonify([c.to_dict() for c in courses])


@api.route("/units", methods=["GET"])
@login_required
def get_units():
    course_id = _to_uuid(request.args.get("course_id"))
    if course_id:
        course = Course.query.get(course_id)
        if not course:
            return jsonify({"error": "Course not found."}), 404
        units = sorted(course.units, key=lambda u: u.code)
    else:
        units = Unit.query.order_by(Unit.code).all()
    return jsonify([u.to_dict() for u in units])


@api.route("/register", methods=["POST"])
@login_required
def register():
    data = request.get_json(force=True)

    required = ["name", "student_id", "gender", "email", "phone", "course_id"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not data["email"].lower().endswith("@students.ouk.ac.ke"):
        return jsonify({"error": "Email must end in @students.ouk.ac.ke."}), 400

    course_id = _to_uuid(data["course_id"])
    if not course_id or not Course.query.get(course_id):
        return jsonify({"error": "Invalid course selected."}), 400

    unit_ids = [_to_uuid(uid) for uid in data.get("unit_ids", [])]
    unit_ids = [uid for uid in unit_ids if uid]
    units = Unit.query.filter(Unit.id.in_(unit_ids)).all() if unit_ids else []
    if data.get("unit_ids") and len(units) != len(data["unit_ids"]):
        return jsonify({"error": "One or more selected units are invalid."}), 400

    if Student.query.filter_by(student_id=data["student_id"]).first():
        return jsonify({"error": "Student ID already registered."}), 409

    student = Student(
        name=data["name"],
        student_id=data["student_id"],
        gender=data["gender"],
        email=data["email"],
        phone=data["phone"],
        course_id=course_id,
        units=units,
    )
    db.session.add(student)
    db.session.flush()  # get student.id before commit

    # Always link to the currently logged-in user if they aren't linked yet
    current_user = User.query.get(_session_user_id())
    if current_user.student_id is None:
        current_user.student_id = student.id
    # Also link any other account that shares the student email (e.g. a
    # student who later created their own account with their student address)
    else:
        other = User.query.filter_by(email=data["email"]).first()
        if other and other.student_id is None:
            other.student_id = student.id

    try:
        group = assign_group(student)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 403

    _audit("student.enroll", "student", student.id, {"student_name": student.name})

    return jsonify({
        "student": student.to_dict(),
        "group": group.to_dict(),
    }), 201


@api.route("/public/student/<path:student_id>", methods=["GET"])
def public_get_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"error": "Student not found."}), 404

    group = Group.query.get(student.group_id) if student.group_id else None
    members = []
    if group:
        members = [
            {"name": m.name, "course": m.course.name if m.course else None, "gender": m.gender}
            for m in group.students
        ]

    return jsonify({
        "student": student.to_dict(),
        "group": {
            "id": str(group.id),
            "name": group.name,
            "whatsapp_link": group.whatsapp_link,
            "members": members,
        } if group else None,
    })


@api.route("/groups", methods=["GET"])
@login_required
def get_groups():
    groups = Group.query.order_by(Group.id).all()
    return jsonify([g.to_dict() for g in groups])


@api.route("/student/<path:student_id>", methods=["GET"])
@login_required
def get_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if not student:
        return jsonify({"error": "Student not found."}), 404
    group = Group.query.get(student.group_id)
    return jsonify({
        "student": student.to_dict(),
        "group": group.to_dict() if group else None,
    })
