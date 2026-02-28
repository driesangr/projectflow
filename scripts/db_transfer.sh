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

# Container-Name-Mapping (Docker exec statt lokalem pg_dump)
container_for() {
    case "$1" in
        dev)        echo "6cf45cc547f0_projectflow-db-1" ;;
        staging)    echo "projectflow-staging-db-1" ;;
        production) echo "projectflow-production-db-1" ;;
        *)          echo -e "\033[0;31mERROR: Unbekannte Umgebung '$1'. Gültig: dev | staging | production\033[0m" >&2; exit 1 ;;
    esac
}

SOURCE_ENV=${1:-dev}
TARGET_ENV=${2:-staging}
SOURCE_CONTAINER=$(container_for "$SOURCE_ENV")
TARGET_CONTAINER=$(container_for "$TARGET_ENV")

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
echo "  Quelle : ${SOURCE_ENV} (${SOURCE_CONTAINER})"
echo "  Ziel   : ${TARGET_ENV} (${TARGET_CONTAINER})"
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

echo -e "${YELLOW}[1/3] Dump aus ${SOURCE_ENV} (Container: ${SOURCE_CONTAINER})...${NC}"
docker exec "${SOURCE_CONTAINER}" \
    pg_dump -U "$DB_USER" "$DB_NAME" --no-owner --no-acl \
    > "$DUMP_FILE"
echo "  Dump erstellt: $(du -sh "$DUMP_FILE" | cut -f1)"

echo -e "${YELLOW}[2/3] Ziel-DB leeren (${TARGET_ENV}, Container: ${TARGET_CONTAINER})...${NC}"
docker exec "${TARGET_CONTAINER}" \
    psql -U "$DB_USER" "$DB_NAME" \
    -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" \
    > /dev/null

echo -e "${YELLOW}[3/3] Restore in ${TARGET_ENV} (Container: ${TARGET_CONTAINER})...${NC}"
docker exec -i "${TARGET_CONTAINER}" \
    psql -U "$DB_USER" "$DB_NAME" \
    < "$DUMP_FILE" \
    > /dev/null

rm "$DUMP_FILE"

echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Transfer abgeschlossen: ${SOURCE_ENV} → ${TARGET_ENV}${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo ""
