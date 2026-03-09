@echo off
setlocal
cd /d %~dp0

where py >nul 2>&1
if %errorlevel%==0 (
  py -3 miner\windows_gui.py
  exit /b
)

where python >nul 2>&1
if %errorlevel%==0 (
  python miner\windows_gui.py
  exit /b
)

echo Python 3 is required.
echo 1) Download from https://www.python.org/downloads/windows/
echo 2) During install, tick "Add Python to PATH"
echo 3) Run this file again.
pause
