# ProjectFlow – Claude Code Arbeitsanweisungen

## Kontext

Du arbeitest am Projekt **ProjectFlow** – einem hierarchischen Projektmanagement-Tool
(FastAPI-Backend, Vue 3-Frontend, PostgreSQL).

Die aktuelle Aufgabe ist die Implementierung des **granularen Rechtemanagements**.
Alle User Stories und Tasks sind in ProjectFlow erfasst und müssen während der
Bearbeitung mit Status-Updates versehen werden.

---

## Status-Tracking: Pflichtverhalten

> **Wichtig:** Diese Anweisungen gelten für ALLE Tasks, die du bearbeitest.
> Kein Task darf ohne Status-Update gestartet oder abgeschlossen werden.

### Mapping-Datei

Die Datei `projectflow_task_map.json` im Projektroot enthält alle IDs der
User Stories und Tasks in ProjectFlow. Sie hat folgende Struktur:

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

Für alle API-Calls benötigst du einen JWT-Token. Hole ihn einmalig pro Session:

```bash
curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"
```

Speichere den Token in einer Shell-Variable:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Status-Werte

| Zustand | API-Wert |
|---------|----------|
| Noch nicht begonnen | `"todo"` |
| In Bearbeitung | `"in_progress"` |
| Abgeschlossen | `"done"` |

---

## Workflow pro Task

Halte diesen Ablauf für **jeden einzelnen Task** strikt ein:

### Schritt 1 – Vor Beginn der Implementierung

1. Lese `projectflow_task_map.json` und ermittle die ID des Tasks anhand seines Titels.
2. Setze den Task-Status auf `in_progress`:

```bash
curl -s -X PUT http://localhost:8000/tasks/{TASK_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

3. Prüfe ob alle anderen Tasks der zugehörigen User Story noch `todo` sind.
   Falls ja: setze auch die User Story auf `in_progress`:

```bash
curl -s -X PUT http://localhost:8000/user-stories/{STORY_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

### Schritt 2 – Implementierung

Führe die Implementierung gemäss Task-Beschreibung durch.

### Schritt 3 – Nach Abschluss der Implementierung

1. Setze den Task-Status auf `done`:

```bash
curl -s -X PUT http://localhost:8000/tasks/{TASK_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

2. Prüfe ob **alle** Tasks der zugehörigen User Story nun `done` sind.
   Dazu: lies die User Story und prüfe alle Tasks.
   Falls alle `done`: setze die User Story auf `done`:

```bash
curl -s -X PUT http://localhost:8000/user-stories/{STORY_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

3. Prüfe ob **alle** User Stories des zugehörigen Deliverables nun `done` sind.
   Falls alle `done`: setze das Deliverable auf `done`:

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

# 2. Task-Map lesen und IDs ermitteln
python3 -c "
import json
m = json.load(open('projectflow_task_map.json'))
story = m['user_stories']['B-1 | TypeScript-Typen und API-Client für Permissions erweitern']
task  = story['tasks']['Task B-1.1 | TypeScript-Typen ergänzen']
print('STORY_ID=' + story['id'])
print('TASK_ID='  + task['id'])
print('DELIVERABLE_ID=' + story['deliverable_id'])
"

# 3. Task auf in_progress setzen
curl -s -X PUT http://localhost:8000/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# ... Implementierung ...

# 4. Task auf done setzen
curl -s -X PUT http://localhost:8000/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

---

## Umfang der aktuellen Beauftragung

Aktuell werden die User Stories der **Deliverables B und C** bearbeitet.
Deliverable A ist bereits in Bearbeitung durch eine separate Session.

### Deliverable B – Admin-Oberfläche

- B-1 | TypeScript-Typen und API-Client für Permissions erweitern
  - Task B-1.1 | TypeScript-Typen ergänzen
  - Task B-1.2 | API-Modul permissions.ts erstellen
- B-2 | Permissions-Store (Pinia) implementieren
  - Task B-2.1 | Pinia-Store Grundstruktur erstellen
  - Task B-2.2 | Actions implementieren
  - Task B-2.3 | Getter implementieren
- B-3 | PermissionsTreeNode-Komponente erstellen
  - Task B-3.1 | Komponenten-Grundstruktur und Props
  - Task B-3.2 | Template mit Checkboxen und Status-Indikator
  - Task B-3.3 | Event-Handler und Speicherlogik
- B-4 | ConfigPermissionsView erstellen und in Navigation einbinden
  - Task B-4.1 | ConfigPermissionsView Grundstruktur
  - Task B-4.2 | Template mit Rollen-Selector und Baum
  - Task B-4.3 | Route und Sidebar-Integration

### Deliverable C – Integration & Rollout

- C-1 | Permissions-Engine auf artefaktbasierte Prüfung erweitern
  - Task C-1.1 | check_artifact_permission implementieren
  - Task C-1.2 | require_artifact_permission Dependency-Factory erstellen
- C-2 | Bestehende Router mit granularen Guards absichern
  - Task C-2.1 | Router topics.py aktualisieren
  - Task C-2.2 | Router deliverables.py aktualisieren
  - Task C-2.3 | Router user_stories.py und tasks.py aktualisieren
  - Task C-2.4 | Router projects.py und project_groups.py aktualisieren
- C-3 | Idempotentes Setup-Script für Produktion erstellen
  - Task C-3.1 | Setup-Script setup_granulares_rechtemanagement_apply.py erstellen

---

## Projektstruktur (Kurzübersicht)

```
projectflow/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── permissions.py        ← Permissions-Engine (erweitern in C-1)
│   │   ├── models/
│   │   │   ├── role_permission.py    ← Neues Model (erstellt in A-1)
│   │   │   └── project_membership.py ← ProjectRole-Enum
│   │   ├── routers/
│   │   │   ├── permissions.py        ← Neuer Router (erstellt in A-3)
│   │   │   ├── topics.py             ← Aktualisieren in C-2
│   │   │   ├── deliverables.py       ← Aktualisieren in C-2
│   │   │   ├── user_stories.py       ← Aktualisieren in C-2
│   │   │   ├── tasks.py              ← Aktualisieren in C-2
│   │   │   ├── projects.py           ← Aktualisieren in C-2
│   │   │   └── project_groups.py     ← Aktualisieren in C-2
│   │   ├── schemas/
│   │   │   └── role_permission.py    ← Neue Schemas (erstellt in A-3)
│   │   └── services/
│   │       └── permissions_service.py ← Vererbungslogik (erstellt in A-2)
│   └── alembic/versions/
│       └── 0008_add_role_permissions.py ← Migration (erstellt in A-1)
└── frontend/
    └── src/
        ├── api/
        │   └── permissions.ts        ← Neuer API-Client (B-1)
        ├── stores/
        │   └── permissions.ts        ← Pinia-Store (B-2)
        ├── components/permissions/
        │   └── PermissionsTreeNode.vue ← Baum-Komponente (B-3)
        ├── views/
        │   └── ConfigPermissionsView.vue ← Admin-View (B-4)
        └── types/index.ts            ← Typen ergänzen (B-1)
```

---

## Wichtige Hinweise

- **Rückwärtskompatibilität:** Die bestehenden `require_viewer`, `require_member`,
  `require_manager`, `require_owner` Dependencies in `permissions.py` dürfen nicht
  entfernt werden – sie werden in C-2 ersetzt, aber andere Teile könnten sie noch nutzen.
- **Superuser** bypasst immer alle Checks – dieser Grundsatz darf nie gebrochen werden.
- **Idempotenz:** Alle Datenbankoperationen sollen mehrfach ausführbar sein ohne Fehler.
- **Teststrategie:** Nach jedem Backend-Task: `uvicorn app.main:app` starten und
  den neuen Endpoint manuell mit curl testen bevor der Task auf `done` gesetzt wird.
