#!/bin/bash
# Makes a cloud session ready to run `pytest`, `mypy` and `pre-commit`.
# The container starts with Postgres and Redis installed but stopped, no database and
# no virtualenv. Safe to re-run.
set -euo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

# The settings default to a socket connection as the shell user, which has no Postgres
# role in the container, so point Django at the postgres account the same way CI does.
if [ ! -f .env ]; then
  cat > .env <<'EOF'
export DATABASE_URL=postgres://postgres:postgres@localhost:5432/my_hebrew_dates
export REDIS_URL=redis://localhost:6379/0
EOF
fi

pg_isready -q || service postgresql start
until pg_isready -q; do sleep 1; done
su postgres -c "psql -tAc \"ALTER USER postgres WITH PASSWORD 'postgres'\"" >/dev/null
su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='my_hebrew_dates'\"" | grep -q 1 \
  || su postgres -c "createdb my_hebrew_dates"

redis-cli ping >/dev/null 2>&1 || redis-server --daemonize yes >/dev/null

[ -x venv/bin/python ] || python3 -m venv venv
venv/bin/pip install --quiet -r requirements/local.txt

# Later Bash calls in the session pick up the virtualenv without activating it by hand.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "source \"$PWD/venv/bin/activate\"" >> "$CLAUDE_ENV_FILE"
fi

# Import the whole project, so a session never starts believing it can run the tests when
# something the suite imports is broken.
venv/bin/python manage.py check >/dev/null

echo "Ready: Postgres and Redis up, my_hebrew_dates database present, $(venv/bin/python -V) and dependencies installed."
