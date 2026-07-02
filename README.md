# Schalteinheit für SwitchBot

ESP32 14-Taster-Matrix Controller für SwitchBot Smart Home Geräte.

## Für Kunden — Installation

**Windows:**
1. `tool/install_windows.exe` herunterladen
2. Doppelklick → installiert sich automatisch, erstellt Desktop-Verknüpfung, startet

**Linux:**
1. `tool/install_linux` herunterladen
2. Ausführbar machen: Rechtsklick → Eigenschaften → "Ausführen erlauben"
   (oder `chmod +x install_linux` im Terminal)
3. Doppelklick → installiert sich automatisch, erstellt Desktop-Verknüpfung, startet

Kein Python, keine weiteren Programme nötig — alles ist in der Datei enthalten.

**Deinstallation:** `tool/uninstall_windows.exe` bzw. `tool/uninstall_linux` genauso ausführen.

---

## Repo-Struktur (öffentlich auf GitHub)

```
Schalteinheit-fuer-Switchbot/
├── tool/
│   ├── switchbot_config_v1.0.py     ← Quellcode des Tools
│   ├── SwitchBot-Konfigurator.exe   ← fertig gebaute App (Windows, automatisch)
│   ├── SwitchBot-Konfigurator       ← fertig gebaute App (Linux, automatisch)
│   ├── install.py                   ← Installer-Quellcode
│   ├── install_windows.exe          ← fertiger Installer (automatisch)
│   ├── install_linux                ← fertiger Installer (automatisch)
│   ├── uninstall.py
│   ├── uninstall_windows.exe        ← (automatisch)
│   └── uninstall_linux              ← (automatisch)
├── firmware/
│   └── firmware_v1.0.bin            ← NUR die kompilierte Binary
└── .github/workflows/build.yml      ← baut App + Installer automatisch
```

**Wichtig:** Der ESP32-Firmware-Quellcode (`main.cpp`, `platformio.ini`) bleibt
**ausschließlich lokal** und wird niemals auf GitHub gepusht — das Projekt ist
nicht Open Source. Nur die fertig kompilierte `firmware_v1.0.bin` wird
veröffentlicht, damit das Tool sie herunterladen und per OTA flashen kann.
Ein `.gitignore` verhindert versehentliches Hinzufügen dieser Dateien.

Dateien mit "automatisch" werden von GitHub Actions bei jedem Push
auf `tool/switchbot_config_v*.py`, `install.py` oder `uninstall.py`
neu gebaut und ins Repo committet — nichts davon muss manuell hochgeladen werden.

---

## Workflow für neue Tool-Versionen (Entwickler)

1. `switchbot_config_v1.0.py` kopieren → `switchbot_config_v1.1.py`
2. `VERSION = "1.1"` im neuen File setzen
3. Alte Versionsdatei aus dem Repo löschen (optional, hält es sauber)
4. Neue Datei nach `tool/` pushen
5. GitHub Actions baut automatisch:
   - `SwitchBot-Konfigurator.exe` / `SwitchBot-Konfigurator` (die App selbst)
   - `install_windows.exe` / `install_linux` (Installer, lädt nur die App)
6. Laufende Tools bei Kunden erkennen die neue Version beim Start automatisch
   und aktualisieren sich selbst (Download der neuen App-Binary, kein
   Python/pip nötig).

## Workflow für neue ESP32-Firmware (Entwickler)

1. `main.cpp` (lokal, nicht im Repo) ändern, `FW_VERSION` erhöhen (z.B. `"1.1"`)
2. PlatformIO lokal: `pio run` → `.pio/build/esp32dev/firmware.bin`
3. Umbenennen zu `firmware_v1.1.bin` (Muster: `firmware_v*.bin` ist Pflicht,
   sonst erkennt das Tool die Datei nicht)
4. Nur diese `.bin`-Datei nach `firmware/` im Repo hochladen (alte Version
   kann bleiben oder gelöscht werden) — main.cpp/platformio.ini NIEMALS mit hochladen
5. Tool zeigt bei allen Kunden beim nächsten Start einen Update-Banner an
   (nur wenn die GitHub-Version wirklich neuer ist als die installierte)
6. Kunde klickt "Jetzt flashen" im Tool — läuft per WLAN-OTA, ESP32 muss
   nur im gleichen Netzwerk erreichbar sein, kein USB nötig

---

## ESP32 mDNS

Der ESP32 ist im lokalen Netzwerk erreichbar unter:
```
http://controller-for-switchbot.local
```
Das Tool findet den ESP32 automatisch beim Start über diesen Hostnamen.

## Taster-Pin-Zuordnung

| Taster | GPIO | Hinweis |
|--------|------|---------|
| T1  | 12 | |
| T2  | 13 | |
| T3  | 14 | |
| T4  | 25 | |
| T5  | 26 | |
| T6  | 27 | |
| T7  | 32 | |
| T8  | 33 | |
| T9  | 16 | |
| T10 | 17 | |
| T11 | 18 | |
| T12 | 19 | |
| T13 | 21 | auch Reset-Pin A |
| T14 | 22 | auch Reset-Pin B |

**Werksreset:** T13 + T14 gleichzeitig 5 Sekunden halten
(löscht WLAN-Zugangsdaten + config.json, ESP32 öffnet danach den
Einrichtungs-Hotspot `SwitchBot-Bridge`).

## GitHub Actions Berechtigung

Damit der Workflow automatisch committen darf:
Repo → Settings → Actions → General → Workflow permissions →
**"Read and write permissions"** muss aktiviert sein.
