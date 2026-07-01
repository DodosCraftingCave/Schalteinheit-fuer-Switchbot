#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwitchBot Konfigurator - Installer (vereinfacht)
Lädt die fertig gebaute App von GitHub herunter und installiert sie.
KEIN Python, pip oder PyInstaller am Kunden-PC nötig – alles wird
bereits von GitHub Actions fertig gebaut.
Läuft auf Windows und Linux per Doppelklick.
"""

import sys
import os
import subprocess
import threading
import platform
import shutil
import urllib.request

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    sys.exit(1)

SYSTEM = platform.system()   # "Windows" oder "Linux"

GITHUB_RAW = "https://raw.githubusercontent.com/DodosCraftingCave/Schalteinheit-fuer-Switchbot/main"

if SYSTEM == "Windows":
    APP_NAME    = "SwitchBot-Konfigurator.exe"
    INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\Programme"),
                               "SwitchBot-Konfigurator")
    DESKTOP     = os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")
else:
    APP_NAME    = "SwitchBot-Konfigurator"
    INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "SwitchBot-Konfigurator")
    DESKTOP     = os.path.join(os.path.expanduser("~"), "Desktop")

APP_URL  = f"{GITHUB_RAW}/tool/{APP_NAME}"
APP_DEST = os.path.join(INSTALL_DIR, APP_NAME)


class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SwitchBot Konfigurator – Installation")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.geometry("480x340")
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = 480, 340
        x = (self.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        BG, PANEL, ACCENT = "#1e1e2e", "#2a2a3e", "#7c6af7"
        TEXT, MUTED, GREEN = "#e0e0f0", "#888aaa", "#3dd68c"

        hdr = tk.Frame(self, bg=ACCENT, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SwitchBot Konfigurator",
                 font=("Segoe UI",16,"bold"), bg=ACCENT, fg="white").pack()
        tk.Label(hdr, text="Installation", font=("Segoe UI",10),
                 bg=ACCENT, fg="#d0ccff").pack()

        info = tk.Frame(self, bg=PANEL, pady=12)
        info.pack(fill="x", padx=16, pady=(14,6))
        tk.Label(info, text=f"System: {SYSTEM}\nInstalliert in: {INSTALL_DIR}",
                 bg=PANEL, fg=MUTED, font=("Segoe UI",9),
                 justify="left").pack(padx=12)

        self.log = tk.Text(self, bg="#12121f", fg=TEXT,
                           font=("Consolas",9), relief="flat",
                           state="disabled", height=7)
        self.log.pack(fill="both", expand=True, padx=16, pady=6)
        self.log.tag_config("ok", foreground=GREEN)
        self.log.tag_config("err", foreground="#ff6b6b")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor="#12121f", background=GREEN,
                        bordercolor="#12121f", lightcolor=GREEN, darkcolor=GREEN)
        self.progress = ttk.Progressbar(self, style="green.Horizontal.TProgressbar",
                                        length=448, mode="determinate")
        self.progress.pack(padx=16, pady=(0,6))

        btn_frm = tk.Frame(self, bg=BG)
        btn_frm.pack(fill="x", padx=16, pady=(0,14))

        self.install_btn = tk.Button(btn_frm, text="🚀  Jetzt installieren",
            command=self._start, bg=ACCENT, fg="white",
            activebackground="#5a4dd4", font=("Segoe UI",11,"bold"),
            relief="flat", cursor="hand2", pady=9)
        self.install_btn.pack(fill="x")

        self.close_btn = tk.Button(btn_frm, text="Schließen",
            command=self.destroy, bg=PANEL, fg=MUTED,
            font=("Segoe UI",10), relief="flat", cursor="hand2", pady=6)
        self.close_btn.pack(fill="x", pady=(4,0))
        self.close_btn.pack_forget()

    def _log(self, msg, tag=None):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag or ())
        self.log.see("end")
        self.log.config(state="disabled")
        self.update()

    def _set_progress(self, val):
        self.progress["value"] = val
        self.update()

    def _start(self):
        self.install_btn.config(state="disabled", text="⏳  Installiere…")
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        try:
            self._do_install()
        except Exception as ex:
            self.after(0, self._log, f"[FEHLER] {ex}", "err")
            self.after(0, self.install_btn.config,
                       {"state": "normal", "text": "🚀  Erneut versuchen"})

    def _do_install(self):
        # ── Schritt 1: Zielordner anlegen ──
        self.after(0, self._log, "[1/4] Erstelle Installationsordner…")
        os.makedirs(INSTALL_DIR, exist_ok=True)
        self.after(0, self._set_progress, 15)

        # ── Schritt 2: App von GitHub laden ──
        self.after(0, self._log, f"[2/4] Lade {APP_NAME} von GitHub…")
        req = urllib.request.Request(APP_URL, headers={"User-Agent": "SwitchBot-Installer"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(APP_DEST, "wb") as out:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        out.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = 15 + int(60 * downloaded / total)
                            self.after(0, self._set_progress, pct)
        except Exception as ex:
            self.after(0, self._log, f"[FEHLER] Download fehlgeschlagen: {ex}", "err")
            return

        if not os.path.exists(APP_DEST) or os.path.getsize(APP_DEST) < 1000:
            self.after(0, self._log, "[FEHLER] Heruntergeladene Datei ist ungültig.", "err")
            return

        if SYSTEM == "Linux":
            os.chmod(APP_DEST, 0o755)
        self.after(0, self._log, "[OK] App heruntergeladen.", "ok")
        self.after(0, self._set_progress, 75)

        # ── Schritt 3: Desktop-Verknüpfung ──
        self.after(0, self._log, "[3/4] Erstelle Desktop-Verknüpfung…")
        os.makedirs(DESKTOP, exist_ok=True)

        if SYSTEM == "Windows":
            lnk = os.path.join(DESKTOP, "SwitchBot Konfigurator.lnk")
            ps = (f"$ws=New-Object -ComObject WScript.Shell;"
                  f"$s=$ws.CreateShortcut('{lnk}');"
                  f"$s.TargetPath='{APP_DEST}';"
                  f"$s.WorkingDirectory='{INSTALL_DIR}';"
                  f"$s.Description='SwitchBot ESP32 Konfigurator';"
                  f"$s.Save()")
            subprocess.run(["powershell", "-Command", ps],
                          capture_output=True, text=True)
        else:
            desktop_file = os.path.join(DESKTOP, "SwitchBot-Konfigurator.desktop")
            with open(desktop_file, "w") as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SwitchBot Konfigurator
Comment=ESP32 14-Taster-Matrix Konfigurator
Exec={APP_DEST}
Icon=application-x-executable
Terminal=false
Categories=Utility;
""")
            os.chmod(desktop_file, 0o755)

        self.after(0, self._log, "[OK] Desktop-Verknüpfung erstellt.", "ok")
        self.after(0, self._set_progress, 90)

        # ── Schritt 4: Fertig ──
        self.after(0, self._log, "[4/4] Installation abgeschlossen!", "ok")
        self.after(0, self._set_progress, 100)
        self.after(0, self._finish)

    def _finish(self):
        self.install_btn.config(text="✅  Installation erfolgreich!",
                                bg="#2a4a2a", fg="#3dd68c")
        self.close_btn.pack(fill="x", pady=(4,0))
        if SYSTEM == "Windows":
            os.startfile(APP_DEST)
        else:
            subprocess.Popen([APP_DEST])


if __name__ == "__main__":
    if SYSTEM == "Windows":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)

    InstallerApp().mainloop()
