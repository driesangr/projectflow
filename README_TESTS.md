# ProjectFlow – Integration Tests

## Überblick

Die Integration-Tests testen die REST-API von ProjectFlow gegen einen laufenden Backend-Server.
Sie befinden sich im Verzeichnis `tests/` im Projektroot.

```
tests/
├── conftest.py              # Shared Fixtures (auth_client, cleanup_ids)
├── pytest.ini               # pytest-Konfiguration
├── requirements-test.txt    # Test-Abhängigkeiten
├── functional/
│   ├── test_topics.py       # D2: Topics CRUD + Soft-Delete
│   ├── test_deliverables.py # D3: Deliverables CRUD
│   ├── test_user_stories.py # D4: User Stories CRUD + Status-Flow
│   └── test_tasks.py        # D5: Tasks CRUD + Status-Übergänge
└── utils/
    ├── api_client.py        # Authentifizierter HTTP-Client (httpx)
    └── cleanup.py           # CleanupRegistry für Test-Isolation
```

## Voraussetzungen

- Python 3.11+
- ProjectFlow Backend läuft auf `http://localhost:8000`
- Admin-Account vorhanden (`admin` / `admin123`)

## Installation

```bash
cd tests
pip install -r requirements-test.txt
```

## Tests ausführen

```bash
# Alle Tests
cd tests
python -m pytest -v

# Einzelne Datei
python -m pytest functional/test_topics.py -v

# Mit Ausgabe bei Fehlern
python -m pytest -v --tb=short
```

## Architektur

### auth_client (Session-Fixture)
Ein `httpx.AsyncClient` mit gültigem JWT-Token, der für die gesamte Test-Session
authentifiziert bleibt. Einmalige Anmeldung, alle Tests teilen denselben Client.

### cleanup_ids (Per-Test-Fixture)
Eine `CleanupRegistry`, die IDs von erstellten Artefakten sammelt und nach
jedem Test in umgekehrter Reihenfolge löscht. So bleibt die Datenbank sauber.

```python
async def test_create_topic(auth_client, cleanup_ids):
    resp = await auth_client.post("/topics/", json={"title": "Test", "project_id": PROJECT_ID})
    cleanup_ids.add("topic", resp.json()["id"])  # Wird nach dem Test gelöscht
```

### Async-Loop-Konfiguration
Alle Tests und Fixtures verwenden `asyncio_default_test_loop_scope = session`,
damit der `auth_client` mit gepoolten Verbindungen korrekt funktioniert.

## Testabdeckung

| Datei                   | Getestete Endpoints                          |
|-------------------------|----------------------------------------------|
| `test_topics.py`        | POST, GET, PUT, DELETE `/topics/`            |
| `test_deliverables.py`  | POST, GET, PUT, DELETE `/deliverables/`      |
| `test_user_stories.py`  | POST, GET, PUT `/user-stories/`              |
| `test_tasks.py`         | POST, GET, PUT, DELETE `/tasks/`             |

## Wichtige Hinweise

- Tests sind **idempotent**: Alle erstellten Artefakte werden nach dem Test bereinigt
- Soft-Delete wird explizit getestet: Gelöschte Artefakte liefern 404
- Fehlerfälle (fehlende Pflichtfelder, ungültige Status) werden mit 422 getestet
- Not-Found-Szenarien werden mit zufälligen UUIDs getestet
