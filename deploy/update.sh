#!/usr/bin/env bash
# Snap Buzz — pull latest code and restart. Run on the server from the repo:
#   bash deploy/update.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"
export PATH="$HOME/.local/bin:$PATH"

git pull --ff-only
uv pip install --python .venv/bin/python -r requirements.txt

set -a; source .env; set +a
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput

sudo systemctl restart snapbuzz
sleep 2
systemctl is-active --quiet snapbuzz && echo "Updated and running." \
  || { sudo journalctl -u snapbuzz -n 50 --no-pager; exit 1; }
