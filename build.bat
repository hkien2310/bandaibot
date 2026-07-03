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

:: Kiem tra secrets.py ton tai
if not exist src\secrets.py (
    echo [LOI] Khong tim thay src\secrets.py!
    echo       Chay lenh nay de tao: python generate_secrets.py
    pause
    exit /b 1
)

echo.
echo [1/4] Cai dat dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [LOI] Cai dat dependencies that bai!
    pause
    exit /b 1
)

echo.
echo [2/4] Cai dat Playwright browser (Chromium)...
playwright install chromium
if errorlevel 1 (
    echo [LOI] Cai dat Playwright browser that bai!
    pause
    exit /b 1
)

echo.
echo [3/4] Tao file config template neu chua co...

:: Tao config.json tu file example neu chua co
if not exist config.json (
    if exist config.example.json (
        echo Tao config.json tu config.example.json...
        copy /Y config.example.json config.json
        echo config.json da duoc tao!
    ) else (
        echo [LOI] Khong tim thay config.json va config.example.json!
        pause
        exit /b 1
    )
)

echo.
echo [4/4] Build NamcoBot...
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed ^
    --name "NamcoBot" ^
    --add-data "src;src" ^
    --add-data "config.json;." ^
    --hidden-import=playwright ^
    --hidden-import=playwright.async_api ^
    --hidden-import=gspread ^
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

:: Copy toan bo thu muc NamcoBot (binary)
xcopy /E /I /Y dist\NamcoBot Release\NamcoBot

:: Chi copy config.json (SMS/email settings) - KHONG copy data/ (secrets da baked vao binary)
copy /Y config.json Release\config.json

:: Tao shortcut RUN_BOT.bat de chay cho de
(
    echo @echo off
    echo cd /d "%%~dp0NamcoBot"
    echo start NamcoBot.exe
) > Release\RUN_BOT.bat

echo.
echo ============================================================
echo  BUILD THANH CONG!
echo  Thu muc Release/ chua:
echo    - NamcoBot\    (app chinh)
echo    - config.json  (SMS/email settings cua khach)
echo    - RUN_BOT.bat  (click dup de chay)
echo.
echo  Sheet ID va Google credentials da BAKED vao binary.
echo  Gui khach toan bo thu muc Release/
echo  Khach click dup RUN_BOT.bat la chay duoc.
echo ============================================================
pause
