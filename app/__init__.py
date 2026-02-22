from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")

    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    CORS(app)

    from .routes import api
    from .auth import auth
    app.register_blueprint(api)
    app.register_blueprint(auth)

    return app


def seed_db():
    """Seed reference data. Safe to call multiple times (no-ops if data exists)."""
    _seed_courses()
    _seed_units()
    _seed_course_units()


def _seed_courses():
    from .models import Course, COURSES
    if Course.query.first():
        return
    for name in COURSES:
        db.session.add(Course(name=name))
    db.session.commit()


def _seed_units():
    from .models import Unit, UNITS
    if Unit.query.first():
        return
    for code, name in UNITS:
        db.session.add(Unit(code=code, name=name))
    db.session.commit()


def _seed_course_units():
    from .models import Course, Unit, COURSE_UNIT_MAP
    # Skip if already linked
    if Course.query.filter(Course.units.any()).first():
        return
    for course_name, unit_codes in COURSE_UNIT_MAP.items():
        course = Course.query.filter_by(name=course_name).first()
        if not course:
            continue
        for code in unit_codes:
            unit = Unit.query.filter_by(code=code).first()
            if unit and unit not in course.units:
                course.units.append(unit)
    db.session.commit()
