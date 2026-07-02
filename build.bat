@echo off
echo ============================================================
echo BAT DAU DONG GOI PHAN MEM CHO WINDOWS
echo ============================================================

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Building NamcoBot.exe...
pyinstaller --name "NamcoBot" --onefile --windowed --icon=NONE --hidden-import=playwright --hidden-import=gspread --hidden-import=dotenv --hidden-import=pycparser --hidden-import=cffi gui.py

echo.
echo Creating Release folder...
mkdir Release 2>nul
copy dist\NamcoBot.exe Release\NamcoBot.exe
copy config.json Release\config.json
copy .env Release\.env

echo.
echo ============================================================
echo BUILD SUCCESSFUL!
echo Output is in Release folder.
echo ============================================================
pause
