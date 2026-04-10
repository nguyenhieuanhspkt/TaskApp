@echo off
title DEBUG DU LIEU AI - VINH TAN 4
color 0E

:: 1. Lay duong dan goc
set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

:: 2. Duong dan Python trong venv
set PYTHON_EXE="%ROOT_DIR%.venv\Scripts\python.exe"
:: 3. Duong dan file debug
set DEBUG_FILE="%ROOT_DIR%search_item2\search_item\back_end\ai_audit_system\debug_search.py"

echo ======================================================
echo    DANG KIEM TRA CAU TRUC DU LIEU (DEBUG MODE)
echo ======================================================
echo.

:: Chay file debug
%PYTHON_EXE% %DEBUG_FILE%

echo.
echo ======================================================
echo Nhấn phím bất kỳ để thoát...
pause > nul