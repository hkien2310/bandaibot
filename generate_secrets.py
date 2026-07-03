"""
Tạo src/secrets.py từ:
  - config.json          → google_sheet_id
  - data/credentials.json → Google Service Account credentials

Chỉ cần đặt credentials.json vào thư mục data/ rồi chạy build là xong.
"""
import json
from pathlib import Path

def generate():
    root = Path(__file__).parent

    creds_path = root / "data" / "credentials.json"
    cfg_path   = root / "config.json"
    out_path   = root / "src" / "secrets.py"

    # Đọc Sheet ID từ config.json
    if not cfg_path.exists():
        print("[LOI] Khong tim thay config.json")
        return False
    sheet_id = json.loads(cfg_path.read_text(encoding="utf-8")).get("google_sheet_id", "")
    if not sheet_id:
        print("[LOI] Thieu google_sheet_id trong config.json")
        return False

    # Đọc credentials từ data/credentials.json
    if not creds_path.exists():
        print(f"[LOI] Khong tim thay: {creds_path}")
        print("      Dat file credentials.json vao thu muc data/ roi chay lai!")
        return False
    creds = json.loads(creds_path.read_text(encoding="utf-8"))
    if not creds.get("private_key"):
        print("[LOI] credentials.json khong hop le")
        return False

    # Ghi secrets.py
    out_path.write_text(
        "# AUTO-GENERATED - KHONG COMMIT FILE NAY\n"
        f'GOOGLE_SHEET_ID = "{sheet_id}"\n\n'
        f"GOOGLE_CREDENTIALS = {json.dumps(creds, indent=4, ensure_ascii=False)}\n",
        encoding="utf-8"
    )
    print(f"[OK] src/secrets.py da duoc tao!")
    print(f"     Sheet ID : {sheet_id}")
    print(f"     Email    : {creds.get('client_email', '?')}")
    return True

if __name__ == "__main__":
    if not generate():
        exit(1)
