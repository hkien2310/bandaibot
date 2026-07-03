import json
import os
import shutil
from pathlib import Path
import sys

# Load .env file (dev local) — phải chạy trước khi đọc os.environ
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Xác định thư mục gốc ─────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    ROOT_DIR   = Path(sys.executable).parent   # cạnh exe/app
    BUNDLE_DIR = Path(sys._MEIPASS)            # bên trong binary
else:
    ROOT_DIR   = Path(__file__).parent.parent   # thư mục project
    BUNDLE_DIR = ROOT_DIR

# Lần đầu chạy binary: extract config.json cạnh exe
if getattr(sys, 'frozen', False):
    dest = ROOT_DIR / "config.json"
    src  = BUNDLE_DIR / "config.json"
    if not dest.exists() and src.exists():
        shutil.copy2(str(src), str(dest))

# ── Load JSON configs ─────────────────────────────────────────────────────
def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

CONFIG_FILE      = ROOT_DIR / "config.json"        # cố định, committed
USER_CONFIG_FILE = ROOT_DIR / "user_config.json"    # client nhập qua GUI (local)

_cfg  = _load_json(CONFIG_FILE)
_ucfg = _load_json(USER_CONFIG_FILE)

def _get(key, default=""):
    """
    Thứ tự ưu tiên:
      1. Env var (từ .env hoặc shell) — cho dev/test
      2. user_config.json              — client nhập qua GUI
      3. config.json                   — giá trị cố định
      4. default                       — hardcode fallback
    """
    env_val = os.environ.get(key.upper(), "").strip()
    if env_val:
        return env_val
    if key in _ucfg:
        return _ucfg[key]
    return _cfg.get(key, default)

# ── Paths ─────────────────────────────────────────────────────────────────
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── Bot settings (config.json — cố định) ─────────────────────────────────
BROWSER_PATH       = _cfg.get("browser_path", "")
HEADLESS           = _cfg.get("headless", False)
WORKER_COUNT       = _cfg.get("worker_count", 1)
EMAIL_OTP_TIMEOUT  = _cfg.get("email_otp_timeout", 120)
SMS_OTP_TIMEOUT    = _cfg.get("sms_otp_timeout", 300)
DEFAULT_PASSWORD   = _cfg.get("default_password", "Namco2025!")
DEFAULT_GENDER     = _cfg.get("default_gender", "回答しない")
DEFAULT_PREFECTURE = _cfg.get("default_prefecture", "東京都")
KEEP_BROWSER_OPEN  = _cfg.get("keep_browser_open", False)

# ── Email (mode cố định, credentials qua .env / user_config) ─────────────
EMAIL_MODE            = _cfg.get("email_mode", "alias")
CATCHALL_EMAIL_PREFIX = _cfg.get("catchall_email_prefix", "acc")
CATCHALL_INBOX        = _get("catchall_inbox", "")
CATCHALL_PASSWORD     = _get("catchall_password", "")
CATCHALL_DOMAIN       = _get("catchall_domain", "")

# ── SMS (URL cố định, credentials qua .env / user_config) ────────────────
SMS_ENABLED    = _cfg.get("sms_enabled", True)
SMS_BASE_URL   = _cfg.get("sms_base_url", "https://northdinhjpn.online")
SMS_SERVICE_ID = str(_cfg.get("sms_service_id", "4005"))
SMS_COUNTRY    = _cfg.get("sms_country", "jpn")
SMS_SERVER     = str(_cfg.get("sms_server", "2"))
SMS_USERNAME   = _get("sms_username", "")
SMS_PASSWORD   = _get("sms_password", "")

# ── Proxy ─────────────────────────────────────────────────────────────────
USE_PROXY              = _cfg.get("use_proxy", True)
MAX_ACCOUNTS_PER_PROXY = int(_cfg.get("max_accounts_per_proxy", 10))

# ── Google Sheets (credentials bundled vào binary) ────────────────────────
GOOGLE_SHEET_ID = _cfg.get("google_sheet_id", "")

def _load_google_credentials() -> dict:
    """Đọc credentials.json từ bundle (binary) hoặc data/ (dev)."""
    for base in [BUNDLE_DIR, ROOT_DIR]:
        path = base / "data" / "credentials.json"
        if path.exists():
            return _load_json(path)
    return {}

GOOGLE_CREDENTIALS = _load_google_credentials()

# ── Runtime flag ──────────────────────────────────────────────────────────
STOP_FLAG = False
