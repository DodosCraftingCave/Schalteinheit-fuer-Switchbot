#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwitchBot Konfigurator - Installer
Läuft auf Windows und Linux per Doppelklick.
"""

import sys
import os
import subprocess
import threading
import platform
import shutil

# tkinter importieren — falls nicht vorhanden, installieren
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "tk"], capture_output=True)
    import tkinter as tk
    from tkinter import ttk

SYSTEM   = platform.system()   # "Windows" oder "Linux"
SCRIPT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

# Änderung: Wenn install.py bereits als PyInstaller-Binary läuft (frozen),
# zeigt sys.executable auf die eingefrorene Umgebung, NICHT auf ein echtes
# Python. Für pip/PyInstaller-Aufrufe brauchen wir ein echtes System-Python.
def find_system_python():
    """Findet ein echtes System-Python, auch wenn dieses Skript selbst
    als PyInstaller-Binary läuft (sys.frozen)."""
    if not getattr(sys, "frozen", False):
        return sys.executable
    candidates = ["python3", "python"] if SYSTEM != "Windows" else ["python", "py"]
    for cand in candidates:
        found = shutil.which(cand)
        if found:
            return found
    return None

PYTHON_BIN = find_system_python()

# Installationspfade je System
if SYSTEM == "Windows":
    INSTALL_DIR  = os.path.join(os.environ.get("ProgramFiles","C:\\Programme"),
                                "SwitchBot-Konfigurator")
    DESKTOP      = os.path.join(os.environ.get("PUBLIC","C:\\Users\\Public"), "Desktop")
    APP_EXE      = os.path.join(INSTALL_DIR, "SwitchBot-Konfigurator.exe")
else:  # Linux
    INSTALL_DIR  = os.path.join(os.path.expanduser("~"), ".local", "share", "SwitchBot-Konfigurator")
    DESKTOP      = os.path.join(os.path.expanduser("~"), "Desktop")
    APP_EXE      = os.path.join(INSTALL_DIR, "SwitchBot-Konfigurator")


class InstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SwitchBot Konfigurator – Installation")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
        self.geometry("500x400")
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w = 500; h = 400
        x = (self.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        BG     = "#1e1e2e"
        PANEL  = "#2a2a3e"
        ACCENT = "#7c6af7"
        TEXT   = "#e0e0f0"
        MUTED  = "#888aaa"
        GREEN  = "#3dd68c"

        # Kopf
        hdr = tk.Frame(self, bg=ACCENT, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SwitchBot Konfigurator",
                 font=("Segoe UI",16,"bold"), bg=ACCENT, fg="white").pack()
        tk.Label(hdr, text="Installation",
                 font=("Segoe UI",10), bg=ACCENT, fg="#d0ccff").pack()

        # Info
        info = tk.Frame(self, bg=PANEL, pady=12)
        info.pack(fill="x", padx=16, pady=(14,6))
        tk.Label(info,
                 text=f"System: {SYSTEM}\nInstalliert in: {INSTALL_DIR}",
                 bg=PANEL, fg=MUTED, font=("Segoe UI",9),
                 justify="left").pack(padx=12)

        # Log-Bereich
        log_frm = tk.Frame(self, bg=BG)
        log_frm.pack(fill="both", expand=True, padx=16, pady=6)
        self.log = tk.Text(log_frm, bg="#12121f", fg=TEXT,
                           font=("Consolas",9), relief="flat",
                           state="disabled", height=8)
        self.log.pack(fill="both", expand=True)
        self.log.tag_config("ok",     foreground=GREEN)
        self.log.tag_config("err",    foreground="#ff6b6b")
        self.log.tag_config("warn",   foreground="#f0a500")
        self.log.tag_config("normal", foreground=TEXT)

        # Fortschrittsbalken
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("green.Horizontal.TProgressbar",
                        troughcolor="#12121f", background=GREEN,
                        bordercolor="#12121f", lightcolor=GREEN, darkcolor=GREEN)
        self.progress = ttk.Progressbar(self, style="green.Horizontal.TProgressbar",
                                        length=468, mode="determinate")
        self.progress.pack(padx=16, pady=(0,6))

        # Buttons
        btn_frm = tk.Frame(self, bg=BG)
        btn_frm.pack(fill="x", padx=16, pady=(0,12))

        self.install_btn = tk.Button(btn_frm,
            text="🚀  Jetzt installieren",
            command=self._start,
            bg=ACCENT, fg="white", activebackground="#5a4dd4",
            font=("Segoe UI",11,"bold"), relief="flat",
            cursor="hand2", pady=9)
        self.install_btn.pack(fill="x")

        self.close_btn = tk.Button(btn_frm,
            text="Schließen",
            command=self.destroy,
            bg="#2a2a3e", fg=MUTED,
            font=("Segoe UI",10), relief="flat",
            cursor="hand2", pady=6)
        self.close_btn.pack(fill="x", pady=(4,0))
        self.close_btn.pack_forget()   # erst nach Installation sichtbar

    def _log(self, msg, tag="normal"):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")
        self.update()

    def _set_progress(self, val):
        self.progress["value"] = val
        self.update()

    def _start(self):
        self.install_btn.config(state="disabled", text="⏳  Installation läuft…")
        threading.Thread(target=self._install, daemon=True).start()

    def _install(self):
        try:
            self._do_install()
        except Exception as ex:
            self.after(0, self._log, f"[FEHLER] {ex}", "err")
            self.after(0, self.install_btn.config,
                       {"state": "normal", "text": "🚀  Erneut versuchen"})

    def _run(self, cmd, **kwargs):
        """Führt einen Befehl aus und gibt (returncode, stdout+stderr) zurück."""
        result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
        return result.returncode, result.stdout + result.stderr

    def _do_install(self):
        steps = 6

        # ── Schritt 0: System-Python prüfen ──
        if not PYTHON_BIN:
            self.after(0, self._log,
                "[FEHLER] Kein System-Python gefunden. Bitte Python3 installieren:", "err")
            if SYSTEM == "Linux":
                self.after(0, self._log,
                    "  sudo apt install python3 python3-pip python3-tk", "err")
            else:
                self.after(0, self._log, "  https://python.org", "err")
            return

        # ── Schritt 1: Python-Abhängigkeiten ──
        self.after(0, self._log, "[1/6] Installiere Python-Pakete…")
        if SYSTEM == "Windows":
            rc, out = self._run([PYTHON_BIN, "-m", "pip", "install",
                                 "--quiet", "requests", "pyinstaller"])
        else:
            rc, out = self._run([PYTHON_BIN, "-m", "pip", "install",
                                 "--quiet", "requests", "pyinstaller",
                                 "--break-system-packages"])
            if rc != 0:
                rc, out = self._run([PYTHON_BIN, "-m", "pip", "install",
                                     "--quiet", "requests", "pyinstaller"])
        if rc != 0:
            self.after(0, self._log, f"[FEHLER] pip: {out}", "err")
            return
        self.after(0, self._log, "[OK] Pakete installiert.", "ok")
        self.after(0, self._set_progress, 100 // steps * 1)

        # ── Schritt 2: Tool-Script finden ──
        self.after(0, self._log, "[2/6] Suche Tool-Script…")
        import glob
        scripts = glob.glob(os.path.join(SCRIPT_DIR, "switchbot_config_v*_beta.py"))
        if not scripts:
            self.after(0, self._log, "[FEHLER] switchbot_config_v*_beta.py nicht gefunden.", "err")
            return
        py_script = sorted(scripts)[-1]   # neueste Version nehmen
        self.after(0, self._log, f"[OK] {os.path.basename(py_script)}", "ok")
        self.after(0, self._set_progress, 100 // steps * 2)

        # ── Schritt 3: .exe / Binary bauen ──
        self.after(0, self._log, "[3/6] Baue ausfuehrbare Datei (kann etwas dauern)…")
        import tempfile
        work_dir = tempfile.mkdtemp(prefix="switchbot_build_")
        build_script = os.path.join(work_dir, "switchbot_config.py")
        shutil.copy(py_script, build_script)

        cmd = [PYTHON_BIN, "-m", "PyInstaller",
               "--onefile", "--windowed",
               "--name", "SwitchBot-Konfigurator",
               "--distpath", os.path.join(work_dir, "dist"),
               "--workpath", os.path.join(work_dir, "build"),
               "--specpath", work_dir,
               build_script]
        rc, out = self._run(cmd)

        exe_name = "SwitchBot-Konfigurator.exe" if SYSTEM == "Windows" else "SwitchBot-Konfigurator"
        built_exe = os.path.join(work_dir, "dist", exe_name)

        if rc != 0 or not os.path.exists(built_exe):
            self.after(0, self._log, f"[FEHLER] PyInstaller:\n{out}", "err")
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        self.after(0, self._log, "[OK] Ausfuehrbare Datei erstellt.", "ok")
        self.after(0, self._set_progress, 100 // steps * 3)

        # ── Schritt 4: In Installationsordner kopieren ──
        self.after(0, self._log, f"[4/6] Installiere nach {INSTALL_DIR}…")
        os.makedirs(INSTALL_DIR, exist_ok=True)
        dest_exe = os.path.join(INSTALL_DIR, exe_name)
        shutil.copy2(built_exe, dest_exe)
        if SYSTEM == "Linux":
            os.chmod(dest_exe, 0o755)
        shutil.rmtree(work_dir, ignore_errors=True)
        self.after(0, self._log, "[OK] Installiert.", "ok")
        self.after(0, self._set_progress, 100 // steps * 4)

        # ── Schritt 5: Desktop-Verknüpfung ──
        self.after(0, self._log, "[5/6] Erstelle Desktop-Verknuepfung…")
        os.makedirs(DESKTOP, exist_ok=True)

        if SYSTEM == "Windows":
            # .lnk per PowerShell
            lnk = os.path.join(DESKTOP, "SwitchBot Konfigurator.lnk")
            ps  = (f"$ws=New-Object -ComObject WScript.Shell;"
                   f"$s=$ws.CreateShortcut('{lnk}');"
                   f"$s.TargetPath='{dest_exe}';"
                   f"$s.WorkingDirectory='{INSTALL_DIR}';"
                   f"$s.Description='SwitchBot ESP32 Konfigurator';"
                   f"$s.Save()")
            self._run(["powershell", "-Command", ps])
        else:
            # .desktop Datei
            desktop_file = os.path.join(DESKTOP, "SwitchBot-Konfigurator.desktop")
            with open(desktop_file, "w") as f:
                f.write(f"""[Desktop Entry]
Version=1.0
Type=Application
Name=SwitchBot Konfigurator
Comment=ESP32 14-Taster-Matrix Konfigurator
Exec={dest_exe}
Icon=application-x-executable
Terminal=false
Categories=Utility;
""")
            os.chmod(desktop_file, 0o755)

        self.after(0, self._log, "[OK] Desktop-Verknuepfung erstellt.", "ok")
        self.after(0, self._set_progress, 100 // steps * 5)

        # ── Schritt 6: Fertig ──
        self.after(0, self._log, "[6/6] Installation abgeschlossen!", "ok")
        self.after(0, self._set_progress, 100)
        self.after(0, self._finish, dest_exe)

    def _finish(self, exe_path):
        self.install_btn.config(
            text="✅  Installation erfolgreich!",
            bg="#2a4a2a", fg="#3dd68c")
        self.close_btn.pack(fill="x", pady=(4,0))

        # Programm direkt starten
        if SYSTEM == "Windows":
            os.startfile(exe_path)
        else:
            subprocess.Popen([exe_path])


if __name__ == "__main__":
    # Auf Windows: Admin-Check
    if SYSTEM == "Windows":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)

    InstallerApp().mainloop()
