@echo off
chcp 65001 >nul
echo ============================================================
echo BẮT ĐẦU ĐÓNG GÓI PHẦN MỀM CHO WINDOWS
echo ============================================================

REM Cài đặt thư viện nếu chưa có
echo Đang cài đặt các thư viện cần thiết...
pip install -r requirements.txt
pip install pyinstaller

REM Build file exe
echo.
echo Đang build file NamcoBot.exe...
pyinstaller --name "NamcoBot" --onefile --windowed --icon=NONE --hidden-import=playwright --hidden-import=gspread --hidden-import=dotenv --hidden-import=pycparser --hidden-import=cffi gui.py

echo.
echo Tạo thư mục Release...
mkdir Release 2>nul
copy dist\NamcoBot.exe Release\NamcoBot.exe
copy config.json Release\config.json
copy .env Release\.env

echo.
echo ============================================================
echo 🎉 BUILD THÀNH CÔNG!
echo Sản phẩm nằm trong thư mục: \Release\
echo Bạn chỉ cần nén (ZIP) thư mục Release này và gửi cho khách hàng là chạy được ngay.
echo ============================================================
pause
