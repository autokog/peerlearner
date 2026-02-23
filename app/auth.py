import json
from functools import wraps
from flask import Blueprint, request, jsonify, session
from . import db
from .models import AuditLog, Student, User

auth = Blueprint("auth", __name__, url_prefix="/api/auth")

OUK_DOMAIN = "ouk.ac.ke"


def _valid_ouk_email(email: str) -> bool:
    return email.lower().endswith(f"@{OUK_DOMAIN}") or \
           email.lower().endswith(f".{OUK_DOMAIN}")


def _try_link(user: User) -> None:
    """If a student record shares this user's email and isn't linked yet, link them."""
    if user.student_id is not None:
        return
    student = Student.query.filter_by(email=user.email).first()
    if student and student.user is None:
        user.student_id = student.id
        db.session.commit()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Authentication required."}), 401
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required."}), 403
        return f(*args, **kwargs)
    return decorated


def _get_ip() -> str:
    """Return the real client IP, honouring X-Forwarded-For from trusted proxies."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr


def _audit(action: str, entity_type: str = None, entity_id: int = None, detail: dict = None) -> None:
    """Write an audit log entry capturing full request metadata."""
    entry = AuditLog(
        user_id=session.get("user_id"),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=json.dumps(detail) if detail is not None else None,
        ip_address=_get_ip(),
        user_agent=request.user_agent.string or None,
        method=request.method,
        path=request.path,
        referrer=request.referrer or None,
    )
    db.session.add(entry)
    db.session.commit()


@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True)

    required = ["email", "password"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    if not _valid_ouk_email(data["email"]):
        return jsonify({"error": f"Email must be a valid OUK email (ending in {OUK_DOMAIN})."}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered."}), 409

    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    user = User(email=data["email"])
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    _try_link(user)

    session.permanent = True
    session["user_id"] = user.id

    _audit("user.register", "user", user.id, {"email": user.email})

    return jsonify({"user": user.to_dict()}), 201


@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email and password are required."}), 400

    if not _valid_ouk_email(data["email"]):
        return jsonify({"error": f"Email must be a valid OUK email (ending in {OUK_DOMAIN})."}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password."}), 401

    _try_link(user)

    session.permanent = True
    session["user_id"] = user.id

    _audit("user.login", "user", user.id, {"email": user.email})

    return jsonify({"user": user.to_dict()})


@auth.route("/logout", methods=["POST"])
def logout():
    user_id = session.get("user_id")
    if user_id:
        _audit("user.logout", "user", user_id)
    session.pop("user_id", None)
    return jsonify({"message": "Logged out."})


@auth.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated."}), 401
    user = User.query.get(user_id)
    if not user:
        session.pop("user_id", None)
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"user": user.to_dict()})
