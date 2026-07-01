@echo off
setlocal enabledelayedexpansion
title SwitchBot Konfigurator - Installation
color 0A

echo.
echo  ============================================
echo   SwitchBot Konfigurator - Installation
echo  ============================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Starte neu mit Adminrechten...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set INSTALL_DIR=%ProgramFiles%\SwitchBot-Konfigurator
set PY_SCRIPT=%~dp0switchbot_config_v0.8_beta.py
set EXE_NAME=SwitchBot-Konfigurator_v0.8_beta
set WORK_DIR=C:\switchbot_build

echo  [1/6] Pruefe Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Python nicht gefunden. Lade Python 3.12 herunter...
    set PY_INSTALLER=%TEMP%\python_installer.exe
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '!PY_INSTALLER!'}"
    if not exist "!PY_INSTALLER!" ( echo  [FEHLER] Download fehlgeschlagen. & pause & exit /b 1 )
    "!PY_INSTALLER!" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    del "!PY_INSTALLER!"
    set "PATH=%PATH%;%ProgramFiles%\Python312;%ProgramFiles%\Python312\Scripts"
    python --version >nul 2>&1
    if %errorLevel% neq 0 ( echo  [FEHLER] Python-Installation fehlgeschlagen. & pause & exit /b 1 )
    echo  [OK] Python installiert.
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  [OK] %%i
)

echo.
echo  [2/6] Installiere Abhaengigkeiten...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet requests pyinstaller esptool
if %errorLevel% neq 0 ( echo  [FEHLER] pip install fehlgeschlagen. & pause & exit /b 1 )
echo  [OK] requests + pyinstaller + esptool installiert.

echo.
echo  [3/6] Erstelle .exe...
if exist "%WORK_DIR%" rmdir /S /Q "%WORK_DIR%"
mkdir "%WORK_DIR%"
copy /Y "%PY_SCRIPT%" "%WORK_DIR%\switchbot_config.py" >nul
if not exist "%WORK_DIR%\switchbot_config.py" (
    echo  [FEHLER] switchbot_config.py nicht gefunden neben install.bat
    pause & exit /b 1
)
cd /D "%WORK_DIR%"
python -m PyInstaller --onefile --windowed --name "%EXE_NAME%" switchbot_config.py
if %errorLevel% neq 0 ( echo  [FEHLER] PyInstaller fehlgeschlagen. & pause & exit /b 1 )
if not exist "%WORK_DIR%\dist\%EXE_NAME%.exe" ( echo  [FEHLER] .exe nicht erstellt. & pause & exit /b 1 )
echo  [OK] .exe erstellt.

echo.
echo  [4/6] Installiere nach Programme...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy /Y "%WORK_DIR%\dist\%EXE_NAME%.exe" "%INSTALL_DIR%\%EXE_NAME%.exe" >nul
echo  [OK] %INSTALL_DIR%

echo.
echo  [5/6] Desktop-Verknuepfung...
set SHORTCUT=%Public%\Desktop\SwitchBot Konfigurator.lnk
powershell -Command "& { $ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath='%INSTALL_DIR%\%EXE_NAME%.exe'; $s.WorkingDirectory='%INSTALL_DIR%'; $s.Description='SwitchBot ESP32 Konfigurator'; $s.Save() }"
if exist "%SHORTCUT%" ( echo  [OK] Desktop-Verknuepfung erstellt. ) else ( echo  [!] Verknuepfung fehlgeschlagen. )

echo.
echo  [6/6] Aufraeumen...
cd /D "%~dp0"
rmdir /S /Q "%WORK_DIR%" >nul 2>&1
echo  [OK] Temp-Dateien geloescht.

echo.
echo  ============================================
echo   Installation abgeschlossen!
echo   Starte SwitchBot Konfigurator...
echo  ============================================
echo.
timeout /t 2 /nobreak >nul
start "" "%INSTALL_DIR%\%EXE_NAME%.exe"
exit /b 0
