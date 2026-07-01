@echo off
setlocal
title SwitchBot Konfigurator - Deinstallation
color 0C

echo.
echo  ============================================
echo   SwitchBot Konfigurator - Deinstallation
echo  ============================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Starte neu mit Adminrechten...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set INSTALL_DIR=%ProgramFiles%\SwitchBot-Konfigurator
set SHORTCUT=%Public%\Desktop\SwitchBot Konfigurator.lnk

echo  [1/3] Loesche Programm-Ordner...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo  [OK] %INSTALL_DIR% geloescht.
) else (
    echo  [!] Ordner nicht gefunden – bereits deinstalliert?
)

echo.
echo  [2/3] Loesche Desktop-Verknuepfung...
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo  [OK] Verknuepfung geloescht.
) else (
    echo  [!] Verknuepfung nicht gefunden.
)

echo.
echo  [3/3] Python deinstallieren?
set /p DELPYTHON="Python ebenfalls entfernen? (j/n): "
if /i "%DELPYTHON%"=="j" (
    echo  Deinstalliere Python 3.12...
    powershell -Command "Get-Package -Name 'Python 3*' | Uninstall-Package -Force" >nul 2>&1
    echo  [OK] Python deinstalliert.
) else (
    echo  [OK] Python bleibt installiert.
)

echo.
echo  ============================================
echo   Deinstallation abgeschlossen!
echo  ============================================
echo.
pause
exit /b 0
