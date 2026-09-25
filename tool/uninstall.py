#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SwitchBot Konfigurator - Deinstaller
Läuft auf Windows und Linux per Doppelklick.
"""

import sys
import os
import shutil
import subprocess
import platform
import threading

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    sys.exit(1)

SYSTEM = platform.system()

# Änderung: Muss zum neuen Installationsort in install.py passen
# (%LOCALAPPDATA% statt %ProgramFiles%, kein Admin-Recht mehr nötig).
if SYSTEM == "Windows":
    INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA",
                               os.path.expanduser("~\\AppData\\Local")),
                               "SwitchBot-Konfigurator")
    DESKTOP     = os.path.join(os.path.expanduser("~"), "Desktop")
    SHORTCUT    = os.path.join(DESKTOP, "SwitchBot Konfigurator.lnk")
else:
    INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "SwitchBot-Konfigurator")
    DESKTOP     = os.path.join(os.path.expanduser("~"), "Desktop")
    SHORTCUT    = os.path.join(DESKTOP, "SwitchBot-Konfigurator.desktop")


# Palette 1:1 aus den :root-Tokens von switchbot_config_v2.0.py übernommen,
# damit Installer/Uninstaller und Tool wie aus einem Guss wirken.
BG          = "#000000"  # --bg
SURFACE     = "#0A0A0B"  # --surface
SURFACE_ALT = "#161617"  # --surface-alt
TEXT        = "#EDF1F5"  # --text
MUTED       = "#8996A6"  # --muted
SUCCESS     = "#3ECF8E"  # --success
DANGER      = "#FF6B6B"  # --danger — Deinstallation ist eine destruktive
                          # Aktion, daher wie im Tool in Rot


class UninstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SwitchBot Konfigurator – Deinstallation")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.geometry("460x280")
        self._center()
        self._build()

    def _center(self):
        self.update_idletasks()
        w=460; h=280
        x = (self.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        hdr = tk.Frame(self, bg=SURFACE, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SwitchBot Konfigurator",
                 font=("Segoe UI",15,"bold"), bg=SURFACE, fg=DANGER).pack()
        tk.Label(hdr, text="Deinstallation",
                 font=("Segoe UI",10), bg=SURFACE, fg=MUTED).pack()

        info = tk.Frame(self, bg=SURFACE_ALT, pady=10)
        info.pack(fill="x", padx=16, pady=(12,6))
        tk.Label(info,
                 text=f"Folgendes wird entfernt:\n"
                      f"• {INSTALL_DIR}\n"
                      f"• Desktop-Verknüpfung",
                 bg=SURFACE_ALT, fg=MUTED, font=("Segoe UI",9),
                 justify="left").pack(padx=12)

        self.log = tk.Text(self, bg=SURFACE, fg=TEXT,
                           font=("Consolas",9), relief="flat", highlightthickness=0,
                           state="disabled", height=4)
        self.log.pack(fill="x", padx=16, pady=4)
        self.log.tag_config("ok",  foreground=SUCCESS)
        self.log.tag_config("err", foreground=DANGER)

        btn_frm = tk.Frame(self, bg=BG)
        btn_frm.pack(fill="x", padx=16, pady=(4,12))

        self.uninstall_btn = tk.Button(btn_frm,
            text="🗑  Jetzt deinstallieren",
            command=self._confirm,
            bg=DANGER, fg="#FFFFFF",
            font=("Segoe UI",11,"bold"), relief="flat",
            cursor="hand2", pady=9)
        self.uninstall_btn.pack(fill="x")

        tk.Button(btn_frm, text="Abbrechen", command=self.destroy,
                  bg=SURFACE_ALT, fg=MUTED, font=("Segoe UI",10),
                  relief="flat", cursor="hand2", pady=6).pack(fill="x", pady=(4,0))

    def _log(self, msg, tag="normal"):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")
        self.update()

    def _confirm(self):
        if messagebox.askyesno("Bestätigen",
                "SwitchBot Konfigurator wirklich deinstallieren?"):
            self.uninstall_btn.config(state="disabled")
            threading.Thread(target=self._uninstall, daemon=True).start()

    def _uninstall(self):
        # Programm-Ordner löschen
        if os.path.exists(INSTALL_DIR):
            shutil.rmtree(INSTALL_DIR, ignore_errors=True)
            self.after(0, self._log, f"[OK] {INSTALL_DIR} gelöscht.", "ok")
        else:
            self.after(0, self._log, "[!] Installationsordner nicht gefunden.")

        # Desktop-Verknüpfung löschen
        if os.path.exists(SHORTCUT):
            os.remove(SHORTCUT)
            self.after(0, self._log, "[OK] Desktop-Verknüpfung gelöscht.", "ok")
        else:
            self.after(0, self._log, "[!] Desktop-Verknüpfung nicht gefunden.")

        self.after(0, self._log, "[OK] Deinstallation abgeschlossen.", "ok")
        self.after(0, self.uninstall_btn.config,
                   {"text": "✅  Fertig – Fenster schließen",
                    "command": self.destroy,
                    "state": "normal",
                    "bg": SUCCESS, "fg": "#04140A"})


if __name__ == "__main__":
    # Änderung: Keine UAC-Elevation mehr nötig — Installationsort ist
    # %LOCALAPPDATA% (gehört dem aktuellen Nutzer), nicht mehr %ProgramFiles%.
    UninstallerApp().mainloop()
