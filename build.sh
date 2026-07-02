#!/bin/bash
# Build ra file chạy độc lập

echo "Đang kích hoạt môi trường ảo..."
source .venv/bin/activate

echo "Cài đặt PyInstaller nếu chưa có..."
pip install pyinstaller

echo "Đang tiến hành đóng gói (Build)..."
pyinstaller --noconfirm --onefile --windowed \
    --name "NamcoBot" \
    --add-data "src:src" \
    gui.py

echo "Tạo thư mục Release..."
mkdir -p Release
mkdir -p Release/data

# Copy file thực thi
if [ -d "dist/NamcoBot.app" ]; then
    cp -r dist/NamcoBot.app Release/
    cp dist/NamcoBot Release/ 2>/dev/null || true
else
    cp dist/NamcoBot.exe Release/
fi

# Copy config ra cạnh exe
cp config.json Release/
cp .env Release/
cp data/credentials.json Release/data/ 2>/dev/null || true

echo "============================================================"
echo "🎉 BUILD THÀNH CÔNG!"
echo "Sản phẩm nằm trong thư mục: /Release/"
echo "Zip cả thư mục Release gửi khách là chạy được."
echo "============================================================"
