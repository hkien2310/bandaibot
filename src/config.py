import json
import os
import shutil
from pathlib import Path
import sys

# Xác định ROOT_DIR (thư mục gốc cạnh exe)
if getattr(sys, 'frozen', False):
    ROOT_DIR   = Path(sys.executable).parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    ROOT_DIR   = Path(__file__).parent.parent
    BUNDLE_DIR = ROOT_DIR

def _extract_if_missing(rel_path: str):
    dest = ROOT_DIR / rel_path
    src  = BUNDLE_DIR / rel_path
    if not dest.exists() and src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))

# Lần đầu chạy: tự extract config.json cạnh exe
if getattr(sys, 'frozen', False):
    _extract_if_missing("config.json")

def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

# --- config.json: giá trị cố định, đã commit lên git ---
CONFIG_FILE = ROOT_DIR / "config.json"
_cfg = _load_json(CONFIG_FILE)

# --- user_config.json: credentials client tự nhập (local only) ---
USER_CONFIG_FILE = ROOT_DIR / "user_config.json"
_ucfg = _load_json(USER_CONFIG_FILE)

def _get(key, default=""):
    """Ưu tiên: user_config.json > config.json > default"""
    if key in _ucfg:
        return _ucfg[key]
    return _cfg.get(key, default)

# Paths
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Bot settings (cố định trong config.json)
BROWSER_PATH        = _cfg.get("browser_path", "")
HEADLESS            = _cfg.get("headless", False)
WORKER_COUNT        = _cfg.get("worker_count", 1)
EMAIL_OTP_TIMEOUT   = _cfg.get("email_otp_timeout", 120)
SMS_OTP_TIMEOUT     = _cfg.get("sms_otp_timeout", 300)
DEFAULT_PASSWORD    = _cfg.get("default_password", "Namco2025!")
DEFAULT_GENDER      = _cfg.get("default_gender", "回答しない")
DEFAULT_PREFECTURE  = _cfg.get("default_prefecture", "東京都")
KEEP_BROWSER_OPEN   = _cfg.get("keep_browser_open", False)

# Email config
EMAIL_MODE            = _cfg.get("email_mode", "alias")
CATCHALL_EMAIL_PREFIX = _cfg.get("catchall_email_prefix", "acc")
CATCHALL_INBOX        = _get("catchall_inbox", "")
CATCHALL_PASSWORD     = _get("catchall_password", "")
CATCHALL_DOMAIN       = _get("catchall_domain", "")

# SMS config (URL/service cố định, credentials từ user_config)
SMS_ENABLED    = _cfg.get("sms_enabled", True)
SMS_BASE_URL   = _cfg.get("sms_base_url", "https://northdinhjpn.online")
SMS_SERVICE_ID = str(_cfg.get("sms_service_id", "4005"))
SMS_COUNTRY    = _cfg.get("sms_country", "jpn")
SMS_SERVER     = str(_cfg.get("sms_server", "2"))
SMS_USERNAME   = _get("sms_username", "")
SMS_PASSWORD   = _get("sms_password", "")

# Proxy
USE_PROXY              = _cfg.get("use_proxy", True)
MAX_ACCOUNTS_PER_PROXY = int(_cfg.get("max_accounts_per_proxy", 10))

# ── Google Sheets (bundled vào binary khi build) ──────────────────────────
GOOGLE_SHEET_ID = _cfg.get("google_sheet_id", "")

def _load_google_credentials() -> dict:
    """Đọc credentials từ bundle (trong binary) hoặc data/ folder."""
    # Ưu tiên: file trong bundle (đã bake vào app)
    bundle_creds = BUNDLE_DIR / "data" / "credentials.json"
    if bundle_creds.exists():
        return _load_json(bundle_creds)
    # Fallback: file cạnh exe (dev mode)
    local_creds = ROOT_DIR / "data" / "credentials.json"
    return _load_json(local_creds)

GOOGLE_CREDENTIALS = _load_google_credentials()

# Biến cờ hiệu toàn cục để ngắt bot
STOP_FLAG = False
