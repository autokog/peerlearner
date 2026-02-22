#!/bin/sh
set -e
flask db-create
exec gunicorn --bind 0.0.0.0:5000 --workers 2 manage:app
