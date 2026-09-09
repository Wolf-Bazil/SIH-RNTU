#!/usr/bin/env bash
# Complete removal of ORCA from vps1.eteon.net. Run as root.
#
# Removes: the orca containers, images, volumes and network; /opt/orca;
# the orca nginx site; the orca.eteon.net certificate lineage.
#
# Does not touch: eteon.service, the eteon nginx site, the eteon.net
# certificate, the evolution stack, or any shared docker image layer still
# referenced by another container.

set -uo pipefail

APP_DIR="/opt/orca"
DOMAIN="orca.eteon.net"
COMPOSE_FILE="${APP_DIR}/deploy/docker-compose.prod.yml"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }

log "Stopping and removing the orca stack"
if [ -f "${COMPOSE_FILE}" ]; then
    docker compose -f "${COMPOSE_FILE}" down -v --rmi local --remove-orphans
else
    # Fall back to the project label if the compose file is already gone.
    docker ps -aq --filter "label=com.docker.compose.project=orca" | xargs -r docker rm -f
    docker network rm orca_net 2>/dev/null
fi

log "Removing ${APP_DIR}"
rm -rf "${APP_DIR}"

log "Removing the nginx site"
rm -f /etc/nginx/sites-enabled/orca /etc/nginx/sites-available/orca
if nginx -t; then
    systemctl reload nginx
else
    echo "nginx config test failed after removal -- inspect before reloading" >&2
fi

log "Removing the TLS certificate"
certbot delete --cert-name "${DOMAIN}" --non-interactive 2>/dev/null \
    || echo "no ${DOMAIN} certificate to delete"

log "Remaining orca artifacts (should be empty)"
docker ps -a --filter "name=orca" --format '{{.Names}}'
docker network ls --filter "name=orca" --format '{{.Name}}'
ls -d "${APP_DIR}" 2>/dev/null

log "Done. Delete the orca DNS record in Cloudflare to finish."
