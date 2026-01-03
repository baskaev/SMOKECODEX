#!/bin/sh
set -e

python - <<'PY'
import time
import psycopg2
from urllib.parse import urlparse
import os

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL not set")
parsed = urlparse(url)

for _ in range(30):
    try:
        conn = psycopg2.connect(
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432,
        )
        conn.close()
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Database not ready")
PY

exec uvicorn app.main:app --host "$APP_HOST" --port "$APP_PORT"
