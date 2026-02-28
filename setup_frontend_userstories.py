"""
Legt User Stories für das Frontend-Konfigurationsmenü an.
Sucht das Deliverable "Rechtemanagement" und fügt die Stories hinzu.

Ausführen: python3 setup_frontend_userstories.py
"""
import sys
import requests

BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

USER_STORIES = [
    # 1 – Avatar
    (
        "Avatar-Dropdown in der Top-Bar",
        "Als eingeloggter User möchte ich oben rechts einen Avatar mit meinen Initialen sehen, "
        "der bei Klick ein Dropdown mit Profil-Link und Abmelden-Button öffnet.",
        "• Avatar zeigt Initialen (aus full_name oder username)\n"
        "• Farbe spiegelt globale Rolle wider (lila=superuser, blau=admin, grau=user)\n"
        "• Dropdown zeigt: Name, E-Mail, Rolle-Badge, 'Mein Profil', ggf. 'Konfiguration', 'Abmelden'\n"
        "• 'Konfiguration' nur sichtbar für Admin und Superuser\n"
        "• Klick außerhalb des Dropdowns schließt es\n"
        "• Abmelden leert den Token und leitet zu /login weiter",
        3, 7,
    ),
    # 2 – Profil-View
    (
        "Profil-Seite für alle User (/profile)",
        "Als User möchte ich auf einer eigenen Seite mein Profil einsehen und bearbeiten können, "
        "um Name, E-Mail und Passwort zu aktualisieren.",
        "• Route /profile erreichbar für alle eingeloggten User\n"
        "• Zeigt: Initialen-Avatar, Username, Rolle-Badge\n"
        "• Felder editierbar: Name, E-Mail\n"
        "• Passwort-Änderung: Neues Passwort + Wiederholung (Validierung client-seitig)\n"
        "• Leeres Passwortfeld = kein Passwort-Update\n"
        "• Erfolgsmeldung nach Speichern (auto-ausblenden nach 3s)\n"
        "• Liste eigener Projektmitgliedschaften (Projekt + Rolle, read-only)",
        3, 8,
    ),
    # 3 – Sidebar Konfig-Link
    (
        "Konfiguration-Menüpunkt in der Sidebar (Admin+)",
        "Als Admin oder Superuser möchte ich in der Sidebar einen Menüpunkt 'Konfiguration' sehen, "
        "der mich zur Benutzerverwaltung führt.",
        "• Menüpunkt mit Zahnrad-Icon, nur sichtbar wenn global_role = admin oder superuser\n"
        "• Aktiver Zustand (active-class) wenn Route /config/users aktiv ist\n"
        "• Für normale User ist der Menüpunkt nicht sichtbar und die Route nicht erreichbar\n"
        "• Route-Guard leitet nicht berechtigte User zur Startseite weiter",
        2, 6,
    ),
    # 4 – Benutzerliste
    (
        "Benutzerverwaltung: Liste aller User (/config/users)",
        "Als Admin möchte ich alle User in einer Tabelle sehen und nach Name, E-Mail und Rolle filtern können.",
        "• Tabelle mit Spalten: Benutzer (Avatar+Name), E-Mail, Globale Rolle, Status, Aktionen\n"
        "• Suchfeld filtert über username, full_name und email\n"
        "• Filter-Dropdowns für Rolle und Aktiv-Status\n"
        "• Eigenes Konto ist in der Liste sichtbar, aber nicht löschbar\n"
        "• Ladeindikator während fetch\n"
        "• Fehleranzeige bei API-Fehlern",
        3, 8,
    ),
    # 5 – User anlegen
    (
        "Benutzerverwaltung: Neuen User anlegen",
        "Als Admin möchte ich über ein Modal-Formular neue User anlegen können, "
        "um Teammitglieder ohne DB-Zugriff zu registrieren.",
        "• Button 'Neuer Benutzer' öffnet Modal\n"
        "• Pflichtfelder: Username, E-Mail, Passwort\n"
        "• Optionale Felder: Name, Globale Rolle\n"
        "• Nur Superuser sieht 'Superuser' als Rollenwahl\n"
        "• Fehlermeldung bei Duplikat (HTTP 409)\n"
        "• Nach erfolgreichem Anlegen: Modal schließt, Liste wird aktualisiert",
        3, 8,
    ),
    # 6 – User bearbeiten
    (
        "Benutzerverwaltung: User bearbeiten und deaktivieren",
        "Als Admin möchte ich einen bestehenden User bearbeiten können, "
        "um Name, E-Mail, Rolle und Aktiv-Status zu ändern.",
        "• Bearbeiten-Icon öffnet Modal mit vorausgefüllten Werten\n"
        "• Felder: Name, E-Mail, Passwort (optional), Globale Rolle, Aktiv-Checkbox\n"
        "• Rollenänderung zu 'Superuser' nur für Superuser möglich (Option ausgeblendet)\n"
        "• Eigenes Konto: Rolle und is_active nicht änderbar (Felder deaktiviert oder ausgeblendet)\n"
        "• Erfolgsmeldung nach Speichern",
        3, 7,
    ),
    # 7 – User löschen
    (
        "Benutzerverwaltung: User soft-löschen (Superuser only)",
        "Als Superuser möchte ich einen User über einen Löschen-Button entfernen können, "
        "mit einer Sicherheitsabfrage um versehentliches Löschen zu verhindern.",
        "• Löschen-Icon nur sichtbar für Superuser und nicht beim eigenen Account\n"
        "• Klick öffnet ConfirmDelete-Dialog mit Benutzername\n"
        "• Nach Bestätigung: User verschwindet aus der Liste\n"
        "• Fehlermeldung wenn letzter Superuser gelöscht werden soll",
        2, 5,
    ),
    # 8 – Mitglieder-Tab
    (
        "Mitglieder-Tab in der Projektdetailansicht",
        "Als Projektowner möchte ich in der Projektdetailansicht einen Tab 'Mitglieder' sehen, "
        "in dem ich das Projektteam verwalten kann.",
        "• Neuer Tab 'Mitglieder' in ProjectDetailView neben den bestehenden Tabs\n"
        "• Zeigt alle Mitglieder mit Avatar, Name, E-Mail und Rolle\n"
        "• Owner und Admin können Rollen per Dropdown ändern\n"
        "• Owner und Admin können Mitglieder über Trash-Icon entfernen (mit Confirm)\n"
        "• 'Mitglied hinzufügen'-Button öffnet Inline-Formular mit User-Picker und Rollen-Auswahl\n"
        "• User-Picker zeigt nur User, die noch nicht Mitglied sind\n"
        "• Fehlermeldung bei Versuch, letzten Owner zu entfernen\n"
        "• Normale Member sehen die Liste read-only (kein Bearbeiten/Entfernen)",
        5, 9,
    ),
]

def login(session):
    r = session.post(f"{BASE_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD})
    r.raise_for_status()
    session.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    print(f"✓ Eingeloggt als '{USERNAME}'")

def find_deliverable(session):
    for project in session.get(f"{BASE_URL}/projects/").json():
        for topic in session.get(f"{BASE_URL}/projects/{project['id']}").json().get("topics", []):
            for d in session.get(f"{BASE_URL}/topics/{topic['id']}").json().get("deliverables", []):
                if "rechtemanagement" in d["title"].lower():
                    print(f"✓ Deliverable: '{d['title']}'")
                    return d
    print("✗ Deliverable 'Rechtemanagement' nicht gefunden!", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    session = requests.Session()
    print("=" * 60)
    print("  Frontend Konfigurationsmenü – User Stories")
    print("=" * 60 + "\n")
    login(session)
    deliverable = find_deliverable(session)
    print(f"\n📝 Lege {len(USER_STORIES)} User Stories an...\n")
    for i, (title, desc, ac, sp, bv) in enumerate(USER_STORIES, 1):
        r = session.post(f"{BASE_URL}/user-stories/", json={
            "title": title, "description": desc, "acceptance_criteria": ac,
            "story_points": sp, "business_value": bv,
            "deliverable_id": deliverable["id"], "status": "todo",
        })
        status = "✓" if r.status_code == 201 else f"✗ {r.status_code}"
        print(f"  [{i:02d}/{len(USER_STORIES)}] {status} {title}")
    print(f"\n✅ Fertig! {len(USER_STORIES)} User Stories angelegt.")
