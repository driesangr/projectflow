# Project Flow – Claude Code Arbeitsanweisungen

## Kontext

Du arbeitest am Projekt **Project Flow** – einem hierarchischen Projektmanagement-Tool
(FastAPI-Backend, Vue 3-Frontend, PostgreSQL).

Alle Artefakte mit Status (Deliverables, User Stories, Tasks) müssen während der
Bearbeitung konsequent mit Status-Updates versehen werden.

---

## Status-Tracking: Pflichtverhalten

> **Wichtig:** Diese Anweisungen gelten für ALLE Artefakte auf ALLEN Ebenen.
> Kein Task, keine User Story und kein Deliverable darf ohne Status-Update
> gestartet oder abgeschlossen werden.

### Artefakt-Hierarchie und Status-Verantwortung

```
Deliverable  →  hat Status: todo | in_progress | done
  └── User Story  →  hat Status: todo | in_progress | done
        └── Task  →  hat Status: todo | in_progress | done
```

Die Regel ist einfach: **Status wird von unten nach oben weitergegeben.**
Sobald das erste Kind `in_progress` ist, wird auch der Elternteil `in_progress`.
Sobald alle Kinder `done` sind, wird auch der Elternteil `done`.

### Mapping-Datei

Die Task-Map-JSON-Datei im Projektroot enthält alle IDs. Sie hat folgende Struktur:

```json
{
  "base_url": "http://localhost:8000",
  "deliverables": {
    "Titel des Deliverables": {
      "id": "uuid",
      "status_endpoint": "http://localhost:8000/deliverables/uuid"
    }
  },
  "user_stories": {
    "Titel der User Story": {
      "id": "uuid",
      "deliverable_id": "uuid",
      "status_endpoint": "http://localhost:8000/user-stories/uuid",
      "tasks": {
        "Titel des Tasks": {
          "id": "uuid",
          "status_endpoint": "http://localhost:8000/tasks/uuid"
        }
      }
    }
  }
}
```

### Authentifizierung

Token einmalig pro Session holen und in Variable speichern:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Status-Werte

| Zustand | API-Wert |
|---|---|
| Noch nicht begonnen | `"todo"` |
| In Bearbeitung | `"in_progress"` |
| Abgeschlossen | `"done"` |

---

## Workflow pro Task

Halte diesen Ablauf für **jeden einzelnen Task** strikt ein:

### Schritt 1 – Vor Beginn der Implementierung

1. Lese die Task-Map-JSON und ermittle Task-ID, Story-ID und Deliverable-ID.

2. Setze den **Task** auf `in_progress`:
```bash
curl -s -X PUT http://localhost:8000/tasks/{TASK_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

3. Falls die **User Story** noch `todo` ist: setze sie auf `in_progress`:
```bash
curl -s -X PUT http://localhost:8000/user-stories/{STORY_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

4. Falls das **Deliverable** noch `todo` ist: setze es auf `in_progress`:
```bash
curl -s -X PUT http://localhost:8000/deliverables/{DELIVERABLE_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Schritt 2 – Implementierung

Führe die Implementierung gemäss Task-Beschreibung durch.

### Schritt 3 – Nach Abschluss der Implementierung

1. Setze den **Task** auf `done`:
```bash
curl -s -X PUT http://localhost:8000/tasks/{TASK_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

2. Prüfe ob **alle Tasks** der User Story nun `done` sind.
   Falls ja: setze die **User Story** auf `done`:
```bash
curl -s -X PUT http://localhost:8000/user-stories/{STORY_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

3. Prüfe ob **alle User Stories** des Deliverables nun `done` sind.
   Falls ja: setze das **Deliverable** auf `done`:
```bash
curl -s -X PUT http://localhost:8000/deliverables/{DELIVERABLE_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Beispiel: Vollständiger Ablauf für einen Task

```bash
# 1. Token holen
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. IDs aus Task-Map ermitteln
python3 -c "
import json
m = json.load(open('projectflow_task_map.json'))
story = m['user_stories']['B-1 | TypeScript-Typen und API-Client für Permissions erweitern']
task  = story['tasks']['Task B-1.1 | TypeScript-Typen ergänzen']
print('STORY_ID=' + story['id'])
print('TASK_ID='  + task['id'])
print('DELIVERABLE_ID=' + story['deliverable_id'])
"

# 3. Alle drei Ebenen auf in_progress setzen (falls noch todo)
curl -s -X PUT http://localhost:8000/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

curl -s -X PUT http://localhost:8000/user-stories/$STORY_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

curl -s -X PUT http://localhost:8000/deliverables/$DELIVERABLE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# ... Implementierung ...

# 4. Task auf done setzen, dann Kaskade prüfen und ggf. Story + Deliverable nachziehen
curl -s -X PUT http://localhost:8000/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Projektstruktur (Kurzübersicht)

```
projectflow/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── permissions.py
│   │   ├── models/
│   │   ├── routers/
│   │   │   ├── topics.py
│   │   │   ├── deliverables.py
│   │   │   ├── user_stories.py
│   │   │   ├── tasks.py
│   │   │   ├── projects.py
│   │   │   └── project_groups.py
│   │   ├── schemas/
│   │   └── services/
│   └── alembic/versions/
├── frontend/
│   └── src/
│       ├── api/
│       ├── stores/
│       ├── components/
│       ├── views/
│       └── types/index.ts
└── tests/
    ├── conftest.py
    ├── pytest.ini
    ├── requirements-test.txt
    ├── functional/
    │   ├── test_topics.py
    │   ├── test_deliverables.py
    │   ├── test_user_stories.py
    │   └── test_tasks.py
    └── utils/
        ├── api_client.py
        └── cleanup.py
```

---

## Wichtige Hinweise

- **Projektname:** "Project Flow" (mit Leerzeichen) – API-Feld ist `title`, nicht `name`
- **Rückwärtskompatibilität:** Die bestehenden `require_viewer`, `require_member`,
  `require_manager`, `require_owner` Dependencies in `permissions.py` dürfen nicht
  entfernt werden.
- **Superuser** bypasst immer alle Permission-Checks – dieser Grundsatz darf nie gebrochen werden.
- **Idempotenz:** Alle Datenbankoperationen sollen mehrfach ausführbar sein ohne Fehler.
- **Soft-Delete:** Kein Hard-Delete – gelöschte Artefakte werden mit `is_deleted=True` markiert.
- **Teststrategie:** Nach jedem Backend-Task: `uvicorn app.main:app` starten und
  den neuen Endpoint manuell mit curl testen bevor der Task auf `done` gesetzt wird.
