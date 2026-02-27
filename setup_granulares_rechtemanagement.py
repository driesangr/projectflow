"""
setup_granulares_rechtemanagement.py
=====================================
Legt alle Deliverables, User Stories und Tasks für das granulare
Rechtemanagement in ProjectFlow an.

Struktur:
  Deliverable A – Datenmodell & Backend
  Deliverable B – Admin-Oberfläche (Frontend)
  Deliverable C – Integration & Setup-Script

Ausführen:
    python3 setup_granulares_rechtemanagement.py

Voraussetzungen:
  - ProjectFlow läuft lokal auf http://localhost:8000 (Backend)
  - Ein Admin-User mit den unten konfigurierten Credentials existiert
  - Das Projekt "Project Flow" und das Topic "Rechtemanagement" existieren bereits
"""

import sys
import requests

# ── Konfiguration ─────────────────────────────────────────────────────────────

BASE_URL  = "http://localhost:8000"
USERNAME  = "admin"
PASSWORD  = "admin123"

# Name des Projekts und des Topics, unter dem die Deliverables angelegt werden
TARGET_PROJECT_TITLE = "Project Flow"
TARGET_TOPIC_TITLE   = "Rechtemanagement"

# ── Deliverable-Beschreibungen ────────────────────────────────────────────────

DELIVERABLE_A_TITLE       = "Granulares Rechtemanagement – Datenmodell & Backend"
DELIVERABLE_A_DESCRIPTION = """\
Erweiterung des bestehenden Rechtemanagements um ein feingranulares,
artefaktbasiertes Berechtigungssystem auf Datenbankebene und im Backend.

Kernkonzept:
  - Neue Tabelle role_permissions: speichert Rechte pro Rolle + Artefakt-Typ
  - Rechtetypen: can_read, can_write, can_create, can_delete
  - Vererbung: inherit_to_children propagiert Rechte dynamisch nach unten
  - Konfliktauflösung: spezifischere Rechte überschreiben vererbte Rechte
  - Hierarchie: ProjectGroup → Project → Topic → Deliverable → UserStory → Task

Technische Basis: Alembic-Migration, SQLAlchemy-Model, FastAPI-Endpoints,
erweiterte Permissions-Engine, die bestehende project_memberships-Tabelle
und permissions.py werden kompatibel erweitert.\
"""

DELIVERABLE_B_TITLE       = "Granulares Rechtemanagement – Admin-Oberfläche"
DELIVERABLE_B_DESCRIPTION = """\
Vue 3 Admin-Interface zur Konfiguration des granularen Rechtemanagements.

Kernkonzept:
  - Neue View: ConfigPermissionsView.vue
  - Workflow: Rolle auswählen → Baum navigieren → Rechte konfigurieren
  - Baum-Ansicht mit allen 6 Artefakt-Ebenen (ProjectGroup bis Task)
  - Visuelle Unterscheidung: explizit gesetzt vs. vererbt vs. kein Recht
  - Vererbungs-Toggle: "Auf alle Kindelemente anwenden" pro Knoten
  - Bulk-Aktion mit Vorschau: zeigt Anzahl betroffener Knoten vor dem Speichern
  - Filter: "Nur explizit gesetzte Rechte anzeigen"
  - Konflikt-Markierung: überschriebene vererbte Rechte werden hervorgehoben

Technische Basis: Vue 3 Composition API, TypeScript, Tailwind CSS,
neue API-Client-Methoden, Integration in bestehende Sidebar-Navigation.\
"""

DELIVERABLE_C_TITLE       = "Granulares Rechtemanagement – Integration & Rollout"
DELIVERABLE_C_DESCRIPTION = """\
Integration der neuen Permissions-Engine in alle bestehenden Router,
Absicherung aller Endpoints gegen das neue Rechtesystem sowie
das finale idempotente Setup-Script für die Produktion.

Kernkonzept:
  - Alle bestehenden FastAPI-Router werden mit den neuen granularen Guards
    abgesichert (ersetzt bzw. ergänzt die bisherigen require_viewer/member-Guards)
  - Superuser bypassen weiterhin alle Checks
  - Rückwärtskompatibilität: bestehende project_memberships bleiben erhalten
  - Idempotentes Migrations-Script für bestehende Installationen
  - Dokumentation der Rollenkonfiguration

Technische Basis: Anpassung aller Router-Dateien, erweitertes permissions.py,
Alembic-Migration, Seed-Script für Standard-Rollenkonfiguration.\
"""

# ── User Stories & Tasks ──────────────────────────────────────────────────────
#
# Format User Story: (title, description, acceptance_criteria, story_points, business_value)
# Format Task:       (title, description)  → werden der jeweils vorherigen Story zugeordnet
#
# Tasks sind so formuliert, dass Claude Code sie direkt verarbeiten kann.
# Claude Code-Anweisung: "Arbeite alle Tasks in den User Stories X, Y, Z ab."

DELIVERABLE_A_STORIES = [

    # ── A-1 ──────────────────────────────────────────────────────────────────
    (
        "A-1 | Datenmodell role_permissions anlegen",
        "Als Entwickler möchte ich eine neue Tabelle role_permissions, die pro Kombination "
        "aus Projektrolle und Artefakt-Typ die vier Rechte (read, write, create, delete) "
        "sowie das Vererbungsflag speichert, damit Berechtigungen feingranular und "
        "rollenbasiert konfiguriert werden können.",
        "• Tabelle role_permissions mit Spalten: id (UUID PK), project_role (FK/Enum: "
        "owner/manager/member/viewer), artifact_type (Enum: project_group/project/topic/"
        "deliverable/user_story/task), can_read (bool), can_write (bool), can_create (bool), "
        "can_delete (bool), inherit_to_children (bool, default false), "
        "created_at, updated_at\n"
        "• Unique-Constraint auf (project_role, artifact_type)\n"
        "• Alle bool-Felder haben Default false außer can_read (Default true)\n"
        "• SQLAlchemy-Model RolePermission in app/models/role_permission.py\n"
        "• Alembic-Migration 0008 ist idempotent (mehrfaches Ausführen ohne Fehler)\n"
        "• Model ist in app/models/__init__.py registriert",
        5, 10,
    ),
    [
        (
            "Task A-1.1 | Enum ArtifactType erstellen",
            "Erstelle in app/models/role_permission.py einen Python-Enum ArtifactType "
            "mit den Werten: project_group, project, topic, deliverable, user_story, task. "
            "Erstelle zusätzlich den zugehörigen PostgreSQL-Enum-Typ 'artifacttype' in der "
            "Alembic-Migration. Der Enum soll als String-Enum (str, enum.Enum) implementiert "
            "werden analog zu ProjectRole in app/models/project_membership.py.",
        ),
        (
            "Task A-1.2 | SQLAlchemy-Model RolePermission erstellen",
            "Erstelle in app/models/role_permission.py das SQLAlchemy-Model RolePermission "
            "mit folgenden Spalten: id (UUID, PK, gen_random_uuid()), project_role (Enum "
            "ProjectRole, not null), artifact_type (Enum ArtifactType, not null), "
            "can_read (Boolean, default True, not null), can_write (Boolean, default False, "
            "not null), can_create (Boolean, default False, not null), can_delete (Boolean, "
            "default False, not null), inherit_to_children (Boolean, default False, not null), "
            "created_at und updated_at (via TimestampMixin aus app/models/base.py). "
            "Füge UniqueConstraint auf (project_role, artifact_type) hinzu. "
            "Registriere das Model in app/models/__init__.py.",
        ),
        (
            "Task A-1.3 | Alembic-Migration 0008 erstellen",
            "Erstelle die Datei backend/alembic/versions/0008_add_role_permissions.py. "
            "Die Migration soll idempotent sein (DO $$ BEGIN ... IF NOT EXISTS ... END $$). "
            "Sie soll: (1) den PostgreSQL-Enum-Typ 'artifacttype' anlegen falls nicht "
            "vorhanden, (2) die Tabelle role_permissions mit allen Spalten anlegen falls "
            "nicht vorhanden, (3) den Unique-Index auf (project_role, artifact_type) anlegen. "
            "down_revision = '0007'. Die downgrade()-Funktion soll die Tabelle und den "
            "Enum-Typ wieder entfernen. Orientiere dich am Muster von "
            "backend/alembic/versions/0007_add_roles_and_memberships.py.",
        ),
    ],

    # ── A-2 ──────────────────────────────────────────────────────────────────
    (
        "A-2 | Vererbungslogik im Backend implementieren",
        "Als Entwickler möchte ich, dass beim Setzen von inherit_to_children=true auf "
        "einem Knoten die Rechte automatisch an alle Kindelement-Typen in der Hierarchie "
        "propagiert werden, wobei explizit gesetzte Rechte auf Kindknoten nicht "
        "überschrieben werden (spezifischere Rechte gewinnen).",
        "• Funktion propagate_permissions(role, artifact_type, permissions, db) in "
        "app/services/permissions_service.py vorhanden\n"
        "• Die Hierarchie project_group→project→topic→deliverable→user_story→task "
        "ist als geordnete Liste definiert\n"
        "• Propagation überschreibt nur Einträge ohne explizit gesetztes Flag "
        "(is_explicit=false) – Einträge mit is_explicit=true bleiben unverändert\n"
        "• Neue Spalte is_explicit (bool, default true) auf role_permissions\n"
        "• Bei Änderung von inherit_to_children=false auf true: sofortige Propagation\n"
        "• Bei Änderung von inherit_to_children=true auf false: Propagation wird "
        "gestoppt, bereits propagierte Einträge werden gelöscht\n"
        "• Unit-Tests für die Propagationslogik in backend/tests/test_permissions_service.py",
        8, 10,
    ),
    [
        (
            "Task A-2.1 | Spalte is_explicit zu role_permissions hinzufügen",
            "Erweitere die Alembic-Migration 0008 (oder erstelle 0008b) um die Spalte "
            "is_explicit (Boolean, default True, not null) auf der Tabelle role_permissions. "
            "Aktualisiere das SQLAlchemy-Model RolePermission in app/models/role_permission.py "
            "entsprechend. is_explicit=True bedeutet: direkt vom Admin gesetzt. "
            "is_explicit=False bedeutet: durch Vererbung propagiert.",
        ),
        (
            "Task A-2.2 | Hierarchie-Konstante und Hilfsfunktion definieren",
            "Erstelle app/services/permissions_service.py. Definiere darin die Konstante "
            "ARTIFACT_HIERARCHY als geordnete Liste: "
            "['project_group', 'project', 'topic', 'deliverable', 'user_story', 'task']. "
            "Implementiere die Hilfsfunktion get_children(artifact_type: ArtifactType) -> "
            "list[ArtifactType], die alle untergeordneten Artefakt-Typen zurückgibt. "
            "Beispiel: get_children('topic') → ['deliverable', 'user_story', 'task'].",
        ),
        (
            "Task A-2.3 | Funktion propagate_permissions implementieren",
            "Implementiere in app/services/permissions_service.py die async-Funktion "
            "propagate_permissions(role: ProjectRole, artifact_type: ArtifactType, "
            "source_permission: RolePermission, db: AsyncSession) -> None. "
            "Die Funktion soll: (1) alle Kind-Artefakt-Typen via get_children() ermitteln, "
            "(2) für jeden Kind-Typ prüfen ob ein Eintrag mit is_explicit=True existiert – "
            "wenn ja: überspringen, (3) wenn kein expliziter Eintrag existiert: einen neuen "
            "Eintrag anlegen oder den bestehenden is_explicit=False-Eintrag aktualisieren "
            "mit den Werten aus source_permission (can_read, can_write, can_create, "
            "can_delete), jedoch inherit_to_children=False setzen. "
            "Implementiere auch clear_propagated_permissions(role, artifact_type, db), "
            "die alle is_explicit=False-Einträge unterhalb des gegebenen Knotens löscht.",
        ),
        (
            "Task A-2.4 | Unit-Tests für Propagationslogik schreiben",
            "Erstelle backend/tests/test_permissions_service.py mit pytest-Tests für "
            "propagate_permissions und clear_propagated_permissions. Teste mindestens: "
            "(1) Propagation von topic nach unten schreibt deliverable/user_story/task, "
            "(2) expliziter Eintrag auf deliverable wird nicht überschrieben, "
            "(3) clear_propagated_permissions löscht nur is_explicit=False-Einträge, "
            "(4) Propagation mit inherit_to_children=False propagiert nichts. "
            "Nutze pytest-asyncio und eine In-Memory-SQLite-Testdatenbank.",
        ),
    ],

    # ── A-3 ──────────────────────────────────────────────────────────────────
    (
        "A-3 | CRUD-API für role_permissions erstellen",
        "Als Admin möchte ich über eine REST-API die Rechte pro Rolle und Artefakt-Typ "
        "lesen, setzen und zurücksetzen können, damit die Admin-Oberfläche diese "
        "Daten abrufen und speichern kann.",
        "• GET /admin/permissions/ – alle Einträge (filterbar nach role)\n"
        "• GET /admin/permissions/{role}/{artifact_type} – einzelner Eintrag\n"
        "• PUT /admin/permissions/{role}/{artifact_type} – anlegen oder aktualisieren "
        "(upsert); löst Propagation aus wenn inherit_to_children=true\n"
        "• DELETE /admin/permissions/{role}/{artifact_type} – Eintrag löschen "
        "(setzt Rechte auf Default zurück)\n"
        "• Alle Endpoints erfordern global_role=admin oder superuser\n"
        "• Pydantic-Schemas in app/schemas/role_permission.py\n"
        "• Router in app/routers/permissions.py registriert in app/main.py",
        5, 9,
    ),
    [
        (
            "Task A-3.1 | Pydantic-Schemas erstellen",
            "Erstelle app/schemas/role_permission.py mit folgenden Pydantic-Schemas: "
            "RolePermissionBase (can_read, can_write, can_create, can_delete, "
            "inherit_to_children – alle Optional[bool]), "
            "RolePermissionCreate (erbt von Base, role: ProjectRole, "
            "artifact_type: ArtifactType – beide required), "
            "RolePermissionUpdate (erbt von Base – alle Felder optional), "
            "RolePermissionResponse (erbt von Base, zusätzlich: id, project_role, "
            "artifact_type, is_explicit, created_at, updated_at; Config: from_attributes=True). "
            "Importiere ProjectRole aus app/models/project_membership und "
            "ArtifactType aus app/models/role_permission.",
        ),
        (
            "Task A-3.2 | Router app/routers/permissions.py erstellen",
            "Erstelle app/routers/permissions.py mit prefix='/admin/permissions' und "
            "tag='permissions'. Implementiere folgende Endpoints: "
            "(1) GET / → list[RolePermissionResponse], Query-Parameter role: Optional[ProjectRole]; "
            "(2) GET /{role}/{artifact_type} → RolePermissionResponse, 404 wenn nicht vorhanden; "
            "(3) PUT /{role}/{artifact_type} → RolePermissionResponse, Body: RolePermissionUpdate, "
            "Upsert-Logik (update wenn vorhanden, insert wenn nicht), setzt is_explicit=True, "
            "ruft propagate_permissions() auf wenn inherit_to_children=True, "
            "ruft clear_propagated_permissions() auf wenn inherit_to_children von True auf False wechselt; "
            "(4) DELETE /{role}/{artifact_type} → 204, löscht Eintrag. "
            "Alle Endpoints nutzen require_global_admin() aus app/core/permissions.py.",
        ),
        (
            "Task A-3.3 | Router in main.py registrieren",
            "Importiere den neuen Router aus app/routers/permissions.py in app/main.py "
            "und registriere ihn via app.include_router(permissions_router). "
            "Füge den Import in den Kommentar-Block '# ── New routers ──' ein. "
            "Stelle sicher, dass der Router nach memberships_router registriert wird.",
        ),
    ],

    # ── A-4 ──────────────────────────────────────────────────────────────────
    (
        "A-4 | Standard-Rollenkonfiguration als Seed-Daten definieren",
        "Als Entwickler möchte ich eine vordefinierte Standard-Konfiguration für alle "
        "Projektrollen, die beim ersten Start oder per Script eingespielt werden kann, "
        "damit ein neues System sofort sinnvoll vorkonfiguriert ist.",
        "• Seed-Daten definiert für alle 4 Rollen × 6 Artefakt-Typen = 24 Einträge\n"
        "• owner: volle Rechte auf allen Ebenen\n"
        "• manager: read/write/create auf allen Ebenen, kein delete\n"
        "• member: read auf ProjectGroup/Project/Topic/Deliverable, "
        "read/write/create auf UserStory/Task\n"
        "• viewer: nur read auf allen Ebenen\n"
        "• Seed-Funktion in app/services/permissions_service.py vorhanden\n"
        "• Seed ist idempotent: bestehende is_explicit=True-Einträge werden nicht überschrieben\n"
        "• Seed kann via CLI aufgerufen werden: python -m app.services.permissions_service seed",
        3, 8,
    ),
    [
        (
            "Task A-4.1 | Seed-Daten-Konstante definieren",
            "Definiere in app/services/permissions_service.py die Konstante "
            "DEFAULT_PERMISSIONS als Liste von Dicts mit den Schlüsseln "
            "project_role, artifact_type, can_read, can_write, can_create, can_delete. "
            "Die Konfiguration soll sein: "
            "owner: alle 4 Rechte true auf allen 6 Ebenen; "
            "manager: can_read=True, can_write=True, can_create=True, can_delete=False auf allen 6 Ebenen; "
            "member: can_read=True, can_write=False, can_create=False, can_delete=False auf "
            "project_group/project/topic/deliverable; can_read=True, can_write=True, "
            "can_create=True, can_delete=False auf user_story/task; "
            "viewer: can_read=True, alle anderen False auf allen 6 Ebenen.",
        ),
        (
            "Task A-4.2 | Seed-Funktion implementieren",
            "Implementiere in app/services/permissions_service.py die async-Funktion "
            "seed_default_permissions(db: AsyncSession, overwrite: bool = False) -> int. "
            "Die Funktion iteriert über DEFAULT_PERMISSIONS und legt für jeden Eintrag "
            "einen RolePermission-Datensatz an, sofern kein Eintrag mit is_explicit=True "
            "für diese (project_role, artifact_type)-Kombination existiert (idempotent). "
            "Bei overwrite=True werden bestehende is_explicit=True-Einträge überschrieben. "
            "Die Funktion gibt die Anzahl der angelegten/aktualisierten Einträge zurück. "
            "Implementiere zusätzlich einen __main__-Block, der seed_default_permissions "
            "mit overwrite=False aufruft, sodass das Script direkt ausführbar ist.",
        ),
    ],
]

DELIVERABLE_B_STORIES = [

    # ── B-1 ──────────────────────────────────────────────────────────────────
    (
        "B-1 | TypeScript-Typen und API-Client für Permissions erweitern",
        "Als Frontend-Entwickler möchte ich TypeScript-Typen und API-Client-Funktionen "
        "für das Permissions-System, damit ich die Admin-Oberfläche typsicher "
        "implementieren kann.",
        "• Typ ArtifactType in frontend/src/types/index.ts ergänzt\n"
        "• Interface RolePermission in frontend/src/types/index.ts ergänzt\n"
        "• API-Modul frontend/src/api/permissions.ts mit allen CRUD-Funktionen\n"
        "• Funktionen: listPermissions(role?), getPermission(role, artifactType), "
        "upsertPermission(role, artifactType, data), deletePermission(role, artifactType)\n"
        "• Alle Funktionen sind typsiert und nutzen den bestehenden apiClient aus "
        "frontend/src/api/client.ts",
        3, 7,
    ),
    [
        (
            "Task B-1.1 | TypeScript-Typen ergänzen",
            "Ergänze frontend/src/types/index.ts um folgende Typen: "
            "ArtifactType als Union-Type: 'project_group' | 'project' | 'topic' | "
            "'deliverable' | 'user_story' | 'task'; "
            "Interface RolePermission mit Feldern: id (string), project_role (ProjectRole), "
            "artifact_type (ArtifactType), can_read (boolean), can_write (boolean), "
            "can_create (boolean), can_delete (boolean), inherit_to_children (boolean), "
            "is_explicit (boolean), created_at (string), updated_at (string); "
            "Interface RolePermissionUpdate mit allen optionalen boolean-Feldern: "
            "can_read?, can_write?, can_create?, can_delete?, inherit_to_children?.",
        ),
        (
            "Task B-1.2 | API-Modul permissions.ts erstellen",
            "Erstelle frontend/src/api/permissions.ts. Importiere apiClient aus "
            "./client und die Typen RolePermission, RolePermissionUpdate, ProjectRole, "
            "ArtifactType aus ../types. Implementiere und exportiere folgende Funktionen: "
            "listPermissions(role?: ProjectRole): Promise<RolePermission[]> → GET /admin/permissions/ mit optionalem ?role=; "
            "getPermission(role: ProjectRole, artifactType: ArtifactType): Promise<RolePermission> → GET /admin/permissions/{role}/{artifactType}; "
            "upsertPermission(role: ProjectRole, artifactType: ArtifactType, data: RolePermissionUpdate): Promise<RolePermission> → PUT /admin/permissions/{role}/{artifactType}; "
            "deletePermission(role: ProjectRole, artifactType: ArtifactType): Promise<void> → DELETE /admin/permissions/{role}/{artifactType}.",
        ),
    ],

    # ── B-2 ──────────────────────────────────────────────────────────────────
    (
        "B-2 | Permissions-Store (Pinia) implementieren",
        "Als Frontend-Entwickler möchte ich einen Pinia-Store für das Permissions-System, "
        "der den State der Konfiguration hält, Lade- und Speichervorgänge kapselt "
        "und die Vererbungslogik für die UI aufbereitet.",
        "• Pinia-Store usePermissionsStore in frontend/src/stores/permissions.ts\n"
        "• State: permissions (Map<string, RolePermission>), selectedRole, loading, error\n"
        "• Actions: fetchPermissions(role), savePermission(role, artifactType, data), "
        "resetPermission(role, artifactType)\n"
        "• Getter: getPermission(role, artifactType), isInherited(role, artifactType), "
        "getEffectivePermission(role, artifactType)\n"
        "• isInherited gibt true zurück wenn is_explicit=false\n"
        "• getEffectivePermission gibt das gültige Recht zurück (explizit hat Vorrang)",
        5, 8,
    ),
    [
        (
            "Task B-2.1 | Pinia-Store Grundstruktur erstellen",
            "Erstelle frontend/src/stores/permissions.ts. Definiere den Store mit "
            "usePermissionsStore via defineStore('permissions', ...). "
            "State: permissions als Ref auf Map<string, RolePermission> (Key-Format: "
            "'role:artifact_type', z.B. 'member:topic'), selectedRole als Ref auf "
            "ProjectRole | null (initial null), loading als Ref auf boolean (initial false), "
            "error als Ref auf string | null (initial null). "
            "Importiere alle benötigten Typen aus ../types und alle API-Funktionen "
            "aus ../api/permissions.",
        ),
        (
            "Task B-2.2 | Actions implementieren",
            "Implementiere in usePermissionsStore folgende Actions: "
            "fetchPermissions(role: ProjectRole): ruft listPermissions(role) auf, "
            "befüllt die permissions-Map, setzt loading/error korrekt; "
            "savePermission(role: ProjectRole, artifactType: ArtifactType, "
            "data: RolePermissionUpdate): ruft upsertPermission() auf, aktualisiert "
            "den Store-Eintrag, gibt das gespeicherte RolePermission zurück; "
            "resetPermission(role: ProjectRole, artifactType: ArtifactType): "
            "ruft deletePermission() auf, entfernt den Eintrag aus der Map. "
            "Alle Actions sollen Fehler fangen und in error speichern.",
        ),
        (
            "Task B-2.3 | Getter implementieren",
            "Implementiere in usePermissionsStore folgende berechnete Properties "
            "(computed): getPermission als Funktion (role, artifactType) → "
            "RolePermission | undefined, liest aus der permissions-Map mit Key "
            "'role:artifact_type'; isInherited als Funktion (role, artifactType) → "
            "boolean, gibt true zurück wenn der Eintrag exists und is_explicit===false; "
            "hasConflict als Funktion (role, artifactType) → boolean, gibt true zurück "
            "wenn ein Eintrag is_explicit=false hat aber ein Elternelement "
            "inherit_to_children=true hat (zeigt überschriebene Vererbung an).",
        ),
    ],

    # ── B-3 ──────────────────────────────────────────────────────────────────
    (
        "B-3 | PermissionsTreeNode-Komponente erstellen",
        "Als Admin möchte ich im Berechtigungsbaum für jeden Artefakt-Typ eine Zeile "
        "sehen, die den Namen des Artefakts, die vier Checkboxen (lesen/schreiben/"
        "anlegen/löschen), den Vererbungs-Toggle und visuelle Status-Indikatoren zeigt.",
        "• Komponente frontend/src/components/permissions/PermissionsTreeNode.vue\n"
        "• Props: artifactType (ArtifactType), role (ProjectRole), depth (number für Einrückung)\n"
        "• Zeigt: Artefakt-Label (deutsch), 4 Checkboxen, inherit-Toggle\n"
        "• Visueller Status: grüner Punkt = explizit gesetzt, grauer Punkt = vererbt, "
        "kein Punkt = kein Recht\n"
        "• Checkbox-Änderungen rufen savePermission() im Store auf\n"
        "• Inherit-Toggle mit Vorschau: zeigt Tooltip 'X Kindelemente werden aktualisiert'\n"
        "• Disabled-State wenn Rolle superuser (superuser ist nicht konfigurierbar)\n"
        "• Loading-Spinner während Speichervorgang",
        8, 9,
    ),
    [
        (
            "Task B-3.1 | Komponenten-Grundstruktur und Props",
            "Erstelle frontend/src/components/permissions/PermissionsTreeNode.vue als "
            "Vue 3 Single File Component mit <script setup lang='ts'>. "
            "Definiere Props via defineProps: artifactType (ArtifactType, required), "
            "role (ProjectRole, required), depth (number, default 0). "
            "Importiere usePermissionsStore und alle benötigten Typen. "
            "Definiere eine computed-Property permission, die den aktuellen Eintrag "
            "aus dem Store liest. Definiere eine computed-Property isInherited. "
            "Definiere eine Konstante ARTIFACT_LABELS: Record<ArtifactType, string> "
            "mit deutschen Bezeichnungen: project_group='Projektgruppe', "
            "project='Projekt', topic='Topic', deliverable='Deliverable', "
            "user_story='User Story', task='Task'.",
        ),
        (
            "Task B-3.2 | Template mit Checkboxen und Status-Indikator",
            "Implementiere das <template> von PermissionsTreeNode.vue. "
            "Struktur: Ein div mit padding-left basierend auf depth*20px. "
            "Zeige links einen Status-Indikator (grüner Kreis wenn is_explicit=true, "
            "grauer Kreis wenn is_explicit=false/vererbt, leerer Kreis wenn kein Eintrag). "
            "Zeige den ARTIFACT_LABELS-Wert als Label (Breite: 150px). "
            "Zeige 4 Checkboxen mit Labels: Lesen, Schreiben, Anlegen, Löschen. "
            "Jede Checkbox ist an can_read/can_write/can_create/can_delete des "
            "permission-Objekts gebunden (falls kein Eintrag: alle unchecked). "
            "Zeige rechts einen Toggle-Button 'Vererben' mit einem Tooltip, der "
            "'Rechte auf alle Kindelemente anwenden' anzeigt. "
            "Nutze ausschließlich Tailwind CSS-Klassen für das Styling.",
        ),
        (
            "Task B-3.3 | Event-Handler und Speicherlogik",
            "Implementiere in PermissionsTreeNode.vue die Methode handlePermissionChange("
            "field: keyof RolePermissionUpdate, value: boolean). Sie soll: "
            "(1) den Store via savePermission() aufrufen mit den aktuellen Werten "
            "plus der Änderung, (2) einen lokalen loading-State (ref: isSaving) setzen "
            "während des Speichervorgangs, (3) bei Fehler eine Error-Message anzeigen. "
            "Implementiere handleInheritToggle(): soll inherit_to_children togggeln und "
            "savePermission aufrufen. Alle Checkboxen und der Toggle-Button sollen "
            "disabled sein wenn isSaving=true oder role==='superuser'.",
        ),
    ],

    # ── B-4 ──────────────────────────────────────────────────────────────────
    (
        "B-4 | ConfigPermissionsView erstellen und in Navigation einbinden",
        "Als Admin möchte ich eine eigene View zur Rechtekonfiguration aufrufen können, "
        "die mir den vollständigen Berechtigungsbaum für die gewählte Rolle anzeigt "
        "und alle Interaktionen aus B-3 zusammenführt.",
        "• View frontend/src/views/ConfigPermissionsView.vue\n"
        "• Rollen-Selector oben: Dropdown mit owner/manager/member/viewer\n"
        "• Baum darunter: alle 6 Artefakt-Typen in korrekter Hierarchie-Reihenfolge "
        "mit PermissionsTreeNode-Komponente, je um eine Ebene eingerückt\n"
        "• Filter-Toggle: 'Nur explizit gesetzte Rechte anzeigen'\n"
        "• Button 'Standard-Konfiguration laden' mit Bestätigungsdialog\n"
        "• Route /admin/permissions in frontend/src/router/index.ts eingetragen\n"
        "• Link 'Berechtigungen' in der Sidebar unter Konfiguration (analog zu "
        "ConfigUsersView)\n"
        "• Route ist nur sichtbar/erreichbar für Nutzer mit global_role=admin oder superuser",
        5, 9,
    ),
    [
        (
            "Task B-4.1 | ConfigPermissionsView Grundstruktur",
            "Erstelle frontend/src/views/ConfigPermissionsView.vue als Vue 3 SFC. "
            "Importiere usePermissionsStore, PermissionsTreeNode, alle Typen. "
            "Definiere: selectedRole als ref<ProjectRole>('member'), "
            "showOnlyExplicit als ref<boolean>(false). "
            "Beim Mounten (onMounted) und bei Änderung von selectedRole (watch): "
            "rufe store.fetchPermissions(selectedRole.value) auf. "
            "Definiere die Konstante ROLE_OPTIONS als Array mit allen 4 Projektrollen "
            "und deutschen Labels: owner='Eigentümer', manager='Manager', "
            "member='Mitglied', viewer='Betrachter'.",
        ),
        (
            "Task B-4.2 | Template mit Rollen-Selector und Baum",
            "Implementiere das <template> von ConfigPermissionsView.vue. "
            "Oben: Seitenüberschrift 'Berechtigungen konfigurieren', darunter ein "
            "<select>-Element für selectedRole mit den ROLE_OPTIONS. "
            "Rechts davon: Checkbox 'Nur explizit gesetzte Rechte anzeigen' für "
            "showOnlyExplicit. Darunter: eine Tabelle oder ein div mit Header-Zeile "
            "(Spalten: Artefakt, Lesen, Schreiben, Anlegen, Löschen, Vererben). "
            "Im Body: eine PermissionsTreeNode-Komponente für jeden ArtifactType in "
            "Reihenfolge project_group(depth=0), project(depth=1), topic(depth=2), "
            "deliverable(depth=3), user_story(depth=4), task(depth=5). "
            "Filtere bei showOnlyExplicit=true alle Knoten ohne expliziten Eintrag heraus. "
            "Zeige einen Lade-Spinner wenn store.loading=true.",
        ),
        (
            "Task B-4.3 | Route und Sidebar-Integration",
            "Füge in frontend/src/router/index.ts eine neue Route ein: "
            "path: '/admin/permissions', name: 'config-permissions', "
            "component: () => import('../views/ConfigPermissionsView.vue'), "
            "meta: { requiresAuth: true, requiresAdmin: true }. "
            "Platziere die Route im Bereich der anderen Admin/Config-Routen, "
            "nach der Route für ConfigUsersView. "
            "Füge in der Sidebar-Komponente (suche in frontend/src/components/layout/ "
            "nach der Sidebar) einen neuen Link 'Berechtigungen' mit der Route "
            "'config-permissions' ein, analog zum bestehenden Link für Benutzerverwaltung. "
            "Der Link soll nur für Nutzer mit global_role 'admin' oder 'superuser' "
            "sichtbar sein.",
        ),
    ],
]

DELIVERABLE_C_STORIES = [

    # ── C-1 ──────────────────────────────────────────────────────────────────
    (
        "C-1 | Permissions-Engine auf artefaktbasierte Prüfung erweitern",
        "Als Entwickler möchte ich die bestehende permissions.py um Funktionen erweitern, "
        "die nicht nur die Projektmitgliedschaft prüfen, sondern auch die granularen "
        "Rechte aus role_permissions auswerten, damit alle Endpoints das neue System nutzen.",
        "• Neue Funktion check_artifact_permission(user, project_id, artifact_type, "
        "required_permission, db) in app/core/permissions.py\n"
        "• required_permission ist einer der Werte: 'read', 'write', 'create', 'delete'\n"
        "• Superuser: bypassen immer\n"
        "• Admins: dürfen nur 'read'\n"
        "• Alle anderen: Projektrolle ermitteln, dann role_permissions prüfen\n"
        "• Neue Dependency-Factory require_artifact_permission(artifact_type, permission)\n"
        "• Bestehende require_viewer/member/manager/owner bleiben für Rückwärtskompatibilität\n"
        "• Bei fehlendem role_permissions-Eintrag: Fallback auf bisherige Logik",
        5, 10,
    ),
    [
        (
            "Task C-1.1 | check_artifact_permission implementieren",
            "Erweitere app/core/permissions.py um die async-Funktion "
            "check_artifact_permission(user: User, project_id: UUID, "
            "artifact_type: ArtifactType, required_permission: str, "
            "db: AsyncSession) -> bool. "
            "Die Funktion soll: (1) bei superuser immer True zurückgeben, "
            "(2) bei admin nur bei required_permission=='read' True zurückgeben, "
            "(3) die Projektrolle des Users via get_project_role() ermitteln, "
            "(4) den RolePermission-Eintrag für (role, artifact_type) aus der DB laden, "
            "(5) das entsprechende can_*-Feld prüfen und zurückgeben, "
            "(6) bei fehlendem Eintrag als Fallback die bestehende Projektrollenprüfung "
            "nutzen (owner/manager=True für alles, member=True für read/write/create, "
            "viewer=True nur für read). "
            "Importiere RolePermission und ArtifactType aus den Models.",
        ),
        (
            "Task C-1.2 | require_artifact_permission Dependency-Factory erstellen",
            "Implementiere in app/core/permissions.py die Dependency-Factory "
            "require_artifact_permission(artifact_type: ArtifactType, "
            "permission: str) -> Callable. "
            "Die zurückgegebene async-Funktion soll als FastAPI-Dependency nutzbar sein, "
            "project_id aus dem Pfad lesen, check_artifact_permission() aufrufen und "
            "bei False eine HTTPException 403 werfen mit der Nachricht "
            "'Keine Berechtigung: {permission} auf {artifact_type}'. "
            "Erstelle praktische Shortcuts analog zu require_viewer/member: "
            "require_topic_read = require_artifact_permission('topic', 'read'), "
            "require_topic_write = require_artifact_permission('topic', 'write'), "
            "require_story_create = require_artifact_permission('user_story', 'create'), "
            "require_task_write = require_artifact_permission('task', 'write').",
        ),
    ],

    # ── C-2 ──────────────────────────────────────────────────────────────────
    (
        "C-2 | Bestehende Router mit granularen Guards absichern",
        "Als Entwickler möchte ich, dass alle bestehenden FastAPI-Router die neuen "
        "granularen Permissions-Guards nutzen, damit das Rechtesystem überall greift.",
        "• Router topics.py: GET-Endpoints nutzen require_artifact_permission('topic','read'), "
        "POST/PUT nutzen require_artifact_permission('topic','write'), "
        "POST (create) nutzt require_artifact_permission('project','create'), "
        "DELETE nutzt require_artifact_permission('topic','delete')\n"
        "• Router deliverables.py: analog mit artifact_type='deliverable'\n"
        "• Router user_stories.py: analog mit artifact_type='user_story'\n"
        "• Router tasks.py: analog mit artifact_type='task'\n"
        "• Router projects.py: analog mit artifact_type='project'\n"
        "• Router project_groups.py: analog mit artifact_type='project_group'\n"
        "• Bestehende require_viewer/member/manager-Dependencies werden ersetzt\n"
        "• Superuser-Bypass bleibt erhalten\n"
        "• Alle Router-Tests laufen weiterhin durch",
        8, 10,
    ),
    [
        (
            "Task C-2.1 | Router topics.py aktualisieren",
            "Aktualisiere app/routers/topics.py. Ersetze alle Dependency-Nutzungen von "
            "require_viewer, require_member, require_manager, require_owner durch die "
            "entsprechenden require_artifact_permission-Calls: "
            "GET-Endpoints (list, get): Depends(require_artifact_permission('topic', 'read')); "
            "PUT/PATCH-Endpoints (update): Depends(require_artifact_permission('topic', 'write')); "
            "POST-Endpoint (create topic): Depends(require_artifact_permission('project', 'create')); "
            "DELETE-Endpoint: Depends(require_artifact_permission('topic', 'delete')). "
            "Importiere require_artifact_permission aus app.core.permissions. "
            "Entferne nicht mehr benötigte Imports.",
        ),
        (
            "Task C-2.2 | Router deliverables.py aktualisieren",
            "Aktualisiere app/routers/deliverables.py analog zu Task C-2.1. "
            "Mapping: GET→('deliverable','read'), PUT/PATCH→('deliverable','write'), "
            "POST (create)→('topic','create'), DELETE→('deliverable','delete'). "
            "Ersetze alle alten Dependency-Imports.",
        ),
        (
            "Task C-2.3 | Router user_stories.py und tasks.py aktualisieren",
            "Aktualisiere app/routers/user_stories.py und app/routers/tasks.py "
            "analog zu Task C-2.1. "
            "user_stories.py Mapping: GET→('user_story','read'), "
            "PUT/PATCH→('user_story','write'), POST (create)→('deliverable','create'), "
            "DELETE→('user_story','delete'). "
            "tasks.py Mapping: GET→('task','read'), PUT/PATCH→('task','write'), "
            "POST (create)→('user_story','create'), DELETE→('task','delete').",
        ),
        (
            "Task C-2.4 | Router projects.py und project_groups.py aktualisieren",
            "Aktualisiere app/routers/projects.py und app/routers/project_groups.py "
            "analog zu Task C-2.1. "
            "projects.py Mapping: GET→('project','read'), PUT/PATCH→('project','write'), "
            "POST (create)→('project_group','create'), DELETE→('project','delete'). "
            "project_groups.py Mapping: GET→('project_group','read'), "
            "PUT/PATCH→('project_group','write'), "
            "POST (create)→require_global_admin() [Projektgruppen erstellen bleibt Admin-only], "
            "DELETE→('project_group','delete').",
        ),
    ],

    # ── C-3 ──────────────────────────────────────────────────────────────────
    (
        "C-3 | Idempotentes Setup-Script für Produktion erstellen",
        "Als Entwickler möchte ich ein einzelnes Python-Script, das ich auf einer "
        "frischen oder bestehenden Installation ausführen kann, um alle Datenbank-"
        "migrationen durchzuführen, die Standard-Rollenkonfiguration einzuspielen "
        "und die korrekten Artefakte in ProjectFlow anzulegen – ohne manuelle Eingriffe.",
        "• Script setup_granulares_rechtemanagement_apply.py im Projektroot\n"
        "• Schritt 1: Alembic-Migrationen bis head ausführen\n"
        "• Schritt 2: Seed-Konfiguration über die API einspielen\n"
        "• Schritt 3: Prüfen ob Standard-Konfiguration korrekt geladen wurde\n"
        "• Script ist idempotent: mehrfaches Ausführen ohne Fehler und ohne Duplikate\n"
        "• Aussagekräftige Konsolenausgabe mit ✓/✗ pro Schritt\n"
        "• Konfigurierbar via Umgebungsvariablen: BASE_URL, ADMIN_USERNAME, ADMIN_PASSWORD\n"
        "• Am Ende: Link zur Admin-Oberfläche in der Konsolenausgabe",
        3, 8,
    ),
    [
        (
            "Task C-3.1 | Setup-Script setup_granulares_rechtemanagement_apply.py erstellen",
            "Erstelle das Script projectflow/setup_granulares_rechtemanagement_apply.py. "
            "Konfigurierbare Variablen oben im Script: BASE_URL (default: http://localhost:8000), "
            "USERNAME (default: admin), PASSWORD (default: admin123). "
            "Das Script soll folgende Schritte ausführen und jeweils mit ✓/✗ ausgeben: "
            "(1) Login via POST /auth/login und Token speichern, "
            "(2) GET /admin/permissions/ aufrufen und prüfen ob 24 Einträge (4 Rollen × 6 Typen) "
            "vorhanden sind; falls weniger: PUT-Requests für alle fehlenden Einträge absenden "
            "mit den Standard-Werten aus DELIVERABLE_A_STORIES A-4.1, "
            "(3) Verify: alle 24 Einträge nochmals abrufen und Anzahl bestätigen. "
            "Orientiere dich am Muster und Stil von projectflow/setup_rechtemanagement.py. "
            "Am Ende Ausgabe: 'Fertig! Berechtigungen konfigurierbar unter: "
            "http://localhost:5173/admin/permissions'.",
        ),
    ],
]

# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

def login(session: requests.Session) -> str:
    r = session.post(f"{BASE_URL}/auth/login",
                     data={"username": USERNAME, "password": PASSWORD})
    r.raise_for_status()
    token = r.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✓ Eingeloggt als '{USERNAME}'")
    return token


def find_project_and_topic(session: requests.Session) -> tuple[str, str]:
    """Sucht das Projekt 'Project Flow' und das Topic 'Rechtemanagement'."""
    projects_resp = session.get(f"{BASE_URL}/projects/")
    projects_resp.raise_for_status()
    projects = projects_resp.json()

    for project in projects:
        if project["title"].strip().lower() == TARGET_PROJECT_TITLE.strip().lower():
            topic_resp = session.get(f"{BASE_URL}/projects/{project['id']}")
            topic_resp.raise_for_status()
            project_detail = topic_resp.json()
            for topic in project_detail.get("topics", []):
                if TARGET_TOPIC_TITLE.lower() in topic["title"].lower():
                    print(f"✓ Projekt gefunden: '{project['title']}' (ID: {project['id']})")
                    print(f"✓ Topic gefunden:   '{topic['title']}' (ID: {topic['id']})")
                    return project["id"], topic["id"]

    print(f"✗ Projekt '{TARGET_PROJECT_TITLE}' mit Topic '{TARGET_TOPIC_TITLE}' nicht gefunden!",
          file=sys.stderr)
    sys.exit(1)


def create_deliverable(session: requests.Session, topic_id: str, title: str,
                       description: str) -> dict:
    """Legt ein Deliverable an oder gibt ein bestehendes zurück (idempotent)."""
    topic_detail = session.get(f"{BASE_URL}/topics/{topic_id}").json()
    for d in topic_detail.get("deliverables", []):
        if d["title"].strip().lower() == title.strip().lower():
            print(f"  ~ Deliverable existiert bereits: '{title}'")
            return d

    r = session.post(f"{BASE_URL}/deliverables/", json={
        "title":       title,
        "description": description,
        "topic_id":    topic_id,
        "status":      "todo",
    })
    r.raise_for_status()
    d = r.json()
    print(f"  ✓ Deliverable angelegt: '{title}'")
    return d


def create_user_story(session: requests.Session, deliverable_id: str, title: str,
                      description: str, acceptance_criteria: str,
                      story_points: int, business_value: int) -> dict:
    """Legt eine User Story an oder gibt eine bestehende zurück (idempotent)."""
    deliverable_detail = session.get(
        f"{BASE_URL}/deliverables/{deliverable_id}").json()
    for s in deliverable_detail.get("user_stories", []):
        if s["title"].strip().lower() == title.strip().lower():
            return s  # bereits vorhanden, still

    r = session.post(f"{BASE_URL}/user-stories/", json={
        "title":                title,
        "description":          description,
        "acceptance_criteria":  acceptance_criteria,
        "story_points":         story_points,
        "business_value":       business_value,
        "deliverable_id":       deliverable_id,
        "status":               "todo",
    })
    r.raise_for_status()
    return r.json()


def create_task(session: requests.Session, story_id: str, title: str,
                description: str) -> dict:
    """Legt einen Task an oder gibt einen bestehenden zurück (idempotent)."""
    story_detail = session.get(f"{BASE_URL}/user-stories/{story_id}").json()
    for t in story_detail.get("tasks", []):
        if t["title"].strip().lower() == title.strip().lower():
            return t  # bereits vorhanden, still

    r = session.post(f"{BASE_URL}/tasks/", json={
        "title":           title,
        "description":     description,
        "user_story_id":   story_id,
        "status":          "todo",
    })
    r.raise_for_status()
    return r.json()


def process_deliverable(session: requests.Session, topic_id: str,
                        title: str, description: str, stories_and_tasks: list,
                        task_map: dict) -> None:
    """Verarbeitet ein vollständiges Deliverable mit User Stories und Tasks."""
    print(f"\n{'='*60}")
    print(f"  Deliverable: {title}")
    print(f"{'='*60}")

    deliverable = create_deliverable(session, topic_id, title, description)
    deliverable_id = deliverable["id"]

    # Deliverable in Map aufnehmen
    task_map["deliverables"][title] = {
        "id":     deliverable_id,
        "title":  title,
        "status_endpoint": f"{BASE_URL}/deliverables/{deliverable_id}",
    }

    story_count = 0
    task_count  = 0
    current_story_id    = None
    current_story_title = None

    for item in stories_and_tasks:
        if isinstance(item, tuple) and len(item) == 5:
            # User Story
            s_title, s_desc, s_ac, s_sp, s_bv = item
            story = create_user_story(session, deliverable_id,
                                      s_title, s_desc, s_ac, s_sp, s_bv)
            current_story_id    = story["id"]
            current_story_title = s_title
            story_count += 1
            print(f"  [{story_count:02d}] ✓ Story: {s_title}")

            # Story in Map aufnehmen
            task_map["user_stories"][s_title] = {
                "id":              current_story_id,
                "title":           s_title,
                "deliverable_id":  deliverable_id,
                "status_endpoint": f"{BASE_URL}/user-stories/{current_story_id}",
                "tasks":           {},
            }

        elif isinstance(item, list) and current_story_id:
            # Tasks für die zuletzt erstellte Story
            for t_title, t_desc in item:
                task = create_task(session, current_story_id, t_title, t_desc)
                task_count += 1
                print(f"         ✓ Task: {t_title}")

                # Task in Map aufnehmen
                task_map["user_stories"][current_story_title]["tasks"][t_title] = {
                    "id":              task["id"],
                    "title":           t_title,
                    "story_id":        current_story_id,
                    "status_endpoint": f"{BASE_URL}/tasks/{task['id']}",
                }

    print(f"\n  → {story_count} User Stories, {task_count} Tasks angelegt.")


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import pathlib

    session = requests.Session()

    print("=" * 60)
    print("  ProjectFlow – Granulares Rechtemanagement Setup")
    print("=" * 60 + "\n")

    login(session)
    project_id, topic_id = find_project_and_topic(session)

    # Task-Map wird während der Ausführung befüllt
    task_map: dict = {
        "base_url":    BASE_URL,
        "deliverables": {},
        "user_stories": {},
    }

    # Deliverable A
    process_deliverable(
        session, topic_id,
        DELIVERABLE_A_TITLE,
        DELIVERABLE_A_DESCRIPTION,
        DELIVERABLE_A_STORIES,
        task_map,
    )

    # Deliverable B
    process_deliverable(
        session, topic_id,
        DELIVERABLE_B_TITLE,
        DELIVERABLE_B_DESCRIPTION,
        DELIVERABLE_B_STORIES,
        task_map,
    )

    # Deliverable C
    process_deliverable(
        session, topic_id,
        DELIVERABLE_C_TITLE,
        DELIVERABLE_C_DESCRIPTION,
        DELIVERABLE_C_STORIES,
        task_map,
    )

    total_stories = (
        sum(1 for i in DELIVERABLE_A_STORIES if isinstance(i, tuple)) +
        sum(1 for i in DELIVERABLE_B_STORIES if isinstance(i, tuple)) +
        sum(1 for i in DELIVERABLE_C_STORIES if isinstance(i, tuple))
    )
    total_tasks = (
        sum(len(i) for i in DELIVERABLE_A_STORIES if isinstance(i, list)) +
        sum(len(i) for i in DELIVERABLE_B_STORIES if isinstance(i, list)) +
        sum(len(i) for i in DELIVERABLE_C_STORIES if isinstance(i, list))
    )

    # Task-Map als JSON speichern (wird von CLAUDE.md genutzt)
    map_path = pathlib.Path(__file__).parent / "projectflow_task_map.json"
    map_path.write_text(json.dumps(task_map, indent=2, ensure_ascii=False))
    print(f"\n✓ Task-Map gespeichert: {map_path}")

    print("\n" + "=" * 60)
    print(f"  ✅ Fertig!")
    print(f"     3 Deliverables angelegt")
    print(f"     {total_stories} User Stories angelegt")
    print(f"     {total_tasks} Tasks angelegt")
    print(f"\n  → Projekt öffnen:        http://localhost:5173")
    print(f"  → Task-Map für Claude Code: {map_path.name}")
    print("=" * 60)
