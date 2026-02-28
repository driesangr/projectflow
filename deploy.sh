#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Project Flow – Deploy Script
#
# Usage:
#   ./deploy.sh staging              # neuester Git-Tag
#   ./deploy.sh staging v0.3.1      # bestimmter Tag
#   ./deploy.sh production v1.0.0
#
# Voraussetzungen:
#   - .env.staging bzw. .env.production muss existieren (aus .example kopieren)
#   - Docker + Docker Compose installiert
#   - git pull läuft (SSH-Key oder Credentials hinterlegt)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ENVIRONMENT=${1:-staging}
VERSION=${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo "latest")}

COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"
ENV_FILE=".env.${ENVIRONMENT}"
COMPOSE_PROJECT="projectflow-${ENVIRONMENT}"

# ── Farben ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Project Flow – Deploy                ║"
echo "╚══════════════════════════════════════════╝"
echo "  Umgebung : ${ENVIRONMENT}"
echo "  Version  : ${VERSION}"
echo "  Compose  : ${COMPOSE_FILE}"
echo ""

# ── Sicherheitsabfrage bei Production ─────────────────────────────────────────
if [[ "${ENVIRONMENT}" == "production" ]]; then
    echo -e "${RED}ACHTUNG: Ziel ist PRODUCTION!${NC}"
    read -r -p "Wirklich deployen? [ja/N] "
    if [[ ! "${REPLY}" == "ja" ]]; then
        echo "Abgebrochen."
        exit 0
    fi
fi

# ── Prüfungen ─────────────────────────────────────────────────────────────────
if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo -e "${RED}ERROR: $COMPOSE_FILE nicht gefunden.${NC}"
    exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}ERROR: $ENV_FILE nicht gefunden.${NC}"
    echo "  Vorlage kopieren: cp ${ENV_FILE}.example ${ENV_FILE}"
    echo "  Dann Passwörter und SECRET_KEY anpassen."
    exit 1
fi

# ── 1. Code aktualisieren ─────────────────────────────────────────────────────
echo -e "${YELLOW}[1/4] Code aktualisieren...${NC}"
git fetch --tags --force
git checkout "${VERSION}" 2>/dev/null || git pull origin master

# ── 2. Docker Images bauen ────────────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Docker Images bauen (${VERSION})...${NC}"
VERSION="${VERSION}" docker compose -p "${COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" build

# ── 3. Container neu starten ──────────────────────────────────────────────────
# DB wird nur gestartet, falls noch nicht running (verhindert Naming-Konflikte).
# Alembic-Migrationen laufen automatisch über entrypoint.sh beim Backend-Start.
echo -e "${YELLOW}[3/4] Container neu starten...${NC}"
VERSION="${VERSION}" docker compose -p "${COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" up -d --no-recreate db 2>/dev/null || true
VERSION="${VERSION}" docker compose -p "${COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" up -d backend frontend

# ── 4. Health Check ───────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Health Check...${NC}"
sleep 8

if [[ "${ENVIRONMENT}" == "production" ]]; then
    # In production the backend is not exposed; check via the frontend nginx proxy
    FRONTEND_PORT=$(grep -oP '"\K[0-9]+(?=:80")' "${COMPOSE_FILE}" | head -1 || echo "8080")
    if curl -sf "http://localhost:${FRONTEND_PORT}/api/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}  Frontend+API (Port ${FRONTEND_PORT}): OK${NC}"
    else
        echo -e "${YELLOW}  WARNUNG: Nicht erreichbar auf Port ${FRONTEND_PORT}.${NC}"
        echo "  Logs prüfen: docker compose -p ${COMPOSE_PROJECT} -f ${COMPOSE_FILE} logs --tail=50"
    fi
else
    # In staging the backend port is exposed directly
    BACKEND_PORT=$(grep -oP '"\K[0-9]+(?=:8000")' "${COMPOSE_FILE}" | head -1 || echo "8000")
    if curl -sf "http://localhost:${BACKEND_PORT}/docs" > /dev/null 2>&1; then
        echo -e "${GREEN}  Backend (Port ${BACKEND_PORT}): OK${NC}"
    else
        echo -e "${YELLOW}  WARNUNG: Backend auf Port ${BACKEND_PORT} nicht erreichbar.${NC}"
        echo "  Logs prüfen: docker compose -p ${COMPOSE_PROJECT} -f ${COMPOSE_FILE} logs backend --tail=50"
    fi
fi

# ── Container-Status ──────────────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}Container-Status:${NC}"
docker compose -p "${COMPOSE_PROJECT}" -f "${COMPOSE_FILE}" ps

echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deploy abgeschlossen: ${ENVIRONMENT} @ ${VERSION}${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo ""
