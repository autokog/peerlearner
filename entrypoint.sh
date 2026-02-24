#!/bin/sh
set -e

# Bring schema up to date via Alembic.
# If the DB was previously bootstrapped with db.create_all() (no alembic_version table),
# stamp it at head so Alembic adopts the existing schema without re-running DDL.
if ! flask db upgrade; then
    flask db stamp head
    flask db upgrade
fi

flask db-create
exec gunicorn --bind 0.0.0.0:8080 --workers 2 manage:app
