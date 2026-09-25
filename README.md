# Schalteinheit für SwitchBot

Mit dieser Schalteinheit steuerst du deine **SwitchBot Smart-Home-Geräte über 14 echte Taster** – ganz ohne Handy.
Jedem Taster kannst du ein Gerät, eine IR-Fernbedienung oder eine Szene samt Befehl zuweisen.

Die Einrichtung erledigst du bequem am PC mit dem **SwitchBot Konfigurator**.

---

## Inhalt

- [Was du brauchst](#was-du-brauchst)
- [Die Taster im Überblick](#die-taster-im-überblick)
- [1. Konfigurator installieren](#1-konfigurator-installieren)
- [2. Schalteinheit ins WLAN bringen](#2-schalteinheit-ins-wlan-bringen)
- [3. SwitchBot-Zugangsdaten besorgen](#3-switchbot-zugangsdaten-besorgen)
- [4. Taster belegen](#4-taster-belegen)
- [Updates](#updates)
- [Werksreset](#werksreset)
- [Hilfe bei Problemen](#hilfe-bei-problemen)
- [Deinstallation](#deinstallation)

---

## Was du brauchst

- die Schalteinheit mit Stromversorgung
- einen PC mit **Windows** oder **Linux**
- ein **2,4-GHz-WLAN**, in dem sich PC und Schalteinheit befinden
- ein **SwitchBot-Konto** mit deinen Geräten (SwitchBot-App)

Python oder andere Programme brauchst du **nicht** – alles Nötige steckt im Installer.

---

## Die Taster im Überblick

Die 14 Taster sind in **7 Reihen mit je 2 Tastern** angeordnet, getrennt durch das Beschriftungsfeld in der Mitte.
**Links** liegen die **ungeraden**, **rechts** die **geraden** Nummern.
Halte die Schalteinheit so, dass der **Ladeanschluss unten** ist – dann sind Taster 1 und 2 oben.

```
┌───────────────────────────────────┐
│  [  1 ]   Beschriftung    [  2 ]  │
│                                   │
│  [  3 ]   Beschriftung    [  4 ]  │
│                                   │
│  [  5 ]   Beschriftung    [  6 ]  │
│                                   │
│  [  7 ]   Beschriftung    [  8 ]  │
│                                   │
│  [  9 ]   Beschriftung    [ 10 ]  │
│                                   │
│  [ 11 ]   Beschriftung    [ 12 ]  │
│                                   │
│  [ 13 ]   Beschriftung    [ 14 ]  │
│                                   │
└───────────────[ ▭ ]───────────────┘
                  ▲
            Ladeanschluss
```

Die Nummern entsprechen den Zeilen *Taster 1* bis *Taster 14* im Konfigurator.

---

## 1. Konfigurator installieren

### Windows

1. [**install_windows.exe** herunterladen](https://github.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/releases/latest/download/install_windows.exe)
2. Datei doppelklicken.
3. Der Konfigurator wird installiert, bekommt eine Verknüpfung auf dem Desktop und startet automatisch.

> **Hinweis:** Erscheint die Meldung *„Der Computer wurde durch Windows geschützt“*, klicke auf
> **Weitere Informationen → Trotzdem ausführen**.
> Administratorrechte sind nicht nötig.

### Linux

1. [**install_linux** herunterladen](https://github.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/releases/latest/download/install_linux)
2. Datei ausführbar machen:
   Rechtsklick → **Eigenschaften** → **„Als Programm ausführen erlauben“**
   oder im Terminal:
   ```bash
   chmod +x install_linux
   ```
3. Datei doppelklicken.
4. Der Konfigurator wird installiert, bekommt eine Verknüpfung auf dem Desktop und startet automatisch.

---

## 2. Schalteinheit ins WLAN bringen

Beim ersten Start (oder nach einem [Werksreset](#werksreset)) öffnet die Schalteinheit einen eigenen WLAN-Hotspot:

| | |
|---|---|
| **Hotspot-Name** | `SwitchBot-Bridge` |

1. Mit Handy oder PC mit dem WLAN **`SwitchBot-Bridge`** verbinden.
2. Auf der Einrichtungsseite dein Heim-WLAN auswählen und das Passwort eingeben.
3. Speichern – die Schalteinheit startet neu und verbindet sich mit deinem WLAN.

Danach ist sie in deinem Netzwerk unter folgender Adresse erreichbar:

```
http://controller-for-switchbot.local
```

---

## 3. SwitchBot-Zugangsdaten besorgen

Der Konfigurator braucht **Token** und **Secret** deines SwitchBot-Kontos, um deine Geräte zu laden.

1. SwitchBot-App öffnen → **Profil** → **Einstellungen**
2. **10× auf „App-Version“ tippen** – es erscheinen die **Entwickleroptionen**.
3. Dort findest du **Token** und **Secret (Client Secret)**. Beide kopieren.

> Behandle Token und Secret wie ein Passwort und gib sie nicht weiter.

---

## 4. Taster belegen

1. **SwitchBot Konfigurator** über die Desktop-Verknüpfung starten.
   Die Schalteinheit wird automatisch im Netzwerk gesucht.
2. **Token** und **Secret** eintragen.
3. Auf **🔍 SwitchBot Geräte laden** klicken.
   Alle Geräte, IR-Fernbedienungen und Szenen deines Kontos erscheinen in der Auswahl.
4. Für jeden Taster (1–14) ein **Gerät / eine Szene** und den gewünschten **Befehl** wählen
   (z. B. *Ein*, *Aus*, *Umschalten*, *Szene ausführen*).
5. Auf **💾 + ⬆ Speichern & direkt hochladen** klicken – fertig!

Zusätzlich wird eine Sicherung als `config.json` auf deinem Desktop abgelegt.

<details>
<summary><strong>Unterstützte Geräte (Auswahl)</strong></summary>

- **Bot**, **Curtain**, **Blind Tilt**, **Roller Shade**
- **Smart Locks** (Lock, Lock Pro, Lock Ultra, Lock Lite, Lock Vision …)
- **Plugs** und **Relay Switches**
- **Lampen**: Color Bulb, Strip Light, Ceiling Light
- **Luftbefeuchter**, **Ventilatoren**, **Luftreiniger**
- **Saugroboter** (K10+, S1, S1 Plus)
- **IR-Fernbedienungen** aus dem Hub (TV, Klimaanlage, Lautsprecher, DIY …)
- **Szenen** aus der SwitchBot-App

Nicht aufgeführte Geräte lassen sich in der Regel mit *Ein* / *Aus* schalten.

</details>

---

## Updates

Um Updates musst du dich nicht kümmern:

- **Konfigurator:** Beim Start wird automatisch nach einer neuen Version gesucht. Ein Klick auf **Ja** genügt – der Konfigurator aktualisiert sich selbst.
- **Schalteinheit:** Gibt es neue Software für die Schalteinheit, erscheint im Konfigurator ein oranges Banner.
  Klicke auf **🔄 Jetzt flashen** – das Update läuft per WLAN, **kein USB-Kabel nötig**.
  Die Schalteinheit muss dafür im gleichen Netzwerk wie der PC sein.

> Während eines Updates die Schalteinheit bitte **nicht vom Strom trennen**.

---

## Werksreset

**Taster 13 und Taster 14 (unterste Reihe) gleichzeitig 5 Sekunden gedrückt halten.**

Dabei werden die WLAN-Zugangsdaten und die Tasterbelegung gelöscht.
Anschließend öffnet die Schalteinheit wieder den Hotspot `SwitchBot-Bridge` – weiter geht es mit [Schritt 2](#2-schalteinheit-ins-wlan-bringen).

---

## Hilfe bei Problemen

<details>
<summary><strong>Der Konfigurator findet die Schalteinheit nicht</strong></summary>

- Sind PC und Schalteinheit im **gleichen WLAN**?
- Auf **🔍 Suchen** klicken, um die Suche erneut zu starten.
- Alternativ die **IP-Adresse** der Schalteinheit manuell eintragen (zu finden z. B. in der Geräteübersicht deines Routers).
- Hilft nichts: Schalteinheit kurz vom Strom trennen und neu starten.

</details>

<details>
<summary><strong>„SwitchBot Geräte laden“ schlägt fehl</strong></summary>

- **Token** und **Secret** noch einmal prüfen – keine Leerzeichen am Anfang oder Ende.
- Besteht eine Internetverbindung?

</details>

<details>
<summary><strong>Die Schalteinheit verbindet sich nicht mit meinem WLAN</strong></summary>

- Die Schalteinheit unterstützt nur **2,4-GHz-WLAN**.
- WLAN-Passwort prüfen und die Einrichtung per [Werksreset](#werksreset) wiederholen.

</details>

---

## Deinstallation

| System  | Datei |
|---------|-------|
| Windows | [**uninstall_windows.exe**](https://github.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/releases/latest/download/uninstall_windows.exe) herunterladen und doppelklicken |
| Linux   | [**uninstall_linux**](https://github.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/releases/latest/download/uninstall_linux) herunterladen, ausführbar machen (siehe oben) und doppelklicken |

Der Konfigurator und die Desktop-Verknüpfung werden entfernt.
