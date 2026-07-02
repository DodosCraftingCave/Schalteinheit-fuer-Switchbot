#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwitchBot Konfigurator
Version: 1.0
GitHub:  https://github.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, sys, threading, time, hmac, hashlib, base64, uuid
import urllib.request, urllib.error, socket, subprocess

# ════════════════════════════════════════════════════════════════
#  KONSTANTEN
# ════════════════════════════════════════════════════════════════
VERSION          = "1.1"
GITHUB_RAW       = "https://raw.githubusercontent.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/main"
GITHUB_API       = "https://api.github.com/repos/DodosCraftingCave/Schalteinheit-fuer-Switchbot/contents"
MDNS_HOST        = "controller-for-switchbot.local"
ESP_FALLBACK_IP  = ""   # wird automatisch befüllt
CONFIG_PATH      = os.path.join(os.path.expanduser("~"), "Desktop", "config.json")
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
#  HILFSFUNKTIONEN
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
        items.append({"label":    f"[Gerät] {d['deviceName']}",
                      "name":     d["deviceName"], "id": d["deviceId"],
                      "type":     d["deviceType"],  "category": "Device"})
    for ir in body.get("infraredRemoteList", []):
        items.append({"label":    f"[IR] {ir['deviceName']}",
                      "name":     ir["deviceName"], "id": ir["deviceId"],
                      "type":     ir.get("remoteType","Others"), "category": "IR Remote"})
    res_s = requests.get("https://api.switch-bot.com/v1.1/scenes",
                         headers=headers, timeout=10)
    res_s.raise_for_status()
    for s in res_s.json().get("body", []):
        items.append({"label":    f"[Szene] {s['sceneName']}",
                      "name":     s["sceneName"], "id": s["sceneId"],
                      "type":     "Scene", "category": "Scene"})
    return items

def get_commands(item):
    if item["category"] == "Scene":      return ["execute"]
    if item["category"] == "IR Remote":  return IR_COMMANDS.get(item["type"], FALLBACK_COMMANDS)
    return DEVICE_COMMANDS.get(item["type"], FALLBACK_COMMANDS)

def github_get(path):
    """Lädt eine Datei vom GitHub-Repo als String."""
    url = f"{GITHUB_RAW}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return r.read().decode()

def resolve_esp_ip():
    """
    Versucht controller-for-switchbot.local aufzulösen.
    Gibt IP-String zurück oder '' wenn nicht gefunden.
    """
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

def esp_upload_config(ip, config_dict):
    """Lädt config.json direkt per HTTP auf den ESP hoch."""
    import requests
    data = json.dumps(config_dict, indent=2, ensure_ascii=False).encode("utf-8")
    files = {"data": ("config.json", data, "application/json")}
    r = requests.post(f"http://{ip}/upload", files=files, timeout=15)
    return r.text

def esp_flash_firmware(ip, bin_data):
    """Flasht firmware.bin per HTTP OTA auf den ESP.
    Änderung: Timeout von 120s auf 300s erhöht (kann bei langsamem WLAN
    knapp werden), Aufruf-Signatur bereinigt (progress_cb wurde nie
    genutzt)."""
    import requests
    files = {"data": ("firmware.bin", bin_data, "application/octet-stream")}
    r = requests.post(f"http://{ip}/ota", files=files, timeout=300)
    return r.text

def validate_firmware_binary(data):
    """Prüft ob die heruntergeladene Datei plausibel eine gültige
    ESP32-Firmware ist, bevor geflasht wird. Verhindert dass z.B. eine
    GitHub-404-HTML-Seite versehentlich als 'Firmware' geflasht wird.
    Gültige ESP32-Firmware-Images beginnen mit dem Magic-Byte 0xE9."""
    if len(data) < 100_000:
        return False, f"Datei zu klein ({len(data)} Bytes) – keine gültige Firmware."
    if data[0] != 0xE9:
        return False, "Datei beginnt nicht mit dem ESP32-Firmware-Magic-Byte (0xE9)."
    return True, ""


# ════════════════════════════════════════════════════════════════
#  AUTO-UPDATE
# ════════════════════════════════════════════════════════════════
def parse_version(v):
    """Wandelt Versionsstrings wie '1.0' oder '0.8_beta' in ein Tuple zum Vergleichen um.
    Änderung: Zahlenteile werden auf eine feste Länge aufgefüllt (mit Nullen),
    damit z.B. '1.0' und '1.0.0' korrekt als GLEICHWERTIG erkannt werden.
    Vorher wurde eine kürzere Zahlenfolge durch reinen Tuple-Längen-Vergleich
    fälschlich als 'kleiner' gewertet, selbst wenn die Version identisch war."""
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
    """
    Sucht neueste switchbot_config_v*.py auf GitHub (mit oder ohne _beta-Suffix).
    Gibt (neue_version, download_url) zurück oder (None, None).
    """
    try:
        # Änderung: Datei liegt im tool/-Unterordner, nicht im Repo-Root —
        # vorher wurde immer im Root gesucht und nie etwas gefunden, seit
        # die Struktur auf tool/ + firmware/ umgestellt wurde.
        files = github_list("tool")
        candidates = []
        for f in files:
            name = f["name"]
            if name.startswith("switchbot_config_v") and name.endswith(".py"):
                ver = name.replace("switchbot_config_v","").replace(".py","")
                candidates.append((parse_version(ver), ver, f["download_url"]))
        if not candidates:
            return None, None
        candidates.sort(reverse=True)
        best_ver = candidates[0][1]
        best_url = candidates[0][2]
        if parse_version(best_ver) > parse_version(VERSION):
            return best_ver, best_url
    except Exception:
        pass
    return None, None

def check_firmware_update():
    """
    Sucht neueste firmware_v*.bin im firmware/-Ordner auf GitHub (mit oder ohne _beta-Suffix).
    Gibt (neue_version, download_url) zurück oder (None, None).
    """
    try:
        files = github_list("firmware")
        candidates = []
        for f in files:
            name = f["name"]
            if name.startswith("firmware_v") and name.endswith(".bin"):
                ver = name.replace("firmware_v","").replace(".bin","")
                candidates.append((parse_version(ver), ver, f["download_url"]))
        if not candidates:
            return None, None
        candidates.sort(reverse=True)
        best_ver = candidates[0][1]
        best_url = candidates[0][2]
        return best_ver, best_url
    except Exception:
        return None, None

def do_tool_self_update(app, new_version):
    """
    Lädt die fertig gebaute App-Binary von GitHub herunter (gebaut von
    GitHub Actions) und ersetzt die aktuell laufende Datei.
    Kein lokales pip/pyinstaller mehr nötig – funktioniert beim Kunden
    ohne jegliche Python-Installation.

    Im Quellcode-Betrieb (python3 switchbot_config_v...py, nicht als
    Binary gebaut) wird nur eine Info-Meldung angezeigt, da es dort
    keine "laufende Binary" zum Ersetzen gibt.

    Änderung: Nimmt jetzt eine App-Referenz entgegen, damit alle
    messagebox-Aufrufe über app.after() sicher auf dem Main-Thread
    laufen — vorher wurden sie direkt aus dem Update-Hintergrundthread
    aufgerufen, was bei Tkinter zu Freezes/Abstürzen führen kann.
    """
    if not getattr(sys, "frozen", False):
        app.after(0, lambda: messagebox.showinfo("Update verfügbar",
            f"Neue Version v{new_version} verfügbar.\n\n"
            f"Das Tool läuft gerade aus dem Quellcode (nicht als Programm).\n"
            f"Bitte die neue Version manuell von GitHub laden."))
        return

    try:
        import shutil
        import platform as _platform

        is_windows = _platform.system() == "Windows"
        app_name   = "SwitchBot-Konfigurator.exe" if is_windows else "SwitchBot-Konfigurator"
        url        = f"{GITHUB_RAW}/tool/{app_name}"
        exe_path   = sys.executable
        tmp_path   = exe_path + ".new"

        req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
        with urllib.request.urlopen(req, timeout=30) as r, open(tmp_path, "wb") as out:
            shutil.copyfileobj(r, out)

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
            subprocess.Popen(["cmd", "/c", bat_path],
                              creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)
        else:
            # Linux erlaubt das Ersetzen einer laufenden ausführbaren Datei direkt
            os.chmod(tmp_path, 0o755)
            os.replace(tmp_path, exe_path)
            os.execv(exe_path, [exe_path])
    except Exception as e:
        err = str(e)
        app.after(0, lambda: messagebox.showerror("Update-Fehler", err))


# ════════════════════════════════════════════════════════════════
#  HAUPT-APP
# ════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"SwitchBot Konfigurator  v{VERSION}")
        self.resizable(False, False)
        self.configure(bg="#00688B")

        self.all_items   = []
        self.dev_cbs     = []
        self.cmd_cbs     = []
        self.dev_vars    = []
        self.cmd_vars    = []
        self.esp_ip      = tk.StringVar(value="")
        self.esp_current_fw = None  # tatsächlich installierte ESP-Firmware-Version (aus /status)
        self.fw_update     = None   # neue FW-Version falls verfügbar
        self.fw_update_url = None   # Download-URL der neuen Firmware

        self._build()

        # Änderung #14: Auto-Update + ESP-Discovery beim Start im Hintergrund
        threading.Thread(target=self._startup_checks, daemon=True).start()

    # ── UI-Aufbau ────────────────────────────────────────────────
    def _build(self):
        BG     = "#00688B"
        PANEL  = "#005575"
        ACCENT = "#E63946"
        TEXT   = "#FFFFFF"
        MUTED  = "#CFE8F0"
        INPUT  = "#004358"
        GREEN  = "#2ECC71"
        ORANGE = "#F4A300"
        BORDER = "#2E86AB"

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox",
            fieldbackground=INPUT, background=INPUT,
            foreground=TEXT, selectbackground=ACCENT,
            arrowcolor=ACCENT, bordercolor=BORDER)
        style.map("TCombobox", fieldbackground=[("readonly", INPUT)])

        # ── Kopf ──
        hdr = tk.Frame(self, bg=ACCENT, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SwitchBot Konfigurator",
                 font=("Segoe UI",15,"bold"), bg=ACCENT, fg="white").pack()
        tk.Label(hdr, text=f"v{VERSION}  ·  ESP32 14-Taster-Matrix",
                 font=("Segoe UI",9), bg=ACCENT, fg="#FFE0E0").pack()

        # ── Firmware-Update Banner (initial versteckt) ──
        self.fw_banner = tk.Frame(self, bg=ORANGE, pady=6)
        self.fw_banner_lbl = tk.Label(self.fw_banner,
            text="", bg=ORANGE, fg="#3D2400",
            font=("Segoe UI",9,"bold"))
        self.fw_banner_lbl.pack(side="left", padx=12)
        self.fw_flash_btn = tk.Button(self.fw_banner,
            text="🔄 Jetzt flashen", bg="#C27C00", fg="white",
            font=("Segoe UI",9,"bold"), relief="flat", cursor="hand2",
            command=self._flash_firmware)
        self.fw_flash_btn.pack(side="right", padx=12)
        # Banner erst anzeigen wenn Update da

        # ── API-Zugangsdaten ──
        cred = tk.LabelFrame(self, text=" API Zugangsdaten ",
                             bg=PANEL, fg=MUTED, font=("Segoe UI",9),
                             bd=1, relief="solid")
        cred.pack(fill="x", padx=14, pady=(12,4))
        for row_i, (lbl, attr, show) in enumerate([
            ("Token:",  "ent_token",  ""),
            ("Secret:", "ent_secret", "•"),
        ]):
            tk.Label(cred, text=lbl, bg=PANEL, fg=MUTED,
                     font=("Segoe UI",9), width=8, anchor="w").grid(
                row=row_i, column=0, padx=(8,4), pady=4, sticky="w")
            e = tk.Entry(cred, show=show, bg=INPUT, fg=TEXT,
                         insertbackground=TEXT, relief="flat",
                         font=("Consolas",10), width=52,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT)
            e.grid(row=row_i, column=1, padx=(0,8), pady=4, sticky="ew")
            setattr(self, attr, e)
        cred.columnconfigure(1, weight=1)

        # ── ESP32 Verbindung ──
        esp_frm = tk.LabelFrame(self, text=" ESP32 Verbindung ",
                                bg=PANEL, fg=MUTED, font=("Segoe UI",9),
                                bd=1, relief="solid")
        esp_frm.pack(fill="x", padx=14, pady=4)

        tk.Label(esp_frm, text="IP-Adresse:", bg=PANEL, fg=MUTED,
                 font=("Segoe UI",9), width=12, anchor="w").grid(
            row=0, column=0, padx=(8,4), pady=4, sticky="w")
        esp_ip_entry = tk.Entry(esp_frm, textvariable=self.esp_ip,
                                bg=INPUT, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=("Consolas",10), width=20,
                                highlightthickness=1, highlightbackground=BORDER,
                                highlightcolor=ACCENT)
        esp_ip_entry.grid(row=0, column=1, padx=(0,4), pady=4, sticky="w")

        self.esp_status_lbl = tk.Label(esp_frm, text="⏳ Suche ESP32…",
            bg=PANEL, fg=MUTED, font=("Segoe UI",9))
        self.esp_status_lbl.grid(row=0, column=2, padx=4, sticky="w")

        tk.Button(esp_frm, text="🔍 Suchen",
            command=lambda: threading.Thread(target=self._discover_esp, daemon=True).start(),
            bg=ACCENT, fg="white", relief="flat", font=("Segoe UI",9),
            cursor="hand2", padx=8).grid(row=0, column=3, padx=(4,8), pady=4)

        # ── Aktionsbuttons ──
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=14, pady=4)

        self.scan_btn = tk.Button(btn_row, text="🔍  SwitchBot Geräte laden",
            command=self._load,
            bg=ACCENT, fg="white", activebackground="#C5303C",
            font=("Segoe UI",10,"bold"), relief="flat", cursor="hand2", pady=7)
        self.scan_btn.pack(side="left", fill="x", expand=True, padx=(0,4))

        self.upload_btn = tk.Button(btn_row, text="⬆  Direkt auf ESP laden",
            command=self._upload_to_esp,
            bg="#1F6B4C", fg=GREEN, activebackground="#27AE60",
            font=("Segoe UI",10,"bold"), relief="flat", cursor="hand2", pady=7)
        self.upload_btn.pack(side="left", fill="x", expand=True, padx=(4,0))

        self.status_lbl = tk.Label(self, text="Token + Secret eintragen, dann laden.",
            bg=BG, fg=MUTED, font=("Segoe UI",9))
        self.status_lbl.pack()

        # ── Taster-Tabelle ──
        outer = tk.LabelFrame(self, text=" Taster-Zuordnung ",
                              bg=PANEL, fg=MUTED, font=("Segoe UI",9),
                              bd=1, relief="solid")
        outer.pack(fill="both", expand=True, padx=14, pady=(8,4))

        canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0, height=380)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        tbl = tk.Frame(canvas, bg=PANEL)
        win_id = canvas.create_window((0,0), window=tbl, anchor="nw")
        tbl.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Header
        for c, (txt, w) in enumerate([("Taster",10),("Gerät",35),("Befehl",20)]):
            tk.Label(tbl, text=txt, bg=BORDER, fg=MUTED,
                     font=("Segoe UI",8,"bold"), width=w,
                     anchor="w", padx=4, pady=3).grid(
                row=0, column=c, sticky="ew", padx=1, pady=(0,2))

        # 14 Zeilen
        for i, pin in enumerate(PINS):
            row_bg = PANEL if i % 2 == 0 else "#004964"
            r = i + 1
            tk.Label(tbl, text=f"Taster {i+1}",
                     bg=row_bg, fg=TEXT,
                     font=("Segoe UI",9,"bold"),
                     width=10, anchor="w", padx=6).grid(
                row=r, column=0, sticky="ew", padx=1, pady=1)

            dev_var = tk.StringVar(value="– kein Gerät / Szene –")
            cmd_var = tk.StringVar(value="")
            self.dev_vars.append(dev_var)
            self.cmd_vars.append(cmd_var)

            dev_cb = ttk.Combobox(tbl, textvariable=dev_var,
                                  values=["– kein Gerät / Szene –"],
                                  state="readonly", width=33)
            dev_cb.grid(row=r, column=1, sticky="ew", padx=2, pady=1)
            self.dev_cbs.append(dev_cb)

            cmd_cb = ttk.Combobox(tbl, textvariable=cmd_var,
                                  values=[], state="readonly", width=18)
            cmd_cb.grid(row=r, column=2, sticky="ew", padx=2, pady=1)
            self.cmd_cbs.append(cmd_cb)

            def _on_dev(e, idx=i):
                sel  = self.dev_vars[idx].get()
                item = next((x for x in self.all_items if x["label"] == sel), None)
                if not item:
                    self.cmd_cbs[idx]["values"] = []
                    self.cmd_vars[idx].set("")
                    return
                cmds = get_commands(item)
                self.cmd_cbs[idx]["values"] = cmds
                self.cmd_vars[idx].set(cmds[0] if cmds else "")
            dev_cb.bind("<<ComboboxSelected>>", _on_dev)

        for c in range(3):
            tbl.columnconfigure(c, weight=1 if c == 1 else 0)

        # ── Speichern-Button ──
        save_row = tk.Frame(self, bg=BG)
        save_row.pack(fill="x", padx=14, pady=(4,4))

        tk.Button(save_row, text="💾  config.json auf Desktop speichern",
            command=self._save,
            bg=GREEN, fg="#04140A", activebackground="#27AE60",
            font=("Segoe UI",10,"bold"), relief="flat",
            cursor="hand2", pady=8).pack(side="left", fill="x", expand=True, padx=(0,4))

        self.save_upload_btn = tk.Button(save_row, text="💾 + ⬆  Speichern & direkt hochladen",
            command=self._save_and_upload,
            bg="#1B5E42", fg=GREEN,
            font=("Segoe UI",10,"bold"), relief="flat",
            cursor="hand2", pady=8)
        self.save_upload_btn.pack(side="left", fill="x", expand=True, padx=(4,0))

        tk.Label(self, text=f"Desktop-Pfad: {CONFIG_PATH}",
                 bg=BG, fg=MUTED, font=("Segoe UI",8)).pack(pady=(0,8))

    # ── Startup-Checks (Thread) ──────────────────────────────────
    def _startup_checks(self):
        """Läuft beim Start: Tool-Update + ESP-Discovery + FW-Check."""
        # 1. Tool-Update prüfen
        # Änderung: messagebox.askyesno lief vorher direkt in diesem
        # Hintergrund-Thread — Tkinter-Dialoge dürfen nur vom Main-Thread
        # aus aufgerufen werden. Jetzt über self.after() sicher verschoben;
        # der eigentliche Download läuft bei Bestätigung in einem weiteren
        # Thread, damit die Oberfläche währenddessen nicht einfriert.
        try:
            new_ver, dl_url = check_tool_update()
            if new_ver:
                def _prompt_tool_update():
                    ans = messagebox.askyesno("Tool-Update verfügbar",
                        f"Neue Version v{new_ver} verfügbar (aktuell v{VERSION}).\n"
                        f"Jetzt automatisch updaten?")
                    if ans:
                        threading.Thread(target=do_tool_self_update,
                                          args=(self, new_ver), daemon=True).start()
                self.after(0, _prompt_tool_update)
        except Exception:
            pass

        # 2. ESP32 suchen (setzt dabei self.esp_current_fw)
        self._discover_esp()

        # 3. Firmware-Update prüfen — Änderung: nur anzeigen wenn die
        # GitHub-Version tatsächlich neuer ist als die auf dem ESP
        # installierte Version (vorher wurde der Banner immer gezeigt,
        # sobald irgendeine Firmware im Repo lag, unabhängig vom
        # tatsächlichen Stand des Geräts).
        try:
            fw_ver, fw_url = check_firmware_update()
            if fw_ver and self.esp_current_fw:
                if parse_version(fw_ver) > parse_version(self.esp_current_fw):
                    self.fw_update = fw_ver
                    self.fw_update_url = fw_url
                    self.after(0, self._show_fw_banner, fw_ver)
            elif fw_ver and not self.esp_current_fw:
                # ESP nicht gefunden -> können nicht sicher vergleichen,
                # trotzdem informieren aber vorsichtiger formuliert
                self.fw_update = fw_ver
                self.fw_update_url = fw_url
                self.after(0, self._show_fw_banner, fw_ver, True)
        except Exception:
            pass

    def _discover_esp(self):
        """Sucht ESP32 per mDNS, setzt IP ins Feld und merkt sich die
        installierte Firmware-Version für den Update-Vergleich."""
        self.after(0, lambda: self.esp_status_lbl.config(
            text="⏳ Suche ESP32…", fg="#CFE8F0"))
        # Änderung: Timeout für mDNS-Auflösung setzen, sonst kann das unter
        # Windows ohne Bonjour/mDNS-Unterstützung sehr lange hängen bleiben.
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(4)
        try:
            ip = resolve_esp_ip()
        finally:
            socket.setdefaulttimeout(old_timeout)
        if not ip:
            # Fallback: direkt per IP aus Feld versuchen
            ip = self.esp_ip.get().strip()
        if ip:
            status = esp_get_status(ip)
            if status:
                self.esp_current_fw = status.get("fw")
                self.after(0, lambda: self.esp_ip.set(ip))
                self.after(0, lambda: self.esp_status_lbl.config(
                    text=f"✅ Gefunden · {status.get('buttons',0)}/14 Taster · "
                         f"FW v{status.get('fw','?')}",
                    fg="#2ECC71"))
                return
        self.after(0, lambda: self.esp_status_lbl.config(
            text="❌ Nicht gefunden – IP manuell eintragen", fg="#FF6B6B"))

    def _show_fw_banner(self, fw_ver, unknown_current=False):
        """Zeigt den Firmware-Update-Banner an.
        Änderung: Text korrigiert — der Flash läuft über WLAN (HTTP OTA
        an die ESP32-IP), nicht per USB. Der alte Text war schlicht falsch
        und hätte Kunden unnötig verwirrt."""
        if unknown_current:
            text = (f"⚠  Firmware v{fw_ver} verfügbar – ESP32 muss im "
                    f"Netzwerk erreichbar sein zum Prüfen/Flashen")
        else:
            text = (f"⚠  Neue ESP32-Firmware v{fw_ver} verfügbar "
                    f"(aktuell v{self.esp_current_fw}) – bereit zum Flashen")
        self.fw_banner_lbl.config(text=text)
        self.fw_banner.pack(fill="x", after=self.children.get("!frame"))

    # ── Geräte laden ─────────────────────────────────────────────
    def _load(self):
        token  = self.ent_token.get().strip()
        secret = self.ent_secret.get().strip()
        if not token or not secret:
            messagebox.showerror("Fehler", "Token und Secret ausfüllen!")
            return
        self.scan_btn.config(state="disabled", text="⏳  Lade…")
        self.status_lbl.config(text="Verbinde mit SwitchBot API…")
        self.update()
        threading.Thread(target=self._do_load, args=(token, secret), daemon=True).start()

    def _do_load(self, token, secret):
        try:
            items = fetch_all(token, secret)
            self.all_items = items
            self.after(0, self._update_dropdowns)
        except Exception as ex:
            err = str(ex)
            self.after(0, lambda: messagebox.showerror("API Fehler", err))
            self.after(0, lambda: self.scan_btn.config(
                state="normal", text="🔍  SwitchBot Geräte laden"))
            self.after(0, lambda: self.status_lbl.config(text="❌ Laden fehlgeschlagen."))

    def _update_dropdowns(self):
        labels = ["– kein Gerät / Szene –"] + [x["label"] for x in self.all_items]
        for cb in self.dev_cbs:
            cb["values"] = labels
        dev = sum(1 for x in self.all_items if x["category"]=="Device")
        ir  = sum(1 for x in self.all_items if x["category"]=="IR Remote")
        sc  = sum(1 for x in self.all_items if x["category"]=="Scene")
        self.status_lbl.config(
            text=f"✅  {dev} Geräte · {ir} IR · {sc} Szenen geladen.")
        self.scan_btn.config(state="normal", text="🔄  Erneut laden")

    # ── Config bauen ─────────────────────────────────────────────
    def _build_config(self):
        token  = self.ent_token.get().strip()
        secret = self.ent_secret.get().strip()
        if not token or not secret:
            messagebox.showerror("Fehler", "Token und Secret ausfüllen!")
            return None
        devices = []
        for i, pin in enumerate(PINS):
            sel = self.dev_vars[i].get()
            cmd = self.cmd_vars[i].get().strip()
            if sel == "– kein Gerät / Szene –" or not cmd:
                continue
            item = next((x for x in self.all_items if x["label"] == sel), None)
            if not item:
                continue
            param = "0,ff,50" if cmd == "setPosition" else "default"
            entry = {
                "taster":     i + 1,
                "pin":        pin,
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
        return {"api_token": token, "api_secret": secret, "devices": devices}

    # ── Speichern ────────────────────────────────────────────────
    def _save(self):
        cfg = self._build_config()
        if not cfg:
            return
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Gespeichert",
                f"{CONFIG_PATH}\n{len(cfg['devices'])} Taster konfiguriert.")
        except Exception as ex:
            messagebox.showerror("Fehler", str(ex))

    # ── Direkt auf ESP hochladen ─────────────────────────────────
    def _upload_to_esp(self):
        ip = self.esp_ip.get().strip()
        if not ip:
            messagebox.showerror("Fehler",
                "Keine ESP32-IP bekannt.\nBitte 'Suchen' klicken oder IP manuell eintragen.")
            return
        # Bestehende config.json laden falls vorhanden
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
        else:
            messagebox.showerror("Fehler",
                "Keine config.json auf dem Desktop gefunden.\nBitte zuerst speichern.")
            return
        # Änderung: Beide Upload-Buttons sperren, solange eine Anfrage läuft.
        # Verhindert überlappende Upload-Requests beim ESP (mehrfaches
        # schnelles Klicken konnte vorher zu korrupter config.json führen).
        self.upload_btn.config(state="disabled", text="⏳ Wird hochgeladen…")
        self.save_upload_btn.config(state="disabled")
        self.status_lbl.config(text="⏳ Lade hoch…")
        self.update()
        threading.Thread(target=self._do_upload, args=(ip, cfg), daemon=True).start()

    def _do_upload(self, ip, cfg):
        try:
            result = esp_upload_config(ip, cfg)
            self.after(0, lambda: self.status_lbl.config(
                text=f"✅ {result}"))
        except Exception as ex:
            err = str(ex)
            self.after(0, lambda: messagebox.showerror("Upload-Fehler", err))
            self.after(0, lambda: self.status_lbl.config(text="❌ Upload fehlgeschlagen."))
        finally:
            self.after(0, lambda: self.upload_btn.config(
                state="normal", text="⬆  Direkt auf ESP laden"))
            self.after(0, lambda: self.save_upload_btn.config(state="normal"))

    # ── Speichern + Hochladen kombiniert ─────────────────────────
    def _save_and_upload(self):
        cfg = self._build_config()
        if not cfg:
            return
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception as ex:
            messagebox.showerror("Fehler beim Speichern", str(ex))
            return
        ip = self.esp_ip.get().strip()
        if not ip:
            messagebox.showinfo("Gespeichert",
                f"config.json gespeichert.\nKein ESP32 gefunden – bitte manuell hochladen.")
            return
        self.upload_btn.config(state="disabled")
        self.save_upload_btn.config(state="disabled", text="⏳ Wird hochgeladen…")
        self.status_lbl.config(text="⏳ Speichere & lade hoch…")
        self.update()
        threading.Thread(target=self._do_upload, args=(ip, cfg), daemon=True).start()

    # ── Firmware flashen ─────────────────────────────────────────
    def _flash_firmware(self):
        ip = self.esp_ip.get().strip()
        if not ip:
            messagebox.showerror("Fehler",
                "ESP32 nicht gefunden.\nBitte 'Suchen' klicken oder IP manuell "
                "eintragen — der ESP32 muss im gleichen Netzwerk erreichbar sein.")
            return
        if not messagebox.askyesno("Firmware-Update",
                f"ESP32 Firmware v{self.fw_update} von GitHub flashen?\n"
                f"ESP32 IP: {ip}\n\nDer ESP32 startet nach dem Flash neu."):
            return
        self.fw_flash_btn.config(state="disabled", text="⏳ Lade firmware.bin…")
        threading.Thread(target=self._do_flash, args=(ip,), daemon=True).start()

    def _do_flash(self, ip):
        try:
            # firmware.bin von GitHub laden (exakte URL aus Dateiliste)
            url = self.fw_update_url or f"{GITHUB_RAW}/firmware/firmware_v{self.fw_update}.bin"
            req = urllib.request.Request(url, headers={"User-Agent":"SwitchBot-Tool"})
            with urllib.request.urlopen(req, timeout=30) as r:
                bin_data = r.read()

            # Änderung: Sicherheitscheck vor dem Flash — verhindert dass eine
            # fehlerhaft heruntergeladene Datei (z.B. GitHub-404-Seite statt
            # echter .bin) den ESP32 in einen unbrauchbaren Zustand bringt.
            valid, reason = validate_firmware_binary(bin_data)
            if not valid:
                self.after(0, lambda: messagebox.showerror(
                    "Ungültige Firmware", f"Flash abgebrochen: {reason}"))
                return

            self.after(0, lambda: self.fw_flash_btn.config(text="⏳ Flashe ESP32…"))
            result = esp_flash_firmware(ip, bin_data)
            self.after(0, lambda: messagebox.showinfo("Flash OK", result))
            self.after(0, lambda: self.fw_banner.pack_forget())
            self.fw_update = None
        except Exception as ex:
            err = str(ex)
            self.after(0, lambda: messagebox.showerror("Flash-Fehler", err))
        finally:
            self.after(0, lambda: self.fw_flash_btn.config(
                state="normal", text="🔄 Jetzt flashen"))


# ════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    App().mainloop()
