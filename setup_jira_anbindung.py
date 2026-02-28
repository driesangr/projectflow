"""
setup_jira_anbindung.py
=======================
Legt das Topic "Jira Anbindung" im Projekt "Project Flow" an und befüllt es
mit allen Deliverables, User Stories und Tasks für die Jira-Integration.

Ausführen:
    python3 setup_jira_anbindung.py

Voraussetzungen:
    - requests ist in der Backend-Umgebung enthalten (requirements.txt)
    - Project Flow läuft auf http://localhost:8000 (anpassbar via BASE_URL)

Deliverable-Reihenfolge (sequenziell abzuarbeiten):
    J1 | Datenbankmodell: Externe ID-Felder
    J2 | Jira API-Client
    J3 | Import: Jira → Project Flow
    J4 | Export: Project Flow → Jira
    J5 | Sync-Status & Konfliktbehandlung
    J6 | REST-Endpunkte & Frontend-Integration
    J7 | Tests & Dokumentation
"""

import json
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

PROJECT_NAME = "Project Flow"

# ---------------------------------------------------------------------------
# Struktur
# ---------------------------------------------------------------------------

DELIVERABLES_AND_STORIES = [

    # =========================================================================
    # J1 – Datenbankmodell: Externe ID-Felder
    # Muss als erstes abgeschlossen sein – alle weiteren Deliverables bauen darauf auf.
    # =========================================================================
    {
        "title": "J1 | Datenbankmodell: Externe ID-Felder",
        "description": (
            "Erweiterung der bestehenden Modelle (UserStory, Task) um Jira-spezifische "
            "Felder: jira_key, jira_sync_status, last_synced_at. "
            "Inkl. Alembic-Migration und Schema-Erweiterung. "
            "Dieses Deliverable ist Voraussetzung für alle weiteren Deliverables."
        ),
        "user_stories": [
            {
                "title": "J1-1 | Modelle um Jira-Felder erweitern",
                "description": (
                    "Als Entwickler möchte ich, dass UserStory und Task die nötigen "
                    "Jira-Felder kennen, damit eine eindeutige Zuordnung zwischen "
                    "Project Flow Artefakten und Jira Issues möglich ist."
                ),
                "acceptance_criteria": (
                    "• Modell UserStory erhält: jira_key (str, nullable, unique), "
                    "jira_sync_status (enum, nullable), last_synced_at (datetime, nullable)\n"
                    "• Modell Task erhält dieselben drei Felder\n"
                    "• jira_sync_status Enum: synced | modified | conflict\n"
                    "• Bestehende Felder und Funktionalität bleiben unverändert\n"
                    "• Alle neuen Felder sind optional (nullable) – keine Breaking Changes"
                ),
                "story_points": 3,
                "business_value": 10,
                "tasks": [
                    {
                        "title": "Task J1-1.1 | JiraSyncStatus-Enum und Felder in models/user_story.py ergänzen",
                        "description": (
                            "Füge in app/models/user_story.py hinzu:\n"
                            "  import enum\n"
                            "  class JiraSyncStatus(str, enum.Enum):\n"
                            "      synced   = 'synced'\n"
                            "      modified = 'modified'\n"
                            "      conflict = 'conflict'\n\n"
                            "Neue Spalten in UserStory:\n"
                            "  jira_key         = Column(String, nullable=True, unique=True, index=True)\n"
                            "  jira_sync_status = Column(Enum(JiraSyncStatus), nullable=True)\n"
                            "  last_synced_at   = Column(DateTime(timezone=True), nullable=True)"
                        ),
                        "effort_hours": 0.5,
                    },
                    {
                        "title": "Task J1-1.2 | Dieselben Felder in models/task.py ergänzen",
                        "description": (
                            "Analog zu J1-1.1: JiraSyncStatus-Enum importieren (aus user_story.py "
                            "oder in eigene app/models/jira.py auslagern) und die drei Spalten "
                            "jira_key, jira_sync_status, last_synced_at zu Task hinzufügen."
                        ),
                        "effort_hours": 0.5,
                    },
                    {
                        "title": "Task J1-1.3 | Schemas (Pydantic) für neue Felder erweitern",
                        "description": (
                            "In app/schemas/user_story.py und app/schemas/task.py:\n"
                            "  • UserStoryResponse und TaskResponse um die drei neuen Felder ergänzen\n"
                            "  • Felder sind Optional[str] / Optional[JiraSyncStatus] / Optional[datetime]\n"
                            "  • UserStoryUpdate und TaskUpdate: jira_key und jira_sync_status "
                            "ergänzen (last_synced_at wird nur intern gesetzt)"
                        ),
                        "effort_hours": 0.5,
                    },
                ],
            },
            {
                "title": "J1-2 | Alembic-Migration erstellen und anwenden",
                "description": (
                    "Als Entwickler möchte ich eine idempotente Datenbankmigration, "
                    "die die neuen Spalten anlegt ohne bestehende Daten zu verändern."
                ),
                "acceptance_criteria": (
                    "• Neue Migrationsdatei unter alembic/versions/ (fortlaufende Nummer)\n"
                    "• Migration fügt alle 6 neuen Spalten hinzu (3x UserStory, 3x Task)\n"
                    "• Migration ist idempotent (mehrfaches Ausführen ohne Fehler)\n"
                    "• alembic upgrade head läuft ohne Fehler durch\n"
                    "• alembic downgrade -1 macht die Änderungen rückgängig"
                ),
                "story_points": 2,
                "business_value": 10,
                "tasks": [
                    {
                        "title": "Task J1-2.1 | Migrationsdatei generieren und prüfen",
                        "description": (
                            "cd backend && alembic revision --autogenerate "
                            "-m 'add_jira_fields_to_userstory_and_task'\n"
                            "Generierte Datei prüfen: enthält sie alle 6 neuen Spalten? "
                            "Enum-Typ korrekt definiert? upgrade() und downgrade() vollständig?"
                        ),
                        "effort_hours": 0.5,
                    },
                    {
                        "title": "Task J1-2.2 | Migration anwenden und Datenbankzustand verifizieren",
                        "description": (
                            "alembic upgrade head ausführen.\n"
                            "Danach via psql oder SQLAlchemy prüfen:\n"
                            "  SELECT column_name, data_type FROM information_schema.columns\n"
                            "  WHERE table_name IN ('user_stories', 'tasks')\n"
                            "  AND column_name LIKE 'jira%' OR column_name = 'last_synced_at';\n"
                            "Erwartung: 6 neue Spalten vorhanden."
                        ),
                        "effort_hours": 0.5,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # J2 – Jira API-Client
    # Isolierter, testbarer HTTP-Client für die Jira REST API v3 (Cloud).
    # =========================================================================
    {
        "title": "J2 | Jira API-Client",
        "description": (
            "Eigenständiger, wiederverwendbarer Python-Client für die Jira REST API v3 (Cloud). "
            "Kapselt Authentifizierung, HTTP-Kommunikation und Fehlerbehandlung. "
            "Wird von Import- und Export-Services genutzt. "
            "Voraussetzung: J1 abgeschlossen."
        ),
        "user_stories": [
            {
                "title": "J2-1 | Jira-Konfiguration und Authentifizierung",
                "description": (
                    "Als Entwickler möchte ich, dass Jira-Credentials sicher über "
                    "Umgebungsvariablen konfiguriert werden, damit keine Zugangsdaten "
                    "im Code landen."
                ),
                "acceptance_criteria": (
                    "• Neue Umgebungsvariablen: JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN\n"
                    "• Konfiguration in app/core/config.py ergänzt (Pydantic BaseSettings)\n"
                    "• Fehlende Konfiguration wirft beim Start einen klaren Fehler\n"
                    "• .env.example enthält die drei neuen Variablen mit Platzhaltern\n"
                    "• Jira-Konfiguration ist optional – fehlt sie, ist die Jira-Funktionalität "
                    "deaktiviert ohne dass die App abstürzt"
                ),
                "story_points": 2,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task J2-1.1 | Jira-Settings in app/core/config.py ergänzen",
                        "description": (
                            "In app/core/config.py (Pydantic BaseSettings):\n"
                            "  jira_base_url:    Optional[str] = None  # z.B. https://mein.atlassian.net\n"
                            "  jira_user_email:  Optional[str] = None\n"
                            "  jira_api_token:   Optional[str] = None\n\n"
                            "  @property\n"
                            "  def jira_enabled(self) -> bool:\n"
                            "      return all([self.jira_base_url, self.jira_user_email, self.jira_api_token])"
                        ),
                        "effort_hours": 0.5,
                    },
                    {
                        "title": "Task J2-1.2 | .env.example um Jira-Variablen ergänzen",
                        "description": (
                            "Füge in .env.example hinzu:\n"
                            "  # Jira Integration (optional)\n"
                            "  JIRA_BASE_URL=https://your-instance.atlassian.net\n"
                            "  JIRA_USER_EMAIL=your@email.com\n"
                            "  JIRA_API_TOKEN=your_api_token_here"
                        ),
                        "effort_hours": 0.25,
                    },
                ],
            },
            {
                "title": "J2-2 | JiraClient-Klasse implementieren",
                "description": (
                    "Als Entwickler möchte ich einen sauberen HTTP-Client, der alle "
                    "nötigen Jira-API-Operationen kapselt, damit Import- und "
                    "Export-Services nicht direkt mit HTTP hantieren müssen."
                ),
                "acceptance_criteria": (
                    "• Klasse JiraClient in app/services/jira_client.py\n"
                    "• Authentifizierung via HTTP Basic Auth (email + API token)\n"
                    "• Methoden: get_issue(key), search_issues(jql, max_results), "
                    "create_issue(payload), update_issue(key, payload), get_project(key)\n"
                    "• Alle Methoden sind async (httpx.AsyncClient)\n"
                    "• HTTP-Fehler werden in aussagekräftige JiraClientError-Exceptions umgewandelt\n"
                    "• Logging aller ausgehenden Requests (DEBUG-Level)"
                ),
                "story_points": 4,
                "business_value": 10,
                "tasks": [
                    {
                        "title": "Task J2-2.1 | JiraClientError und Basisstruktur erstellen",
                        "description": (
                            "Erstelle app/services/jira_client.py:\n"
                            "  class JiraClientError(Exception):\n"
                            "      def __init__(self, status_code: int, message: str): ...\n\n"
                            "  class JiraClient:\n"
                            "      def __init__(self, base_url, email, token): ...\n"
                            "      async def _request(self, method, path, **kwargs) -> dict:\n"
                            "          # httpx.AsyncClient mit Basic Auth\n"
                            "          # Fehlerbehandlung: 401→CredentialsError, 404→NotFound, etc."
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task J2-2.2 | Methoden get_issue, search_issues implementieren",
                        "description": (
                            "get_issue(key: str) → dict:\n"
                            "  GET /rest/api/3/issue/{key}\n"
                            "  Gibt das rohe Jira-Issue-Dict zurück\n\n"
                            "search_issues(jql: str, max_results: int = 50) → list[dict]:\n"
                            "  POST /rest/api/3/issue/search\n"
                            "  Body: {jql, maxResults, fields: [summary, description, status, "
                            "issuetype, priority, assignee, story_points, subtasks, parent]}\n"
                            "  Gibt liste der Issues zurück (paginiert, max_results beachten)"
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task J2-2.3 | Methoden create_issue, update_issue, get_project implementieren",
                        "description": (
                            "create_issue(payload: dict) → dict:\n"
                            "  POST /rest/api/3/issue\n\n"
                            "update_issue(key: str, payload: dict) → None:\n"
                            "  PUT /rest/api/3/issue/{key}\n\n"
                            "get_project(project_key: str) → dict:\n"
                            "  GET /rest/api/3/project/{project_key}\n"
                            "  Wird für Validierung beim Import genutzt"
                        ),
                        "effort_hours": 1.0,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # J3 – Import: Jira → Project Flow
    # =========================================================================
    {
        "title": "J3 | Import: Jira → Project Flow",
        "description": (
            "Import-Service und API-Endpunkt: Liest Issues aus einem Jira-Projekt "
            "und legt sie als User Stories und Tasks in Project Flow an. "
            "Mapping: Epic→Deliverable, Story→UserStory, Sub-task→Task. "
            "Voraussetzungen: J1 und J2 abgeschlossen."
        ),
        "user_stories": [
            {
                "title": "J3-1 | Jira-zu-ProjectFlow Mapping-Logik",
                "description": (
                    "Als Entwickler möchte ich eine saubere Mapping-Funktion, die ein "
                    "Jira-Issue-Dict in ein Project Flow Artefakt-Dict umwandelt."
                ),
                "acceptance_criteria": (
                    "• Funktion map_jira_issue_to_user_story(issue: dict) → UserStoryCreate\n"
                    "• Funktion map_jira_issue_to_task(issue: dict) → TaskCreate\n"
                    "• Mapping: summary→title, description→description, "
                    "story_points→story_points, assignee.displayName→owner_name\n"
                    "• Jira-Status wird auf Project Flow Status gemappt: "
                    "To Do→todo, In Progress→in_progress, Done→done\n"
                    "• jira_key wird aus issue.key gesetzt\n"
                    "• Fehlende Jira-Felder führen nicht zum Absturz (Defaults verwenden)"
                ),
                "story_points": 3,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task J3-1.1 | Mapping-Funktionen in app/services/jira_mapper.py implementieren",
                        "description": (
                            "Erstelle app/services/jira_mapper.py mit:\n"
                            "  JIRA_STATUS_MAP = {\n"
                            "      'To Do': 'todo',\n"
                            "      'In Progress': 'in_progress',\n"
                            "      'Done': 'done',\n"
                            "  }\n\n"
                            "  def map_jira_issue_to_user_story(issue, deliverable_id) -> dict\n"
                            "  def map_jira_issue_to_task(issue, user_story_id) -> dict\n\n"
                            "Beide Funktionen extrahieren Felder aus issue['fields'] und "
                            "geben ein dict zurück, das direkt als Payload für den POST-Endpunkt nutzbar ist."
                        ),
                        "effort_hours": 1.5,
                    },
                ],
            },
            {
                "title": "J3-2 | Import-Service implementieren",
                "description": (
                    "Als Nutzer möchte ich ein gesamtes Jira-Projekt importieren können, "
                    "wobei Epics als Deliverables, Stories als User Stories und "
                    "Sub-tasks als Tasks angelegt werden."
                ),
                "acceptance_criteria": (
                    "• Service-Funktion import_from_jira(jira_project_key, topic_id, db) in "
                    "app/services/jira_import.py\n"
                    "• Epics werden als Deliverables angelegt (oder bestehende per jira_key gefunden)\n"
                    "• Stories werden als User Stories unter dem passenden Deliverable angelegt\n"
                    "• Sub-tasks werden als Tasks unter der passenden User Story angelegt\n"
                    "• Bereits importierte Artefakte (jira_key vorhanden) werden übersprungen, "
                    "nicht doppelt angelegt\n"
                    "• Rückgabe: ImportResult mit Zählern (created, skipped, errors)"
                ),
                "story_points": 5,
                "business_value": 10,
                "tasks": [
                    {
                        "title": "Task J3-2.1 | Import-Service Grundstruktur und Epic-Import",
                        "description": (
                            "Erstelle app/services/jira_import.py:\n"
                            "  class ImportResult: created / skipped / errors\n\n"
                            "  async def import_from_jira(jira_project_key, topic_id, db, jira_client):\n"
                            "      # 1. Alle Epics des Projekts laden (JQL: project=KEY AND issuetype=Epic)\n"
                            "      # 2. Pro Epic: prüfen ob Deliverable mit jira_key existiert\n"
                            "      #    Falls nein: Deliverable anlegen, jira_key setzen\n"
                            "      #    Falls ja: überspringen (skipped++)"
                        ),
                        "effort_hours": 2.0,
                    },
                    {
                        "title": "Task J3-2.2 | Story- und Sub-task-Import implementieren",
                        "description": (
                            "Aufbauend auf J3-2.1:\n"
                            "  # 3. Pro Epic: Stories laden (JQL: project=KEY AND issuetype=Story AND 'Epic Link'=EPIC_KEY)\n"
                            "  #    Story → UserStory anlegen (map_jira_issue_to_user_story)\n"
                            "  #    jira_key, jira_sync_status='synced', last_synced_at=now() setzen\n"
                            "  # 4. Pro Story: Sub-tasks laden\n"
                            "  #    Sub-task → Task anlegen (map_jira_issue_to_task)\n"
                            "  #    jira_key, jira_sync_status='synced', last_synced_at=now() setzen\n"
                            "  # 5. ImportResult zurückgeben"
                        ),
                        "effort_hours": 2.0,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # J4 – Export: Project Flow → Jira
    # =========================================================================
    {
        "title": "J4 | Export: Project Flow → Jira",
        "description": (
            "Export-Service: Schreibt geänderte Project Flow Artefakte zurück nach Jira. "
            "Nur Artefakte mit jira_key und jira_sync_status='modified' werden exportiert. "
            "Voraussetzungen: J1, J2, J3 abgeschlossen."
        ),
        "user_stories": [
            {
                "title": "J4-1 | Modified-Tracking: jira_sync_status automatisch setzen",
                "description": (
                    "Als System möchte ich, dass jira_sync_status automatisch auf 'modified' "
                    "gesetzt wird, wenn ein Artefakt mit jira_key in Project Flow bearbeitet wird."
                ),
                "acceptance_criteria": (
                    "• PUT /user-stories/{id} setzt jira_sync_status auf 'modified', "
                    "falls jira_key gesetzt und Status bisher 'synced' war\n"
                    "• Gleiches gilt für PUT /tasks/{id}\n"
                    "• Änderungen, die nur last_synced_at oder jira_sync_status betreffen, "
                    "lösen kein erneutes 'modified' aus\n"
                    "• Bei neu importierten Artefakten bleibt Status 'synced'"
                ),
                "story_points": 2,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task J4-1.1 | Modified-Tracking in routers/user_stories.py und tasks.py",
                        "description": (
                            "In der update_user_story und update_task Funktion:\n"
                            "Nach dem Setzen der neuen Feldwerte prüfen:\n"
                            "  if story.jira_key and story.jira_sync_status == JiraSyncStatus.synced:\n"
                            "      story.jira_sync_status = JiraSyncStatus.modified\n"
                            "Analog für Tasks."
                        ),
                        "effort_hours": 1.0,
                    },
                ],
            },
            {
                "title": "J4-2 | Export-Service implementieren",
                "description": (
                    "Als Nutzer möchte ich alle 'modified' Artefakte mit einem API-Call "
                    "nach Jira zurückschreiben können."
                ),
                "acceptance_criteria": (
                    "• Service-Funktion export_to_jira(db, jira_client) in app/services/jira_export.py\n"
                    "• Alle UserStories und Tasks mit jira_sync_status='modified' werden geladen\n"
                    "• Pro Artefakt: Jira-Issue via PUT /rest/api/3/issue/{key} aktualisieren\n"
                    "• Felder: summary (←title), description, status (via Transition-API)\n"
                    "• Nach erfolgreichem Export: jira_sync_status='synced', last_synced_at=now()\n"
                    "• Rückgabe: ExportResult mit exported / errors"
                ),
                "story_points": 4,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task J4-2.1 | Export-Service Grundstruktur und Feld-Export",
                        "description": (
                            "Erstelle app/services/jira_export.py:\n"
                            "  class ExportResult: exported / errors\n\n"
                            "  async def export_to_jira(db, jira_client) -> ExportResult:\n"
                            "      # 1. Alle modified UserStories + Tasks laden\n"
                            "      # 2. Pro Artefakt: payload bauen (title→summary, etc.)\n"
                            "      # 3. jira_client.update_issue(jira_key, payload) aufrufen\n"
                            "      # 4. Bei Erfolg: synced + last_synced_at aktualisieren"
                        ),
                        "effort_hours": 2.0,
                    },
                    {
                        "title": "Task J4-2.2 | Status-Export via Jira Transition-API",
                        "description": (
                            "Jira-Status können nicht direkt gesetzt werden – es braucht Transitions.\n"
                            "In jira_client.py ergänzen:\n"
                            "  get_transitions(key: str) → list[dict]  # verfügbare Übergänge\n"
                            "  transition_issue(key: str, transition_id: str) → None\n\n"
                            "In jira_export.py: Wenn sich der Status geändert hat:\n"
                            "  transitions = await jira_client.get_transitions(key)\n"
                            "  passende Transition anhand des Ziel-Status finden und ausführen."
                        ),
                        "effort_hours": 1.5,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # J5 – Sync-Status & Konfliktbehandlung
    # =========================================================================
    {
        "title": "J5 | Sync-Status & Konfliktbehandlung",
        "description": (
            "Erkennung und Behandlung von Konflikten: Wenn ein Artefakt sowohl in "
            "Project Flow als auch in Jira geändert wurde, soll der Konflikt sichtbar "
            "gemacht und auflösbar sein. "
            "Voraussetzungen: J1–J4 abgeschlossen."
        ),
        "user_stories": [
            {
                "title": "J5-1 | Konflikterkennung beim Import",
                "description": (
                    "Als System möchte ich beim erneuten Import erkennen, wenn ein Artefakt "
                    "in Project Flow 'modified' ist und in Jira ebenfalls geändert wurde."
                ),
                "acceptance_criteria": (
                    "• Beim Import: wenn jira_key bereits existiert und jira_sync_status='modified', "
                    "wird das Artefakt auf jira_sync_status='conflict' gesetzt statt überschrieben\n"
                    "• Konflikt-Artefakte werden im ImportResult separat gezählt und gelistet\n"
                    "• Kein automatisches Überschreiben bei Konflikt"
                ),
                "story_points": 3,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task J5-1.1 | Konflikt-Logik in jira_import.py ergänzen",
                        "description": (
                            "Im Import-Service beim Prüfen bestehender Artefakte:\n"
                            "  existing = query by jira_key\n"
                            "  if existing.jira_sync_status == 'modified':\n"
                            "      existing.jira_sync_status = 'conflict'\n"
                            "      result.conflicts.append(existing.id)\n"
                            "      continue  # nicht überschreiben\n"
                            "  else:\n"
                            "      # Felder aktualisieren, status='synced'"
                        ),
                        "effort_hours": 1.0,
                    },
                ],
            },
            {
                "title": "J5-2 | Konflikt-Auflösung API-Endpunkt",
                "description": (
                    "Als Nutzer möchte ich Konflikte über die API auflösen können, "
                    "indem ich entscheide ob die Project Flow Version oder die Jira Version gewinnt."
                ),
                "acceptance_criteria": (
                    "• POST /jira/resolve-conflict/{artifact_type}/{artifact_id}\n"
                    "• Body: { 'resolution': 'keep_local' | 'use_jira' }\n"
                    "• keep_local: jira_sync_status='modified', Artefakt wird beim nächsten "
                    "Export nach Jira geschrieben\n"
                    "• use_jira: Jira-Version wird geladen und Artefakt wird überschrieben, "
                    "jira_sync_status='synced'\n"
                    "• Rückgabe: aktualisiertes Artefakt"
                ),
                "story_points": 3,
                "business_value": 7,
                "tasks": [
                    {
                        "title": "Task J5-2.1 | Konflikt-Auflösungs-Endpunkt in routers/jira.py implementieren",
                        "description": (
                            "Erstelle app/routers/jira.py (wird in J6 in main.py eingebunden):\n"
                            "  POST /jira/resolve-conflict/{artifact_type}/{artifact_id}\n"
                            "  artifact_type: 'user_story' | 'task'\n"
                            "  resolution: 'keep_local' | 'use_jira'\n\n"
                            "  keep_local: status auf 'modified' setzen\n"
                            "  use_jira: jira_client.get_issue(jira_key) → Felder überschreiben → "
                            "status auf 'synced', last_synced_at=now()"
                        ),
                        "effort_hours": 2.0,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # J6 – REST-Endpunkte & Integration
    # =========================================================================
    {
        "title": "J6 | REST-Endpunkte & Integration",
        "description": (
            "Alle Jira-Operationen werden über einen dedizierten /jira-Router "
            "exponiert und in die bestehende FastAPI-App eingebunden. "
            "Voraussetzungen: J1–J5 abgeschlossen."
        ),
        "user_stories": [
            {
                "title": "J6-1 | Jira-Router mit Import- und Export-Endpunkten",
                "description": (
                    "Als Nutzer möchte ich Import und Export über klar definierte "
                    "REST-Endpunkte anstoßen können."
                ),
                "acceptance_criteria": (
                    "• POST /jira/import  → Body: {jira_project_key, topic_id} → ImportResult\n"
                    "• POST /jira/export  → kein Body → ExportResult\n"
                    "• GET  /jira/status  → listet alle Artefakte mit jira_key und deren sync_status\n"
                    "• GET  /jira/conflicts → listet alle Artefakte mit jira_sync_status='conflict'\n"
                    "• Alle Endpunkte erfordern Authentifizierung (require_manager oder höher)\n"
                    "• Router ist in app/main.py eingebunden unter Prefix /jira"
                ),
                "story_points": 3,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task J6-1.1 | /jira/import und /jira/export Endpunkte",
                        "description": (
                            "In app/routers/jira.py:\n"
                            "  router = APIRouter(prefix='/jira', tags=['jira'])\n\n"
                            "  POST /import: JiraClient aus Settings instanziieren, "
                            "import_from_jira(jira_project_key, topic_id, db, jira_client) aufrufen, "
                            "ImportResult zurückgeben\n\n"
                            "  POST /export: export_to_jira(db, jira_client) aufrufen, "
                            "ExportResult zurückgeben"
                        ),
                        "effort_hours": 1.5,
                    },
                    {
                        "title": "Task J6-1.2 | /jira/status und /jira/conflicts Endpunkte",
                        "description": (
                            "GET /jira/status:\n"
                            "  SELECT alle UserStories + Tasks WHERE jira_key IS NOT NULL\n"
                            "  Rückgabe: Liste mit id, title, artifact_type, jira_key, "
                            "jira_sync_status, last_synced_at\n\n"
                            "GET /jira/conflicts:\n"
                            "  WHERE jira_sync_status = 'conflict'\n"
                            "  Rückgabe: analog, aber nur Konflikte"
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task J6-1.3 | Router in app/main.py einbinden",
                        "description": (
                            "In app/main.py:\n"
                            "  from app.routers import jira as jira_router\n"
                            "  app.include_router(jira_router.router)\n\n"
                            "Nur einbinden wenn settings.jira_enabled == True, "
                            "sonst Endpunkte weglassen (graceful degradation)."
                        ),
                        "effort_hours": 0.5,
                    },
                ],
            },
        ],
    },

    # =========================================================================
    # J7 – Tests & Dokumentation
    # =========================================================================
    {
        "title": "J7 | Tests & Dokumentation",
        "description": (
            "Funktionstests für alle Jira-Endpunkte (mit Mock-JiraClient) "
            "und Entwicklerdokumentation. "
            "Voraussetzungen: J1–J6 abgeschlossen."
        ),
        "user_stories": [
            {
                "title": "J7-1 | Funktionstests mit Mock-JiraClient",
                "description": (
                    "Als Entwickler möchte ich die Import/Export-Logik ohne echte "
                    "Jira-Instanz testen können."
                ),
                "acceptance_criteria": (
                    "• Mock-Klasse MockJiraClient mit denselben Methoden wie JiraClient\n"
                    "• Test: Import erstellt korrekte Anzahl Deliverables / UserStories / Tasks\n"
                    "• Test: Export sendet nur 'modified' Artefakte an Jira\n"
                    "• Test: Konflikterkennung setzt Status korrekt auf 'conflict'\n"
                    "• Alle Tests laufen ohne JIRA_API_TOKEN in der Umgebung"
                ),
                "story_points": 4,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task J7-1.1 | MockJiraClient und Import-Tests",
                        "description": (
                            "Erstelle tests/functional/test_jira_import.py:\n"
                            "  Fixture mock_jira_client gibt MockJiraClient zurück mit\n"
                            "  vordefinierten Issues (2 Epics, 3 Stories pro Epic, 2 Sub-tasks)\n\n"
                            "  test_import_creates_deliverables: assert len(deliverables) == 2\n"
                            "  test_import_creates_user_stories: assert len(stories) == 6\n"
                            "  test_import_idempotent: zweiter Import → alles skipped"
                        ),
                        "effort_hours": 2.0,
                    },
                    {
                        "title": "Task J7-1.2 | Export- und Konflikt-Tests",
                        "description": (
                            "tests/functional/test_jira_export.py:\n"
                            "  test_export_only_modified: nur modified Artefakte werden exportiert\n"
                            "  test_export_sets_synced: nach Export ist status='synced'\n\n"
                            "tests/functional/test_jira_conflicts.py:\n"
                            "  test_conflict_detected_on_reimport\n"
                            "  test_resolve_conflict_keep_local\n"
                            "  test_resolve_conflict_use_jira"
                        ),
                        "effort_hours": 2.0,
                    },
                ],
            },
            {
                "title": "J7-2 | Entwicklerdokumentation",
                "description": (
                    "Als Entwickler möchte ich eine klare Dokumentation der Jira-Anbindung, "
                    "damit ich sie konfigurieren, nutzen und erweitern kann."
                ),
                "acceptance_criteria": (
                    "• docs/jira_integration.md erstellt\n"
                    "• Abschnitte: Voraussetzungen, Konfiguration (.env), "
                    "Jira API Token erstellen, Import-Workflow, Export-Workflow, "
                    "Konfliktbehandlung, Erweiterung (neue Felder mappen)\n"
                    "• curl-Beispiele für alle /jira-Endpunkte"
                ),
                "story_points": 2,
                "business_value": 7,
                "tasks": [
                    {
                        "title": "Task J7-2.1 | docs/jira_integration.md schreiben",
                        "description": (
                            "Erstelle backend/docs/jira_integration.md mit allen Abschnitten "
                            "laut Acceptance Criteria. Halte es praxisnah: "
                            "konkrete curl-Beispiele, keine theoretischen Ausführungen."
                        ),
                        "effort_hours": 1.5,
                    },
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Helper functions (identisch mit setup_testmodul.py)
# ---------------------------------------------------------------------------

def login(session: requests.Session) -> None:
    r = session.post(f"{BASE_URL}/auth/login",
                     data={"username": USERNAME, "password": PASSWORD})
    r.raise_for_status()
    token = r.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✓ Eingeloggt als '{USERNAME}'")


def get_project(session: requests.Session) -> dict:
    projects = session.get(f"{BASE_URL}/projects/").json()
    if not projects:
        print("✗ Keine Projekte gefunden.", file=sys.stderr)
        sys.exit(1)
    for p in projects:
        if p["title"] == PROJECT_NAME:
            print(f"✓ Projekt gefunden: '{p['title']}'")
            return p
    print(f"✗ Projekt '{PROJECT_NAME}' nicht gefunden.", file=sys.stderr)
    print(f"  Verfügbare Projekte: {[p['title'] for p in projects]}", file=sys.stderr)
    sys.exit(1)


def create_topic(session: requests.Session, project_id: str) -> dict:
    topics = session.get(f"{BASE_URL}/topics/", params={"project_id": project_id}).json()
    for t in topics:
        if t["title"] == "Jira Anbindung":
            print(f"  ℹ Topic 'Jira Anbindung' existiert bereits (ID: {t['id']})")
            return t

    r = session.post(f"{BASE_URL}/topics/", json={
        "title": "Jira Anbindung",
        "description": (
            "Bidirektionale Jira-Integration für Project Flow.\n\n"
            "Deliverables (sequenziell abzuarbeiten):\n"
            "  J1 | Datenbankmodell: Externe ID-Felder\n"
            "  J2 | Jira API-Client\n"
            "  J3 | Import: Jira → Project Flow\n"
            "  J4 | Export: Project Flow → Jira\n"
            "  J5 | Sync-Status & Konfliktbehandlung\n"
            "  J6 | REST-Endpunkte & Integration\n"
            "  J7 | Tests & Dokumentation\n\n"
            "Voraussetzung: JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN in .env"
        ),
        "project_id": project_id,
    })
    if r.status_code == 201:
        topic = r.json()
        print(f"  ✓ Topic 'Jira Anbindung' erstellt (ID: {topic['id']})")
        return topic
    else:
        print(f"  ✗ Topic-Erstellung fehlgeschlagen: {r.status_code} – {r.text}", file=sys.stderr)
        sys.exit(1)


def create_deliverable(session, topic_id, data):
    r = session.post(f"{BASE_URL}/deliverables/", json={
        "title": data["title"],
        "description": data.get("description", ""),
        "topic_id": topic_id,
        "status": "todo",
    })
    if r.status_code == 201:
        d = r.json()
        print(f"    ✓ Deliverable: '{d['title']}'")
        return d
    print(f"    ✗ Deliverable fehlgeschlagen ({r.status_code}): {r.text}")
    return {}


def create_user_story(session, deliverable_id, story):
    r = session.post(f"{BASE_URL}/user-stories/", json={
        "title": story["title"],
        "description": story.get("description", ""),
        "acceptance_criteria": story.get("acceptance_criteria", ""),
        "story_points": story.get("story_points", 3),
        "business_value": story.get("business_value", 7),
        "deliverable_id": deliverable_id,
        "status": "todo",
    })
    if r.status_code == 201:
        us = r.json()
        print(f"      ✓ User Story: '{us['title']}'")
        return us
    print(f"      ✗ User Story fehlgeschlagen ({r.status_code}): {r.text}")
    return {}


def create_task(session, user_story_id, task):
    r = session.post(f"{BASE_URL}/tasks/", json={
        "title": task["title"],
        "description": task.get("description", ""),
        "effort_hours": task.get("effort_hours"),
        "user_story_id": user_story_id,
        "status": "todo",
    })
    if r.status_code == 201:
        t = r.json()
        print(f"        ✓ Task: '{t['title']}'")
        return t
    print(f"        ✗ Task fehlgeschlagen ({r.status_code}): {r.text}")
    return {}


def save_task_map(task_map: dict) -> None:
    path = Path("projectflow_jira_task_map.json")
    path.write_text(json.dumps(task_map, indent=2, ensure_ascii=False))
    print(f"\n✅ Task-Map gespeichert: {path.resolve()}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 65)
    print("  Project Flow – Jira Anbindung Setup")
    print("=" * 65 + "\n")

    session = requests.Session()
    login(session)

    project = get_project(session)
    project_id = str(project["id"])

    print(f"\n📁 Lege Topic 'Jira Anbindung' an...")
    topic = create_topic(session, project_id)
    topic_id = str(topic["id"])

    task_map: dict = {
        "base_url": BASE_URL,
        "topic_id": topic_id,
        "project_id": project_id,
        "deliverables": {},
        "user_stories": {},
    }

    total_deliverables = 0
    total_stories = 0
    total_tasks = 0

    print(f"\n📦 Lege {len(DELIVERABLES_AND_STORIES)} Deliverables an...\n")

    for d_data in DELIVERABLES_AND_STORIES:
        deliverable = create_deliverable(session, topic_id, d_data)
        if not deliverable:
            continue
        total_deliverables += 1
        d_id = str(deliverable["id"])

        task_map["deliverables"][d_data["title"]] = {
            "id": d_id,
            "status_endpoint": f"{BASE_URL}/deliverables/{d_id}",
        }

        for story_data in d_data.get("user_stories", []):
            story = create_user_story(session, d_id, story_data)
            if not story:
                continue
            total_stories += 1
            s_id = str(story["id"])

            task_map["user_stories"][story_data["title"]] = {
                "id": s_id,
                "deliverable_id": d_id,
                "status_endpoint": f"{BASE_URL}/user-stories/{s_id}",
                "tasks": {},
            }

            for task_data in story_data.get("tasks", []):
                task = create_task(session, s_id, task_data)
                if not task:
                    continue
                total_tasks += 1
                t_id = str(task["id"])

                task_map["user_stories"][story_data["title"]]["tasks"][task_data["title"]] = {
                    "id": t_id,
                    "status_endpoint": f"{BASE_URL}/tasks/{t_id}",
                }

        print()

    save_task_map(task_map)

    print("\n" + "=" * 65)
    print(f"  ✅ Setup abgeschlossen!")
    print(f"     Topic:        1  (Jira Anbindung)")
    print(f"     Deliverables: {total_deliverables}")
    print(f"     User Stories: {total_stories}")
    print(f"     Tasks:        {total_tasks}")
    print("=" * 65)
    print(f"\n  → Topic 'Jira Anbindung' ist jetzt in Project Flow verfügbar.")
    print(f"  → Task-Map: projectflow_jira_task_map.json")
    print(f"\n  Nächste Schritte:")
    print(f"  1. Jira Cloud Account erstellen (kostenlos auf atlassian.com)")
    print(f"  2. API Token generieren: Account Settings → Security → API Tokens")
    print(f"  3. .env befüllen: JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN")
    print(f"  4. Claude Code mit J1 beauftragen (Datenbankmodell)")


if __name__ == "__main__":
    main()
