# Projektkontext: Project Flow

> **Hinweis an Claude:** Diese Datei ist dein Startpunkt für jede neue Unterhaltung
> zu diesem Projekt. Lies sie vollständig bevor du antwortest. Wenn wir im Verlauf
> der Unterhaltung etwas Neues besprechen, das für zukünftige Sessions relevant ist
> (neue Konventionen, Entscheidungen, erledigter Stand, geänderte Strukturen), weise
> mich am Ende der Unterhaltung darauf hin und schlage konkret vor, was in dieser
> Datei ergänzt oder aktualisiert werden sollte.

---

## Projekt-Übersicht

**Project Flow** ist ein hierarchisches Projektmanagement-Tool, das selbst zur
Verwaltung seiner eigenen Entwicklung genutzt wird (dogfooding).

| Komponente | Technologie |
|---|---|
| Backend | FastAPI, Python, SQLAlchemy (async), PostgreSQL |
| Frontend | Vue 3, TypeScript, Pinia, Tailwind CSS |
| Auth | JWT via `/auth/login` |
| Laufzeit lokal | `http://localhost:8000` (Backend) |

---

## Datenmodell / Hierarchie

```
Project
  └── Topic
        └── Deliverable
              └── User Story
                    └── Task
```

- Jede Ebene hat CRUD-Endpunkte (REST)
- **Soft-Delete** überall: `is_deleted=True`, kein Hard-Delete
- Status-Werte für Deliverables, User Stories und Tasks: `todo` | `in_progress` | `done`
- Superuser bypassed immer alle Permission-Checks

---

## API-Konventionen

**Login:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

**Wichtig:** Projekt-Schema verwendet `title`, nicht `name`.

**Endpunkte (Auswahl):**
```
POST   /topics/             → Topic anlegen
GET    /topics/{id}
PUT    /topics/{id}
DELETE /topics/{id}         → Soft-Delete

POST   /deliverables/
PUT    /deliverables/{id}
DELETE /deliverables/{id}

POST   /user-stories/
PUT    /user-stories/{id}

POST   /tasks/
PUT    /tasks/{id}
DELETE /tasks/{id}
```

---

## Credentials (lokal)

| Parameter | Wert |
|---|---|
| Admin-User | `admin` |
| Passwort | `admin123` |
| Projekt | **Project Flow** (mit Leerzeichen, nicht "ProjectFlow") |

---

## Setup-Scripts

| Script | Zweck |
|---|---|
| `setup_testmodul.py` | Legt Topic "Testmodul" mit allen Deliverables, User Stories und Tasks in Project Flow an |
| `setup_granulares_rechtemanagement.py` | Legt Artefakte für das Rechtemanagement-Feature an |
| `setup_frontend_userstories.py` | Legt User Stories für das Frontend-Konfigurationsmenü an |

**Ausführen:**
```bash
python3 setup_testmodul.py
```
`requests` muss nicht separat installiert werden – ist Teil der Backend-Umgebung.

Alle Scripts erzeugen eine `*_task_map.json` mit den IDs aller angelegten Artefakte
(für Claude Code als Mapping-Datei).

---

## Testmodul (aktueller Stand)

Im Topic **"Testmodul"** (angelegt via `setup_testmodul.py`) sind folgende
Deliverables definiert:

| Deliverable | Inhalt |
|---|---|
| D1 – Testframework-Basis | Projektstruktur, auth_client-Fixture, cleanup-Fixture |
| D2 – Testszenarien: Topics | CRUD + Soft-Delete Tests |
| D3 – Testszenarien: Deliverables | CRUD inkl. Hierarchie-Prüfung |
| D4 – Testszenarien: User Stories | CRUD + Status-Flow |
| D5 – Testszenarien: Tasks | CRUD + Status-Transitions |
| D6 – CI & Dokumentation | README_TESTS.md + GitHub Actions Workflow |

**Testframework-Prinzipien:**
- pytest + httpx (async), kein Selenium
- Max. 3 Szenarien pro Use Case
- Cleanup-Fixture sorgt für Test-Isolation
- Konfiguration via Umgebungsvariablen (BASE_URL, TEST_USER, TEST_PASSWORD)
- Framework ist generisch – wiederverwendbar für andere FastAPI-Projekte

---

## Wichtige Entscheidungen & Konventionen

- **Projektname immer mit Leerzeichen:** "Project Flow" (nicht "ProjectFlow")
- **Felder:** Projekte haben `title`, nicht `name`
- **Weniger ist mehr bei Tests:** Lieber 2 klare Szenarien als 5 halbgare
- **Scripts sind idempotent:** Mehrfaches Ausführen soll keine Duplikate erzeugen
- **Claude Code vs. Claude.ai:** Setup-Scripts und Task-Maps sind für Claude Code.
  Diese Datei (`PROJEKTKONTEXT.md`) ist für Claude.ai (Chat).

---

## Offene Themen / nächste Schritte

- [ ] `setup_testmodul.py` ausführen und prüfen ob alle Artefakte korrekt angelegt wurden
- [ ] Claude Code beauftragen, das Testframework (D1) zu implementieren
- [ ] Claude Code beauftragen, die Testszenarien (D2–D5) zu implementieren
- [ ] CI-Workflow (D6) einrichten
- [ ] Jira-Anbindung: Details besprechen und Konzept erarbeiten (siehe unten)

---

## Geplante Erweiterung: Jira-Anbindung

### Status
Design abgeschlossen – `setup_jira_anbindung.py` erstellt, bereit zur Ausführung.

### Entschiedenes Konzept
- Jira Cloud (REST API v3), Authentifizierung via API Token
- Bidirektionaler Sync (Import + Export)
- Neue Felder auf UserStory und Task: `jira_key`, `jira_sync_status`, `last_synced_at`
- `jira_sync_status` Enum: `synced` | `modified` | `conflict`
- Bei Bearbeitung eines Artefakts in Project Flow → automatisch `modified`
- Konflikt = beide Seiten geändert → manuelle Auflösung (keep_local / use_jira)

### Hierarchie-Mapping

| Project Flow | Jira |
|---|---|
| Topic | Project |
| Deliverable | Epic |
| User Story | Story |
| Task | Sub-task |

### Deliverable-Reihenfolge (sequenziell!)

| # | Deliverable | Inhalt |
|---|---|---|
| J1 | Datenbankmodell | jira_key, jira_sync_status, last_synced_at + Migration |
| J2 | Jira API-Client | JiraClient-Klasse, async httpx, Fehlerbehandlung |
| J3 | Import | Jira → Project Flow, Mapping-Logik, Idempotenz |
| J4 | Export | Project Flow → Jira, Modified-Tracking, Transition-API |
| J5 | Sync & Konflikte | Konflikterkennung, Auflösungs-Endpunkt |
| J6 | REST-Endpunkte | /jira/import, /jira/export, /jira/status, /jira/conflicts |
| J7 | Tests & Docs | MockJiraClient, Funktionstests, Entwicklerdokumentation |

### Jira API Token (kostenlos)
1. Kostenlosen Jira Cloud Account auf atlassian.com erstellen (bis 10 User gratis)
2. Testprojekt anlegen
3. API Token generieren: Account Settings → Security → API Tokens
4. In `.env` eintragen: `JIRA_BASE_URL`, `JIRA_USER_EMAIL`, `JIRA_API_TOKEN`

### Noch zu klären
- Welche Felder sollen synchronisiert werden (Assignee, Priority, Labels, ...)?
- Soll Sync nur manuell (API-Call) oder auch automatisch (Webhook/Scheduler) laufen?

---

## Gesprächshistorie (wichtige Erkenntnisse)

| Datum | Erkenntnis |
|---|---|
| 2026-02-27 | Projekt heisst "Project Flow" mit Leerzeichen – API-Feld ist `title` nicht `name` |
| 2026-02-27 | `requests` muss nicht installiert werden, ist in Backend-requirements.txt enthalten |
| 2026-02-27 | Testmodul-Struktur definiert und setup_testmodul.py erstellt |
| 2026-02-27 | Jira-Design finalisiert: bidirektionaler Sync, 7 Deliverables (J1–J7), setup_jira_anbindung.py erstellt |
