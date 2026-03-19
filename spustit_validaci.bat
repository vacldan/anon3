@echo off
chcp 65001 >nul
cd /d "%~dp0"

REM Spustit bez konzole (pythonw) - pokud selze, zkusit s python
pythonw validation_ui.py 2>nul
if errorlevel 1 (
    python validation_ui.py
    if errorlevel 1 pause
)
