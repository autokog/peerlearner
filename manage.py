import random
import click
from app import create_app, db, seed_db
from app.models import Course, Student, Group, Unit, User
from app.grouping import assign_group

app = create_app()


# ---------------------------------------------------------------------------
# Database management commands
# ---------------------------------------------------------------------------

@app.cli.command("db-create")
def db_create():
    """Create all tables and seed reference data (safe to run multiple times)."""
    db.create_all()
    seed_db()
    click.secho("Database ready.", fg="green")


def _drop_all_cascade():
    """Drop and recreate the public schema — handles FK constraints in any order."""
    with db.engine.connect() as conn:
        conn.execute(db.text("DROP SCHEMA public CASCADE"))
        conn.execute(db.text("CREATE SCHEMA public"))
        conn.commit()


@app.cli.command("db-reset")
def db_reset():
    """Drop every table, recreate the schema, and re-seed reference data."""
    _drop_all_cascade()
    db.create_all()
    seed_db()
    click.secho("Database reset — all tables recreated and reference data seeded.", fg="green")


@app.cli.command("db-drop")
def db_drop():
    """Drop every table (destructive — data is lost)."""
    _drop_all_cascade()
    click.secho("All tables dropped.", fg="yellow")


@app.cli.command("link-units")
@click.argument("course_id")
@click.argument("unit_ids", nargs=-1, required=True)
def link_units(course_id: str, unit_ids: tuple) -> None:
    """Link units to a course by ID. Use 'flask list-courses' and 'flask list-units' to find IDs."""
    import uuid as _uuid
    try:
        course = Course.query.get(_uuid.UUID(course_id))
    except ValueError:
        click.secho(f"Invalid course ID: {course_id}", fg="red")
        return
    if not course:
        click.secho(f"No course found with ID: {course_id}", fg="red")
        return

    click.secho(f"Course: {course.name}", fg="cyan")

    linked, skipped, not_found = [], [], []
    for uid in unit_ids:
        try:
            unit = Unit.query.get(_uuid.UUID(uid))
        except ValueError:
            not_found.append(uid)
            continue
        if not unit:
            not_found.append(uid)
        elif unit in course.units:
            skipped.append(unit.code)
        else:
            course.units.append(unit)
            linked.append(unit.code)

    if linked:
        db.session.commit()
        for code in linked:
            click.secho(f"  + {code}", fg="green")
    for code in skipped:
        click.secho(f"  ~ {code} (already linked)", fg="yellow")
    for uid in not_found:
        click.secho(f"  ! {uid} (not found)", fg="red")


@app.cli.command("list-courses")
def list_courses() -> None:
    """List all courses with their IDs."""
    for c in Course.query.order_by(Course.name).all():
        click.echo(f"{c.id}  {c.name}")


@app.cli.command("list-units")
def list_units() -> None:
    """List all units with their IDs."""
    for u in Unit.query.order_by(Unit.code).all():
        click.echo(f"{u.id}  {u.code}  {u.name}")


@app.cli.command("make-admin")
@click.argument("email")
def make_admin(email: str) -> None:
    """Grant admin privileges to the user with the given EMAIL."""
    user = User.query.filter_by(email=email).first()
    if not user:
        click.secho(f"No user found with email: {email}", fg="red")
        return
    user.role = "admin"
    db.session.commit()
    click.secho(f"✓ {email} is now an admin.", fg="green")

# ---------------------------------------------------------------------------
# Fake data pools
# ---------------------------------------------------------------------------

FEMALE_FIRST = [
    "Amina", "Beatrice", "Cynthia", "Diana", "Esther", "Faith", "Grace",
    "Hellen", "Irene", "Joyce", "Karen", "Lydia", "Mary", "Nancy", "Olive",
    "Pauline", "Queen", "Rose", "Sarah", "Tabitha", "Umi", "Violet", "Wanjiru",
]

MALE_FIRST = [
    "Aaron", "Brian", "Collins", "Dennis", "Edwin", "Francis", "George",
    "Hassan", "Ian", "James", "Kevin", "Linus", "Michael", "Newton", "Oscar",
    "Patrick", "Quentin", "Robert", "Samuel", "Thomas", "Umar", "Victor",
    "Walter", "Xavier", "Yusuf", "Zack",
]

LAST_NAMES = [
    "Waweru", "Kamau", "Odhiambo", "Mwangi", "Otieno", "Ndung'u", "Kimani",
    "Kariuki", "Mutua", "Njoroge", "Achieng", "Omondi", "Mburu", "Gitau",
    "Chebet", "Koech", "Langat", "Ruto", "Kiptoo", "Sang", "Juma", "Omar",
    "Abdi", "Hassan", "Mugo", "Njeru", "Maina", "Wambua", "Kilonzo",
]

PHONE_PREFIXES = ["0700", "0710", "0720", "0722", "0723", "0733", "0740", "0790"]


def _student_id(serial: int) -> str:
    return f"ST03/{serial:05d}/2025"


def _email(student_id: str) -> str:
    return student_id.replace("/", "") + "@students.ouk.ac.ke"


def _phone() -> str:
    return random.choice(PHONE_PREFIXES) + str(random.randint(100000, 999999))


def _make_student(serial: int, gender: str, course_id: int, units: list) -> Student:
    first = random.choice(FEMALE_FIRST if gender == "female" else MALE_FIRST)
    last = random.choice(LAST_NAMES)
    sid = _student_id(serial)
    return Student(
        name=f"{first} {last}",
        student_id=sid,
        gender=gender,
        email=_email(sid),
        phone=_phone(),
        course_id=course_id,
        units=units,
    )


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------

@app.cli.command("fake")
@click.option("--count", default=20, show_default=True, help="Number of students to create.")
@click.option("--reset", is_flag=True, help="Delete all existing students and groups first.")
def fake(count: int, reset: bool) -> None:
    """Populate the database with fake student data."""

    if reset:
        Student.query.delete()
        Group.query.delete()
        db.session.commit()
        click.echo("Cleared existing students and groups.")

    # Find the next available serial number
    start_serial = 34000 + Student.query.count() + 1

    created = 0
    skipped = 0

    course_ids = [c.id for c in Course.query.all()]
    if not course_ids:
        click.secho("No courses found — run the server once to seed them first.", fg="red")
        return

    all_units = Unit.query.all()

    for i in range(count):
        serial = start_serial + i

        # Guarantee at least 30 % female so groups can satisfy the constraint
        gender = "female" if random.random() < 0.4 else "male"
        course_id = random.choice(course_ids)
        # Each student picks 3–6 random units
        units = random.sample(all_units, k=min(random.randint(3, 6), len(all_units)))

        student = _make_student(serial, gender, course_id, units)

        if Student.query.filter_by(student_id=student.student_id).first():
            skipped += 1
            continue

        db.session.add(student)

        try:
            assign_group(student)
            db.session.commit()
            created += 1
            click.echo(f"  + {student.name} ({student.gender}, {student.course.name}) → {student.group.name}")
        except ValueError as exc:
            db.session.rollback()
            click.secho(f"  ! {exc}", fg="yellow")
            break

    click.secho(
        f"\nDone — {created} student(s) created, {skipped} skipped.",
        fg="green",
    )


if __name__ == "__main__":
    app.cli.main()
