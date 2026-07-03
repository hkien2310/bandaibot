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
echo [4/5] Tao file config template neu chua co...

::  Tao config.json tu file example neu chua co
if not exist config.json (
    if exist config.example.json (
        echo Tao config.json tu config.example.json...
        copy /Y config.example.json config.json
        echo config.json da duoc tao! Nho dien Google Sheet ID vao config.json truoc khi chay bot.
    ) else (
        echo [LOI] Khong tim thay config.json va config.example.json!
        pause
        exit /b 1
    )
)

:: Tao .env template neu chua co
if not exist .env (
    echo Tao .env template...
    (
        echo EMAIL_MODE=alias
        echo CATCHALL_INBOX=
        echo CATCHALL_PASSWORD=
        echo CATCHALL_DOMAIN=
        echo CATCHALL_EMAIL_PREFIX=acc
        echo SMS_ENABLED=true
        echo SMS_BASE_URL=https://northdinhjpn.online
        echo SMS_USERNAME=
        echo SMS_PASSWORD=
        echo SMS_SERVICE_ID=1017
        echo SMS_COUNTRY=jpn
        echo SMS_SERVER=2
        echo USE_PROXY=true
        echo MAX_ACCOUNTS_PER_PROXY=10
    ) > .env
    echo .env da duoc tao!
)

:: Tao thu muc data neu chua co
if not exist data mkdir data

:: Tao credentials.json placeholder neu chua co
if not exist data\credentials.json (
    echo {} > data\credentials.json
    echo data\credentials.json placeholder da duoc tao - nho thay the bang file that!
)

echo.
echo [5/5] Build NamcoBot...
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
echo Tao thu muc Release...
if exist Release rmdir /s /q Release
mkdir Release

:: Copy toan bo thu muc NamcoBot
xcopy /E /I /Y dist\NamcoBot Release\NamcoBot

:: Copy file cau hinh ra ngoai cung cap voi thu muc NamcoBot
copy /Y config.json Release\config.json
copy /Y .env Release\.env
if exist data\credentials.json (
    mkdir Release\data 2>nul
    copy /Y data\credentials.json Release\data\credentials.json
)

:: Tao shortcut RUN_BOT.bat de chay cho de
(
    echo @echo off
    echo cd /d "%%~dp0NamcoBot"
    echo start NamcoBot.exe
) > Release\RUN_BOT.bat

echo.
echo ============================================================
echo  BUILD THANH CONG!
echo  Thu muc Release/ chua toan bo file can thiet.
echo.
echo  LUU Y QUAN TRONG:
echo  - Thay the Release\data\credentials.json bang file that
echo  - Dien day du thong tin vao Release\.env
echo  - Dien Google Sheet ID vao Release\config.json
echo.
echo  Gui khach toan bo thu muc Release/
echo  Khach click dup RUN_BOT.bat la chay duoc.
echo ============================================================
pause
