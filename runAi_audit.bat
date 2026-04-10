@echo off
title He thong Tham dinh Vat tu Unified v3.0 - AI Audit
color 0A

:: 1. Thiet lap duong dan den Python trong .venv (Hieu da cung cap)
set VENV_PYTHON="D:\TaskApp_kiet\TaskApp\.venv\Scripts\python.exe"

:: 2. Thiet lap thu muc goc cua Code va thu muc chay Script
set PROJECT_ROOT=D:\TaskApp_kiet\TaskApp\search_item2\search_item\back_end
set SCRIPT_DIR=%PROJECT_ROOT%\database\src

:: 3. Cau hinh PYTHONPATH de cac file nhin thay nhau
set PYTHONPATH=%PROJECT_ROOT%;%SCRIPT_DIR%

:: 4. Di chuyen vao thu muc chua file main.py de nap file .env va Excel
cd /d "%SCRIPT_DIR%"

:: 5. Kiem tra xem file Python co ton tai khong truoc khi chay
echo ---------------------------------------------------
echo       DANG KHOI DONG HE THONG AI AUDIT...
echo ---------------------------------------------------

if exist %VENV_PYTHON% (
    %VENV_PYTHON% main.py
) else (
    echo [LOI] Khong tim thay Python tai: %VENV_PYTHON%
    echo Hieu kiem tra lai xem thu muc .venv co bi di chuyen khong nhe!
)

:: 6. Giu cua so terminal de xem ket qua hoac loi
echo.
echo ---------------------------------------------------
echo Da hoan thanh! Nhan phim bat ky de thoat...
pause > nul