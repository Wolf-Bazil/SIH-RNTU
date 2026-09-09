#!/usr/bin/env bash
# ORCA installer for vps1.eteon.net. Run as root on the VPS.
#
# Everything this script creates lives in exactly two places:
#   /opt/orca                                  (code, .env, containers)
#   /etc/nginx/sites-{available,enabled}/orca  (one site file + symlink)
# plus a Let's Encrypt lineage named orca.eteon.net.
# uninstall.sh removes precisely those and nothing else.
#
# The eteon Next.js service (127.0.0.1:3000) and the evolution stack
# (127.0.0.1:8080) are never touched.

set -euo pipefail

REPO_URL="https://github.com/Wolf-Bazil/SIH-RNTU.git"
APP_DIR="/opt/orca"
DOMAIN="orca.eteon.net"
PORT="8100"
COMPOSE_FILE="${APP_DIR}/deploy/docker-compose.prod.yml"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "run as root"

log "Checking the port is still free"
if ss -tln | grep -qE "127\.0\.0\.1:${PORT}\b"; then
    die "127.0.0.1:${PORT} is already in use. Pick another port and update deploy/docker-compose.prod.yml and deploy/orca.nginx.conf."
fi

log "Ensuring the docker compose plugin is present"
if ! docker compose version >/dev/null 2>&1; then
    apt-get update -qq
    # Docker here comes from Ubuntu's own `docker.io` package, which pairs with
    # `docker-compose-v2`. Docker's upstream repo calls it
    # `docker-compose-plugin`. Try whichever this host actually offers.
    if apt-cache show docker-compose-v2 >/dev/null 2>&1; then
        apt-get install -y docker-compose-v2
    else
        apt-get install -y docker-compose-plugin
    fi
    docker compose version >/dev/null 2>&1 || die "docker compose plugin still unavailable"
fi

log "Fetching the code into ${APP_DIR}"
# The directory usually already exists, because .env has to be copied in
# before the first run. Initialise in place rather than cloning, so a
# non-empty target is not an error and .env is never disturbed.
if [ ! -d "${APP_DIR}/.git" ]; then
    mkdir -p "${APP_DIR}"
    git -C "${APP_DIR}" init -q
    git -C "${APP_DIR}" remote add origin "${REPO_URL}"
fi
git -C "${APP_DIR}" remote set-url origin "${REPO_URL}"
git -C "${APP_DIR}" fetch --depth 1 origin main
# Tracked files are forced to match origin/main; .env is untracked and so is
# left alone by both reset and clean.
git -C "${APP_DIR}" reset --hard origin/main
git -C "${APP_DIR}" clean -fd -e .env

# .env is gitignored, so it never arrives with the clone. Copy it up first:
#   scp .env root@160.250.205.84:/opt/orca/.env
[ -f "${APP_DIR}/.env" ] || die "${APP_DIR}/.env is missing. Copy it from your machine:
    scp .env root@160.250.205.84:${APP_DIR}/.env"
chmod 600 "${APP_DIR}/.env"

log "Building and starting the orca stack"
docker compose -f "${COMPOSE_FILE}" up -d --build

log "Waiting for the backend to report healthy"
for i in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
        echo "backend healthy after ${i}0s"
        break
    fi
    [ "$i" -eq 30 ] && die "backend did not become healthy. Inspect: docker compose -f ${COMPOSE_FILE} logs"
    sleep 10
done

log "Installing the nginx site"
install -m 0644 "${APP_DIR}/deploy/orca.nginx.conf" /etc/nginx/sites-available/orca
ln -sfn /etc/nginx/sites-available/orca /etc/nginx/sites-enabled/orca
nginx -t || die "nginx config test failed; the site was written but not reloaded"
systemctl reload nginx

log "Requesting the TLS certificate"
# Separate lineage from eteon.net, so revoking one leaves the other intact.
# The ACME account already exists from the eteon.net certificate, so certbot
# reuses it and asks for nothing.
certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --redirect || \
    die "certbot failed. The site is live over plain HTTP; fix DNS or rerun:
    certbot --nginx -d ${DOMAIN}"

nginx -t && systemctl reload nginx

log "Done. https://${DOMAIN}"
