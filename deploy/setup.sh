#!/usr/bin/env bash
# =============================================================================
# Snap Buzz — one-time server setup for Ubuntu (EC2).
#
# Usage (run as the normal 'ubuntu' user from inside the cloned repo):
#
#   bash deploy/setup.sh                              # no domain: HTTP on public IP
#   bash deploy/setup.sh snap.example.com you@mail.com  # domain: HTTPS via Let's Encrypt
#
# Safe to re-run. Never overwrites an existing .env, database or media.
# =============================================================================
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_USER="$(id -un)"
SERVICE=snapbuzz
PY_VERSION=3.14

say() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }

if [[ "$APP_USER" == "root" ]]; then
  echo "Run this as your normal user (e.g. ubuntu), not root. It uses sudo where needed." >&2
  exit 1
fi
if [[ -n "$DOMAIN" && -z "$EMAIL" ]]; then
  echo "With a domain, also pass an email for Let's Encrypt: bash deploy/setup.sh $DOMAIN you@mail.com" >&2
  exit 1
fi

# --- 1. System packages ------------------------------------------------------
say "Installing system packages (nginx, redis, certbot)"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  nginx redis-server git curl sqlite3 certbot python3-certbot-nginx
sudo systemctl enable --now redis-server

# --- 2. Python 3.14 + virtualenv via uv --------------------------------------
if ! command -v uv >/dev/null 2>&1 && [[ ! -x "$HOME/.local/bin/uv" ]]; then
  say "Installing uv (Python manager)"
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

say "Creating virtualenv with Python $PY_VERSION"
cd "$APP_DIR"
[[ -d .venv ]] || uv venv --python "$PY_VERSION" .venv
uv pip install --python .venv/bin/python -r requirements.txt

# --- 3. Work out host name ---------------------------------------------------
if [[ -n "$DOMAIN" ]]; then
  HOST="$DOMAIN"
  SCHEME=https
else
  TOKEN="$(curl -s -X PUT http://169.254.169.254/latest/api/token \
            -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
  HOST="$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
            http://169.254.169.254/latest/meta-data/public-ipv4 || true)"
  [[ -n "$HOST" ]] || HOST="$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')"
  SCHEME=http
fi
say "Host: $HOST ($SCHEME)"

# --- 4. .env (created once, never overwritten) -------------------------------
if [[ ! -f .env ]]; then
  say "Creating .env with a fresh secret key"
  SECRET="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))')"
  cat > .env <<EOF
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=$SECRET
DJANGO_ALLOWED_HOSTS=$HOST,localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=$SCHEME://$HOST
DJANGO_HTTPS=$([[ $SCHEME == https ]] && echo true || echo false)
REDIS_URL=redis://127.0.0.1:6379/0
EOF
  chmod 600 .env
else
  say ".env already exists — leaving it unchanged"
fi

# --- 5. Django: migrate + static ---------------------------------------------
say "Running migrations and collectstatic"
mkdir -p media/avatar media/snaps media/stories
set -a; source .env; set +a
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py check --deploy || true

# --- 6. systemd service (Daphne) ---------------------------------------------
say "Installing systemd service '$SERVICE'"
sed -e "s#__APP_DIR__#$APP_DIR#g" -e "s#__APP_USER__#$APP_USER#g" \
  deploy/snapbuzz.service | sudo tee /etc/systemd/system/$SERVICE.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

# --- 7. Nginx ----------------------------------------------------------------
say "Configuring Nginx"
# Nginx (www-data) must be able to traverse into the app dir to serve static/media
chmod o+x "$APP_DIR"
d="$APP_DIR"; while [[ "$d" != "/" ]]; do sudo chmod o+x "$d"; d="$(dirname "$d")"; done

sed -e "s#__SERVER_NAME__#$HOST#g" -e "s#__APP_DIR__#$APP_DIR#g" \
  deploy/nginx.conf | sudo tee /etc/nginx/sites-available/$SERVICE >/dev/null
sudo ln -sf /etc/nginx/sites-available/$SERVICE /etc/nginx/sites-enabled/$SERVICE
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# --- 8. HTTPS ----------------------------------------------------------------
if [[ -n "$DOMAIN" ]]; then
  say "Requesting Let's Encrypt certificate for $DOMAIN"
  sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect
fi

# --- Done --------------------------------------------------------------------
sleep 2
if systemctl is-active --quiet "$SERVICE"; then
  say "Done! Open: $SCHEME://$HOST"
else
  echo "Service failed to start. Logs:  sudo journalctl -u $SERVICE -n 50 --no-pager" >&2
  exit 1
fi
if [[ "$SCHEME" == http ]]; then
  echo "NOTE: Without HTTPS, browsers block the Camera and Snap Map (location)."
  echo "      Point a domain at this IP and re-run: bash deploy/setup.sh your.domain you@mail.com"
  echo "      (delete .env first so it regenerates with the domain, or edit it by hand)"
fi
echo "Create an admin user:  cd $APP_DIR && set -a && source .env && set +a && .venv/bin/python manage.py createsuperuser"
