#!/bin/bash
# Build NamcoBot cho macOS
set -e

echo "============================================================"
echo " BAT DAU DONG GOI NAMCO BOT CHO MACOS"
echo "============================================================"

# Kiểm tra credentials.json
if [ ! -f "data/credentials.json" ]; then
    echo "[LOI] Khong tim thay data/credentials.json!"
    echo "      Dat file credentials.json vao thu muc data/ roi chay lai."
    exit 1
fi

echo ""
echo "[1/3] Kich hoat venv & cai dat dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "[2/3] Cai dat Playwright browser (Chromium)..."
playwright install chromium

echo ""
echo "[3/3] Build NamcoBot.app..."
pyinstaller --noconfirm --onedir --windowed \
    --name "NamcoBot" \
    --add-data "src:src" \
    --add-data "config.json:." \
    --add-data "data/credentials.json:data" \
    --hidden-import=playwright \
    --hidden-import=playwright.async_api \
    --hidden-import=gspread \
    --hidden-import=pycparser \
    --hidden-import=cffi \
    --hidden-import=cryptography \
    --hidden-import=google.auth \
    --hidden-import=google.oauth2.service_account \
    --collect-all playwright \
    gui.py

echo ""
echo "Tao thu muc Release..."
rm -rf Release
mkdir -p Release

cp -r dist/NamcoBot.app Release/
cp config.json Release/config.json

echo ""
echo "============================================================"
echo " BUILD THANH CONG!"
echo " Thu muc Release/ chua:"
echo "   - NamcoBot.app  (ung dung chinh, double-click de chay)"
echo "   - config.json   (SMS/email settings cua khach)"
echo ""
echo " credentials.json da duoc BUNDLE vao ben trong app."
echo " Gui khach toan bo thu muc Release/"
echo "============================================================"
