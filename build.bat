@echo off
chcp 65001 >nul
echo ============================================================
echo  BAT DAU DONG GOI NAMCO BOT CHO WINDOWS
echo ============================================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Chua cai Python!
    pause & exit /b 1
)

if not exist data\credentials.json (
    echo [LOI] Khong tim thay data\credentials.json!
    echo       Dat file credentials.json vao thu muc data\ roi chay lai.
    pause & exit /b 1
)

echo.
echo [1/3] Cai dat dependencies...
pip install -r requirements.txt
if errorlevel 1 ( echo [LOI] That bai! & pause & exit /b 1 )

echo.
echo [2/3] Cai dat Playwright browser (Chromium)...
playwright install chromium
if errorlevel 1 ( echo [LOI] That bai! & pause & exit /b 1 )

echo.
echo [3/3] Build NamcoBot...
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed ^
    --name "NamcoBot" ^
    --add-data "src;src" ^
    --add-data "config.json;." ^
    --add-data "data/credentials.json;data" ^
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

if errorlevel 1 ( echo [LOI] Build that bai! & pause & exit /b 1 )

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
echo  credentials.json da duoc BUNDLE vao ben trong app.
echo  Gui khach toan bo thu muc Release/
echo ============================================================
pause
