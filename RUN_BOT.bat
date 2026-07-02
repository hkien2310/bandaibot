@echo off
echo ==================================================
echo   KHOI DONG NAMCO PARKS AUTO REGISTER BOT
echo ==================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Khong tim thay moi truong ao Python (.venv)!
    echo Vui long cai dat Python va chay file INSTALL.bat truoc.
    pause
    exit /b
)

echo Dang kich hoat moi truong...
call .venv\Scripts\activate.bat

echo.
echo ==================================================
echo   BAT DAU CHAY TOOL (Vui long khong tat cua so nay)
echo ==================================================
echo.

set PYTHONUNBUFFERED=1
python main.py

echo.
echo ==================================================
echo   DA CHAY XONG!
echo ==================================================
pause
