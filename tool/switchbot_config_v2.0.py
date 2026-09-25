#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwitchBot Konfigurator
GitHub:  https://github.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot
"""

import json, os, sys, time, hmac, hashlib, base64, uuid, secrets, platform
import urllib.request, urllib.error, socket, subprocess

import webview
from cryptography.fernet import Fernet, InvalidToken

# ════════════════════════════════════════════════════════════════
#  KONSTANTEN
# ════════════════════════════════════════════════════════════════
VERSION          = "2.0"
GITHUB_RAW       = "https://raw.githubusercontent.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/main"
GITHUB_API       = "https://api.github.com/repos/DodosCraftingCave/Schalteinheit-fuer-Switchbot/contents"
MDNS_HOST        = "controller-for-switchbot.local"
CONFIG_PATH      = os.path.join(os.path.expanduser("~"), "Desktop", "config.json")
# Token/Secret werden nicht im Klartext abgelegt, sondern lokal mit einem
# einzigartigen, bei der ersten Ausführung dieser Version einmalig erzeugten
# Schlüssel symmetrisch verschlüsselt (Standard-Schlüsselverschlüsselung).
# Der Schlüssel selbst hat keine inhaltliche Bedeutung, er dient nur als
# Eingabe der mathematischen Ver-/Entschlüsselungsfunktion, siehe
# _load_or_create_key()/_cipher() weiter unten.
APP_DATA_DIR     = os.path.join(os.path.expanduser("~"), ".switchbot_configurator")
KEY_FILE         = os.path.join(APP_DATA_DIR, "secret.key")
CREDS_FILE       = os.path.join(APP_DATA_DIR, "credentials.enc")
PINS             = [12, 13, 14, 25, 26, 27, 32, 33, 16, 17, 18, 19, 21, 22]

DEVICE_COMMANDS = {
    "Bot":                          ["turnOn", "turnOff", "press"],
    "Curtain":                      ["turnOn", "turnOff", "setPosition"],
    "Curtain3":                     ["turnOn", "turnOff", "setPosition"],
    "Blind Tilt":                   ["closeUp", "closeDown", "fullyOpen", "setPosition"],
    "Roller Shade":                 ["turnOn", "turnOff", "setPosition"],
    "Smart Lock":                   ["lock", "unlock"],
    "Smart Lock Pro":               ["lock", "unlock"],
    "Smart Lock Ultra":             ["lock", "unlock"],
    "Lock Lite":                    ["lock", "unlock"],
    "Lock Vision":                  ["lock", "unlock"],
    "Lock Vision Pro":              ["lock", "unlock"],
    "Keypad":                       ["createKey", "deleteKey"],
    "Keypad Touch":                 ["createKey", "deleteKey"],
    "Keypad Vision":                ["createKey", "deleteKey"],
    "Keypad Vision Pro":            ["createKey", "deleteKey"],
    "Plug":                         ["turnOn", "turnOff", "toggle"],
    "Plug Mini (US)":               ["turnOn", "turnOff", "toggle"],
    "Plug Mini (EU)":               ["turnOn", "turnOff", "toggle"],
    "Plug Mini (JP)":               ["turnOn", "turnOff", "toggle"],
    "Relay Switch 1":               ["turnOn", "turnOff"],
    "Relay Switch 1PM":             ["turnOn", "turnOff"],
    "Relay Switch 2PM":             ["turnOn", "turnOff"],
    "Color Bulb":                   ["turnOn", "turnOff", "toggle", "setBrightness", "setColor", "setColorTemperature"],
    "Strip Light":                  ["turnOn", "turnOff", "toggle", "setBrightness", "setColor", "setColorTemperature"],
    "Strip Light 3":                ["turnOn", "turnOff", "toggle", "setBrightness", "setColor"],
    "Ceiling Light":                ["turnOn", "turnOff", "toggle", "setBrightness", "setColorTemperature"],
    "Ceiling Light Pro":            ["turnOn", "turnOff", "toggle", "setBrightness", "setColorTemperature"],
    "Humidifier":                   ["turnOn", "turnOff", "setMode"],
    "Humidifier2":                  ["turnOn", "turnOff", "setMode"],
    "Fan":                          ["turnOn", "turnOff", "swing", "setAllSpeed"],
    "Circulator Fan":               ["turnOn", "turnOff", "swing", "setAllSpeed"],
    "Air Purifier VOC":             ["turnOn", "turnOff", "toggle", "setMode"],
    "Air Purifier Table":           ["turnOn", "turnOff", "toggle", "setMode"],
    "K10+":                         ["start", "stop", "dock"],
    "Robot Vacuum Cleaner S1":      ["start", "stop", "dock"],
    "Robot Vacuum Cleaner S1 Plus": ["start", "stop", "dock"],
}

IR_COMMANDS = {
    "TV":               ["turnOn", "turnOff", "volumeAdd", "volumeSub",
                         "channelAdd", "channelSub", "setMute",
                         "FastForward", "Rewind", "Next", "Previous", "Pause"],
    "IPTV/Streamer":    ["turnOn", "turnOff", "volumeAdd", "volumeSub",
                         "channelAdd", "channelSub", "setMute"],
    "Set Top Box":      ["turnOn", "turnOff", "volumeAdd", "volumeSub", "setMute"],
    "DVD":              ["turnOn", "turnOff", "FastForward", "Rewind",
                         "Next", "Previous", "Pause", "Stop", "Play"],
    "Fan":              ["turnOn", "turnOff", "swing", "lowSpeed", "middleSpeed", "highSpeed"],
    "Air Conditioner":  ["turnOn", "turnOff", "setAll"],
    "Air Purifier":     ["turnOn", "turnOff", "mode", "fan", "speed"],
    "Speaker":          ["turnOn", "turnOff", "volumeAdd", "volumeSub",
                         "setMute", "Next", "Previous", "Pause"],
    "DIY":              ["turnOn", "turnOff"],
    "Others":           ["turnOn", "turnOff"],
}

FALLBACK_COMMANDS = ["turnOn", "turnOff"]


# ════════════════════════════════════════════════════════════════
#  HILFSFUNKTIONEN (unverändert aus v1.1 übernommen)
# ════════════════════════════════════════════════════════════════
def make_headers(token, secret):
    nonce = str(uuid.uuid4())
    t     = str(int(round(time.time() * 1000)))
    msg   = token + t + nonce
    sign  = base64.b64encode(
        hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()
    ).decode()
    return {"Authorization": token, "sign": sign,
            "nonce": nonce, "t": t, "Content-Type": "application/json"}

def fetch_all(token, secret):
    import requests
    headers = make_headers(token, secret)
    items   = []
    res  = requests.get("https://api.switch-bot.com/v1.1/devices",
                        headers=headers, timeout=10)
    res.raise_for_status()
    body = res.json().get("body", {})
    for d in body.get("deviceList", []):
        item = {"label":    f"[Gerät] {d['deviceName']}",
                "name":     d["deviceName"], "id": d["deviceId"],
                "type":     d["deviceType"],  "category": "Device"}
        item["commands"] = get_commands(item)
        items.append(item)
    for ir in body.get("infraredRemoteList", []):
        item = {"label":    f"[IR] {ir['deviceName']}",
                "name":     ir["deviceName"], "id": ir["deviceId"],
                "type":     ir.get("remoteType","Others"), "category": "IR Remote"}
        item["commands"] = get_commands(item)
        items.append(item)
    res_s = requests.get("https://api.switch-bot.com/v1.1/scenes",
                         headers=headers, timeout=10)
    res_s.raise_for_status()
    for s in res_s.json().get("body", []):
        item = {"label":    f"[Szene] {s['sceneName']}",
                "name":     s["sceneName"], "id": s["sceneId"],
                "type":     "Scene", "category": "Scene"}
        item["commands"] = get_commands(item)
        items.append(item)
    return items

def get_commands(item):
    if item["category"] == "Scene":      return ["execute"]
    if item["category"] == "IR Remote":  return IR_COMMANDS.get(item["type"], FALLBACK_COMMANDS)
    return DEVICE_COMMANDS.get(item["type"], FALLBACK_COMMANDS)

def resolve_esp_ip():
    """Versucht controller-for-switchbot.local aufzulösen. Gibt IP-String zurück oder ''."""
    try:
        ip = socket.getaddrinfo(MDNS_HOST, 80)[0][4][0]
        return ip
    except Exception:
        return ""

def esp_get_status(ip):
    """Fragt /status vom ESP ab. Gibt dict oder None zurück."""
    try:
        url = f"http://{ip}/status"
        req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except Exception:
        return None

def esp_get_challenge(ip, timeout=8):
    """Holt eine frische, einmalig gültige Nonce von GET /challenge (main.cpp
    requireAuth(), Änderung #17) — jede signierte Anfrage braucht eine neue,
    da die Nonce nach dem ersten Prüfversuch verbraucht ist und nur 30s gültig
    bleibt (siehe Firmware-Spec in der temporären Projekt-Erinnerung)."""
    req = urllib.request.Request(f"http://{ip}/challenge", headers={"User-Agent": "SwitchBot-Tool"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["nonce"]

def esp_auth_headers(ip, admin_password, method, path, body_bytes=None, timeout=8):
    """Baut X-Auth-Nonce/X-Auth-Sign (und bei body_bytes zusätzlich X-Body-
    SHA256) für einen HMAC-Challenge-Response-Request.

    Ohne body_bytes (z.B. GET /config): signature = hex(HMAC-SHA256(
    admin_password, nonce + ':' + METHOD + ':' + path)) — 3 Segmente.

    Mit body_bytes (Pflicht für POST /upload und /ota, main.cpp Änderung #18):
    signature = hex(HMAC-SHA256(admin_password, nonce + ':' + METHOD + ':' +
    path + ':' + sha256_hex(body_bytes))) — 4. Segment bindet die Signatur an
    den tatsächlichen Inhalt, damit ein aktiver MITM den Body nach dem
    Signieren nicht mehr unbemerkt tauschen kann (schließt die in main.cpp
    Änderung #17 noch offene Lücke). body_bytes müssen exakt die Bytes des
    data-Feldwerts sein, NICHT der komplette multipart-Request-Body."""
    nonce = esp_get_challenge(ip, timeout=timeout)
    parts = [nonce, method.upper(), path]
    headers = {"X-Auth-Nonce": nonce}
    if body_bytes is not None:
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        parts.append(body_hash)
        headers["X-Body-SHA256"] = body_hash
    msg = ":".join(parts).encode("utf-8")
    headers["X-Auth-Sign"] = hmac.new(admin_password.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    return headers

def esp_set_admin_password(ip, new_password):
    """Bootstrap auf einem frischen/ungekoppelten ESP32: POST /setadminpass,
    Form-Feld 'pass' (mind. 8 Zeichen). Läuft unauthentifiziert (nur IP-Filter)
    — MUSS als allererster Schritt aufgerufen werden, solange main.cpp noch
    kein Admin-Passwort gespeichert hat; danach läuft alles über HMAC gegen
    genau dieses Passwort."""
    import requests
    r = requests.post(f"http://{ip}/setadminpass", data={"pass": new_password}, timeout=10)
    if r.status_code >= 400:
        raise Exception(r.text.strip() or f"ESP32 hat das Setzen des Passworts abgelehnt (HTTP {r.status_code}).")
    return r.text

def esp_change_admin_password(ip, old_password, new_password):
    """Ändert ein BEREITS gesetztes Admin-Passwort. Im Unterschied zu
    esp_set_admin_password() (reiner Bootstrap-Weg, nur für ein frisches
    Gerät ohne Passwort) authentifiziert dieser Aufruf sich mit dem
    aktuell bekannten alten Passwort — main.cpp verlangt requireAuth() für
    /setadminpass, sobald bereits ein Passwort gespeichert ist (sonst 401
    'Nicht angemeldet'). Fehlte bisher im Tool: der 'Auf neuem Gerät
    setzen'-Button ruft ausschließlich den unauthentifizierten Bootstrap-Weg
    auf, der auf einem bereits gekoppelten Gerät zurecht abgelehnt wird."""
    import requests
    headers = esp_auth_headers(ip, old_password, "POST", "/setadminpass")
    r = requests.post(f"http://{ip}/setadminpass", data={"pass": new_password}, headers=headers, timeout=10)
    _raise_for_esp_auth_status(r)
    if r.status_code >= 400:
        raise Exception(r.text.strip() or f"ESP32 hat das Ändern des Passworts abgelehnt (HTTP {r.status_code}).")
    return r.text

def _raise_for_esp_auth_status(r):
    if r.status_code == 400:
        raise Exception(r.text.strip() or "ESP32 hat den Request abgelehnt (400) — Body-Prüfsumme oder Header ungültig.")
    if r.status_code == 401:
        raise Exception("ESP32 hat die Anmeldung abgelehnt (401) — Admin-Passwort prüfen.")
    if r.status_code == 403:
        # main.cpp Änderung #20: u.a. gesperrt solange noch das Werks-
        # Standardpasswort aktiv ist — Firmware-Text ist bereits verständlich,
        # 1:1 durchreichen statt zu verallgemeinern.
        raise Exception(r.text.strip() or "ESP32 hat den Request abgelehnt (403).")
    if r.status_code == 429:
        raise Exception("ESP32 sperrt wegen zu vieler Fehlversuche kurzzeitig (429) — bitte kurz warten.")

def esp_upload_config(ip, config_dict, admin_password=None):
    """Lädt config.json direkt per HTTP auf den ESP hoch. Ein bereits per
    /setadminpass gekoppeltes ESP32 verlangt via requireAuth() eine gültige
    HMAC-Challenge-Response-Signatur inkl. Body-Hash (siehe esp_auth_headers,
    main.cpp Änderung #18) — ohne die antwortet die Firmware mit 400/401."""
    import requests
    data = json.dumps(config_dict, indent=2, ensure_ascii=False).encode("utf-8")
    files = {"data": ("config.json", data, "application/json")}
    headers = esp_auth_headers(ip, admin_password, "POST", "/upload", body_bytes=data) if admin_password else {}
    r = requests.post(f"http://{ip}/upload", files=files, headers=headers, timeout=15)
    _raise_for_esp_auth_status(r)
    return r.text

def esp_flash_firmware(ip, bin_data, admin_password=None):
    """Flasht firmware.bin per HTTP OTA auf den ESP — ebenfalls per HMAC-
    Challenge-Response inkl. Body-Hash gegen requireAuth() abgesichert
    (siehe esp_upload_config)."""
    import requests
    files = {"data": ("firmware.bin", bin_data, "application/octet-stream")}
    headers = esp_auth_headers(ip, admin_password, "POST", "/ota", body_bytes=bin_data) if admin_password else {}
    r = requests.post(f"http://{ip}/ota", files=files, headers=headers, timeout=300)
    _raise_for_esp_auth_status(r)
    return r.text

def validate_firmware_binary(data):
    """Prüft ob die heruntergeladene Datei plausibel eine gültige ESP32-Firmware
    ist (Magic-Byte 0xE9), bevor geflasht wird — verhindert dass z.B. eine
    GitHub-404-HTML-Seite versehentlich als 'Firmware' geflasht wird."""
    if len(data) < 100_000:
        return False, f"Datei zu klein ({len(data)} Bytes) – keine gültige Firmware."
    if data[0] != 0xE9:
        return False, "Datei beginnt nicht mit dem ESP32-Firmware-Magic-Byte (0xE9)."
    return True, ""

def git_blob_sha1(data):
    """Berechnet den Git-Blob-SHA1 genau wie ihn die GitHub-Contents-API für
    jede Datei mitliefert. Wird genutzt, um heruntergeladene Updates (App-
    Binary, Firmware) gegen den von GitHub gemeldeten Hash zu verifizieren,
    bevor sie ausgeführt bzw. geflasht werden — schützt gegen Bit-Fehler,
    abgebrochene Downloads und Manipulation auf dem Übertragungsweg
    (z.B. durch einen kompromittierten Proxy/CDN-Knoten)."""
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


# ════════════════════════════════════════════════════════════════
#  AUTO-UPDATE (unverändert aus v1.1 übernommen)
# ════════════════════════════════════════════════════════════════
def parse_version(v):
    """Wandelt Versionsstrings wie '1.0' oder '0.8_beta' in ein Tuple zum Vergleichen um.
    Zahlenteile werden auf eine feste Länge aufgefüllt, damit z.B. '1.0' und
    '1.0.0' korrekt als GLEICHWERTIG erkannt werden."""
    v = v.strip().lstrip("v")
    is_beta = "_beta" in v
    nums = v.replace("_beta","").replace("-beta","")
    try:
        parts = [int(x) for x in nums.split(".")]
    except ValueError:
        parts = [0]
    while len(parts) < 4:
        parts.append(0)
    return (parts[:4], 0 if is_beta else 1)

def github_list(path):
    """Listet Dateien in einem GitHub-Ordner per API."""
    url = f"{GITHUB_API}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())

def check_tool_update():
    """Sucht neueste switchbot_config_v*.py auf GitHub. Gibt (neue_version, url, sha)
    oder (None, None, None) zurück. sha ist der Git-Blob-SHA1 der zugehörigen, bereits
    kompilierten App-Binary im selben tool/-Ordner (nicht der .py-Quelldatei!) — wird
    von apply_tool_update() genutzt, um den heruntergeladenen Binary-Download vor der
    Ausführung zu verifizieren."""
    try:
        files = github_list("tool")
        candidates = []
        for f in files:
            name = f["name"]
            if name.startswith("switchbot_config_v") and name.endswith(".py"):
                ver = name.replace("switchbot_config_v","").replace(".py","")
                candidates.append((parse_version(ver), ver, f["download_url"]))
        if not candidates:
            return None, None, None
        candidates.sort(reverse=True)
        best_ver = candidates[0][1]
        best_url = candidates[0][2]
        if parse_version(best_ver) > parse_version(VERSION):
            app_name = "SwitchBot-Konfigurator.exe" if platform.system() == "Windows" else "SwitchBot-Konfigurator"
            binary_sha = next((f.get("sha") for f in files if f["name"] == app_name), None)
            return best_ver, best_url, binary_sha
    except Exception:
        pass
    return None, None, None

def check_firmware_update():
    """Sucht neueste firmware_v*.bin im firmware/-Ordner auf GitHub. Gibt
    (version, url, sha) oder (None, None, None) zurück. sha ist der Git-Blob-SHA1
    der .bin-Datei, genutzt von flash_firmware() zur Integritätsprüfung vor dem Flashen."""
    try:
        files = github_list("firmware")
        candidates = []
        for f in files:
            name = f["name"]
            if name.startswith("firmware_v") and name.endswith(".bin"):
                ver = name.replace("firmware_v","").replace(".bin","")
                candidates.append((parse_version(ver), ver, f["download_url"], f.get("sha")))
        if not candidates:
            return None, None, None
        candidates.sort(reverse=True)
        return candidates[0][1], candidates[0][2], candidates[0][3]
    except Exception:
        return None, None, None


# ════════════════════════════════════════════════════════════════
#  LOKALE VERSCHLÜSSELUNG DER ZUGANGSDATEN
# ════════════════════════════════════════════════════════════════
def _write_secure_file(path, data: bytes):
    """Schreibt eine Datei mit von Anfang an restriktiven Rechten (0600 – nur
    Besitzer darf lesen/schreiben). Nutzt os.open() mit explizitem mode statt
    open()+chmod() im Nachhinein, damit die Datei zu keinem Zeitpunkt (auch
    nicht für den kurzen Moment zwischen Erstellung und chmod) mit den
    Standard-Umask-Rechten für andere lokale Benutzer lesbar ist."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)

def _load_or_create_key():
    """Liest den lokalen Schlüssel, oder erzeugt ihn beim allerersten Start
    (Neuinstallation oder Update auf diese Version) einmalig: 16 zufällige
    Bytes (128 Bit, Standardgröße für AES-128). Der Schlüssel hat selbst
    keine Bedeutung — er ist nur der Input für die mathematische Funktion
    in _cipher()."""
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    try:
        os.chmod(APP_DATA_DIR, 0o700)
    except Exception:
        pass
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    raw = secrets.token_bytes(16)
    _write_secure_file(KEY_FILE, raw)
    return raw

def _cipher():
    """Standard-Schlüsselverschlüsselung (Fernet/AES) mit dem lokalen
    Schlüssel als Eingabe. Fernet erwartet einen 32-Byte-Schlüssel, daher
    wird der 16-Byte-Schlüssel per SHA-256 auf die passende Länge gebracht."""
    raw = _load_or_create_key()
    fernet_key = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
    return Fernet(fernet_key)


# ════════════════════════════════════════════════════════════════
#  JS-API — Brücke zwischen Frontend (HTML/JS) und Python-Backend
# ════════════════════════════════════════════════════════════════
class Api:
    def __init__(self):
        self.window   = None   # nach create_window() gesetzt
        self.items    = []     # zuletzt via load_devices geladene Geräte/IR/Szenen
        self.esp_ip   = ""
        self.esp_fw   = None

    # ── Fenster ──
    def toggle_fullscreen(self):
        self.window.toggle_fullscreen()
        return {"ok": True}

    # ── Bootstrap ──
    def bootstrap(self):
        return {"version": VERSION, "pins": PINS, "configPath": CONFIG_PATH}

    # ── Zugangsdaten lokal verschlüsselt speichern (SwitchBot Token/Secret
    #    UND das ESP32-Admin-Passwort für HTTP Basic Auth) ──
    def save_credentials(self, token, secret, esp_password=""):
        try:
            f = _cipher()
            data = {
                "token":        f.encrypt((token or "").encode()).decode(),
                "secret":       f.encrypt((secret or "").encode()).decode(),
                "esp_password": f.encrypt((esp_password or "").encode()).decode(),
            }
            _write_secure_file(CREDS_FILE, json.dumps(data).encode("utf-8"))
            return {"ok": True}
        except Exception as ex:
            return {"ok": False, "error": str(ex)}

    def load_credentials(self):
        if not os.path.exists(CREDS_FILE):
            return {"ok": True, "token": "", "secret": "", "esp_password": ""}
        try:
            with open(CREDS_FILE, encoding="utf-8") as fh:
                data = json.load(fh)
            f = _cipher()
            token        = f.decrypt(data["token"].encode()).decode()        if data.get("token")        else ""
            secret       = f.decrypt(data["secret"].encode()).decode()       if data.get("secret")       else ""
            esp_password = f.decrypt(data["esp_password"].encode()).decode() if data.get("esp_password") else ""
            return {"ok": True, "token": token, "secret": secret, "esp_password": esp_password}
        except (InvalidToken, KeyError, ValueError):
            return {"ok": True, "token": "", "secret": "", "esp_password": ""}
        except Exception as ex:
            return {"ok": False, "token": "", "secret": "", "esp_password": "", "error": str(ex)}

    def clear_credentials(self):
        try:
            if os.path.exists(CREDS_FILE):
                os.remove(CREDS_FILE)
            return {"ok": True}
        except Exception as ex:
            return {"ok": False, "error": str(ex)}

    # ── SwitchBot-Geräte laden ──
    def load_devices(self, token, secret):
        token, secret = (token or "").strip(), (secret or "").strip()
        if not token or not secret:
            return {"ok": False, "error": "Token und Secret ausfüllen."}
        try:
            items = fetch_all(token, secret)
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        self.items = items
        out = [dict(it, commands=get_commands(it)) for it in items]
        counts = {
            "device": sum(1 for x in items if x["category"] == "Device"),
            "ir":     sum(1 for x in items if x["category"] == "IR Remote"),
            "scene":  sum(1 for x in items if x["category"] == "Scene"),
        }
        return {"ok": True, "items": out, "counts": counts}

    # ── ESP32 ──
    def discover_esp(self, manual_ip=""):
        # Bei manuell eingetragener IP direkt diese versuchen — der
        # mDNS-Umweg würde sonst bei jedem Klick auf "Verbinden" erst
        # ~5s auf die (dann unnötige) .local-Auflösung warten.
        manual_ip = (manual_ip or "").strip()
        if manual_ip:
            ip = manual_ip
        else:
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(4)
            try:
                ip = resolve_esp_ip()
            finally:
                socket.setdefaulttimeout(old_timeout)
        if ip:
            status = esp_get_status(ip)
            if status:
                self.esp_ip = ip
                self.esp_fw = status.get("fw")
                # main.cpp Änderung #20: "defaultPass" zeigt an, ob noch das aus
                # der Chip-ID abgeleitete Werks-Standardpasswort aktiv ist — dann
                # sind /upload, /ota, /config, /setcreds gesperrt (403), bis der
                # Nutzer über "Passwort ändern" ein eigenes Passwort setzt.
                return {"ok": True, "ip": ip, "buttons": status.get("buttons", 0),
                        "fw": status.get("fw", "?"), "defaultPass": bool(status.get("defaultPass", False))}
        return {"ok": False}

    # ── Auto-Update-Check (Tool + Firmware) ──
    def check_updates(self):
        result = {"tool": None, "firmware": None}
        try:
            new_ver, dl_url, bin_sha = check_tool_update()
            if new_ver:
                result["tool"] = {"version": new_ver, "url": dl_url, "sha": bin_sha}
        except Exception:
            pass
        try:
            # Banner nur zeigen, wenn tatsächlich ein ESP32 gefunden wurde und
            # dessen Firmware-Version bekannt ist — sonst wäre "Firmware
            # verfügbar" irreführend, wenn gar kein Gerät im Netz hängt.
            if self.esp_fw:
                fw_ver, fw_url, fw_sha = check_firmware_update()
                if fw_ver and parse_version(fw_ver) > parse_version(self.esp_fw):
                    result["firmware"] = {"version": fw_ver, "url": fw_url, "current": self.esp_fw, "sha": fw_sha}
        except Exception:
            pass
        return result

    def apply_tool_update(self, new_version, expected_sha=None):
        """Lädt die fertig gebaute App-Binary von GitHub herunter (gebaut von GitHub
        Actions) und ersetzt die aktuell laufende Datei. Im Quellcode-Betrieb (nicht
        als Binary gebaut) gibt es nichts zu ersetzen — dann nur ein Hinweis."""
        if not getattr(sys, "frozen", False):
            return {"ok": False, "sourceMode": True,
                    "error": f"Läuft aus dem Quellcode – bitte v{new_version} manuell von GitHub laden."}
        try:
            import shutil
            is_windows = platform.system() == "Windows"
            app_name   = "SwitchBot-Konfigurator.exe" if is_windows else "SwitchBot-Konfigurator"
            url        = f"{GITHUB_RAW}/tool/{app_name}"
            exe_path   = sys.executable
            tmp_path   = exe_path + ".new"

            req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
            with urllib.request.urlopen(req, timeout=30) as r, open(tmp_path, "wb") as out:
                shutil.copyfileobj(r, out)

            # Integritätsprüfung: heruntergeladene Binary muss exakt dem von
            # GitHub gemeldeten Hash entsprechen, bevor sie die laufende App
            # ersetzt und ausgeführt wird — verhindert dass eine unterwegs
            # beschädigte oder manipulierte Datei zur Ausführung kommt.
            if expected_sha:
                with open(tmp_path, "rb") as f:
                    actual_sha = git_blob_sha1(f.read())
                if actual_sha != expected_sha:
                    os.remove(tmp_path)
                    return {"ok": False, "error": "Update abgebrochen: Integritätsprüfung fehlgeschlagen (Prüfsumme stimmt nicht überein)."}

            if is_windows:
                # Windows kann die laufende .exe nicht direkt überschreiben →
                # kleiner Batch-Helfer wartet bis der Prozess beendet ist.
                bat_path = exe_path + "_update.bat"
                with open(bat_path, "w") as bat:
                    bat.write(f'''@echo off
timeout /t 2 /nobreak >nul
move /Y "{tmp_path}" "{exe_path}"
start "" "{exe_path}"
del "%~f0"
''')
                subprocess.Popen(["cmd", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
                os._exit(0)  # sofortiger Prozess-Exit — sys.exit() würde in diesem
                             # Hintergrund-Thread nur den Thread beenden, nicht den Prozess
            else:
                os.chmod(tmp_path, 0o755)
                os.replace(tmp_path, exe_path)
                os.execv(exe_path, [exe_path])
        except Exception as ex:
            return {"ok": False, "error": str(ex)}

    # ── Speichern ──
    def save_config(self, token, secret, assignments):
        """assignments: Liste von {taster,pin,deviceId,command} — nur belegte Taster."""
        token, secret = (token or "").strip(), (secret or "").strip()
        if not token or not secret:
            return {"ok": False, "error": "Token und Secret ausfüllen."}
        devices = []
        for a in assignments:
            item = next((x for x in self.items if x["id"] == a["deviceId"]), None)
            if not item:
                continue
            cmd = a["command"]
            param = "0,ff,50" if cmd == "setPosition" else "default"
            entry = {
                "taster":     a["taster"],
                "pin":        a["pin"],
                "deviceId":   item["id"],
                "deviceName": item["name"],
                "deviceType": item["type"],
                "category":   item["category"],
                "command":    cmd,
                "parameter":  param,
            }
            if item["category"] == "Scene":
                entry["isScene"] = True
            devices.append(entry)
        cfg = {"api_token": token, "api_secret": secret, "devices": devices}
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            # config.json enthält Token/Secret im Klartext (die ESP32-Firmware
            # braucht sie so, um selbst gegen die SwitchBot-API zu signieren) —
            # Dateirechte wenigstens auf den eigenen Benutzer einschränken.
            try:
                os.chmod(CONFIG_PATH, 0o600)
            except Exception:
                pass
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        return {"ok": True, "count": len(devices), "path": CONFIG_PATH, "config": cfg}

    # ── Auf ESP hochladen ──
    def upload_config(self, ip, config=None, admin_password=None):
        ip = (ip or "").strip()
        if not ip:
            return {"ok": False, "error": "Keine ESP32-IP bekannt. Bitte zuerst verbinden."}
        cfg = config
        if cfg is None:
            if not os.path.exists(CONFIG_PATH):
                return {"ok": False, "error": "Keine config.json auf dem Desktop gefunden."}
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
        try:
            result = esp_upload_config(ip, cfg, admin_password=(admin_password or "").strip() or None)
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        return {"ok": True, "result": result}

    # ── Admin-Passwort auf einem frischen ESP32 setzen (Bootstrap) ──
    def setup_esp_admin_password(self, ip, new_password):
        ip = (ip or "").strip()
        new_password = (new_password or "").strip()
        if not ip:
            return {"ok": False, "error": "Keine ESP32-IP bekannt. Bitte zuerst verbinden."}
        if len(new_password) < 8:
            return {"ok": False, "error": "Admin-Passwort muss mindestens 8 Zeichen haben."}
        try:
            result = esp_set_admin_password(ip, new_password)
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        return {"ok": True, "result": result}

    # ── Admin-Passwort auf einem BEREITS gekoppelten ESP32 ändern ──
    def change_esp_admin_password(self, ip, old_password, new_password):
        ip = (ip or "").strip()
        old_password = (old_password or "").strip()
        new_password = (new_password or "").strip()
        if not ip:
            return {"ok": False, "error": "Keine ESP32-IP bekannt. Bitte zuerst verbinden."}
        if not old_password:
            return {"ok": False, "error": "Aktuelles Admin-Passwort eintragen (oben im Feld)."}
        if len(new_password) < 8:
            return {"ok": False, "error": "Neues Admin-Passwort muss mindestens 8 Zeichen haben."}
        try:
            result = esp_change_admin_password(ip, old_password, new_password)
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        return {"ok": True, "result": result}

    # ── Aktuelle Konfiguration vom ESP zurücklesen ──
    def load_from_esp(self, ip, admin_password=None):
        """Liest die aktuell auf dem ESP32 gespeicherte config.json zurück.
        Erwartet einen GET /config Endpunkt in der Firmware, der dasselbe
        JSON liefert, das save_config() schreibt bzw. upload_config()
        hochlädt — {api_token, api_secret, devices:[...]}. requireAuth() in
        main.cpp verlangt dafür eine HMAC-Challenge-Response-Signatur (siehe
        esp_auth_headers), sobald ein Admin-Passwort gesetzt ist. Ist
        admin_password leer, wird trotzdem unauthentifiziert versucht — main.cpp
        liefert dann sauber 401 (kein anderer Recovery-Pfad über die Software:
        sobald main.cpp ein adminPass gespeichert hat, sperrt /config IMMER
        ohne gültige Signatur, unabhängig vom config.json-Zustand. Der einzige
        echte Recovery-Weg ist ein physischer Werksreset am Gerät, danach neu
        über setup_esp_admin_password()/'Auf neuem Gerät setzen' bootstrappen)."""
        ip = (ip or "").strip()
        admin_password = (admin_password or "").strip()
        if not ip:
            return {"ok": False, "error": "Keine ESP32-IP bekannt. Bitte zuerst verbinden."}
        try:
            url = f"http://{ip}/config"
            headers = {"User-Agent": "SwitchBot-Tool"}
            if admin_password:
                headers.update(esp_auth_headers(ip, admin_password, "GET", "/config"))
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as r:
                cfg = json.loads(r.read())
        except urllib.error.HTTPError as ex:
            body = ex.read().decode("utf-8", errors="replace").strip()
            if ex.code == 401:
                return {"ok": False, "error": body or "ESP32 hat die Anmeldung abgelehnt (401) — Admin-Passwort prüfen."}
            if ex.code == 403:
                # main.cpp Änderung #20: u.a. gesperrt solange noch das Werks-
                # Standardpasswort aktiv ist — Firmware-Text ist bereits
                # verständlich, 1:1 durchreichen.
                return {"ok": False, "error": body or "ESP32 hat den Request abgelehnt (403)."}
            if ex.code == 429:
                return {"ok": False, "error": body or "ESP32 sperrt wegen zu vieler Fehlversuche kurzzeitig (429) — bitte kurz warten."}
            return {"ok": False, "error": body or str(ex)}
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        return {"ok": True, "config": cfg}

    # ── Firmware flashen ──
    def flash_firmware(self, ip, fw_version, fw_url, expected_sha=None, admin_password=None):
        ip = (ip or "").strip()
        if not ip:
            return {"ok": False, "error": "ESP32 nicht gefunden. Bitte zuerst verbinden."}
        try:
            url = fw_url or f"{GITHUB_RAW}/firmware/firmware_v{fw_version}.bin"
            req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
            with urllib.request.urlopen(req, timeout=30) as r:
                bin_data = r.read()

            valid, reason = validate_firmware_binary(bin_data)
            if not valid:
                return {"ok": False, "error": f"Flash abgebrochen: {reason}"}

            if expected_sha and git_blob_sha1(bin_data) != expected_sha:
                return {"ok": False, "error": "Flash abgebrochen: Integritätsprüfung der Firmware fehlgeschlagen (Prüfsumme stimmt nicht überein)."}

            result = esp_flash_firmware(ip, bin_data, admin_password=(admin_password or "").strip() or None)
        except Exception as ex:
            return {"ok": False, "error": str(ex)}
        return {"ok": True, "result": result}


# ════════════════════════════════════════════════════════════════
#  FRONTEND (eine einzelne HTML-Seite, von pywebview gerendert)
# ════════════════════════════════════════════════════════════════
PAGE_HTML = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SwitchBot Konfigurator</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap">
<style>
:root{
  /* Dunkle Palette, an die frühere Tkinter-Version angelehnt: gedecktes
     Blaugrau statt reinem Weiß/Hellgrau — bewusst als einziges Theme,
     kein Hell/Dunkel-Umschalten. */
  --bg:#000000; --surface:#0A0A0B; --surface-alt:#161617; --border:#2B3542;
  --text:#EDF1F5; --muted:#8996A6;
  --accent:#4C8DFF; --accent-strong:#3B72D6; --accent-soft:#182A45; --accent-ink:#FFFFFF;
  --success:#3ECF8E; --success-soft:#173226;
  --danger:#FF6B6B; --danger-soft:#3A1D1D;
  --warning:#F0A93B; --warning-soft:#3A2C14;
  --cat-device:#4C8DFF; --cat-ir:#9B8CFF; --cat-scene:#F0A93B;
  --shadow:0 1px 2px rgba(0,0,0,.35), 0 6px 18px rgba(0,0,0,.4);
  --font-display:'Sora',system-ui,sans-serif;
  --font-body:'Inter',system-ui,sans-serif;
  --font-mono:'JetBrains Mono',ui-monospace,monospace;
}

*{box-sizing:border-box;}
html,body{margin:0;padding:0;height:100%;}
body{
  background:var(--bg); color:var(--text); font-family:var(--font-body);
  font-size:14px; -webkit-font-smoothing:antialiased;
  min-height:100vh; display:flex; flex-direction:column;
}
button{font-family:inherit;}
::selection{background:var(--accent-soft);}

/* ── Topbar ── */
.topbar{
  position:sticky; top:0; z-index:30; background:var(--surface);
  border-bottom:1px solid var(--border);
  display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:12px;
  padding:14px 20px;
}
.topbar-side{display:flex; align-items:center;}
.topbar-right{justify-content:flex-end;}
.topbar-center{display:flex; align-items:center; gap:12px; justify-self:center;}
.topbar h1{
  font-family:var(--font-display); font-weight:800; font-size:24px; margin:0;
  color:var(--danger); white-space:nowrap; letter-spacing:-.01em;
  font-variant-ligatures:none;
  -webkit-font-variant-ligatures:none;
}
.topbar .ver{
  font-family:var(--font-mono); font-size:10.5px; color:var(--muted);
  background:var(--surface-alt); border:1px solid var(--border);
  border-radius:999px; padding:2px 8px;
}
.esp-pill{
  display:flex; align-items:center; gap:6px; font-size:12px; color:var(--muted);
  background:var(--surface-alt); border:1px solid var(--border);
  border-radius:999px; padding:5px 10px 5px 8px; cursor:pointer;
}
.esp-pill .dot{width:7px;height:7px;border-radius:50%;background:var(--muted);}
.esp-pill.ok .dot{background:var(--accent);}
.esp-pill.bad .dot{background:var(--danger);}
.icon-btn{
  width:34px;height:34px;border-radius:10px;border:1px solid var(--border);
  background:var(--surface-alt); color:var(--text); cursor:pointer;
  display:flex;align-items:center;justify-content:center;font-size:16px;
}
.icon-btn:hover{background:var(--border);}

/* ── Banner ── */
.banner{
  display:flex; align-items:center; gap:12px; padding:10px 20px;
  font-size:13px; border-bottom:1px solid var(--border);
}
.banner.update{background:var(--accent-soft); color:var(--accent);}
.banner.firmware{background:var(--warning-soft); color:var(--warning);}
.banner.security{background:var(--danger-soft); color:var(--danger);}
.banner b{font-weight:700;}
.banner .spacer{flex:1;}
.banner button{
  border:none; border-radius:8px; padding:6px 12px; font-size:12.5px; font-weight:700;
  cursor:pointer;
}
.banner.update button{background:var(--accent); color:var(--accent-ink);}
.banner.firmware button{background:var(--warning); color:#2A1B00;}
.banner.security button{background:var(--danger); color:#fff;}
.banner .ghost{background:transparent !important; color:inherit !important; font-weight:600;}

/* ── Content ── */
.content{max-width:760px;width:100%;margin:0 auto;padding:22px 20px 100px;flex:1;}
.summary{
  display:flex; align-items:center; gap:8px; flex-wrap:wrap;
  font-size:12.5px; color:var(--muted); margin-bottom:16px;
}
.summary strong{color:var(--text);}
.summary .link-btn{
  background:none;border:none;color:var(--accent);font-weight:700;
  font-size:12.5px;cursor:pointer;padding:0;
}

.tile-grid{
  display:grid; grid-template-columns:repeat(auto-fill,minmax(152px,1fr));
  gap:12px;
}
.tile{
  background:var(--surface); border:2px solid var(--text); border-radius:16px;
  padding:14px; box-shadow:var(--shadow); cursor:pointer; text-align:left;
  transition:transform .12s ease; font:inherit; color:inherit;
  display:flex; flex-direction:column; min-height:128px;
}
.tile:hover{transform:translateY(-2px);}
.tile:focus-visible{outline:2px solid var(--accent); outline-offset:2px;}
.tile.empty{
  background:transparent; border:2px solid var(--border); box-shadow:none;
  align-items:center; justify-content:center; gap:5px; color:var(--muted);
}
.tile.empty .plus{font-size:26px;line-height:1;color:var(--muted);font-weight:700;}
.tile.empty .idx{font-family:var(--font-mono);font-size:14px;font-weight:700;}
.tile .idx-row{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;}
.tile .idx{font-family:var(--font-mono);font-size:13px;font-weight:700;color:var(--muted);}
.tile .pin{display:block;font-size:12px;font-weight:600;color:var(--muted);opacity:.85;}
.tile .cat-dot{width:8px;height:8px;border-radius:50%;margin-top:3px;flex-shrink:0;}
.tile h4{
  margin:0; font-family:var(--font-display); font-weight:800; font-size:19px;
  line-height:1.25; overflow:hidden; text-overflow:ellipsis; display:-webkit-box;
  -webkit-line-clamp:2; -webkit-box-orient:vertical;
}
.tile .cmd-chip{
  align-self:flex-start; margin-top:auto; padding-top:8px;
}
.tile .cmd-chip span{
  font-size:13px; font-weight:800; padding:4px 10px; border-radius:999px;
  background:var(--accent-soft); color:var(--accent);
}

/* ── Bottombar ── */
.bottombar{
  position:sticky; bottom:0; z-index:20; background:var(--surface);
  border-top:1px solid var(--border);
  display:flex; align-items:center; gap:12px; padding:12px 20px;
}
.bottombar .spacer{flex:1;}
.btn{
  border:none; border-radius:10px; padding:10px 16px; font-weight:700; font-size:13px;
  cursor:pointer;
}
.btn.primary{background:var(--accent); color:var(--accent-ink);}
.btn.primary:hover{background:var(--accent-strong);}
.btn.secondary{background:var(--surface-alt); color:var(--text); border:1px solid var(--border);}
.btn.secondary:hover{background:var(--border);}
.btn:disabled{opacity:.55;cursor:default;}

/* ── Overlay / Drawer / Modal ── */
.overlay{
  position:fixed; inset:0; background:rgba(10,15,12,.4);
  opacity:0; pointer-events:none; transition:opacity .15s ease; z-index:40;
}
.overlay.show{opacity:1;pointer-events:auto;}

.drawer{
  position:fixed; top:0; right:0; bottom:0; width:340px; max-width:88vw;
  background:var(--surface); border-left:1px solid var(--border);
  transform:translateX(100%); transition:transform .18s ease; z-index:41;
  display:flex; flex-direction:column;
}
.drawer.show{transform:translateX(0);}
.drawer-head{
  display:flex;align-items:center;gap:10px;padding:16px 18px;
  border-bottom:1px solid var(--border);
}
.drawer-head h3{margin:0;font-family:var(--font-display);font-size:15px;flex:1;}
.drawer-body{padding:18px;overflow-y:auto;flex:1;display:flex;flex-direction:column;gap:20px;}
.field-group label{
  display:block;font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.04em;color:var(--muted);margin-bottom:6px;
}
.field-group input, .esp-row input{
  width:100%;padding:9px 10px;border:1px solid var(--border);border-radius:9px;
  background:var(--surface-alt);color:var(--text);font-family:var(--font-mono);font-size:12.5px;
}
.field-group input:focus, .esp-row input:focus{outline:2px solid var(--accent);outline-offset:-1px;}
.field-group + .field-group{margin-top:10px;}
.remember-row{
  display:flex; align-items:center; gap:8px; margin-top:12px;
  font-size:12.5px; color:var(--text); cursor:pointer;
}
.remember-row input{accent-color:var(--accent); width:15px; height:15px; cursor:pointer;}
.section-title{
  font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;
  color:var(--muted);margin-bottom:10px;
}
.esp-row{display:flex;gap:8px;align-items:center;}
.esp-row input{flex:1;width:auto;}
.esp-status-line{font-size:12px;color:var(--muted);margin-top:8px;}

/* ── Tile-Edit-Modal ── */
.modal{
  position:fixed; top:50%; left:50%; transform:translate(-50%,-46%);
  width:420px; max-width:90vw; max-height:82vh;
  background:var(--surface); border-radius:18px; box-shadow:var(--shadow);
  z-index:42; display:none; flex-direction:column; overflow:hidden;
}
.modal.show{display:flex;}
.modal-head{padding:18px 20px 10px;}
.modal-head h3{margin:0;font-family:var(--font-display);font-size:16px;}
.modal-head .pin-note{font-family:var(--font-mono);font-size:11px;color:var(--muted);margin-top:2px;}
/* Bugfix: #modalHasDevices war ein normaler Block ohne eigenen Flex-Kontext,
   wodurch .modal-list{flex:1} wirkungslos blieb (flex-Properties greifen nur
   bei direkten Kindern eines Flex-Containers). Die Liste wuchs dadurch
   ungebremst mit dem Geräte-Inhalt, statt sich selbst zu begrenzen/scrollen
   — bei vielen Geräten wurden cmd-picker + modal-foot (Übernehmen-Button)
   unter .modal's max-height:82vh/overflow:hidden weggeschnitten, obwohl die
   Geräteauswahl selbst (Highlight) noch funktionierte. Jetzt: eigener
   Flex-Spaltenkontext + min-height:0 (klassischer Flexbox-Fallstrick — ohne
   das bleibt die Default-min-height am Inhalt hängen und die Box wächst
   trotz flex:1 trotzdem über den verfügbaren Platz hinaus). */
#modalHasDevices{display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden;}
.modal-search{padding:0 20px 10px;}
.modal-search input{
  width:100%;padding:9px 12px;border:1px solid var(--border);border-radius:10px;
  background:var(--surface-alt);color:var(--text);font-size:13px;
}
.modal-list{overflow-y:auto;padding:0 10px 10px;flex:1;min-height:0;}
.modal-group-label{
  font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;
  color:var(--muted);padding:8px 10px 4px;
}
.modal-item{
  display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:10px;
  cursor:pointer;font-size:13px;
}
.modal-item:hover{background:var(--surface-alt);}
.modal-item.selected{background:var(--accent-soft);color:var(--accent);font-weight:600;}
.modal-item .cat-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.modal-item .type{margin-left:auto;font-size:11px;color:var(--muted);}
.modal-empty{padding:30px 20px;text-align:center;color:var(--muted);font-size:13px;}
.modal-empty button{margin-top:10px;}

.cmd-picker{padding:12px 20px;border-top:1px solid var(--border);display:none;flex-wrap:wrap;gap:6px;}
.cmd-picker.show{display:flex;}
.cmd-chip-btn{
  border:1px solid var(--border);background:var(--surface-alt);color:var(--text);
  border-radius:999px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;
}
.cmd-chip-btn.selected{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);}

.modal-foot{
  padding:14px 20px;border-top:1px solid var(--border);
  display:flex;gap:8px;align-items:center;
}
.modal-foot .spacer{flex:1;}
.link-danger{background:none;border:none;color:var(--danger);font-weight:700;font-size:12.5px;cursor:pointer;padding:6px 4px;}

/* ── Toasts ── */
#toasts{
  position:fixed; left:50%; bottom:88px; transform:translateX(-50%);
  z-index:50; display:flex; flex-direction:column; gap:8px; align-items:center;
}
.toast{
  background:var(--text); color:var(--bg); padding:10px 16px; border-radius:999px;
  font-size:12.5px; font-weight:600; box-shadow:var(--shadow);
  opacity:0; transform:translateY(6px); transition:opacity .15s ease, transform .15s ease;
  max-width:70vw;
}
.toast.show{opacity:1;transform:translateY(0);}
.toast.error{background:var(--danger);color:#fff;}
.toast.success{background:var(--success);color:#04140A;}

.hidden{display:none !important;}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-side"></div>
  <div class="topbar-center">
    <h1>SwitchBot Konfigurator</h1>
    <span class="ver" id="verTag">v__VERSION__</span>
  </div>
  <div class="topbar-side topbar-right">
    <div class="esp-pill bad" id="espPill" onclick="openDrawer()">
      <span class="dot"></span><span id="espPillText">ESP32 —</span>
    </div>
  </div>
</div>

<div id="banners"></div>

<div class="content">
  <div class="summary" id="summary">Noch keine Geräte geladen.
    <button class="link-btn" onclick="openDrawer()">Zugangsdaten eintragen →</button>
  </div>
  <div class="tile-grid" id="tileGrid"></div>
</div>

<div class="bottombar">
  <button class="icon-btn" title="Einstellungen" onclick="openDrawer()">⚙</button>
  <div class="spacer"></div>
  <button class="btn secondary" id="btnLoadFromEsp" onclick="loadFromEsp()">Laden</button>
  <button class="btn primary" id="btnTransfer" onclick="transferToEsp()">Übertragen</button>
</div>

<div class="overlay" id="drawerOverlay" onclick="closeDrawer()"></div>
<aside class="drawer" id="drawer">
  <div class="drawer-head">
    <h3>Einstellungen</h3>
    <button class="icon-btn" onclick="closeDrawer()">✕</button>
  </div>
  <div class="drawer-body">
    <div>
      <div class="section-title">API-Zugangsdaten</div>
      <div class="field-group">
        <label for="inpToken">Token</label>
        <input id="inpToken" type="text" autocomplete="off" spellcheck="false">
      </div>
      <div class="field-group">
        <label for="inpSecret">Secret</label>
        <input id="inpSecret" type="password" autocomplete="off" spellcheck="false">
      </div>
      <button class="btn primary" style="width:100%;margin-top:4px;" id="btnLoadDevices" onclick="loadDevices()">Geräte laden</button>
    </div>
    <div>
      <div class="section-title">ESP32-Verbindung</div>
      <div class="esp-row">
        <input id="inpEspIp" type="text" placeholder="192.168.x.x" autocomplete="off" spellcheck="false">
        <button class="btn secondary" id="btnConnect" onclick="discoverEsp(true)">Verbinden</button>
      </div>
      <div class="field-group" style="margin-top:10px;">
        <label for="inpEspPassword">Admin-Passwort (aktuell / bekannt)</label>
        <input id="inpEspPassword" type="password" autocomplete="off" spellcheck="false">
      </div>
      <button class="btn secondary" style="width:100%;margin-top:6px;" id="btnSetEspPassword" onclick="setupEspAdminPassword()">Auf neuem Gerät setzen</button>
      <div class="field-group" style="margin-top:10px;">
        <label for="inpEspNewPassword">Neues Admin-Passwort (Gerät hat schon eins)</label>
        <input id="inpEspNewPassword" type="password" autocomplete="off" spellcheck="false" placeholder="mind. 8 Zeichen">
      </div>
      <button class="btn secondary" style="width:100%;margin-top:6px;" id="btnChangeEspPassword" onclick="changeEspAdminPassword()">Passwort ändern</button>
      <div class="esp-status-line" id="espStatusLine">Suche automatisch…</div>
    </div>
    <label class="remember-row">
      <input type="checkbox" id="chkRemember" onchange="onRememberToggle()">
      <span>Zugangsdaten sicher speichern</span>
    </label>
    <div style="margin-top:auto;font-size:11px;color:var(--muted);display:flex;flex-direction:column;gap:6px;">
      <span id="drawerConfigPath" style="font-family:var(--font-mono);word-break:break-all;">__CONFIG_PATH__</span>
      <span>F11 — Vollbildmodus</span>
    </div>
  </div>
</aside>

<div class="overlay" id="modalOverlay" onclick="closeModal()"></div>
<div class="modal" id="modal">
  <div class="modal-head">
    <h3 id="modalTitle">Taster 1</h3>
    <div class="pin-note" id="modalPinNote">GPIO 12</div>
  </div>
  <div id="modalNoDevices" class="modal-empty hidden">
    Noch keine Geräte geladen.
    <br><button class="btn primary" onclick="closeModal();openDrawer();">Zugangsdaten öffnen</button>
  </div>
  <div id="modalHasDevices">
    <div class="modal-search">
      <input id="modalSearch" type="text" placeholder="Gerät suchen…" oninput="renderModalList()">
    </div>
    <div class="modal-list" id="modalList"></div>
    <div class="cmd-picker" id="cmdPicker"></div>
  </div>
  <div class="modal-foot">
    <button class="link-danger hidden" id="btnClearAssign" onclick="clearAssignment()">Zuweisung entfernen</button>
    <div class="spacer"></div>
    <button class="btn secondary" onclick="closeModal()">Abbrechen</button>
    <button class="btn primary" id="btnApplyAssign" onclick="applyAssignment()" disabled>Übernehmen</button>
  </div>
</div>

<div id="toasts"></div>

<script>
const PINS = __PINS_JSON__;
const CAT_LABELS = {"Device":"Geräte","IR Remote":"IR-Fernbedienungen","Scene":"Szenen"};
const CAT_DOT = {"Device":"var(--cat-device)","IR Remote":"var(--cat-ir)","Scene":"var(--cat-scene)"};

let state = {
  version: "__VERSION__",
  items: [],             // geladene Geräte/IR/Szenen
  assignments: {},        // tasterIndex -> {deviceId, command}
  espIp: "",
  espConnected: false,
  toolUpdate: null,
  fwUpdate: null,
};
let modalTaster = null;
let modalSelectedId = null;
let modalSelectedCmd = null;

function $(id){ return document.getElementById(id); }

function api(name, ...args){
  return window.pywebview.api[name](...args);
}

window.addEventListener('pywebviewready', init);

async function init(){
  const boot = await api('bootstrap');
  state.version = boot.version;
  $('verTag').textContent = 'v' + boot.version;
  $('drawerConfigPath').textContent = boot.configPath;
  renderTiles();

  const creds = await api('load_credentials');
  if (creds.ok && (creds.token || creds.secret || creds.esp_password)){
    $('inpToken').value = creds.token;
    $('inpSecret').value = creds.secret;
    $('inpEspPassword').value = creds.esp_password;
    $('chkRemember').checked = true;
  }

  await discoverEsp(false);   // muss vor checkUpdates() abgeschlossen sein,
  checkUpdates();             // sonst kennt der Firmware-Check die ESP-Version noch nicht
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'F11'){ e.preventDefault(); api('toggle_fullscreen'); }
  if (e.key === 'Escape'){ closeModal(); closeDrawer(); }
});

/* ── Kacheln ── */
function renderTiles(){
  const grid = $('tileGrid');
  grid.innerHTML = '';
  PINS.forEach((pin, i) => {
    const a = state.assignments[i];
    const tile = document.createElement('button');
    tile.className = 'tile' + (a ? '' : ' empty');
    tile.onclick = () => openModal(i);
    if (a){
      const item = state.items.find(x => x.id === a.deviceId);
      const catColor = item ? CAT_DOT[item.category] : 'var(--muted)';
      tile.innerHTML = `
        <div class="idx-row">
          <span class="idx">${String(i+1).padStart(2,'0')}<span class="pin">GPIO ${pin}</span></span>
          <span class="cat-dot" style="background:${catColor}"></span>
        </div>
        <h4>${escapeHtml(item ? item.name : a.deviceId)}</h4>
        <div class="cmd-chip"><span>${escapeHtml(a.command)}</span></div>`;
    } else {
      tile.innerHTML = `
        <span class="plus">+</span>
        <span class="idx">Taster ${i+1}</span>
        <span class="pin">GPIO ${pin}</span>`;
    }
    grid.appendChild(tile);
  });
  centerLastRow();
  updateSummary();
}

function centerLastRow(){
  // Zentriert eine unvollständige letzte Reihe (z.B. Taster 13/14 unter
  // Taster 10/11 statt linksbündig unter 9/10) — ermittelt die tatsächliche
  // Spaltenzahl live aus dem Grid, damit das auch bei Fenster-Resize korrekt
  // bleibt, statt eine feste Spaltenzahl anzunehmen.
  const grid = $('tileGrid');
  const tiles = Array.from(grid.children);
  tiles.forEach(t => t.style.gridColumnStart = '');
  const cols = getComputedStyle(grid).gridTemplateColumns.split(' ').length;
  const remainder = tiles.length % cols;
  if (remainder === 0 || cols <= 1) return;
  const offset = Math.floor((cols - remainder) / 2);
  tiles.slice(tiles.length - remainder).forEach((tile, idx) => {
    tile.style.gridColumnStart = offset + idx + 1;
  });
}

let _resizeTimer = null;
window.addEventListener('resize', () => {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(centerLastRow, 120);
});

function updateSummary(){
  const n = Object.keys(state.assignments).length;
  const el = $('summary');
  if (state.items.length === 0){
    el.innerHTML = 'Noch keine Geräte geladen. <button class="link-btn" onclick="openDrawer()">Zugangsdaten eintragen →</button>';
    return;
  }
  const c = state.counts || {device:0, ir:0, scene:0};
  el.innerHTML = `<strong>${state.items.length}</strong> geladen (${c.device} Geräte · ${c.ir} IR · ${c.scene} Szenen) &nbsp;·&nbsp; <strong>${n}/14</strong> Taster belegt`;
}

/* ── Einstellungen-Drawer ── */
function openDrawer(){ $('drawer').classList.add('show'); $('drawerOverlay').classList.add('show'); }
function closeDrawer(){ $('drawer').classList.remove('show'); $('drawerOverlay').classList.remove('show'); }

async function loadDevices(){
  const token = $('inpToken').value;
  const secret = $('inpSecret').value;
  const btn = $('btnLoadDevices');
  btn.disabled = true; btn.textContent = 'Lade…';
  const res = await api('load_devices', token, secret);
  btn.disabled = false; btn.textContent = 'Geräte laden';
  if (!res.ok){ showToast('error', res.error); return; }
  state.items = res.items;
  state.counts = res.counts;
  updateSummary();
  renderTiles();
  showToast('success', `${res.items.length} Einträge geladen`);
  if ($('chkRemember').checked) api('save_credentials', token, secret, $('inpEspPassword').value);
}

/* ── Zugangsdaten lokal verschlüsselt speichern ── */
async function onRememberToggle(){
  if ($('chkRemember').checked){
    const token = $('inpToken').value, secret = $('inpSecret').value, espPw = $('inpEspPassword').value;
    if (token || secret || espPw) await api('save_credentials', token, secret, espPw);
  } else {
    await api('clear_credentials');
  }
}

async function setupEspAdminPassword(){
  if (!state.espIp){ showToast('error', 'Kein ESP32 verbunden. Bitte zuerst verbinden.'); return; }
  const pw = $('inpEspPassword').value;
  if (pw.length < 8){ showToast('error', 'Admin-Passwort muss mindestens 8 Zeichen haben.'); return; }
  const btn = $('btnSetEspPassword');
  btn.disabled = true; btn.textContent = 'Setze…';
  const res = await api('setup_esp_admin_password', state.espIp, pw);
  btn.disabled = false; btn.textContent = 'Auf neuem Gerät setzen';
  if (!res.ok){ showToast('error', res.error); return; }
  showToast('success', 'Admin-Passwort auf dem ESP32 gesetzt.');
  if ($('chkRemember').checked) api('save_credentials', $('inpToken').value, $('inpSecret').value, pw);
}

async function changeEspAdminPassword(){
  if (!state.espIp){ showToast('error', 'Kein ESP32 verbunden. Bitte zuerst verbinden.'); return; }
  const oldPw = $('inpEspPassword').value;
  const newPw = $('inpEspNewPassword').value;
  if (!oldPw){ showToast('error', 'Aktuelles Admin-Passwort oben eintragen.'); return; }
  if (newPw.length < 8){ showToast('error', 'Neues Admin-Passwort muss mindestens 8 Zeichen haben.'); return; }
  const btn = $('btnChangeEspPassword');
  btn.disabled = true; btn.textContent = 'Ändere…';
  const res = await api('change_esp_admin_password', state.espIp, oldPw, newPw);
  btn.disabled = false; btn.textContent = 'Passwort ändern';
  if (!res.ok){ showToast('error', res.error); return; }
  showToast('success', 'Admin-Passwort geändert.');
  // Ab jetzt gilt das neue Passwort — Feld oben aktualisieren, damit alle
  // weiteren signierten Anfragen (Upload/OTA/Laden) automatisch damit
  // signieren, sowie das jetzt leere "Neues Passwort"-Feld zurücksetzen.
  $('inpEspPassword').value = newPw;
  $('inpEspNewPassword').value = '';
  if ($('chkRemember').checked) api('save_credentials', $('inpToken').value, $('inpSecret').value, newPw);
}

/* ── ESP32 ── */
async function discoverEsp(manual){
  const btn = $('btnConnect');
  $('espStatusLine').textContent = 'Suche…';
  if (manual){ btn.disabled = true; btn.textContent = 'Sucht…'; }
  const manualIp = manual ? $('inpEspIp').value : '';
  const res = await api('discover_esp', manualIp);
  if (manual){ btn.disabled = false; btn.textContent = 'Verbinden'; }
  const pill = $('espPill');
  if (res.ok){
    state.espIp = res.ip; state.espConnected = true;
    $('inpEspIp').value = res.ip;
    $('espStatusLine').textContent = `Gefunden · ${res.buttons}/14 Taster · FW v${res.fw}`;
    pill.classList.remove('bad'); pill.classList.add('ok');
    $('espPillText').textContent = 'ESP32 verbunden';
    renderDefaultPasswordBanner(!!res.defaultPass);
    checkUpdates();   // jetzt ist die ESP-Firmware-Version bekannt — Banner ggf. nachziehen
  } else {
    state.espConnected = false;
    $('espStatusLine').textContent = 'Nicht gefunden – IP manuell eintragen und "Verbinden" klicken.';
    pill.classList.remove('ok'); pill.classList.add('bad');
    $('espPillText').textContent = 'ESP32 nicht gefunden';
    renderDefaultPasswordBanner(false);
  }
}

/* main.cpp Änderung #20: solange das aus der Chip-ID abgeleitete Werks-
   Standardpasswort noch aktiv ist, sperrt die Firmware /upload, /ota,
   /config, /setcreds mit 403 — hier proaktiv warnen, bevor der Nutzer erst
   auf diesen Fehler läuft. */
function renderDefaultPasswordBanner(show){
  const existing = document.getElementById('bannerDefaultPass');
  if (!show){ if (existing) existing.remove(); return; }
  if (existing) return;
  const b = document.createElement('div');
  b.id = 'bannerDefaultPass';
  b.className = 'banner security';
  b.innerHTML = `<span>ESP32 läuft noch mit dem <b>Werks-Standardpasswort</b> — Übertragen/Laden/Flashen sind gesperrt, bis ein eigenes Admin-Passwort gesetzt ist.</span>
    <div class="spacer"></div>
    <button onclick="openDrawer()">Jetzt ändern</button>`;
  $('banners').appendChild(b);
}

/* ── Updates ── */
async function checkUpdates(){
  const res = await api('check_updates');
  const box = $('banners');
  box.innerHTML = '';
  if (res.tool){
    state.toolUpdate = res.tool;
    const b = document.createElement('div');
    b.className = 'banner update';
    // Versionsstrings kommen aus der GitHub-Dateiliste — vor dem Einsetzen in
    // innerHTML escapen, sonst könnte eine kompromittierte Quelle beliebiges
    // JS einschleusen, das dann vollen Zugriff auf window.pywebview.api hätte.
    b.innerHTML = `<span>Tool-Update <b>v${escapeHtml(res.tool.version)}</b> verfügbar (aktuell v${escapeHtml(state.version)})</span>
      <div class="spacer"></div>
      <button onclick="applyToolUpdate(this)">Jetzt aktualisieren</button>
      <button class="ghost" onclick="this.parentElement.remove()">Später</button>`;
    box.appendChild(b);
  }
  if (res.firmware){
    state.fwUpdate = res.firmware;
    const b = document.createElement('div');
    b.className = 'banner firmware';
    // res.firmware.current stammt aus der /status-Antwort des ESP32 über
    // unauthentifiziertes HTTP im lokalen Netz — ebenfalls escapen, damit ein
    // gespooftes Gerät im selben WLAN kein Skript einschleusen kann.
    const txt = `Neue ESP32-Firmware <b>v${escapeHtml(res.firmware.version)}</b> verfügbar (aktuell v${escapeHtml(res.firmware.current)})`;
    b.innerHTML = `<span>${txt}</span><div class="spacer"></div>
      <button onclick="flashFirmware(this)">Jetzt flashen</button>
      <button class="ghost" onclick="this.parentElement.remove()">Später</button>`;
    box.appendChild(b);
  }
}

async function applyToolUpdate(btn){
  btn.textContent = 'Aktualisiere…'; btn.disabled = true;
  const res = await api('apply_tool_update', state.toolUpdate.version, state.toolUpdate.sha);
  if (res && !res.ok){
    if (res.sourceMode){
      // Self-Update funktioniert nur in der kompilierten Binary (sys.frozen),
      // nicht im Quellcode-Betrieb — statt Toast+Reset (wirkt wie ein Loop bei
      // wiederholtem Klicken) den Banner dauerhaft durch einen klaren Hinweis
      // ersetzen, da ein erneuter Klick hier nie zum Erfolg führen kann.
      const banner = btn.closest('.banner');
      if (banner){
        banner.innerHTML = `<span>Läuft im Quellcode-Modus — Self-Update nicht verfügbar. Bitte die kompilierte Version nutzen oder manuell aktualisieren.</span>`;
      }
      return;
    }
    showToast('error', res.error);
    btn.textContent = 'Jetzt aktualisieren'; btn.disabled = false;
  }
  // bei Erfolg beendet sich der Prozess selbst (Neustart) — kein UI-Update nötig
}

async function flashFirmware(btn){
  if (btn.dataset.confirm !== '1'){
    btn.dataset.confirm = '1';
    btn.textContent = 'Wirklich flashen?';
    setTimeout(() => { btn.dataset.confirm = '0'; btn.textContent = 'Jetzt flashen'; }, 4000);
    return;
  }
  btn.textContent = 'Flashe…'; btn.disabled = true;
  const res = await api('flash_firmware', state.espIp, state.fwUpdate.version, state.fwUpdate.url, state.fwUpdate.sha, $('inpEspPassword').value);
  if (res.ok){
    showToast('success', 'Firmware geflasht — ESP32 startet neu.');
    btn.closest('.banner').remove();
  } else {
    showToast('error', res.error);
    btn.textContent = 'Jetzt flashen'; btn.disabled = false;
  }
}

/* ── Taster-Modal ── */
function openModal(i){
  modalTaster = i;
  modalSelectedId = null;
  modalSelectedCmd = null;
  const a = state.assignments[i];
  if (a){ modalSelectedId = a.deviceId; modalSelectedCmd = a.command; }

  $('modalTitle').textContent = 'Taster ' + (i+1);
  $('modalPinNote').textContent = 'GPIO ' + PINS[i];
  $('modalSearch').value = '';
  $('btnClearAssign').classList.toggle('hidden', !a);

  if (state.items.length === 0){
    $('modalNoDevices').classList.remove('hidden');
    $('modalHasDevices').classList.add('hidden');
  } else {
    $('modalNoDevices').classList.add('hidden');
    $('modalHasDevices').classList.remove('hidden');
    renderModalList();
    renderCmdPicker();
  }
  updateApplyState();
  $('modal').classList.add('show');
  $('modalOverlay').classList.add('show');
}

function closeModal(){
  $('modal').classList.remove('show');
  $('modalOverlay').classList.remove('show');
  modalTaster = null;
}

function renderModalList(){
  const q = $('modalSearch').value.trim().toLowerCase();
  const list = $('modalList');
  list.innerHTML = '';
  ['Device','IR Remote','Scene'].forEach(cat => {
    const items = state.items.filter(x => x.category === cat &&
      x.name.toLowerCase().includes(q));
    if (items.length === 0) return;
    const label = document.createElement('div');
    label.className = 'modal-group-label';
    label.textContent = CAT_LABELS[cat];
    list.appendChild(label);
    items.forEach(item => {
      const row = document.createElement('div');
      row.className = 'modal-item' + (item.id === modalSelectedId ? ' selected' : '');
      row.innerHTML = `<span class="cat-dot" style="background:${CAT_DOT[cat]}"></span>
        <span>${escapeHtml(item.name)}</span><span class="type">${escapeHtml(item.type)}</span>`;
      row.onclick = () => selectDevice(item.id);
      list.appendChild(row);
    });
  });
  if (!list.innerHTML){
    list.innerHTML = '<div class="modal-empty">Keine Treffer.</div>';
  }
}

function selectDevice(id){
  modalSelectedId = id;
  const item = state.items.find(x => x.id === id);
  const cmds = item.commands || [];
  if (!cmds.includes(modalSelectedCmd)) modalSelectedCmd = cmds[0] || null;
  renderModalList();
  renderCmdPicker();
  updateApplyState();
}

function renderCmdPicker(){
  const picker = $('cmdPicker');
  const item = state.items.find(x => x.id === modalSelectedId);
  if (!item){ picker.classList.remove('show'); picker.innerHTML=''; return; }
  picker.classList.add('show');
  picker.innerHTML = (item.commands || []).map(cmd =>
    `<button class="cmd-chip-btn${cmd===modalSelectedCmd?' selected':''}" onclick="selectCommand('${cmd}')">${cmd}</button>`
  ).join('');
}

function selectCommand(cmd){
  modalSelectedCmd = cmd;
  renderCmdPicker();
  updateApplyState();
}

function updateApplyState(){
  $('btnApplyAssign').disabled = !(modalSelectedId && modalSelectedCmd);
}

function applyAssignment(){
  if (!(modalSelectedId && modalSelectedCmd)) return;
  state.assignments[modalTaster] = { deviceId: modalSelectedId, command: modalSelectedCmd,
    taster: modalTaster+1, pin: PINS[modalTaster] };
  closeModal();
  renderTiles();
}

function clearAssignment(){
  delete state.assignments[modalTaster];
  closeModal();
  renderTiles();
}

/* ── Laden / Übertragen ── */
function buildAssignmentList(){
  return Object.values(state.assignments);
}

async function transferToEsp(){
  const token = $('inpToken').value, secret = $('inpSecret').value;
  const btn = $('btnTransfer');
  btn.disabled = true; btn.textContent = 'Speichere…';
  const saveRes = await api('save_config', token, secret, buildAssignmentList());
  if (!saveRes.ok){
    showToast('error', saveRes.error);
    btn.disabled = false; btn.textContent = 'Übertragen';
    return;
  }
  if (!state.espIp){
    showToast('error', 'Kein ESP32 verbunden. Bitte zuerst in den Einstellungen verbinden.');
    btn.disabled = false; btn.textContent = 'Übertragen';
    return;
  }
  btn.textContent = 'Übertrage…';
  const upRes = await api('upload_config', state.espIp, saveRes.config, $('inpEspPassword').value);
  btn.disabled = false; btn.textContent = 'Übertragen';
  if (!upRes.ok){ showToast('error', upRes.error); return; }
  showToast('success', 'Auf ESP32 übertragen');
}

async function loadFromEsp(){
  if (!state.espIp){ showToast('error', 'Kein ESP32 verbunden. Bitte zuerst in den Einstellungen verbinden.'); return; }
  const btn = $('btnLoadFromEsp');
  btn.disabled = true; btn.textContent = 'Lade…';
  const res = await api('load_from_esp', state.espIp, $('inpEspPassword').value);
  btn.disabled = false; btn.textContent = 'Laden';
  if (!res.ok){ showToast('error', res.error); return; }

  const cfg = res.config;
  if (cfg.api_token)  $('inpToken').value = cfg.api_token;
  if (cfg.api_secret) $('inpSecret').value = cfg.api_secret;
  if ($('chkRemember').checked) api('save_credentials', $('inpToken').value, $('inpSecret').value, $('inpEspPassword').value);

  state.assignments = {};
  (cfg.devices || []).forEach(d => {
    const idx = d.taster - 1;
    state.assignments[idx] = { deviceId: d.deviceId, command: d.command, taster: d.taster, pin: d.pin };
    // Gerät kennen wir evtl. noch nicht (falls "Geräte laden" noch nicht
    // lief) — minimalen Eintrag ergänzen, damit die Kachel Namen/Kategorie
    // zeigen kann. "Geräte laden" ersetzt state.items später vollständig
    // und bringt dann auch die echte Befehlsliste zum Weiterbearbeiten mit.
    if (!state.items.find(x => x.id === d.deviceId)){
      const catLabel = d.category === 'Scene' ? 'Szene' : d.category === 'IR Remote' ? 'IR' : 'Gerät';
      state.items.push({
        id: d.deviceId, name: d.deviceName, type: d.deviceType, category: d.category,
        label: `[${catLabel}] ${d.deviceName}`, commands: [],
      });
    }
  });
  renderTiles();
  showToast('success', `${(cfg.devices || []).length} Taster vom ESP32 geladen`);
}

/* ── Toasts ── */
function showToast(type, msg){
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  $('toasts').appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 200);
  }, 4000);
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
</script>
</body>
</html>
"""

PAGE_HTML = (PAGE_HTML
    .replace("__VERSION__", VERSION)
    .replace("__PINS_JSON__", json.dumps(PINS))
    .replace("__CONFIG_PATH__", CONFIG_PATH))


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════
def main():
    api = Api()
    window = webview.create_window(
        f"SwitchBot Konfigurator v{VERSION}",
        html=PAGE_HTML,
        js_api=api,
        width=900, height=760,
        min_size=(480, 560),
        background_color="#10151C",
    )
    api.window = window
    webview.start()

if __name__ == "__main__":
    main()
