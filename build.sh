#!/bin/bash
# Build ra file chạy độc lập - gói TẤT CẢ vào trong exe

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

# Di chuyển file thực thi vào thư mục Release
if [ -d "dist/NamcoBot.app" ]; then
    cp -r dist/NamcoBot.app Release/
    cp dist/NamcoBot Release/ 2>/dev/null || true
else
    cp dist/NamcoBot.exe Release/
fi

echo "============================================================"
echo "🎉 BUILD THÀNH CÔNG!"
echo "Sản phẩm nằm trong thư mục: /Release/"
echo "Chỉ cần gửi file NamcoBot cho khách là chạy được ngay!"
echo "Lần đầu chạy sẽ tự tạo config.json, .env, data/ cạnh file exe."
echo "============================================================"
