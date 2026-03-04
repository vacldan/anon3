@echo off
REM Run all DOCX in this folder through the STRICT anonymizer (Windows helper)
REM Place this BAT in the same folder as:
REM  - drag_and_drop_runner.py
REM  - Czech_Docx_Anonymizer_STRICT_v7_3.py
REM  - cz_names.v1.json

setlocal
set SCRIPT=%~dp0drag_and_drop_runner.py
where python >nul 2>&1
if errorlevel 1 (
  echo Python neni v PATH. Spust prosim ze "Python Console" nebo nainstaluj Python 3.10+.
  pause
  exit /b 1
)
python "%SCRIPT%"
pause
