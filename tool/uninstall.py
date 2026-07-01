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

if SYSTEM == "Windows":
    INSTALL_DIR = os.path.join(os.environ.get("ProgramFiles","C:\\Programme"),
                               "SwitchBot-Konfigurator")
    DESKTOP     = os.path.join(os.environ.get("PUBLIC","C:\\Users\\Public"), "Desktop")
    SHORTCUT    = os.path.join(DESKTOP, "SwitchBot Konfigurator.lnk")
else:
    INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "SwitchBot-Konfigurator")
    DESKTOP     = os.path.join(os.path.expanduser("~"), "Desktop")
    SHORTCUT    = os.path.join(DESKTOP, "SwitchBot-Konfigurator.desktop")


class UninstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SwitchBot Konfigurator – Deinstallation")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")
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
        BG    = "#1e1e2e"
        PANEL = "#2a2a3e"
        MUTED = "#888aaa"
        TEXT  = "#e0e0f0"
        RED   = "#ff6b6b"

        hdr = tk.Frame(self, bg="#c0392b", pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SwitchBot Konfigurator",
                 font=("Segoe UI",15,"bold"), bg="#c0392b", fg="white").pack()
        tk.Label(hdr, text="Deinstallation",
                 font=("Segoe UI",10), bg="#c0392b", fg="#ffc0c0").pack()

        info = tk.Frame(self, bg=PANEL, pady=10)
        info.pack(fill="x", padx=16, pady=(12,6))
        tk.Label(info,
                 text=f"Folgendes wird entfernt:\n"
                      f"• {INSTALL_DIR}\n"
                      f"• Desktop-Verknüpfung",
                 bg=PANEL, fg=MUTED, font=("Segoe UI",9),
                 justify="left").pack(padx=12)

        self.log = tk.Text(self, bg="#12121f", fg=TEXT,
                           font=("Consolas",9), relief="flat",
                           state="disabled", height=4)
        self.log.pack(fill="x", padx=16, pady=4)
        self.log.tag_config("ok",  foreground="#3dd68c")
        self.log.tag_config("err", foreground=RED)

        btn_frm = tk.Frame(self, bg=BG)
        btn_frm.pack(fill="x", padx=16, pady=(4,12))

        self.uninstall_btn = tk.Button(btn_frm,
            text="🗑  Jetzt deinstallieren",
            command=self._confirm,
            bg="#c0392b", fg="white",
            font=("Segoe UI",11,"bold"), relief="flat",
            cursor="hand2", pady=9)
        self.uninstall_btn.pack(fill="x")

        tk.Button(btn_frm, text="Abbrechen", command=self.destroy,
                  bg=PANEL, fg=MUTED, font=("Segoe UI",10),
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
                    "bg": "#2a4a2a"})


if __name__ == "__main__":
    if SYSTEM == "Windows":
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)

    UninstallerApp().mainloop()
