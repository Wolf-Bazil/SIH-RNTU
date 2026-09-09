# Deploying ORCA to vps1.eteon.net

ORCA runs at `https://orca.eteon.net` alongside the existing workloads on the
box. It shares only the host nginx and the Docker daemon; everything else is
its own.

## What is already on the server

| Workload | How it runs | Port |
|---|---|---|
| eteon (Next.js 15) | `eteon.service`, user `eteon`, bare metal | `127.0.0.1:3000` |
| evolution-api | Docker | `127.0.0.1:8080` |
| evo-postgres | Docker | container-internal `5432` |
| nginx | `nginx.service` | `0.0.0.0:80`, `0.0.0.0:443` |

ORCA takes `127.0.0.1:8100`, which is free. The ORCA backend publishes no host
port at all — it is reachable only from the ORCA web container over the
private `orca_net` bridge.

## Isolation

* Compose project name `orca`, so every container, network and volume is
  prefixed and cannot collide with the evolution stack.
* Dedicated `orca_net` bridge, not attached to any other stack.
* Code and secrets confined to `/opt/orca`.
* One nginx file, `/etc/nginx/sites-available/orca`, plus its symlink. The
  eteon site file is never opened.
* Its own Let's Encrypt lineage, `orca.eteon.net`, separate from the
  `eteon.net` lineage that covers `eteon.net` and `www.eteon.net`.

## Install

1. **DNS.** Cloudflare → eteon.net → DNS → Add record:
   type `A`, name `orca`, IPv4 `160.250.205.84`, proxy **on**, TTL auto.
   Wait for it to resolve before step 4.

2. **Push the code.** The VPS pulls from `main` on GitHub.

   ```bash
   git push origin main
   ```

3. **Copy the secrets.** `.env` is gitignored and never reaches the VPS with
   the clone.

   ```bash
   ssh root@160.250.205.84 'mkdir -p /opt/orca'
   scp .env root@160.250.205.84:/opt/orca/.env
   ```

4. **Run the installer.**

   ```bash
   ssh root@160.250.205.84 'git clone --depth 1 https://github.com/Wolf-Bazil/SIH-RNTU.git /tmp/orca-src && bash /tmp/orca-src/deploy/install.sh; rm -rf /tmp/orca-src'
   ```

   The installer is idempotent — rerunning it redeploys the current `main`.

## Update after a push

```bash
ssh root@160.250.205.84 'bash /opt/orca/deploy/install.sh'
```

## Remove, in one command

```bash
ssh root@160.250.205.84 'bash /opt/orca/deploy/uninstall.sh'
```

Then delete the `orca` DNS record in Cloudflare. Nothing belonging to eteon or
evolution is affected.

## Operations

```bash
# logs
ssh root@160.250.205.84 'docker compose -f /opt/orca/deploy/docker-compose.prod.yml logs -f --tail 100'

# restart
ssh root@160.250.205.84 'docker compose -f /opt/orca/deploy/docker-compose.prod.yml restart'

# status
ssh root@160.250.205.84 'docker compose -f /opt/orca/deploy/docker-compose.prod.yml ps'
```

## Notes

* **SSE.** `/api/alerts/stream` is a long-lived Server-Sent Events response.
  Buffering is disabled at both the host nginx and the container nginx, and
  the read timeout is 24h. ORCA emits an alert every 4 seconds, which stays
  inside Cloudflare's ~100s proxy idle limit.
* **Real client IP.** `/etc/nginx/conf.d/cloudflare-realip.conf` is global, so
  `$remote_addr` is the true client IP in the ORCA site too.
* **CORS.** The backend receives `CORS_ORIGINS=https://orca.eteon.net`. The
  frontend is served from the same origin, so no cross-origin request is made
  in normal use.
* **Memory.** The stack idles well under 1 GB; the box has ~6.7 GB available.
