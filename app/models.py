import hashlib
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    # Nullable until the user completes their student profile
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=True, unique=True
    )
    student = db.relationship(
        "Student",
        foreign_keys=[student_id],
        uselist=False,
        backref=db.backref("user", uselist=False),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        email_hash = hashlib.md5(self.email.lower().strip().encode()).hexdigest()
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "is_admin": self.is_admin,
            "student": self.student.to_dict() if self.student else None,
            "gravatar_url": f"https://www.gravatar.com/avatar/{email_hash}?s=80&d=identicon",
        }


COURSES = [
    "Bachelor of Agritechnology and Food Systems",
    "Bachelor of Business and Entrepreneurship",
    "Bachelor of Commerce",
    "Bachelor of Data Science",
    "Bachelor of Economics and Data Science",
    "Bachelor of Economics and Statistics",
    "Bachelor of Science in Computer Science",
    "Bachelor of Science in Cyber Security and Digital Forensics",
    "Bachelor of Science in Interactive Media Technologies",
    "Bachelor of Science in Mathematics and Computing",
    "Bachelor of Technology Education (BCT)",
    "Bachelor of Technology Education (CIT)",
    "Bachelor of Technology Education (EET)",
    "Bachelor of Technology Education (MTT)",
    "Bachelor of Technology Education (PMT)",
]

# Maps course name → unit codes that belong to it
COURSE_UNIT_MAP = {
    "Bachelor of Agritechnology and Food Systems":             ["MAT 101", "SST 111"],
    "Bachelor of Business and Entrepreneurship":               ["BEB 105", "BEB 107", "ECO 101"],
    "Bachelor of Commerce":                                    ["BEB 105", "BEB 107", "ECO 101", "SST 111"],
    "Bachelor of Data Science":                                ["MAT 101", "MAT 103", "SST 111", "CSC 101"],
    "Bachelor of Economics and Data Science":                  ["ECO 101", "SST 111", "MAT 101", "MAT 103"],
    "Bachelor of Economics and Statistics":                    ["ECO 101", "SST 111", "MAT 101"],
    "Bachelor of Science in Computer Science":                 ["CSC 101", "MAT 101", "MAT 103", "BEB 105"],
    "Bachelor of Science in Cyber Security and Digital Forensics": ["CSF 123", "CSF 101", "MAT 101", "CSC 101"],
    "Bachelor of Science in Interactive Media Technologies":   ["CMT 101", "BEB 105"],
    "Bachelor of Science in Mathematics and Computing":        ["MAT 101", "MAT 103", "CSC 101"],
    "Bachelor of Technology Education (BCT)":                  ["BCT 101", "TED 101", "TED 103"],
    "Bachelor of Technology Education (CIT)":                  ["CSC 101", "TED 101", "TED 103"],
    "Bachelor of Technology Education (EET)":                  ["TED 101", "TED 103"],
    "Bachelor of Technology Education (MTT)":                  ["MAT 101", "TED 101", "TED 103"],
    "Bachelor of Technology Education (PMT)":                  ["TED 101", "TED 103"],
}

UNITS = [
    ("CSF 123", "Physics for Computer Systems and Digital Forensics"),
    ("CSF 101", "Intro to Digital Markets Infrastructure"),
    ("CSC 101", "Introduction to Computing Systems"),
    ("MAT 101", "Foundation of Mathematics"),
    ("BEB 105", "IT Entrepreneurship"),
    ("SST 111", "Basic Statistics with R"),
    ("BEB 107", "Entrepreneurial Environment"),
    ("ECO 101", "Introduction to Microeconomics"),
    ("CMT 101", "Sound and Video Production"),
    ("LDT 101", "Educational Theory and Pedagogy"),
    ("BCT 101", "Building and Civil Engineering Practice 1"),
    ("MAT 103", "Calculus I"),
    ("TED 101", "Introduction to Technology Education"),
    ("TED 103", "Basic Engineering Science"),
]

# Association tables — no model classes needed
student_units = db.Table(
    "student_units",
    db.Column("student_id", db.Integer, db.ForeignKey("students.id"), primary_key=True),
    db.Column("unit_id", db.Integer, db.ForeignKey("units.id"), primary_key=True),
)

course_units = db.Table(
    "course_units",
    db.Column("course_id", db.Integer, db.ForeignKey("courses.id"), primary_key=True),
    db.Column("unit_id", db.Integer, db.ForeignKey("units.id"), primary_key=True),
)


class Unit(db.Model):
    __tablename__ = "units"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)

    def to_dict(self):
        return {"id": self.id, "code": self.code, "name": self.name}


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    students = db.relationship("Student", backref="course", lazy=True)
    units = db.relationship("Unit", secondary=course_units, lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    whatsapp_link = db.Column(db.String(500), nullable=True)
    students = db.relationship("Student", backref="group", lazy=True)

    def member_count(self):
        return len(self.students)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "whatsapp_link": self.whatsapp_link,
            "members": [s.to_dict() for s in self.students],
        }


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), nullable=False, unique=True)
    gender = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=True)
    units = db.relationship("Unit", secondary=student_units, lazy=True)

    def to_dict(self):
        email_hash = hashlib.md5(self.email.lower().strip().encode()).hexdigest()
        return {
            "id": self.id,
            "name": self.name,
            "student_id": self.student_id,
            "gender": self.gender,
            "email": self.email,
            "phone": self.phone,
            "group_id": self.group_id,
            "course_id": self.course_id,
            "course": self.course.name if self.course else None,
            "units": [u.to_dict() for u in self.units],
            "has_account": self.user is not None,
            "gravatar_url": f"https://www.gravatar.com/avatar/{email_hash}?s=40&d=identicon",
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action      = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id   = db.Column(db.Integer, nullable=True)
    detail      = db.Column(db.Text, nullable=True)   # business context (JSON)
    ip_address  = db.Column(db.String(45), nullable=True)
    user_agent  = db.Column(db.Text, nullable=True)
    method      = db.Column(db.String(10), nullable=True)
    path        = db.Column(db.String(255), nullable=True)
    referrer    = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user        = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user.email if self.user else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "detail": json.loads(self.detail) if self.detail else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "method": self.method,
            "path": self.path,
            "referrer": self.referrer,
            "created_at": self.created_at.isoformat(),
        }
