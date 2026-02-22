# Grouper

Peer learning — auto-assigns OUK students into balanced study groups.

## Docker setup (recommended)

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Run

```bash
docker compose up --build
```

The app will be available at **http://localhost**.

The database schema and reference data (courses, units) are created automatically on first startup.

### Stop

```bash
docker compose down
```

### Database management

Reset the database (drops all tables, recreates schema, re-seeds reference data):

```bash
docker compose exec backend flask db-reset
```

Drop all tables without recreating:

```bash
docker compose exec backend flask db-drop
```

Full wipe including the Postgres volume (completely clean slate):

```bash
docker compose down -v
docker compose up
```

### Generate fake student data

```bash
docker compose exec backend flask fake --count 30
```

Use `--reset` to clear existing students and groups first:

```bash
docker compose exec backend flask fake --count 30 --reset
```

### Configuration

The following environment variables can be set in `docker-compose.yml`:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | PostgreSQL connection string |
| `SECRET_KEY` | `change-me-in-production` | Flask session secret — change this before deploying |

---

## Local development (without Docker)

### Prerequisites

- Python 3.11+
- [Bun](https://bun.sh)

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask db-create   # create tables and seed reference data (run once)
python manage.py
```

### Frontend

```bash
cd ui
bun install
bun run dev
```

The Vite dev server proxies `/api` requests to the Flask backend on port 5000.
