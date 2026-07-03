"""
Script tạo src/secrets.py từ:
  1. Environment variables (ưu tiên - dùng trên máy build)
  2. data/credentials.json + config.json (fallback - dùng local)

Env vars cần set trên máy build (1 lần duy nhất):
  NAMCO_SHEET_ID   = Google Sheet ID
  NAMCO_CREDS_PATH = Đường dẫn tới credentials.json (vd: C:\\secrets\\credentials.json)
"""
import json
import os
from pathlib import Path

def generate():
    root    = Path(__file__).parent
    out     = root / "src" / "secrets.py"

    # --- Đọc Sheet ID ---
    sheet_id = os.environ.get("NAMCO_SHEET_ID", "").strip()
    if not sheet_id:
        # Fallback: đọc từ config.json
        cfg_path = root / "config.json"
        if cfg_path.exists():
            sheet_id = json.loads(cfg_path.read_text(encoding="utf-8")).get("google_sheet_id", "")
    if not sheet_id:
        print("[LOI] Chua co NAMCO_SHEET_ID. Set env var hoac dien vao config.json")
        return False

    # --- Đọc Google Credentials ---
    creds = None
    creds_path_env = os.environ.get("NAMCO_CREDS_PATH", "").strip()
    if creds_path_env and Path(creds_path_env).exists():
        creds = json.loads(Path(creds_path_env).read_text(encoding="utf-8"))
        print(f"[OK] Doc credentials tu env: {creds_path_env}")
    else:
        # Fallback: đọc từ data/credentials.json
        local_creds = root / "data" / "credentials.json"
        if local_creds.exists():
            creds = json.loads(local_creds.read_text(encoding="utf-8"))
            print(f"[OK] Doc credentials tu local: {local_creds}")

    if not creds or not creds.get("private_key"):
        print("[LOI] Chua co Google credentials. Set NAMCO_CREDS_PATH hoac dat file vao data/credentials.json")
        return False

    # --- Ghi secrets.py ---
    content = (
        "# AUTO-GENERATED boi generate_secrets.py - KHONG COMMIT FILE NAY\n"
        f'GOOGLE_SHEET_ID = "{sheet_id}"\n\n'
        f"GOOGLE_CREDENTIALS = {json.dumps(creds, indent=4, ensure_ascii=False)}\n"
    )
    out.write_text(content, encoding="utf-8")
    print(f"[OK] src/secrets.py da duoc tao!")
    print(f"     Sheet ID : {sheet_id}")
    print(f"     Email    : {creds.get('client_email', '?')}")
    return True

if __name__ == "__main__":
    ok = generate()
    if not ok:
        exit(1)
