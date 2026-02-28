"""
setup_testmodul.py
==================
Legt das Topic "Testmodul" im Projekt "Project Flow" an und befüllt es mit
allen Deliverables, User Stories und Tasks für das Testframework.

Ausführen:
    python3 setup_testmodul.py

Voraussetzungen:
    - requests ist bereits in der Backend-Umgebung enthalten (requirements.txt)
    - Project Flow läuft auf http://localhost:8000 (anpassbar via BASE_URL)
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

PROJECT_NAME = "Project Flow"  # Artefakte werden ausschließlich in diesem Projekt angelegt

# ---------------------------------------------------------------------------
# Testmodul-Struktur
# ---------------------------------------------------------------------------
#
# Aufbau des Testframeworks:
#   - Generisch nutzbar (nicht Project Flow-spezifisch)
#   - API-basierte Funktionstests via pytest + httpx
#   - Fixtures für Auth, Cleanup, Test-Isolation
#   - Pro Entität (Topic, Deliverable, User Story, Task): CRUD-Szenarien
#   - max. 3 Testszenarien pro Use Case (lieber weniger, klar und präzise)
#
# Deliverable-Struktur:
#   D1 | Testframework-Basis
#   D2 | Testszenarien: Topics
#   D3 | Testszenarien: Deliverables
#   D4 | Testszenarien: User Stories
#   D5 | Testszenarien: Tasks
#   D6 | CI-Integration & Dokumentation
# ---------------------------------------------------------------------------

DELIVERABLES_AND_STORIES = [
    # =========================================================================
    # D1 – Testframework-Basis
    # =========================================================================
    {
        "title": "D1 | Testframework-Basis",
        "description": (
            "Generisches, wiederverwendbares pytest-Framework für API-Funktionstests. "
            "Enthält Auth-Fixtures, HTTP-Client-Setup, Cleanup-Utilities und "
            "Konfigurationsmanagement. Kann ohne Änderungen für andere FastAPI-Projekte "
            "übernommen werden."
        ),
        "user_stories": [
            {
                "title": "TF-1 | Projektstruktur und Abhängigkeiten",
                "description": (
                    "Als Entwickler möchte ich eine saubere Testprojektstruktur mit allen "
                    "nötigen Abhängigkeiten, damit Tests isoliert und reproduzierbar laufen."
                ),
                "acceptance_criteria": (
                    "• Verzeichnis tests/ mit conftest.py, pytest.ini und requirements-test.txt\n"
                    "• Abhängigkeiten: pytest, pytest-asyncio, httpx, pytest-env\n"
                    "• pytest.ini konfiguriert asyncio_mode=auto und testpaths\n"
                    "• Umgebungsvariablen BASE_URL, TEST_USER, TEST_PASSWORD via .env.test\n"
                    "• README_TESTS.md erklärt Ausführung und Erweiterung"
                ),
                "story_points": 2,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task TF-1.1 | Verzeichnisstruktur anlegen",
                        "description": (
                            "Lege die Verzeichnisstruktur unter tests/ an:\n"
                            "  tests/\n"
                            "    conftest.py          ← globale Fixtures\n"
                            "    pytest.ini\n"
                            "    requirements-test.txt\n"
                            "    .env.test.example\n"
                            "    functional/\n"
                            "      __init__.py\n"
                            "      test_topics.py\n"
                            "      test_deliverables.py\n"
                            "      test_user_stories.py\n"
                            "      test_tasks.py\n"
                            "    utils/\n"
                            "      __init__.py\n"
                            "      api_client.py\n"
                            "      cleanup.py"
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task TF-1.2 | pytest.ini und requirements-test.txt erstellen",
                        "description": (
                            "pytest.ini:\n"
                            "  [pytest]\n"
                            "  asyncio_mode = auto\n"
                            "  testpaths = tests\n"
                            "  env_files = .env.test\n\n"
                            "requirements-test.txt:\n"
                            "  pytest>=8\n"
                            "  pytest-asyncio>=0.23\n"
                            "  httpx>=0.27\n"
                            "  pytest-env>=1.1\n"
                            "  python-dotenv>=1.0"
                        ),
                        "effort_hours": 0.5,
                    },
                ],
            },
            {
                "title": "TF-2 | Auth-Fixture und HTTP-Client",
                "description": (
                    "Als Tester möchte ich eine fertige HTTP-Client-Fixture mit gültigem "
                    "JWT-Token, damit ich in Testfunktionen direkt authentifizierte Requests "
                    "absetzen kann ohne Boilerplate."
                ),
                "acceptance_criteria": (
                    "• conftest.py stellt Fixture 'auth_client' bereit (scope=function)\n"
                    "• auth_client ist ein httpx.AsyncClient mit gesetztem Bearer-Token\n"
                    "• Login erfolgt einmalig pro Test-Session via /auth/login\n"
                    "• BASE_URL, Username und Passwort kommen aus Umgebungsvariablen\n"
                    "• Bei Login-Fehler bricht die Test-Session mit klarer Fehlermeldung ab"
                ),
                "story_points": 3,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task TF-2.1 | auth_client-Fixture in conftest.py implementieren",
                        "description": (
                            "Implementiere in tests/conftest.py:\n\n"
                            "```python\n"
                            "import os, pytest\n"
                            "import httpx\n\n"
                            "BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:8000')\n\n"
                            "@pytest.fixture(scope='session')\nasync def auth_token():\n"
                            "    async with httpx.AsyncClient(base_url=BASE_URL) as client:\n"
                            "        r = await client.post('/auth/login', data={\n"
                            "            'username': os.getenv('TEST_USER', 'admin'),\n"
                            "            'password': os.getenv('TEST_PASSWORD', 'admin123'),\n"
                            "        })\n"
                            "        assert r.status_code == 200, f'Login failed: {r.text}'\n"
                            "        return r.json()['access_token']\n\n"
                            "@pytest.fixture\nasync def auth_client(auth_token):\n"
                            "    async with httpx.AsyncClient(\n"
                            "        base_url=BASE_URL,\n"
                            "        headers={'Authorization': f'Bearer {auth_token}'},\n"
                            "    ) as client:\n"
                            "        yield client\n"
                            "```"
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task TF-2.2 | API-Client Hilfsklasse erstellen (utils/api_client.py)",
                        "description": (
                            "Erstelle tests/utils/api_client.py mit einer ProjectFlowClient-Klasse:\n"
                            "  - Methoden: create_topic, get_topic, update_topic, delete_topic\n"
                            "  - Ebenso für deliverable, user_story, task\n"
                            "  - Alle Methoden nehmen den auth_client entgegen und geben das\n"
                            "    Response-Objekt zurück (kein internes assert – das liegt beim Test)\n"
                            "  - project_id-Parameter wird aus ENV TEST_PROJECT_ID gelesen falls\n"
                            "    nicht explizit übergeben"
                        ),
                        "effort_hours": 2.0,
                    },
                ],
            },
            {
                "title": "TF-3 | Cleanup-Fixture für Test-Isolation",
                "description": (
                    "Als Tester möchte ich sicher sein, dass jeder Test seine eigenen Daten "
                    "aufräumt, damit Tests in beliebiger Reihenfolge und mehrfach ausführbar sind."
                ),
                "acceptance_criteria": (
                    "• Fixture 'cleanup_ids' sammelt erstellte Ressourcen-IDs pro Test\n"
                    "• Nach dem Test werden alle registrierten Ressourcen via DELETE bereinigt\n"
                    "• Cleanup erfolgt auch bei fehlgeschlagenem Test (yield-Pattern)\n"
                    "• Cleanup-Fehler (z.B. 404) werden ignoriert (Ressource schon weg)\n"
                    "• utils/cleanup.py enthält delete_resource(client, path, resource_id)"
                ),
                "story_points": 2,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task TF-3.1 | cleanup_ids-Fixture und CleanupRegistry implementieren",
                        "description": (
                            "Implementiere in tests/conftest.py:\n\n"
                            "```python\n"
                            "from tests.utils.cleanup import CleanupRegistry\n\n"
                            "@pytest.fixture\nasync def cleanup(auth_client):\n"
                            "    registry = CleanupRegistry(auth_client)\n"
                            "    yield registry\n"
                            "    await registry.run()\n"
                            "```\n\n"
                            "CleanupRegistry in utils/cleanup.py:\n"
                            "  - register(path: str, resource_id: str) → speichert (path, id)\n"
                            "  - run() → iteriert in umgekehrter Reihenfolge und löscht via DELETE\n"
                            "  - Fehler bei DELETE werden gelogged, nicht reraiseed"
                        ),
                        "effort_hours": 1.5,
                    },
                ],
            },
        ],
    },
    # =========================================================================
    # D2 – Testszenarien: Topics
    # =========================================================================
    {
        "title": "D2 | Testszenarien: Topics",
        "description": (
            "Funktionstests für den /topics-Endpunkt: Erstellen, Lesen, Aktualisieren, "
            "Löschen. Bewusst schlank gehalten – max. 3 Szenarien pro Use Case."
        ),
        "user_stories": [
            {
                "title": "TS-T1 | Topic erstellen (Happy Path + Fehlerfälle)",
                "description": (
                    "Als Tester möchte ich verifizieren, dass Topics korrekt erstellt werden "
                    "und die API bei fehlerhaften Eingaben die richtigen Fehlercodes zurückgibt."
                ),
                "acceptance_criteria": (
                    "• Test 1: POST /topics mit gültigem Payload → 201, ID in Response\n"
                    "• Test 2: POST /topics ohne Pflichtfeld 'title' → 422 Unprocessable Entity\n"
                    "• Test 3: POST /topics mit ungültiger project_id → 403 oder 404\n"
                    "• Alle erstellten Topics werden durch Cleanup-Fixture gelöscht"
                ),
                "story_points": 2,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task TS-T1.1 | test_create_topic_success implementieren",
                        "description": (
                            "```python\n"
                            "async def test_create_topic_success(auth_client, cleanup, project_id):\n"
                            "    r = await auth_client.post('/topics/', json={\n"
                            "        'title': 'Test-Topic',\n"
                            "        'project_id': project_id,\n"
                            "    })\n"
                            "    assert r.status_code == 201\n"
                            "    data = r.json()\n"
                            "    assert data['title'] == 'Test-Topic'\n"
                            "    assert 'id' in data\n"
                            "    cleanup.register('/topics', data['id'])\n"
                            "```"
                        ),
                        "effort_hours": 0.5,
                    },
                    {
                        "title": "Task TS-T1.2 | test_create_topic_missing_title und test_create_topic_invalid_project implementieren",
                        "description": (
                            "Test 2 – fehlendes Pflichtfeld:\n"
                            "```python\n"
                            "async def test_create_topic_missing_title(auth_client, project_id):\n"
                            "    r = await auth_client.post('/topics/', json={'project_id': project_id})\n"
                            "    assert r.status_code == 422\n"
                            "```\n\n"
                            "Test 3 – ungültige project_id:\n"
                            "```python\n"
                            "async def test_create_topic_invalid_project(auth_client):\n"
                            "    r = await auth_client.post('/topics/', json={\n"
                            "        'title': 'Orphan', 'project_id': str(uuid4()),\n"
                            "    })\n"
                            "    assert r.status_code in (403, 404)\n"
                            "```"
                        ),
                        "effort_hours": 0.5,
                    },
                ],
            },
            {
                "title": "TS-T2 | Topic lesen und aktualisieren",
                "description": (
                    "Als Tester möchte ich verifizieren, dass GET und PUT auf Topics "
                    "korrekt funktionieren und der 404-Fall sauber behandelt wird."
                ),
                "acceptance_criteria": (
                    "• Test 1: GET /topics/{id} eines existierenden Topics → 200 + korrekte Daten\n"
                    "• Test 2: PUT /topics/{id} mit neuem Titel → 200 + aktualisierter Titel\n"
                    "• Test 3: GET /topics/{not-existing-uuid} → 404"
                ),
                "story_points": 2,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task TS-T2.1 | test_get_topic und test_update_topic implementieren",
                        "description": (
                            "Beide Tests nutzen ein per Fixture angelegtes Topic:\n\n"
                            "```python\n"
                            "@pytest.fixture\nasync def existing_topic(auth_client, cleanup, project_id):\n"
                            "    r = await auth_client.post('/topics/', json={\n"
                            "        'title': 'Fixture-Topic', 'project_id': project_id})\n"
                            "    data = r.json()\n"
                            "    cleanup.register('/topics', data['id'])\n"
                            "    return data\n\n"
                            "async def test_get_topic(auth_client, existing_topic):\n"
                            "    r = await auth_client.get(f\"/topics/{existing_topic['id']}\")\n"
                            "    assert r.status_code == 200\n"
                            "    assert r.json()['title'] == 'Fixture-Topic'\n\n"
                            "async def test_update_topic(auth_client, existing_topic):\n"
                            "    r = await auth_client.put(\n"
                            "        f\"/topics/{existing_topic['id']}\",\n"
                            "        json={'title': 'Updated-Topic'})\n"
                            "    assert r.status_code == 200\n"
                            "    assert r.json()['title'] == 'Updated-Topic'\n"
                            "```"
                        ),
                        "effort_hours": 0.75,
                    },
                    {
                        "title": "Task TS-T2.2 | test_get_topic_not_found implementieren",
                        "description": (
                            "```python\n"
                            "async def test_get_topic_not_found(auth_client):\n"
                            "    fake_id = str(uuid4())\n"
                            "    r = await auth_client.get(f'/topics/{fake_id}')\n"
                            "    assert r.status_code == 404\n"
                            "```"
                        ),
                        "effort_hours": 0.25,
                    },
                ],
            },
            {
                "title": "TS-T3 | Topic löschen (Soft-Delete)",
                "description": (
                    "Als Tester möchte ich verifizieren, dass der Soft-Delete korrekt "
                    "funktioniert und ein gelöschtes Topic nicht mehr abrufbar ist."
                ),
                "acceptance_criteria": (
                    "• Test 1: DELETE /topics/{id} → 204 No Content\n"
                    "• Test 2: GET /topics/{id} nach Löschung → 404\n"
                    "• Test 3: DELETE /topics/{not-existing-uuid} → 404"
                ),
                "story_points": 2,
                "business_value": 7,
                "tasks": [
                    {
                        "title": "Task TS-T3.1 | test_delete_topic und test_deleted_topic_not_found implementieren",
                        "description": (
                            "```python\n"
                            "async def test_delete_topic(auth_client, project_id):\n"
                            "    r = await auth_client.post('/topics/', json={\n"
                            "        'title': 'To-Delete', 'project_id': project_id})\n"
                            "    topic_id = r.json()['id']\n"
                            "    r_del = await auth_client.delete(f'/topics/{topic_id}')\n"
                            "    assert r_del.status_code == 204\n\n"
                            "async def test_deleted_topic_not_found(auth_client, project_id):\n"
                            "    r = await auth_client.post('/topics/', json={\n"
                            "        'title': 'Gone', 'project_id': project_id})\n"
                            "    topic_id = r.json()['id']\n"
                            "    await auth_client.delete(f'/topics/{topic_id}')\n"
                            "    r_get = await auth_client.get(f'/topics/{topic_id}')\n"
                            "    assert r_get.status_code == 404\n"
                            "```"
                        ),
                        "effort_hours": 0.75,
                    },
                ],
            },
        ],
    },
    # =========================================================================
    # D3 – Testszenarien: Deliverables
    # =========================================================================
    {
        "title": "D3 | Testszenarien: Deliverables",
        "description": (
            "Funktionstests für /deliverables. Deliverables sind Topics untergeordnet – "
            "die Tests stellen sicher, dass die Hierarchie korrekt erzwungen wird."
        ),
        "user_stories": [
            {
                "title": "TS-D1 | Deliverable erstellen und lesen",
                "description": (
                    "Als Tester möchte ich verifizieren, dass Deliverables korrekt unter "
                    "einem Topic angelegt und abgerufen werden können."
                ),
                "acceptance_criteria": (
                    "• Test 1: POST /deliverables mit topic_id → 201 + Deliverable-Daten\n"
                    "• Test 2: GET /deliverables?topic_id={id} listet nur Deliverables des Topics\n"
                    "• Test 3: POST /deliverables ohne topic_id → 422"
                ),
                "story_points": 2,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task TS-D1.1 | test_create_deliverable und test_list_deliverables_by_topic",
                        "description": (
                            "Fixture topic_with_cleanup erstellt ein Topic und registriert Cleanup.\n"
                            "test_create_deliverable: POST → assert 201, title stimmt überein.\n"
                            "test_list_deliverables_by_topic: erstelle 2 Deliverables unter topic,\n"
                            "GET ?topic_id={id} → assert len(response) >= 2."
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task TS-D1.2 | test_create_deliverable_missing_topic_id",
                        "description": (
                            "```python\n"
                            "async def test_create_deliverable_missing_topic_id(auth_client):\n"
                            "    r = await auth_client.post('/deliverables/', json={'title': 'Orphan'})\n"
                            "    assert r.status_code == 422\n"
                            "```"
                        ),
                        "effort_hours": 0.25,
                    },
                ],
            },
            {
                "title": "TS-D2 | Deliverable aktualisieren und löschen",
                "description": (
                    "Als Tester möchte ich verifizieren, dass PUT und DELETE auf "
                    "Deliverables korrekt funktionieren."
                ),
                "acceptance_criteria": (
                    "• Test 1: PUT /deliverables/{id} mit geändertem Titel → 200 + neuer Titel\n"
                    "• Test 2: DELETE /deliverables/{id} → 204, danach GET → 404\n"
                    "• Test 3: PUT auf nicht-existierendes Deliverable → 404"
                ),
                "story_points": 2,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task TS-D2.1 | test_update_deliverable, test_delete_deliverable, test_update_nonexistent",
                        "description": (
                            "Alle drei Tests nutzen die existing_deliverable-Fixture (erstellt via\n"
                            "POST und registriert in Cleanup).\n"
                            "test_update_deliverable: PUT → 200, title geändert.\n"
                            "test_delete_deliverable: DELETE → 204, GET → 404.\n"
                            "test_update_nonexistent: PUT /deliverables/{uuid4()} → 404."
                        ),
                        "effort_hours": 1.0,
                    },
                ],
            },
        ],
    },
    # =========================================================================
    # D4 – Testszenarien: User Stories
    # =========================================================================
    {
        "title": "D4 | Testszenarien: User Stories",
        "description": (
            "Funktionstests für /user-stories. Schwerpunkt: Status-Übergänge "
            "und Hierarchiebeziehung zu Deliverables."
        ),
        "user_stories": [
            {
                "title": "TS-US1 | User Story erstellen und Status ändern",
                "description": (
                    "Als Tester möchte ich verifizieren, dass User Stories korrekt angelegt "
                    "und Status-Übergänge (todo → in_progress → done) valide sind."
                ),
                "acceptance_criteria": (
                    "• Test 1: POST /user-stories mit deliverable_id → 201, status='todo'\n"
                    "• Test 2: PUT status zu 'in_progress' → 200, status aktualisiert\n"
                    "• Test 3: PUT status zu 'done' → 200, status='done'"
                ),
                "story_points": 2,
                "business_value": 9,
                "tasks": [
                    {
                        "title": "Task TS-US1.1 | User Story CRUD und Status-Flow implementieren",
                        "description": (
                            "Fixture existing_deliverable gibt ein Deliverable zurück.\n"
                            "test_create_user_story: POST → 201, status == 'todo'.\n"
                            "test_user_story_status_in_progress: POST story → PUT status='in_progress' → 200.\n"
                            "test_user_story_status_done: POST story → PUT status='done' → 200, status=='done'.\n"
                            "Alle erstellten Stories werden per cleanup bereinigt."
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task TS-US1.2 | test_create_user_story_invalid_status",
                        "description": (
                            "```python\n"
                            "async def test_create_user_story_invalid_status(auth_client, deliverable_id):\n"
                            "    r = await auth_client.post('/user-stories/', json={\n"
                            "        'title': 'Bad Status',\n"
                            "        'deliverable_id': deliverable_id,\n"
                            "        'status': 'invalid_value',\n"
                            "    })\n"
                            "    assert r.status_code == 422\n"
                            "```"
                        ),
                        "effort_hours": 0.25,
                    },
                ],
            },
        ],
    },
    # =========================================================================
    # D5 – Testszenarien: Tasks
    # =========================================================================
    {
        "title": "D5 | Testszenarien: Tasks",
        "description": (
            "Funktionstests für /tasks. Tasks sind User Stories untergeordnet "
            "und haben eigene Status-Übergänge."
        ),
        "user_stories": [
            {
                "title": "TS-TK1 | Task erstellen, Status ändern und löschen",
                "description": (
                    "Als Tester möchte ich verifizieren, dass Tasks vollständig "
                    "über die API verwaltet werden können."
                ),
                "acceptance_criteria": (
                    "• Test 1: POST /tasks mit user_story_id → 201, status='todo'\n"
                    "• Test 2: PUT /tasks/{id} status='in_progress' → 200\n"
                    "• Test 3: DELETE /tasks/{id} → 204, danach GET → 404"
                ),
                "story_points": 2,
                "business_value": 8,
                "tasks": [
                    {
                        "title": "Task TS-TK1.1 | test_create_task und test_task_status_transition",
                        "description": (
                            "Fixture existing_user_story gibt eine User Story zurück.\n"
                            "test_create_task: POST → 201, status='todo'.\n"
                            "test_task_status_transition: POST task → PUT status='in_progress' → 200, "
                            "PUT status='done' → 200."
                        ),
                        "effort_hours": 1.0,
                    },
                    {
                        "title": "Task TS-TK1.2 | test_delete_task implementieren",
                        "description": (
                            "```python\n"
                            "async def test_delete_task(auth_client, user_story_id):\n"
                            "    r = await auth_client.post('/tasks/', json={\n"
                            "        'title': 'Temp Task', 'user_story_id': user_story_id})\n"
                            "    task_id = r.json()['id']\n"
                            "    r_del = await auth_client.delete(f'/tasks/{task_id}')\n"
                            "    assert r_del.status_code == 204\n"
                            "    r_get = await auth_client.get(f'/tasks/{task_id}')\n"
                            "    assert r_get.status_code == 404\n"
                            "```"
                        ),
                        "effort_hours": 0.5,
                    },
                ],
            },
        ],
    },
    # =========================================================================
    # D6 – CI-Integration & Dokumentation
    # =========================================================================
    {
        "title": "D6 | CI-Integration und Dokumentation",
        "description": (
            "CI-Pipeline-Integration (GitHub Actions / GitLab CI) und Dokumentation "
            "des Testframeworks für Onboarding neuer Entwickler."
        ),
        "user_stories": [
            {
                "title": "TF-CI1 | README_TESTS.md erstellen",
                "description": (
                    "Als Entwickler möchte ich eine vollständige Dokumentation der "
                    "Testinfrastruktur, damit ich Tests lokal ausführen und erweitern kann."
                ),
                "acceptance_criteria": (
                    "• Abschnitt: Voraussetzungen (Python, pip, laufendes Backend)\n"
                    "• Abschnitt: Lokale Ausführung (pytest-Kommando mit Beispiel-Output)\n"
                    "• Abschnitt: Neue Tests hinzufügen (Fixture-Übersicht, Konventionen)\n"
                    "• Abschnitt: CI/CD-Integration (Verweis auf .github/workflows/tests.yml)\n"
                    "• Abschnitt: Erweiterung auf andere Projekte (Checkliste)"
                ),
                "story_points": 2,
                "business_value": 7,
                "tasks": [
                    {
                        "title": "Task TF-CI1.1 | README_TESTS.md schreiben",
                        "description": (
                            "Schreibe tests/README_TESTS.md mit allen 5 Abschnitten laut\n"
                            "Acceptance Criteria. Verwende Markdown-Formatierung.\n"
                            "Halte es prägnant (max. 200 Zeilen)."
                        ),
                        "effort_hours": 1.5,
                    },
                ],
            },
            {
                "title": "TF-CI2 | GitHub Actions Workflow",
                "description": (
                    "Als DevOps-Engineer möchte ich, dass die Funktionstests bei jedem "
                    "Push auf main automatisch ausgeführt werden."
                ),
                "acceptance_criteria": (
                    "• .github/workflows/tests.yml führt pytest aus\n"
                    "• Service-Container für PostgreSQL und Backend werden hochgefahren\n"
                    "• Tests laufen nach erfolgreichem Backend-Start\n"
                    "• Artefakt mit Testergebnis (JUnit XML) wird gespeichert"
                ),
                "story_points": 3,
                "business_value": 6,
                "tasks": [
                    {
                        "title": "Task TF-CI2.1 | .github/workflows/tests.yml erstellen",
                        "description": (
                            "Erstelle .github/workflows/tests.yml:\n"
                            "- trigger: push auf main, pull_request\n"
                            "- services: postgres:16\n"
                            "- steps: checkout, setup-python, pip install, start backend,\n"
                            "          wait-for-backend (curl retry loop), pytest --junitxml\n"
                            "- artifact: upload junit.xml"
                        ),
                        "effort_hours": 2.0,
                    },
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def login(session: requests.Session) -> None:
    r = session.post(f"{BASE_URL}/auth/login",
                     data={"username": USERNAME, "password": PASSWORD})
    r.raise_for_status()
    token = r.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✓ Eingeloggt als '{USERNAME}'")


def get_or_create_project(session: requests.Session) -> dict:
    projects = session.get(f"{BASE_URL}/projects/").json()
    if not projects:
        print("✗ Keine Projekte gefunden. Bitte erst ein Projekt anlegen.", file=sys.stderr)
        sys.exit(1)

    for p in projects:
        if p["title"] == PROJECT_NAME:
            print(f"✓ Projekt gefunden: '{p['title']}'")
            return p

    print(f"✗ Projekt '{PROJECT_NAME}' nicht gefunden.", file=sys.stderr)
    print(f"  Verfügbare Projekte: {[p['title'] for p in projects]}", file=sys.stderr)
    sys.exit(1)


def create_topic(session: requests.Session, project_id: str) -> dict:
    # Check if topic already exists
    topics = session.get(f"{BASE_URL}/topics/", params={"project_id": project_id}).json()
    for t in topics:
        if t["title"] == "Testmodul":
            print(f"  ℹ Topic 'Testmodul' existiert bereits (ID: {t['id']})")
            return t

    r = session.post(f"{BASE_URL}/topics/", json={
        "title": "Testmodul",
        "description": (
            "Enthält alle Artefakte für das generische Testframework. "
            "Dieses Topic wird durch setup_testmodul.py angelegt und verwaltet.\n\n"
            "Struktur:\n"
            "  D1 | Testframework-Basis (Fixtures, Client, Cleanup)\n"
            "  D2 | Testszenarien: Topics\n"
            "  D3 | Testszenarien: Deliverables\n"
            "  D4 | Testszenarien: User Stories\n"
            "  D5 | Testszenarien: Tasks\n"
            "  D6 | CI-Integration & Dokumentation"
        ),
        "project_id": project_id,
    })
    if r.status_code == 201:
        topic = r.json()
        print(f"  ✓ Topic 'Testmodul' erstellt (ID: {topic['id']})")
        return topic
    else:
        print(f"  ✗ Topic-Erstellung fehlgeschlagen: {r.status_code} – {r.text}", file=sys.stderr)
        sys.exit(1)


def create_deliverable(session: requests.Session, topic_id: str, data: dict) -> dict:
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
    else:
        print(f"    ✗ Deliverable-Erstellung fehlgeschlagen ({r.status_code}): {r.text}")
        return {}


def create_user_story(session: requests.Session, deliverable_id: str, story: dict) -> dict:
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
    else:
        print(f"      ✗ User Story fehlgeschlagen ({r.status_code}): {r.text}")
        return {}


def create_task(session: requests.Session, user_story_id: str, task: dict) -> dict:
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
    else:
        print(f"        ✗ Task fehlgeschlagen ({r.status_code}): {r.text}")
        return {}


def save_task_map(task_map: dict) -> None:
    path = Path("projectflow_testmodul_task_map.json")
    path.write_text(json.dumps(task_map, indent=2, ensure_ascii=False))
    print(f"\n✅ Task-Map gespeichert: {path.resolve()}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 65)
    print("  Project Flow – Testmodul Setup")
    print("=" * 65 + "\n")

    session = requests.Session()
    login(session)

    project = get_or_create_project(session)
    project_id = str(project["id"])

    print(f"\n📁 Lege Topic 'Testmodul' an...")
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
    print(f"     Topic:        1")
    print(f"     Deliverables: {total_deliverables}")
    print(f"     User Stories: {total_stories}")
    print(f"     Tasks:        {total_tasks}")
    print("=" * 65)
    print(f"\n  → Topic 'Testmodul' ist jetzt in Project Flow verfügbar.")
    print(f"  → Task-Map: projectflow_testmodul_task_map.json")
    print(f"\n  Nächste Schritte für Claude Code:")
    print(f"  1. Verzeichnis tests/ im Backend-Root anlegen")
    print(f"  2. User Stories aus D1 abarbeiten (Framework-Basis)")
    print(f"  3. Testszenarien aus D2–D5 implementieren")
    print(f"  4. CI-Workflow aus D6 einrichten")


if __name__ == "__main__":
    main()
