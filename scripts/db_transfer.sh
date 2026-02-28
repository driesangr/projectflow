#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Project Flow – Datenbankinhalt zwischen Umgebungen übertragen
#
# Usage:
#   ./scripts/db_transfer.sh dev staging        # DEV → Staging
#   ./scripts/db_transfer.sh staging production # Staging → Production
#
# Umgebungs-Ports:
#   dev        → 5432
#   staging    → 5433
#   production → 5434  (falls lokal, sonst direkt auf Server ausführen)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Port-Mapping
port_for() {
    case "$1" in
        dev)        echo "5432" ;;
        staging)    echo "5433" ;;
        production) echo "5434" ;;
        *)          echo -e "\033[0;31mERROR: Unbekannte Umgebung '$1'. Gültig: dev | staging | production\033[0m" >&2; exit 1 ;;
    esac
}

SOURCE_ENV=${1:-dev}
TARGET_ENV=${2:-staging}
SOURCE_PORT=$(port_for "$SOURCE_ENV")
TARGET_PORT=$(port_for "$TARGET_ENV")

DB_USER="projectflow"
DB_NAME="projectflow"
DUMP_FILE="/tmp/projectflow_transfer_$(date +%Y%m%d_%H%M%S).sql"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║     Project Flow – DB Transfer           ║"
echo "╚══════════════════════════════════════════╝"
echo "  Quelle : ${SOURCE_ENV} (Port ${SOURCE_PORT})"
echo "  Ziel   : ${TARGET_ENV} (Port ${TARGET_PORT})"
echo "  Dump   : ${DUMP_FILE}"
echo ""

# Sicherheitsabfrage bei Production als Ziel
if [[ "$TARGET_ENV" == "production" ]]; then
    echo -e "${RED}ACHTUNG: Ziel ist PRODUCTION. Alle Daten werden überschrieben!${NC}"
    read -p "Wirklich fortfahren? [ja/N] " -r
    if [[ ! "$REPLY" == "ja" ]]; then
        echo "Abgebrochen."
        exit 0
    fi
fi

# Passwort aus .env-Datei lesen (falls vorhanden)
ENV_FILE=".env.${SOURCE_ENV}"
if [[ -f "$ENV_FILE" ]]; then
    DB_PASSWORD=$(grep -E '^POSTGRES_PASSWORD=' "$ENV_FILE" | cut -d= -f2 | tr -d '"' | tr -d "'")
else
    DB_PASSWORD="projectflow"
fi

echo -e "${YELLOW}[1/3] Dump aus ${SOURCE_ENV} (Port ${SOURCE_PORT})...${NC}"
PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h localhost -p "$SOURCE_PORT" \
    -U "$DB_USER" "$DB_NAME" \
    --no-owner --no-acl \
    > "$DUMP_FILE"
echo "  Dump erstellt: $(du -sh "$DUMP_FILE" | cut -f1)"

# Ziel-Passwort
ENV_FILE_TARGET=".env.${TARGET_ENV}"
if [[ -f "$ENV_FILE_TARGET" ]]; then
    DB_PASSWORD_TARGET=$(grep -E '^POSTGRES_PASSWORD=' "$ENV_FILE_TARGET" | cut -d= -f2 | tr -d '"' | tr -d "'")
else
    DB_PASSWORD_TARGET="projectflow"
fi

echo -e "${YELLOW}[2/3] Ziel-DB leeren (${TARGET_ENV}, Port ${TARGET_PORT})...${NC}"
PGPASSWORD="$DB_PASSWORD_TARGET" psql \
    -h localhost -p "$TARGET_PORT" \
    -U "$DB_USER" "$DB_NAME" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" \
    > /dev/null

echo -e "${YELLOW}[3/3] Restore in ${TARGET_ENV} (Port ${TARGET_PORT})...${NC}"
PGPASSWORD="$DB_PASSWORD_TARGET" psql \
    -h localhost -p "$TARGET_PORT" \
    -U "$DB_USER" "$DB_NAME" \
    < "$DUMP_FILE" \
    > /dev/null

rm "$DUMP_FILE"

echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Transfer abgeschlossen: ${SOURCE_ENV} → ${TARGET_ENV}${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo ""
