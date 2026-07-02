#!/bin/bash
# Build - gói TẤT CẢ vào exe, khách chỉ cần 1 file

echo "Đang kích hoạt môi trường ảo..."
source .venv/bin/activate

echo "Cài đặt PyInstaller nếu chưa có..."
pip install pyinstaller

echo "Đang tiến hành đóng gói (Build)..."
pyinstaller --noconfirm --onefile --windowed \
    --name "NamcoBot" \
    --add-data "src:src" \
    --add-data "config.json:." \
    --add-data ".env:." \
    --add-data "data/credentials.json:data" \
    gui.py

echo "Tạo thư mục Release..."
mkdir -p Release

if [ -d "dist/NamcoBot.app" ]; then
    cp -r dist/NamcoBot.app Release/
    cp dist/NamcoBot Release/ 2>/dev/null || true
else
    cp dist/NamcoBot.exe Release/
fi

echo "============================================================"
echo "🎉 BUILD THÀNH CÔNG!"
echo "Release/ chỉ chứa file NamcoBot - gửi khách chạy luôn."
echo "Lần đầu chạy sẽ tự tạo config.json, .env, data/ cạnh exe."
echo "============================================================"
