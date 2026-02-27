"""
setup_rechtemanagement.py
=========================
Legt die Beschreibung auf dem Deliverable "Rechtemanagement" fest
und erstellt darunter alle User Stories für die Rollen-Erweiterung.

Ausführen:
    python3 setup_rechtemanagement.py
"""

import sys
import requests

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

# ── Beschreibung für das Deliverable ────────────────────────────────────────

DELIVERABLE_DESCRIPTION = """\
Implementierung eines zweistufigen Berechtigungssystems für ProjectFlow.

Stufe 1 – Globale Rollen (systemweit):
  • superuser  – Vollzugriff auf alles, kann andere Superuser erstellen
  • admin      – User-Verwaltung + Lesezugriff auf alle Projekte
  • user        – Standard; Zugriff nur über Projektmitgliedschaften

Stufe 2 – Projekt-Rollen (pro Projekt):
  • owner    – Vollzugriff inkl. Mitgliederverwaltung und Projektlöschung
  • manager  – Vollzugriff auf Projektinhalte, keine Mitgliederverwaltung
  • member   – Erstellen und Bearbeiten eigener Items
  • viewer   – Nur lesender Zugriff

Technische Basis: neue Tabelle project_memberships, GlobalRole-Enum auf User,
owner_id FK auf Project, zentrales Permissions-System als FastAPI-Dependencies.\
"""

# ── User Stories ─────────────────────────────────────────────────────────────
# Format: (title, description, acceptance_criteria, story_points, business_value)

USER_STORIES = [
    # ── Datenbankschicht ──────────────────────────────────────────────────────
    (
        "Globale Rolle auf User-Modell",
        "Als Entwickler möchte ich, dass jeder User eine globale Rolle (superuser/admin/user) "
        "in der Datenbank hat, damit systemweite Berechtigungen persistent gespeichert werden.",
        "• Spalte global_role (Enum: superuser, admin, user) auf Tabelle users vorhanden\n"
        "• Default-Wert ist 'user'\n"
        "• Bestehende Admins (is_admin=true) werden automatisch auf 'admin' migriert\n"
        "• Index auf global_role ist angelegt",
        3, 8,
    ),
    (
        "Tabelle project_memberships anlegen",
        "Als Entwickler möchte ich eine Tabelle project_memberships, die User mit Projekten "
        "und einer Rolle (owner/manager/member/viewer) verknüpft.",
        "• Tabelle project_memberships mit Spalten: id, user_id, project_id, role, created_at, updated_at\n"
        "• Unique-Constraint auf (user_id, project_id): ein User hat pro Projekt genau eine Rolle\n"
        "• FK user_id → users.id ON DELETE CASCADE\n"
        "• FK project_id → projects.id ON DELETE CASCADE\n"
        "• Indizes auf user_id und project_id",
        3, 9,
    ),
    (
        "owner_id FK auf Projekten",
        "Als Entwickler möchte ich, dass ein Projekt einen expliziten Eigentümer (owner_id → users.id) "
        "hat, damit der Ersteller automatisch als Owner eingetragen werden kann.",
        "• Spalte owner_id (UUID, nullable) auf Tabelle projects\n"
        "• FK auf users.id mit ON DELETE SET NULL\n"
        "• Das bestehende Feld owner_name bleibt für Backwards-Kompatibilität erhalten\n"
        "• Alembic-Migration 0007 ist idempotent (mehrfaches Ausführen ohne Fehler)",
        2, 6,
    ),
    (
        "Alembic-Migration 0007 ausführen und testen",
        "Als Entwickler möchte ich, dass die Migration 0007 erfolgreich auf der bestehenden "
        "Datenbank läuft, ohne bestehende Daten zu verlieren.",
        "• alembic upgrade head läuft fehlerfrei durch\n"
        "• alembic downgrade -1 macht alle Änderungen rückstandslos rückgängig\n"
        "• Bestehende User, Projekte und alle anderen Daten sind nach der Migration unverändert\n"
        "• Bestehende is_admin=true User haben global_role='admin'",
        2, 7,
    ),

    # ── Backend: Permissions-System ───────────────────────────────────────────
    (
        "Zentrales Permissions-System implementieren",
        "Als Entwickler möchte ich wiederverwendbare FastAPI-Dependencies für Berechtigungsprüfungen, "
        "damit ich in jedem Router mit einer Zeile die nötige Rolle absichern kann.",
        "• require_project_role(minimum_role) als Dependency-Factory vorhanden\n"
        "• Superuser bypassen alle Checks automatisch\n"
        "• Admins dürfen nur lesende Operationen (viewer-Level) auf Projektdaten\n"
        "• Shortcuts require_viewer, require_member, require_manager, require_owner verfügbar\n"
        "• require_global_admin() und require_superuser() für systemweite Endpoints\n"
        "• Bei fehlender Berechtigung: HTTP 403 mit aussagekräftiger Fehlermeldung",
        5, 10,
    ),
    (
        "Letzter Owner eines Projekts ist geschützt",
        "Als Projektowner möchte ich nicht versehentlich die letzte Owner-Rolle in einem Projekt "
        "entfernen können, damit das Projekt nicht verwaist.",
        "• Versuch, den letzten Owner zu entfernen → HTTP 400 mit Fehlermeldung\n"
        "• Versuch, den letzten Owner auf eine andere Rolle zu ändern → HTTP 400\n"
        "• Funktioniert sowohl beim DELETE /members/{uid} als auch beim PUT /members/{uid}",
        2, 8,
    ),

    # ── Backend: User-Management API ─────────────────────────────────────────
    (
        "API: User auflisten und abrufen (Admin+)",
        "Als Admin möchte ich alle User auflisten und einzelne Profile abrufen können, "
        "damit ich einen Überblick über alle Systemnutzer habe.",
        "• GET /users/ liefert alle nicht-gelöschten User (sortiert nach username)\n"
        "• GET /users/{id} liefert das Profil eines einzelnen Users\n"
        "• Eigenes Profil kann jeder User abrufen (kein Admin nötig)\n"
        "• Fremde Profile: nur Admin oder Superuser\n"
        "• Antwort enthält global_role",
        2, 6,
    ),
    (
        "API: User anlegen (Admin+)",
        "Als Admin möchte ich neue User über die API anlegen können, "
        "damit ich Teammitglieder ohne direkten DB-Zugriff registrieren kann.",
        "• POST /users/ legt neuen User an (Admin oder Superuser)\n"
        "• Passwort wird gehasht gespeichert (bcrypt)\n"
        "• Duplikat-Check auf username und email → HTTP 409\n"
        "• global_role='superuser' darf nur von einem Superuser vergeben werden → sonst HTTP 403\n"
        "• Antwort enthält die vollständige UserResponse (ohne Passwort)",
        3, 7,
    ),
    (
        "API: User bearbeiten und deaktivieren",
        "Als Admin möchte ich User bearbeiten (E-Mail, Name, Rolle, Passwort) und deaktivieren können, "
        "damit ich Accounts pflegen kann ohne sie zu löschen.",
        "• PUT /users/{id} aktualisiert erlaubte Felder\n"
        "• Jeder User darf seine eigene E-Mail und sein Passwort ändern\n"
        "• Rollenänderungen nur durch Admin+\n"
        "• is_active=false blockiert Login (HTTP 400 bei Login-Versuch)\n"
        "• Ein User kann seine eigene Rolle nicht ändern",
        3, 7,
    ),
    (
        "API: User soft-löschen (Superuser only)",
        "Als Superuser möchte ich User soft-löschen können, damit ihre historischen Daten "
        "(Kommentare, Audit-Log) erhalten bleiben.",
        "• DELETE /users/{id} setzt is_deleted=true, deleted_at und is_active=false\n"
        "• Nur Superuser darf löschen → sonst HTTP 403\n"
        "• Superuser kann sich nicht selbst löschen → HTTP 400\n"
        "• Gelöschte User tauchen in GET /users/ nicht mehr auf\n"
        "• Login mit gelöschtem Account nicht möglich",
        2, 5,
    ),

    # ── Backend: Mitgliederverwaltung API ─────────────────────────────────────
    (
        "API: Projektmitglieder auflisten",
        "Als Projektmitglied möchte ich sehen, wer sonst noch in meinem Projekt ist und "
        "welche Rolle die anderen haben.",
        "• GET /projects/{id}/members/ liefert alle Mitglieder mit UserPublic-Objekt\n"
        "• Zugänglich für alle Mitglieder (viewer+)\n"
        "• Superuser und Admins können immer zugreifen",
        1, 5,
    ),
    (
        "API: Mitglied hinzufügen und Rolle ändern",
        "Als Projektowner möchte ich neue Mitglieder einladen und bestehenden Mitgliedern "
        "eine andere Rolle zuweisen können.",
        "• POST /projects/{id}/members/ fügt User mit gewählter Rolle hinzu\n"
        "• Duplikat → HTTP 409\n"
        "• User existiert nicht → HTTP 404\n"
        "• PUT /projects/{id}/members/{uid} ändert die Rolle\n"
        "• Letzter Owner ist geschützt (siehe eigene Story)\n"
        "• Nur Owner darf Mitglieder verwalten → sonst HTTP 403",
        3, 8,
    ),
    (
        "API: Mitglied entfernen",
        "Als Projektowner möchte ich Mitglieder aus einem Projekt entfernen können, "
        "wenn sie nicht mehr beteiligt sind.",
        "• DELETE /projects/{id}/members/{uid} entfernt die Mitgliedschaft\n"
        "• Letzter Owner kann nicht entfernt werden → HTTP 400\n"
        "• Nicht-Mitglied → HTTP 404\n"
        "• Nur Owner darf entfernen → sonst HTTP 403",
        2, 6,
    ),

    # ── Backend: Absicherung bestehender Routers ─────────────────────────────
    (
        "Bestehende Routers mit Permissions absichern",
        "Als Entwickler möchte ich, dass alle bestehenden Endpunkte (Topics, Deliverables, "
        "User Stories, Bugs, Tasks) durch die neuen Permissions-Dependencies geschützt sind.",
        "• Lesende Endpunkte (GET) erfordern mindestens 'viewer'-Rolle im Projekt\n"
        "• Schreibende Endpunkte (POST, PUT) erfordern mindestens 'member'-Rolle\n"
        "• Lösch-Endpunkte (DELETE) erfordern mindestens 'manager'-Rolle\n"
        "• Superuser können weiterhin alles ohne Einschränkung\n"
        "• Alle Änderungen sind rückwärtskompatibel (bestehende Tests laufen durch)",
        5, 9,
    ),
    (
        "Projekt-Ersteller automatisch als Owner eintragen",
        "Als User möchte ich, dass ich beim Erstellen eines Projekts automatisch als Owner "
        "eingetragen werde, damit ich das Projekt sofort verwalten kann.",
        "• POST /projects/ legt nach dem Projekt automatisch einen ProjectMembership-Eintrag an\n"
        "• Der eingeloggte User wird mit Rolle 'owner' eingetragen\n"
        "• owner_id auf dem Projekt wird auf den aktuellen User gesetzt\n"
        "• Superuser werden ebenfalls eingetragen (damit die Liste vollständig ist)",
        2, 8,
    ),

    # ── Skript & Betrieb ──────────────────────────────────────────────────────
    (
        "create_admin Script aktualisieren",
        "Als Systemadministrator möchte ich über das create_admin-Script einen ersten "
        "Superuser oder Admin anlegen können, ohne die Datenbank manuell zu bearbeiten.",
        "• ADMIN_ROLE=superuser|admin steuerbar via Umgebungsvariable\n"
        "• Existierender User wird aktualisiert statt neu angelegt\n"
        "• Fehler bei fehlendem ADMIN_PASSWORD mit verständlicher Meldung\n"
        "• Script läuft sowohl lokal als auch im Docker-Container",
        1, 5,
    ),
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


def find_deliverable(session: requests.Session) -> dict:
    """Sucht das Deliverable 'Rechtemanagement' über alle Projekte."""
    projects = session.get(f"{BASE_URL}/projects/").json()
    for project in projects:
        project_detail = session.get(f"{BASE_URL}/projects/{project['id']}").json()
        for topic in project_detail.get("topics", []):
            topic_detail = session.get(f"{BASE_URL}/topics/{topic['id']}").json()
            for d in topic_detail.get("deliverables", []):
                if "rechtemanagement" in d["title"].lower():
                    print(f"✓ Deliverable gefunden: '{d['title']}' "
                          f"(Projekt: {project['title']}, Topic: {topic['title']})")
                    return d
    print("✗ Deliverable 'Rechtemanagement' nicht gefunden!", file=sys.stderr)
    sys.exit(1)


def update_deliverable_description(session: requests.Session, deliverable: dict) -> None:
    r = session.put(
        f"{BASE_URL}/deliverables/{deliverable['id']}",
        json={"description": DELIVERABLE_DESCRIPTION},
    )
    r.raise_for_status()
    print(f"✓ Beschreibung auf Deliverable gesetzt")


def create_user_stories(session: requests.Session, deliverable_id: str) -> None:
    print(f"\n📝 Lege {len(USER_STORIES)} User Stories an ...\n")
    for i, (title, description, acceptance_criteria, story_points, business_value) in enumerate(USER_STORIES, 1):
        r = session.post(
            f"{BASE_URL}/user-stories/",
            json={
                "title":                title,
                "description":          description,
                "acceptance_criteria":  acceptance_criteria,
                "story_points":         story_points,
                "business_value":       business_value,
                "deliverable_id":       deliverable_id,
                "status":               "todo",
            },
        )
        if r.status_code == 201:
            print(f"  [{i:02d}/{len(USER_STORIES)}] ✓ {title}")
        else:
            print(f"  [{i:02d}/{len(USER_STORIES)}] ✗ FEHLER {r.status_code}: {r.text}")


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    session = requests.Session()

    print("=" * 60)
    print("  ProjectFlow – Rechtemanagement Setup")
    print("=" * 60 + "\n")

    login(session)
    deliverable = find_deliverable(session)
    update_deliverable_description(session, deliverable)
    create_user_stories(session, deliverable["id"])

    print(f"\n✅ Fertig! {len(USER_STORIES)} User Stories angelegt.")
    print(f"   → http://localhost:5173/deliverables/{deliverable['id']}")
