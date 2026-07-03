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
echo "[2/4] Tao src/secrets.py tu env vars..."
python3 generate_secrets.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[LOI] Khong tao duoc secrets.py!"
    echo "Set env vars 1 lan tren may nay:"
    echo "  export NAMCO_SHEET_ID='your-sheet-id'"
    echo "  export NAMCO_CREDS_PATH='/path/to/credentials.json'"
    exit 1
fi

echo ""
echo "[3/4] Cai dat Playwright browser (Chromium)..."
playwright install chromium

echo ""
echo "[4/4] Build NamcoBot.app..."
pyinstaller --noconfirm --onedir --windowed \
    --name "NamcoBot" \
    --add-data "src:src" \
    --add-data "config.json:." \
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
echo "[4/4] Tao thu muc Release..."
rm -rf Release
mkdir -p Release

# Copy app bundle
cp -r dist/NamcoBot.app Release/

# Chỉ copy config.json (SMS/email settings) - KHÔNG copy data/ (secrets đã baked vào binary)
cp config.json Release/config.json

echo ""
echo "============================================================"
echo " BUILD THANH CONG!"
echo " Thu muc Release/ chua:"
echo "   - NamcoBot.app  (ung dung chinh, double-click de chay)"
echo "   - config.json   (SMS/email settings cua khach)"
echo ""
echo " Sheet ID va Google credentials da BAKED vao binary."
echo " Gui khach toan bo thu muc Release/"
echo "============================================================"
