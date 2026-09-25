# Entwickler-Notizen

> Interne Notizen für die Pflege des Repos. Für Kunden ist die [README](README.md) gedacht.

---

## Inhalt

- [Repo-Struktur](#repo-struktur)
- [Firmware-Quellcode bleibt privat](#firmware-quellcode-bleibt-privat)
- [Neue Tool-Version veröffentlichen](#neue-tool-version-veröffentlichen)
- [Neue Firmware veröffentlichen](#neue-firmware-veröffentlichen)
- [GitHub Actions](#github-actions)
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
│   ├── switchbot_config_v1.1.py     ← Quellcode des Konfigurators
│   ├── SwitchBot-Konfigurator.exe   ← fertige App, Windows   (automatisch gebaut)
│   ├── SwitchBot-Konfigurator       ← fertige App, Linux     (automatisch gebaut)
│   ├── install.py                   ← Installer-Quellcode
│   ├── install_windows.exe          ← Installer, Windows     (automatisch gebaut)
│   ├── install_linux                ← Installer, Linux       (automatisch gebaut)
│   ├── uninstall.py                 ← Deinstaller-Quellcode
│   ├── uninstall_windows.exe        ← Deinstaller, Windows   (automatisch gebaut)
│   └── uninstall_linux              ← Deinstaller, Linux     (automatisch gebaut)
├── firmware/
│   └── firmware_v*.bin              ← NUR kompilierte Binaries
└── .github/workflows/build.yml      ← baut App + Installer automatisch
```

> ⚠️ **Ordner- und Dateinamen unter `tool/` und `firmware/` nicht ändern!**
> Installierte Tools bei Kunden laden Updates über feste Pfade vom `main`-Branch
> (siehe [Wie das Tool GitHub nutzt](#wie-das-tool-github-nutzt)). Umbenennen bricht Auto-Update und Installer.

---

## Firmware-Quellcode bleibt privat

Der ESP32-Firmware-Quellcode (`main.cpp`, `platformio.ini`) bleibt **ausschließlich lokal**
und wird **niemals** auf GitHub gepusht – das Projekt ist nicht Open Source.

Veröffentlicht wird nur die kompilierte `firmware_v*.bin`, damit das Tool sie herunterladen
und per OTA flashen kann. Die `.gitignore` verhindert versehentliches Hinzufügen von
`main.cpp`, `platformio.ini`, `src/`, `lib/`, `include/` und `.pio/`.

---

## Neue Tool-Version veröffentlichen

1. `tool/switchbot_config_v1.1.py` kopieren → z. B. `switchbot_config_v1.2.py`
2. Im neuen File die Version anpassen: `VERSION = "1.2"`
3. Alte Versionsdatei aus dem Repo löschen (optional, hält es sauber)
4. Neue Datei nach `tool/` auf `main` pushen
5. GitHub Actions baut automatisch:
   - `SwitchBot-Konfigurator.exe` / `SwitchBot-Konfigurator` (die App)
   - `install_windows.exe` / `install_linux` und `uninstall_windows.exe` / `uninstall_linux`
6. Laufende Tools bei Kunden erkennen die neue Version beim Start und aktualisieren sich
   selbst (Download der neuen App-Binary, kein Python/pip nötig).

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
6. Kunde klickt **„Jetzt flashen“** → Update läuft per WLAN-OTA, kein USB nötig.

Das Tool prüft vor dem Flashen, ob die Datei mit dem ESP32-Magic-Byte `0xE9` beginnt,
damit nicht z. B. eine GitHub-404-Seite geflasht wird.

---

## GitHub Actions

Workflow: [`.github/workflows/build.yml`](.github/workflows/build.yml)

**Auslöser:** Push auf `main`, der eine dieser Dateien ändert:
- `tool/switchbot_config_v*.py`
- `tool/install.py`
- `tool/uninstall.py`
- `.github/workflows/build.yml`

Außerdem manuell über **Actions → Build App + Installer → Run workflow**.

**Ablauf** (nacheinander, jeder Job committet sein Ergebnis direkt nach `main`):

| # | Job | Ergebnis |
|---|-----|----------|
| 1 | `build-app-windows` | `tool/SwitchBot-Konfigurator.exe` |
| 2 | `build-app-linux` | `tool/SwitchBot-Konfigurator` |
| 3 | `build-installer-windows` | `tool/install_windows.exe`, `tool/uninstall_windows.exe` |
| 4 | `build-installer-linux` | `tool/install_linux`, `tool/uninstall_linux` |

Gebaut wird mit Python 3.12 und PyInstaller (`--onefile --windowed`).
Die Binaries nie manuell hochladen – sie werden bei jedem Build überschrieben.

**Einmalige Einstellung**, damit der Workflow committen darf:
Repo → **Settings → Actions → General → Workflow permissions** →
**„Read and write permissions“** aktivieren.

---

## Wie das Tool GitHub nutzt

| Zweck | Quelle |
|-------|--------|
| Tool-Update suchen | GitHub API: Inhalt von `tool/` (sucht `switchbot_config_v*.py`) |
| Tool-Update laden | `raw.githubusercontent.com/.../main/tool/SwitchBot-Konfigurator(.exe)` |
| Firmware-Update suchen | GitHub API: Inhalt von `firmware/` (sucht `firmware_v*.bin`) |
| Firmware laden | `download_url` aus der API bzw. `.../main/firmware/firmware_v<VER>.bin` |
| Installer | lädt `.../main/tool/SwitchBot-Konfigurator(.exe)` |

Daraus folgt: Alles, was auf `main` in `tool/` und `firmware/` liegt, ist sofort für alle
Kunden live. Experimente daher auf einem anderen Branch machen.

**ESP32 im Netzwerk:**
- mDNS-Hostname: `http://controller-for-switchbot.local` (vom Tool beim Start gesucht)
- Endpunkte, die das Tool nutzt: `/status` (Firmware-Version), `/upload` (config.json), `/ota` (Firmware)
- Einrichtungs-Hotspot nach Werksreset: `SwitchBot-Bridge`

---

## Hardware: Taster-Pin-Zuordnung

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
