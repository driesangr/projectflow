#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Project Flow – Deploy Script
#
# Usage:
#   ./deploy.sh staging              # neuester Git-Tag
#   ./deploy.sh staging v0.3.1      # bestimmter Tag
#   ./deploy.sh production v0.3.1
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
git fetch --tags
git checkout "${VERSION}" 2>/dev/null || git pull origin master

# ── 2. Docker Images bauen ────────────────────────────────────────────────────
echo -e "${YELLOW}[2/4] Docker Images bauen (${VERSION})...${NC}"
VERSION="${VERSION}" docker compose -f "${COMPOSE_FILE}" build

# ── 3. Container neu starten ──────────────────────────────────────────────────
# Alembic-Migrationen laufen automatisch beim Backend-Start (CMD im Dockerfile)
echo -e "${YELLOW}[3/4] Container neu starten...${NC}"
VERSION="${VERSION}" docker compose -f "${COMPOSE_FILE}" up -d

# ── 4. Health Check ───────────────────────────────────────────────────────────
echo -e "${YELLOW}[4/4] Health Check...${NC}"
sleep 8

# Backend-Port aus Compose-Datei ermitteln
BACKEND_PORT=$(grep -A1 'backend:' "${COMPOSE_FILE}" | grep -oP '"\K[0-9]+(?=:8000)' | head -1 || echo "8000")

if curl -sf "http://localhost:${BACKEND_PORT}/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}  Backend (Port ${BACKEND_PORT}): OK${NC}"
else
    echo -e "${YELLOW}  WARNUNG: Backend auf Port ${BACKEND_PORT} nicht erreichbar.${NC}"
    echo "  Logs prüfen: docker compose -f ${COMPOSE_FILE} logs backend --tail=50"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Deploy abgeschlossen: ${ENVIRONMENT} @ ${VERSION}${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo ""
