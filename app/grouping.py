import random
from flask import current_app
from . import db
from .models import Group, Student

_ADJECTIVES = [
    "ancient", "blazing", "bold", "brave", "bright", "calm", "clever",
    "cool", "cosmic", "daring", "dazzling", "eager", "electric", "epic",
    "fancy", "fearless", "fierce", "fluffy", "flying", "frozen", "gentle",
    "glowing", "golden", "happy", "heroic", "hidden", "infinite", "jolly",
    "keen", "kind", "laughing", "legendary", "lively", "lucky", "magnetic",
    "mighty", "mystic", "noble", "orbital", "patient", "peaceful", "playful",
    "polished", "powerful", "quiet", "rapid", "radiant", "resilient", "royal",
    "shining", "silent", "silver", "sleek", "smart", "snappy", "solar",
    "sparkling", "speedy", "stellar", "stoic", "sturdy", "super", "swift",
    "tenacious", "tiny", "turbulent", "unique", "valiant", "vibrant",
    "vigilant", "vivid", "wandering", "warm", "wild", "wise", "witty",
    "zealous", "zesty",
]

_NOUNS = [
    "antelope", "aurora", "bison", "blizzard", "butterfly", "canyon",
    "cascade", "cheetah", "comet", "condor", "cosmos", "crystal", "dune",
    "dynamo", "eclipse", "falcon", "firefly", "fjord", "galaxy", "glacier",
    "grove", "harbor", "horizon", "hydra", "inferno", "jaguar", "lantern",
    "lighthouse", "lynx", "mammoth", "meadow", "meteor", "mountain",
    "nebula", "nexus", "nova", "oasis", "ocean", "orca", "osprey",
    "panther", "phoenix", "pinnacle", "pioneer", "planet", "puma",
    "quasar", "rapids", "raven", "reef", "rocket", "rover", "savanna",
    "sequoia", "serpent", "spark", "storm", "summit", "supernova",
    "tempest", "theorem", "tiger", "titan", "tornado", "torrent",
    "tundra", "typhoon", "valley", "vortex", "voyager", "waterfall",
    "wave", "wildfire", "wolf", "zenith",
]


def _unique_name(existing_names: set) -> str:
    """Generate a random adjective-adjective-noun name not already in use."""
    for _ in range(100):
        name = f"{random.choice(_ADJECTIVES)}-{random.choice(_ADJECTIVES)}-{random.choice(_NOUNS)}"
        if name not in existing_names:
            return name
    # Extremely unlikely fallback
    return f"group-{random.randint(10000, 99999)}"


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
        existing_names = {g.name for g in groups}
        group = Group(name=_unique_name(existing_names))
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
