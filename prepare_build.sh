#!/bin/bash
# Tao goi file can thiet de build tren Windows
# Chay tren Mac, sau do copy file zip sang Windows

OUT="build_secrets.zip"

echo "Dong goi file build secrets..."
zip -j "$OUT" src/secrets.py config.json

echo ""
echo "Da tao: $OUT"
echo "Copy file nay sang Windows, giai nen vao dung thu muc du an roi chay build.bat"
echo ""
echo "Tren Windows:"
echo "  1. git clone https://github.com/hkien2310/bandaibot"
echo "  2. Copy secrets.py vao thu muc src/"
echo "  3. Copy config.json vao thu muc goc"
echo "  4. Chay build.bat"
