#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwitchBot Konfigurator
Version: 1.0.0
GitHub:  https://github.com/DEIN-USERNAME/switchbot-konfigurator
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, sys, threading, time, hmac, hashlib, base64, uuid
import urllib.request, urllib.error, socket, subprocess, tempfile

# ════════════════════════════════════════════════════════════════
#  KONSTANTEN
# ════════════════════════════════════════════════════════════════
VERSION          = "0.8_beta"
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

def esp_flash_firmware(ip, bin_data, progress_cb=None):
    """Flasht firmware.bin per HTTP OTA auf den ESP."""
    import requests
    files = {"data": ("firmware.bin", bin_data, "application/octet-stream")}
    r = requests.post(f"http://{ip}/ota", files=files, timeout=120)
    return r.text


# ════════════════════════════════════════════════════════════════
#  AUTO-UPDATE
# ════════════════════════════════════════════════════════════════
def parse_version(v):
    """Wandelt '0.8_beta' oder '1.2' in Tuple zum Vergleichen um."""
    v = v.strip().lstrip("v")
    # beta < release: beta bekommt extra -1
    is_beta = "_beta" in v
    nums = v.replace("_beta","").replace("-beta","")
    try:
        parts = [int(x) for x in nums.split(".")]
    except ValueError:
        parts = [0]
    return (parts, 0 if is_beta else 1)

def github_list(path):
    """Listet Dateien in einem GitHub-Ordner per API."""
    url = f"{GITHUB_API}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())

def check_tool_update():
    """
    Sucht neueste switchbot_config_v*_beta.py auf GitHub.
    Gibt (neue_version, download_url) zurück oder (None, None).
    """
    try:
        files = github_list("")
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
    Sucht neueste firmware_v*_beta.bin im firmware/-Ordner auf GitHub.
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

def do_tool_self_update(new_version, url):
    """
    Lädt neue switchbot_config.py von GitHub,
    ersetzt die laufende .exe und startet neu.
    """
    try:
        install_dir = os.path.dirname(sys.executable)
        exe_path    = sys.executable

        # Neue .py herunterladen (Dateiname enthält Versionsnummer)
        req = urllib.request.Request(url, headers={"User-Agent": "SwitchBot-Tool"})
        with urllib.request.urlopen(req, timeout=15) as r:
            new_code = r.read()

        # Als temp-Datei speichern
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        tmp.write(new_code)
        tmp.close()

        # Batch-Skript: ersetzt .exe nach kurzem Delay (Prozess muss erst beendet sein)
        bat = tempfile.NamedTemporaryFile(delete=False, suffix=".bat", mode="w")
        bat.write(f"""@echo off
timeout /t 2 /nobreak >nul
pip install pyinstaller --quiet
pyinstaller --onefile --windowed --name SwitchBot-Konfigurator "{tmp.name}"
copy /Y dist\\SwitchBot-Konfigurator.exe "{exe_path}"
start "" "{exe_path}"
del "%~f0"
""")
        bat.close()
        subprocess.Popen(["cmd", "/c", bat.name], creationflags=subprocess.CREATE_NO_WINDOW)
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Update-Fehler", str(e))


# ════════════════════════════════════════════════════════════════
#  HAUPT-APP
# ════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"SwitchBot Konfigurator  v{VERSION}")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")

        self.all_items   = []
        self.dev_cbs     = []
        self.cmd_cbs     = []
        self.dev_vars    = []
        self.cmd_vars    = []
        self.esp_ip      = tk.StringVar(value="")
        self.fw_update     = None   # neue FW-Version falls verfügbar
        self.fw_update_url = None   # Download-URL der neuen Firmware

        self._build()

        # Änderung #14: Auto-Update + ESP-Discovery beim Start im Hintergrund
        threading.Thread(target=self._startup_checks, daemon=True).start()

    # ── UI-Aufbau ────────────────────────────────────────────────
    def _build(self):
        BG     = "#1e1e2e"
        PANEL  = "#2a2a3e"
        ACCENT = "#7c6af7"
        TEXT   = "#e0e0f0"
        MUTED  = "#888aaa"
        INPUT  = "#12121f"
        GREEN  = "#3dd68c"
        ORANGE = "#f0a500"
        BORDER = "#3a3a55"

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
                 font=("Segoe UI",9), bg=ACCENT, fg="#d0ccff").pack()

        # ── Firmware-Update Banner (initial versteckt) ──
        self.fw_banner = tk.Frame(self, bg=ORANGE, pady=6)
        self.fw_banner_lbl = tk.Label(self.fw_banner,
            text="", bg=ORANGE, fg="#1a0a00",
            font=("Segoe UI",9,"bold"))
        self.fw_banner_lbl.pack(side="left", padx=12)
        self.fw_flash_btn = tk.Button(self.fw_banner,
            text="🔄 Jetzt flashen", bg="#c07800", fg="white",
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
            bg=ACCENT, fg="white", activebackground="#5a4dd4",
            font=("Segoe UI",10,"bold"), relief="flat", cursor="hand2", pady=7)
        self.scan_btn.pack(side="left", fill="x", expand=True, padx=(0,4))

        self.upload_btn = tk.Button(btn_row, text="⬆  Direkt auf ESP laden",
            command=self._upload_to_esp,
            bg="#2a5a2a", fg=GREEN, activebackground="#3a7a3a",
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
            row_bg = PANEL if i % 2 == 0 else "#252538"
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
            bg=GREEN, fg="#0a1a10", activebackground="#2ab870",
            font=("Segoe UI",10,"bold"), relief="flat",
            cursor="hand2", pady=8).pack(side="left", fill="x", expand=True, padx=(0,4))

        tk.Button(save_row, text="💾 + ⬆  Speichern & direkt hochladen",
            command=self._save_and_upload,
            bg="#1a3a2a", fg=GREEN,
            font=("Segoe UI",10,"bold"), relief="flat",
            cursor="hand2", pady=8).pack(side="left", fill="x", expand=True, padx=(4,0))

        tk.Label(self, text=f"Desktop-Pfad: {CONFIG_PATH}",
                 bg=BG, fg=MUTED, font=("Segoe UI",8)).pack(pady=(0,8))

    # ── Startup-Checks (Thread) ──────────────────────────────────
    def _startup_checks(self):
        """Läuft beim Start: Tool-Update + ESP-Discovery + FW-Check."""
        # 1. Tool-Update prüfen
        try:
            new_ver, dl_url = check_tool_update()
            if new_ver:
                ans = messagebox.askyesno("Tool-Update verfügbar",
                    f"Neue Version v{new_ver} verfügbar (aktuell v{VERSION}).\n"
                    f"Jetzt automatisch updaten?")
                if ans:
                    do_tool_self_update(new_ver, dl_url)
        except Exception:
            pass

        # 2. ESP32 suchen
        self._discover_esp()

        # 3. Firmware-Update prüfen
        try:
            fw_ver, fw_url = check_firmware_update()
            if fw_ver:
                self.fw_update = fw_ver
                self.fw_update_url = fw_url
                self.after(0, self._show_fw_banner, fw_ver)
        except Exception:
            pass

    def _discover_esp(self):
        """Sucht ESP32 per mDNS, setzt IP ins Feld."""
        self.after(0, lambda: self.esp_status_lbl.config(
            text="⏳ Suche ESP32…", fg="#888aaa"))
        ip = resolve_esp_ip()
        if not ip:
            # Fallback: direkt per IP aus Feld versuchen
            ip = self.esp_ip.get().strip()
        if ip:
            status = esp_get_status(ip)
            if status:
                self.after(0, lambda: self.esp_ip.set(ip))
                self.after(0, lambda: self.esp_status_lbl.config(
                    text=f"✅ Gefunden · {status.get('buttons',0)}/14 Taster · "
                         f"FW v{status.get('fw','?')}",
                    fg="#3dd68c"))
                return
        self.after(0, lambda: self.esp_status_lbl.config(
            text="❌ Nicht gefunden – IP manuell eintragen", fg="#ff6b6b"))

    def _show_fw_banner(self, fw_ver):
        """Zeigt den Firmware-Update-Banner an."""
        self.fw_banner_lbl.config(
            text=f"⚠  Neue ESP32-Firmware v{fw_ver} verfügbar – ESP32 per USB anschließen")
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
        self.status_lbl.config(text="⏳ Speichere & lade hoch…")
        self.update()
        threading.Thread(target=self._do_upload, args=(ip, cfg), daemon=True).start()

    # ── Firmware flashen ─────────────────────────────────────────
    def _flash_firmware(self):
        ip = self.esp_ip.get().strip()
        if not ip:
            messagebox.showerror("Fehler",
                "ESP32 nicht gefunden.\nBitte per USB anschließen und IP eintragen.")
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
