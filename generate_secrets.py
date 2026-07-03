"""
Script tạo src/secrets.py từ data/credentials.json và config.json
Chạy lại khi cần cập nhật Google credentials hoặc Sheet ID mới.
"""
import json
from pathlib import Path

def generate():
    root = Path(__file__).parent

    cred_path = root / "data" / "credentials.json"
    cfg_path  = root / "config.json"
    out_path  = root / "src" / "secrets.py"

    if not cred_path.exists():
        print(f"[LOI] Khong tim thay: {cred_path}")
        return
    if not cfg_path.exists():
        print(f"[LOI] Khong tim thay: {cfg_path}")
        return

    creds    = json.loads(cred_path.read_text(encoding="utf-8"))
    cfg      = json.loads(cfg_path.read_text(encoding="utf-8"))
    sheet_id = cfg.get("google_sheet_id", "")

    if not sheet_id:
        print("[LOI] google_sheet_id chua duoc dien trong config.json")
        return

    content = (
        "# AUTO-GENERATED boi generate_secrets.py - KHONG COMMIT FILE NAY\n"
        f'GOOGLE_SHEET_ID = "{sheet_id}"\n\n'
        f"GOOGLE_CREDENTIALS = {json.dumps(creds, indent=4, ensure_ascii=False)}\n"
    )

    out_path.write_text(content, encoding="utf-8")
    print(f"[OK] src/secrets.py da duoc tao thanh cong!")
    print(f"     Sheet ID : {sheet_id}")
    print(f"     Email    : {creds.get('client_email', '?')}")

if __name__ == "__main__":
    generate()
