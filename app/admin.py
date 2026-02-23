from flask import Blueprint, request, jsonify, session
from . import db
from .models import AuditLog, Group, Student
from .auth import admin_required, _audit

admin = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin.route("/groups", methods=["GET"])
@admin_required
def get_groups():
    groups = Group.query.order_by(Group.id).all()
    return jsonify([g.to_dict() for g in groups])


@admin.route("/audit-log", methods=["GET"])
@admin_required
def get_audit_log():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 200)

    pagination = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify({
        "entries": [e.to_dict() for e in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "page": page,
    })


@admin.route("/students/<int:student_id>/move", methods=["POST"])
@admin_required
def move_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404

    data = request.get_json(force=True)
    group_id = data.get("group_id")
    if not group_id:
        return jsonify({"error": "group_id is required."}), 400

    group = Group.query.get(group_id)
    if not group:
        return jsonify({"error": "Group not found."}), 404

    old_group_id = student.group_id
    student.group_id = group_id
    db.session.commit()

    _audit(
        "admin.move_student",
        "student",
        student.id,
        {
            "student_name": student.name,
            "from_group_id": old_group_id,
            "to_group_id": group_id,
            "to_group_name": group.name,
        },
    )

    return jsonify({"student": student.to_dict(), "group": group.to_dict()})
