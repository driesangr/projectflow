#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# deploy-staging.sh  <git-tag>  [api-base-url]
#
# Baut versionierte Docker-Images aus dem angegebenen Git-Tag und startet
# eine Staging-Umgebung parallel zur Dev-Umgebung.
#
# Ports:  Frontend  → http://localhost:5174
#         Backend   → http://localhost:8001
#         Postgres  → localhost:5433
#
# Beispiel:
#   ./deploy-staging.sh v0.0.1
#   ./deploy-staging.sh v0.0.1 http://staging.projectflow.local:8001
# ---------------------------------------------------------------------------
set -euo pipefail

TAG="${1:-}"
API_URL="${2:-http://localhost:8001}"

if [[ -z "$TAG" ]]; then
  echo "Verwendung: $0 <git-tag> [api-base-url]"
  echo "Beispiel:   $0 v0.0.1"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
WORKTREE_DIR="$(mktemp -d /tmp/projectflow-staging-XXXXXX)"

# Worktree beim Beenden immer aufräumen
cleanup() {
  echo ""
  echo "==> Räume temporären Worktree auf …"
  git -C "$REPO_ROOT" worktree remove --force "$WORKTREE_DIR" 2>/dev/null || true
  rm -rf "$WORKTREE_DIR"
}
trap cleanup EXIT

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  ProjectFlow Staging Deploy                      ║"
echo "║  Tag : $TAG"
echo "║  API : $API_URL"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# --- 1. Tag in temporären Worktree auschecken ---------------------------------
echo "==> Checke Tag '$TAG' in temporären Worktree aus …"
git -C "$REPO_ROOT" worktree add "$WORKTREE_DIR" "$TAG"

# --- 2. Backend-Image bauen ---------------------------------------------------
echo ""
echo "==> Baue Backend-Image  projectflow-backend:$TAG …"
docker build \
  -t "projectflow-backend:$TAG" \
  "$WORKTREE_DIR/backend"

# --- 3. Frontend-Image bauen (VITE_API_BASE_URL einbacken) -------------------
echo ""
echo "==> Baue Frontend-Image projectflow-frontend:$TAG …"
echo "    VITE_API_BASE_URL=$API_URL"
docker build \
  --build-arg "VITE_API_BASE_URL=$API_URL" \
  -t "projectflow-frontend:$TAG" \
  "$WORKTREE_DIR/frontend"

# --- 4. Staging-Umgebung starten ---------------------------------------------
echo ""
echo "==> Starte Staging-Umgebung (Compose-Projekt: projectflow-staging) …"
VERSION="$TAG" docker compose \
  -f "$REPO_ROOT/docker-compose.staging.yml" \
  -p "projectflow-staging" \
  up -d --force-recreate

echo ""
echo "✓ Staging-Umgebung läuft:"
echo ""
echo "   Frontend  →  http://localhost:5174"
if [[ "$API_URL" != "http://localhost:8001" ]]; then
  echo "              http://$( echo "$API_URL" | sed 's|http://||' | cut -d: -f1 ):5174"
fi
echo "   Backend   →  http://localhost:8001"
echo "   Postgres  →  localhost:5433"
echo ""
echo "Stoppen mit:"
echo "   docker compose -f docker-compose.staging.yml -p projectflow-staging down"
echo ""
echo "Stoppen + DB-Volume löschen:"
echo "   docker compose -f docker-compose.staging.yml -p projectflow-staging down -v"
echo ""
