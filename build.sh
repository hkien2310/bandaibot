#!/bin/bash
# Build NamcoBot cho macOS
set -e

echo "============================================================"
echo " BAT DAU DONG GOI NAMCO BOT CHO MACOS"
echo "============================================================"

echo ""
echo "[1/4] Kich hoat venv & cai dat dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "[2/4] Cai dat Playwright browser (Chromium)..."
playwright install chromium

echo ""
echo "[3/4] Build NamcoBot.app..."
pyinstaller --noconfirm --onedir --windowed \
    --name "NamcoBot" \
    --add-data "src:src" \
    --add-data "config.json:." \
    --add-data ".env:." \
    --add-data "data/credentials.json:data" \
    --hidden-import=playwright \
    --hidden-import=playwright.async_api \
    --hidden-import=gspread \
    --hidden-import=dotenv \
    --hidden-import=pycparser \
    --hidden-import=cffi \
    --hidden-import=cryptography \
    --hidden-import=google.auth \
    --hidden-import=google.oauth2.service_account \
    --collect-all playwright \
    gui.py

echo ""
echo "[4/4] Tao thu muc Release..."
rm -rf Release
mkdir -p Release

# Copy app bundle
cp -r dist/NamcoBot.app Release/

# Copy file cau hinh ra ngoai (khan cap: truyen cung voi .app)
cp config.json Release/config.json
cp .env Release/.env
mkdir -p Release/data
cp data/credentials.json Release/data/credentials.json

echo ""
echo "============================================================"
echo " BUILD THANH CONG!"
echo " Thu muc Release/ chua:"
echo "   - NamcoBot.app  (ung dung chinh, double-click de chay)"
echo "   - config.json   (cau hinh bot)"
echo "   - .env          (API keys)"
echo "   - data/         (Google credentials)"
echo " Gui khach toan bo thu muc Release/"
echo "============================================================"
