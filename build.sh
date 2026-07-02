#!/bin/bash
# Kịch bản Build ra file chạy độc lập cho Mac/Windows

echo "Đang kích hoạt môi trường ảo..."
source .venv/bin/activate

echo "Cài đặt PyInstaller nếu chưa có..."
pip install pyinstaller

echo "Đang tiến hành đóng gói (Build)..."
# Build 1 file duy nhất, có cửa sổ UI, đính kèm folder src vào ruột file exe
pyinstaller --noconfirm --onefile --windowed \
    --name "NamcoBot" \
    --add-data "src:src" \
    gui.py

echo "Tạo thư mục Release..."
mkdir -p Release
# Di chuyển file thực thi vào thư mục Release
if [ -d "dist/NamcoBot.app" ]; then
    # Trên Mac
    cp -r dist/NamcoBot.app Release/
    cp dist/NamcoBot Release/ 2>/dev/null || true
else
    # Trên Windows
    cp dist/NamcoBot.exe Release/
fi

# Copy các file cấu hình ra ngoài cạnh file thực thi
cp config.json Release/
cp .env Release/

echo "============================================================"
echo "🎉 BUILD THÀNH CÔNG!"
echo "Sản phẩm nằm trong thư mục: /Release/"
echo "Bạn chỉ cần nén (ZIP) thư mục Release này và gửi cho người khác là chạy được ngay."
echo "============================================================"
