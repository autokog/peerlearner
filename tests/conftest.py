import pytest
from app import create_app, db, seed_db


@pytest.fixture(scope="session")
def app():
    application = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SECRET_KEY": "test-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )
    with application.app_context():
        db.create_all()
        seed_db()
        yield application
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    """A test client that is already logged in as a fresh user."""
    client.post(
        "/api/auth/register",
        json={"email": "testuser@ouk.ac.ke", "password": "password123"},
    )
    yield client
    # Cleanup: delete the user created for this fixture
    with client.application.app_context():
        from app.models import User

        u = User.query.filter_by(email="testuser@ouk.ac.ke").first()
        if u:
            db.session.delete(u)
            db.session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def register_user(client, email="coord@ouk.ac.ke", password="pass1234"):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def login_user(client, email="coord@ouk.ac.ke", password="pass1234"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def logout_user(client):
    return client.post("/api/auth/logout")
