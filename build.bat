@echo off
chcp 65001 >nul
echo ============================================================
echo  BAT DAU DONG GOI NAMCO BOT CHO WINDOWS
echo ============================================================

:: Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Chua cai Python! Vui long cai Python 3.11+ tu python.org
    pause
    exit /b 1
)

echo.
echo [1/5] Cai dat dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [LOI] Cai dat dependencies that bai!
    pause
    exit /b 1
)

echo.
echo [2/5] Cai dat Playwright browser (Chromium)...
playwright install chromium
if errorlevel 1 (
    echo [LOI] Cai dat Playwright browser that bai!
    pause
    exit /b 1
)

echo.
echo [3/5] Cai dat PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [LOI] Cai dat PyInstaller that bai!
    pause
    exit /b 1
)

echo.
echo [4/5] Build NamcoBot...
pyinstaller --noconfirm --onedir --windowed ^
    --name "NamcoBot" ^
    --add-data "src;src" ^
    --add-data "config.json;." ^
    --add-data ".env;." ^
    --add-data "data/credentials.json;data" ^
    --hidden-import=playwright ^
    --hidden-import=playwright.async_api ^
    --hidden-import=gspread ^
    --hidden-import=dotenv ^
    --hidden-import=python_dotenv ^
    --hidden-import=pycparser ^
    --hidden-import=cffi ^
    --hidden-import=cryptography ^
    --hidden-import=google.auth ^
    --hidden-import=google.oauth2.service_account ^
    --collect-all playwright ^
    gui.py

if errorlevel 1 (
    echo [LOI] Build that bai! Xem log o tren.
    pause
    exit /b 1
)

echo.
echo [5/5] Tao thu muc Release...
if exist Release rmdir /s /q Release
mkdir Release

:: Copy toan bo thu muc NamcoBot
xcopy /E /I /Y dist\NamcoBot Release\NamcoBot

:: Copy file cau hinh ra ngoai (quan trong: nam cung cap voi thu muc NamcoBot)
copy /Y config.json Release\config.json
copy /Y .env Release\.env
if exist data\credentials.json (
    mkdir Release\data 2>nul
    copy /Y data\credentials.json Release\data\credentials.json
)

:: Tao shortcut RUN_BOT.bat de chay cho de
echo @echo off > Release\RUN_BOT.bat
echo cd /d "%%~dp0NamcoBot" >> Release\RUN_BOT.bat
echo start NamcoBot.exe >> Release\RUN_BOT.bat

echo.
echo ============================================================
echo  BUILD THANH CONG!
echo  Thu muc Release/ chua toan bo file can thiet.
echo  Gui khach toan bo thu muc Release/
echo  Khach click dup RUN_BOT.bat la chay duoc.
echo ============================================================
pause
