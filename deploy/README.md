# Deploying Snap Buzz to EC2 (Ubuntu)

Stack on the server: **Nginx** (HTTPS, static/media, WebSocket proxy) → **Daphne** (Django + Channels, systemd) → **Redis** (channel layer). Database stays SQLite.

## 1. AWS console (one time)

- **Security group** inbound rules: `22` (SSH, ideally *My IP* only), `80` and `443` (Anywhere). Do **not** open `8000`.
- **Elastic IP** (recommended): allocate one and associate it with the instance so the IP doesn't change on restart.
- **Domain** (strongly recommended): add an `A` record pointing to the Elastic IP.
  Browsers only allow **camera** and **location** on HTTPS, so without a domain the Camera page and Snap Map won't work.

## 2. First deploy

SSH in, then:

```bash
sudo mkdir -p /srv/snapbuzz && sudo chown $USER:$USER /srv/snapbuzz
git clone https://github.com/Ishangupta-cyber/Snap-Buzz.git /srv/snapbuzz
cd /srv/snapbuzz

# With a domain (HTTPS, everything works):
bash deploy/setup.sh snap.yourdomain.com you@email.com

# Without a domain (HTTP on the public IP; camera/map blocked by browsers):
bash deploy/setup.sh
```

The script installs Nginx/Redis/Certbot, Python 3.14 (via `uv`), creates `.env` with a random secret key,
runs migrations + collectstatic, and starts the `snapbuzz` service.

Create an admin account:

```bash
cd /srv/snapbuzz && set -a && source .env && set +a
.venv/bin/python manage.py createsuperuser
```

## 3. Updating after you push new code

```bash
cd /srv/snapbuzz && bash deploy/update.sh
```

## Useful commands

| What | Command |
|---|---|
| App logs (live) | `sudo journalctl -u snapbuzz -f` |
| Restart app | `sudo systemctl restart snapbuzz` |
| Nginx errors | `sudo tail -f /var/log/nginx/error.log` |
| Edit settings | `nano /srv/snapbuzz/.env` then restart |
| Backup DB | `sqlite3 /srv/snapbuzz/db.sqlite3 ".backup ~/db-$(date +%F).sqlite3"` |

## Adding a domain later

Point the domain's A record at the server, then:

```bash
cd /srv/snapbuzz
rm .env   # regenerates with the domain (new secret key -> everyone gets logged out once)
bash deploy/setup.sh snap.yourdomain.com you@email.com
```
