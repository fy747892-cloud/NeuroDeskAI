#!/bin/sh
set -eu

attempt=1
max_attempts="${MIGRATION_MAX_ATTEMPTS:-10}"
sleep_seconds="${MIGRATION_RETRY_SECONDS:-3}"

until alembic upgrade head; do
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "Alembic migration failed after $attempt attempts." >&2
    exit 1
  fi

  echo "Alembic migration failed; retrying in ${sleep_seconds}s (${attempt}/${max_attempts})..." >&2
  attempt=$((attempt + 1))
  sleep "$sleep_seconds"
done

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
