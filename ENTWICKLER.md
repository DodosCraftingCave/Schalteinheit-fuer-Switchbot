# Entwickler-Notizen

> Interne Notizen für die Pflege des Repos. Für Kunden ist die [README](README.md) gedacht.

---

## Inhalt

- [Repo-Struktur](#repo-struktur)
- [Firmware-Quellcode bleibt privat](#firmware-quellcode-bleibt-privat)
- [Neue Tool-Version veröffentlichen](#neue-tool-version-veröffentlichen)
- [Neue Firmware veröffentlichen](#neue-firmware-veröffentlichen)
- [GitHub Actions](#github-actions)
- [ESP32-Zugriffsschutz (HMAC-Challenge-Response)](#esp32-zugriffsschutz-hmac-challenge-response)
- [Wie das Tool GitHub nutzt](#wie-das-tool-github-nutzt)
- [Hardware: Taster-Pin-Zuordnung](#hardware-taster-pin-zuordnung)
- [Installationsorte beim Kunden](#installationsorte-beim-kunden)

---

## Repo-Struktur

```
Schalteinheit-fuer-Switchbot/
├── README.md                        ← Kunden-Anleitung
├── ENTWICKLER.md                    ← diese Datei
├── tool/
│   ├── switchbot_config_v2.0.py     ← Quellcode des Konfigurators (pywebview)
│   ├── install.py                   ← Installer-Quellcode
│   ├── uninstall.py                 ← Deinstaller-Quellcode
│   └── requirements.txt             ← Abhängigkeiten für lokale Entwicklung
├── firmware/
│   └── firmware_v*.bin              ← NUR die kompilierte Binary (weiterhin im Git-Baum)
└── .github/workflows/build.yml      ← baut App + Installer, veröffentlicht als Release
```

**Wichtig — fertige Binaries liegen NICHT mehr im Git-Baum:** `SwitchBot-Konfigurator(.exe)`,
`install_windows.exe`/`install_linux`, `uninstall_windows.exe`/`uninstall_linux` werden von
GitHub Actions gebaut und als **Release-Assets** hochgeladen, nicht mehr committet. Grund:
die Linux-App-Binary allein liegt wegen der gebündelten QtWebEngine/Chromium-Engine bei
>180MB — deutlich über GitHubs 100MB-Dateilimit fürs Repo (`libQt5WebEngineCore.so.5` macht
davon ca. 190MB aus, das lässt sich nicht sinnvoll wegtrimmen, es ist die Chromium-Engine
selbst). Nur `firmware_v*.bin` bleibt im Git-Baum (die ist klein genug).

> ⚠️ **Dateinamen-Muster `switchbot_config_v*.py` und `firmware_v*.bin` nicht ändern!**
> Installierte Tools bei Kunden erkennen Updates darüber (siehe
> [Wie das Tool GitHub nutzt](#wie-das-tool-github-nutzt)). Umbenennen bricht Auto-Update.

**Politik-Historie (falls das wieder aufkommt):** Zwischenzeitlich hatte eine andere
Session Tool-/Installer-Quellcode und die CI komplett aus dem öffentlichen Repo entfernt
(analog zur Firmware). Das wurde bewusst wieder rückgängig gemacht: automatisches Bauen
per GitHub Actions ist ohne öffentlich zugänglichen Quellcode nicht möglich (CI baut aus
dem Repo, das die Runner auschecken — kein Henne-Ei-Ausweg ohne privates Repo/Secrets).
Nur `main.cpp`/`platformio.ini` bleiben privat, wie ursprünglich.

---

## Firmware-Quellcode bleibt privat

Der ESP32-Firmware-Quellcode (`main.cpp`, `platformio.ini`) bleibt **ausschließlich lokal**
und wird **niemals** auf GitHub gepusht – das Projekt ist an dieser Stelle nicht Open Source.

Veröffentlicht wird nur die kompilierte `firmware_v*.bin`, damit das Tool sie herunterladen
und per OTA flashen kann. Die `.gitignore` verhindert versehentliches Hinzufügen von
`main.cpp`, `platformio.ini`, `src/`, `lib/`, `include/` und `.pio/`.

Tool- und Installer-Quellcode sind dagegen **öffentlich** (siehe oben) — die Sicherheit
der HMAC-Signierung hängt am geheimen Admin-Passwort, nicht an geheimem Code
(Kerckhoffs'sches Prinzip), es gibt also keinen Sicherheitsgrund, sie zu verstecken.

---

## Neue Tool-Version veröffentlichen

1. `tool/switchbot_config_v2.0.py` kopieren → z. B. `switchbot_config_v2.1.py`
2. Im neuen File die Version anpassen: `VERSION = "2.1"`
3. Alte Versionsdatei aus dem Repo löschen (optional, hält es sauber)
4. Neue Datei nach `tool/` auf `main` pushen
5. GitHub Actions baut automatisch und veröffentlicht als **Release** `v2.1`
   (nicht mehr als Commit ins Repo — siehe [GitHub Actions](#github-actions)):
   - `SwitchBot-Konfigurator.exe` / `SwitchBot-Konfigurator` (die App) + `.sha256`-Prüfsumme
   - `install_windows.exe` / `install_linux` und `uninstall_windows.exe` / `uninstall_linux` + `.sha256`
6. Laufende Tools bei Kunden erkennen die neue Version beim Start (weiterhin über die
   `switchbot_config_v*.py`-Quelldatei im Repo) und laden die neue Binary von
   `github.com/.../releases/latest/download/<name>` — verifizieren sie gegen die
   mitveröffentlichte `.sha256`-Datei, bevor sie sich selbst ersetzen (kein Python/pip nötig).

**Wichtig:**
- Dateiname muss dem Muster `switchbot_config_v<VERSION>.py` folgen – das Tool liest die
  Version aus dem Dateinamen. Ein Suffix wie `_beta` ist erlaubt.
- Die Version im Dateinamen und `VERSION` im Code müssen übereinstimmen, sonst bieten
  Kunden-Tools das Update bei jedem Start erneut an.
- Der Workflow baut immer die **höchste** Version (`sort -V`) aus `tool/`.

---

## Neue Firmware veröffentlichen

1. `main.cpp` (lokal, nicht im Repo) ändern und `FW_VERSION` erhöhen (z. B. `"1.3"`)
2. Lokal mit PlatformIO bauen:
   ```bash
   pio run
   ```
   Ergebnis: `.pio/build/esp32dev/firmware.bin`
3. Umbenennen zu `firmware_v1.3.bin`
   – das Muster `firmware_v*.bin` ist **Pflicht**, sonst erkennt das Tool die Datei nicht.
4. **Nur** diese `.bin`-Datei nach `firmware/` hochladen (alte Versionen dürfen bleiben).
   `main.cpp` / `platformio.ini` **niemals** mit hochladen.
5. Beim nächsten Start zeigt das Tool allen Kunden einen Update-Banner – aber nur, wenn die
   Version auf GitHub wirklich neuer ist als die auf dem ESP installierte (aus `/status`).
6. Kunde klickt **„Jetzt flashen"** → Update läuft per WLAN-OTA, kein USB nötig. Tool
   verifiziert vor dem Flashen sowohl das ESP32-Magic-Byte (`0xE9`) als auch den von
   GitHub gemeldeten Git-Blob-SHA1 der `.bin`-Datei, bevor geflasht wird.

---

## GitHub Actions

Workflow: [`.github/workflows/build.yml`](.github/workflows/build.yml)

**Auslöser:** Push auf `main`, der eine dieser Dateien ändert:
- `tool/switchbot_config_v*.py`
- `tool/install.py`
- `tool/uninstall.py`
- `.github/workflows/build.yml`

Außerdem manuell über **Actions → Build App + Installer → Run workflow**.

**Ablauf** (`prepare-release` läuft zuerst, die vier Build-Jobs hängen nur noch von
diesem einen Job ab — nicht mehr voneinander — und laufen parallel):

| # | Job | Ergebnis |
|---|-----|----------|
| 0 | `prepare-release` | legt Release `v<VERSION>` an (falls noch nicht vorhanden) |
| 1 | `build-app-windows` | Release-Asset `SwitchBot-Konfigurator.exe` (+ `.sha256`) |
| 2 | `build-app-linux` | Release-Asset `SwitchBot-Konfigurator` (+ `.sha256`) |
| 3 | `build-installer-windows` | Release-Assets `install_windows.exe`, `uninstall_windows.exe` (+ `.sha256`) |
| 4 | `build-installer-linux` | Release-Assets `install_linux`, `uninstall_linux` (+ `.sha256`) |

Gebaut wird mit Python 3.12 und PyInstaller (`--onefile --windowed`). Linux nutzt
Qt/QtWebEngine (`PyQt5`, `PyQtWebEngine`, `qtpy`) als pywebview-Renderer, Windows nutzt
`pythonnet` (EdgeChromium/WebView2). Beide Plattformen zusätzlich `cryptography` für die
lokale Zugangsdaten-Verschlüsselung im Tool.

**Warum Releases statt Git-Commit:** Die Linux-App-Binary allein liegt wegen der
gebündelten QtWebEngine/Chromium-Engine bei >180MB (`libQt5WebEngineCore.so.5` macht davon
ca. 190MB unkomprimiert aus) — weit über GitHubs 100MB-Dateilimit fürs Repo. `--collect-all
PyQt5` NICHT verwenden (bläht die Binary durch blindes Kopieren des kompletten
`PyQt5/Qt5/lib`-Verzeichnisses zusätzlich auf, ohne nennenswerten Nutzen — PyInstallers
automatische Hooks für `PyQt5.QtWebEngineWidgets` reichen aus). Jeder Build lädt sein
Ergebnis samt `.sha256`-Prüfsummendatei per `gh release upload ... --clobber` hoch (ersetzt
ein vorhandenes Asset gleichen Namens). Das Tool und `install.py` verifizieren beim
Download gegen diese `.sha256`-Datei, bevor die Binary ausgeführt/installiert wird.

**Einmalige Einstellung**, damit der Workflow Releases anlegen/hochladen darf:
Repo → **Settings → Actions → General → Workflow permissions** →
**„Read and write permissions"** aktivieren (dieselbe Einstellung wie vorher fürs Committen).

---

## ESP32-Zugriffsschutz (HMAC-Challenge-Response)

Seit main.cpp Änderung #17–#20 sind `/upload`, `/ota`, `/config`, `/setcreds`,
`/setwifi`, `/resetwifi` durch ein Challenge-Response-Verfahren geschützt (kein
Basic Auth mehr, das war eine Zwischenstufe):

- `GET /challenge` liefert eine einmalig gültige Nonce (`{"nonce": "..."}`), 30s gültig.
- Signatur: `hex(HMAC-SHA256(admin_password, nonce + ":" + METHOD + ":" + path))`,
  Header `X-Auth-Nonce` + `X-Auth-Sign`. Für `/upload` und `/ota` zusätzlich ein
  viertes Segment `:` + `sha256_hex(body)` sowie Header `X-Body-SHA256` (bindet die
  Signatur an den tatsächlichen Inhalt, main.cpp Änderung #18).
- Neu geflashte Geräte haben ab Werk ein aus der Chip-ID abgeleitetes Standardpasswort
  (nur per Serial-Log auslesbar) — solange das noch aktiv ist, liefern die geschützten
  Endpunkte `403` (`GET /status` zeigt das über `"defaultPass": true` an). Erst nach
  Setzen eines eigenen Passworts (`POST /setadminpass`, im Tool: „Passwort ändern")
  funktionieren Upload/OTA/Config.
- Vollständiges Protokoll (Header-Namen, Fehlercodes, Rate-Limiting) und die
  Tool-seitige Implementierung: siehe Commit-Historie / Session-Notizen, hier nur die
  Kurzfassung für den Überblick.

---

## Wie das Tool GitHub nutzt

| Zweck | Quelle |
|-------|--------|
| Tool-Update suchen | GitHub API: Inhalt von `tool/` (sucht `switchbot_config_v*.py`, nur Dateiname zählt) |
| Tool-Update laden | `github.com/.../releases/latest/download/SwitchBot-Konfigurator(.exe)`, gegen mitveröffentlichte `.sha256`-Datei verifiziert |
| Firmware-Update suchen | GitHub API: Inhalt von `firmware/` (sucht `firmware_v*.bin`) |
| Firmware laden | `download_url` aus der API, gegen Git-Blob-SHA1 verifiziert (liegt weiterhin im Git-Baum, ist klein genug) |
| Installer | lädt `github.com/.../releases/latest/download/SwitchBot-Konfigurator(.exe)`, ebenfalls `.sha256`-verifiziert |

Daraus folgt: Alles, was auf `main` in `tool/` und `firmware/` liegt (Quelldatei-Namen,
Firmware-Binary), sowie jeder neue GitHub-Release ist sofort für alle Kunden live.
Experimente daher auf einem anderen Branch machen.

**ESP32 im Netzwerk:**
- mDNS-Hostname: `http://controller-for-switchbot.local` (vom Tool beim Start gesucht)
- Endpunkte, die das Tool nutzt: `/status`, `/challenge`, `/setadminpass`, `/upload`,
  `/ota`, `/config` (siehe [ESP32-Zugriffsschutz](#esp32-zugriffsschutz-hmac-challenge-response))
- Einrichtungs-Hotspot nach Werksreset: `SwitchBot-Bridge`

---

## Hardware: Taster-Pin-Zuordnung

Anordnung auf dem Gehäuse: 7 Reihen à 2 Taster, ungerade links, gerade rechts,
T1/T2 oben (Skizze in der [README](README.md#die-taster-im-überblick)).

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

**Werksreset:** T13 + T14 gleichzeitig 5 Sekunden halten → löscht WLAN-Zugangsdaten und
`config.json`, danach öffnet der ESP32 den Hotspot `SwitchBot-Bridge`.

---

## Installationsorte beim Kunden

| System | App | Desktop-Verknüpfung |
|--------|-----|---------------------|
| Windows | `%LOCALAPPDATA%\SwitchBot-Konfigurator\` | `Desktop\SwitchBot Konfigurator.lnk` |
| Linux | `~/.local/share/SwitchBot-Konfigurator/` | `~/Desktop/SwitchBot-Konfigurator.desktop` |

Windows installiert bewusst nach `%LOCALAPPDATA%` (nicht `Program Files`), damit das
Auto-Update ohne Admin-Rechte schreiben kann (Fix für *Errno 13*).

Die vom Tool gespeicherte Sicherung liegt unter `~/Desktop/config.json`.
Zugangsdaten (SwitchBot Token/Secret, ESP32-Admin-Passwort) liegen bei aktivierter
"sicher speichern"-Option verschlüsselt unter `~/.switchbot_configurator/` (nicht in
`config.json` — die enthält sie zwangsläufig im Klartext, da die Firmware sie so braucht).
