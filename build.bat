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
echo [2/5] Tao file config template neu chua co...
if not exist config.json (
    if exist config.example.json (
        copy /Y config.example.json config.json
        echo config.json da duoc tao tu template.
    ) else (
        echo [LOI] Khong tim thay config.json va config.example.json!
        pause
        exit /b 1
    )
)

echo.
echo [3/5] Tao src\secrets.py tu env vars...
python generate_secrets.py
if errorlevel 1 (
    echo.
    echo [LOI] Khong tao duoc secrets.py!
    echo.
    echo Cach fix: Set env vars 1 lan tren may nay:
    echo   - NAMCO_SHEET_ID   = Google Sheet ID cua ban
    echo   - NAMCO_CREDS_PATH = Duong dan toi credentials.json
    echo.
    echo Vi du (chay trong PowerShell):
    echo   [System.Environment]::SetEnvironmentVariable("NAMCO_SHEET_ID","your-sheet-id","Machine")
    echo   [System.Environment]::SetEnvironmentVariable("NAMCO_CREDS_PATH","C:\secrets\credentials.json","Machine")
    echo.
    pause
    exit /b 1
)

echo.
echo [4/5] Cai dat Playwright browser (Chromium)...
playwright install chromium
if errorlevel 1 (
    echo [LOI] Cai dat Playwright browser that bai!
    pause
    exit /b 1
)

echo.
echo [5/5] Build NamcoBot...
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

xcopy /E /I /Y dist\NamcoBot Release\NamcoBot
copy /Y config.json Release\config.json

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
echo ============================================================
pause
