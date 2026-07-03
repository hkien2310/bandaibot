import json
import os
import shutil
from pathlib import Path
import sys

# Xác định ROOT_DIR (thư mục gốc)
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    ROOT_DIR = Path(__file__).parent.parent
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

# --- user_config.json: giá trị client tự nhập (gitignored, local only) ---
USER_CONFIG_FILE = ROOT_DIR / "user_config.json"
_ucfg = _load_json(USER_CONFIG_FILE)

def _get(key, default=""):
    """Đọc theo thứ tự ưu tiên: env var > user_config.json > config.json > default"""
    env_val = os.environ.get(key.upper(), "")
    if env_val:
        return env_val
    if key in _ucfg:
        return _ucfg[key]
    return _cfg.get(key, default)

# Paths
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Bot settings (config.json - cố định)
BROWSER_PATH        = _cfg.get("browser_path", "")
HEADLESS            = _cfg.get("headless", False)
WORKER_COUNT        = _cfg.get("worker_count", 1)
EMAIL_OTP_TIMEOUT   = _cfg.get("email_otp_timeout", 120)
SMS_OTP_TIMEOUT     = _cfg.get("sms_otp_timeout", 300)
DEFAULT_PASSWORD    = _cfg.get("default_password", "Namco2025!")
DEFAULT_GENDER      = _cfg.get("default_gender", "回答しない")
DEFAULT_PREFECTURE  = _cfg.get("default_prefecture", "東京都")
KEEP_BROWSER_OPEN   = _cfg.get("keep_browser_open", False)

# Email config - cố định (config.json)
EMAIL_MODE            = _cfg.get("email_mode", "alias")
CATCHALL_EMAIL_PREFIX = _cfg.get("catchall_email_prefix", "acc")

# Email credentials - nhạy cảm (env var > user_config.json)
CATCHALL_INBOX    = _get("catchall_inbox", "")
CATCHALL_PASSWORD = _get("catchall_password", "")
CATCHALL_DOMAIN   = _get("catchall_domain", "")

# SMS config - cố định (config.json)
SMS_ENABLED    = _cfg.get("sms_enabled", True)
SMS_BASE_URL   = _cfg.get("sms_base_url", "https://northdinhjpn.online")
SMS_SERVICE_ID = str(_cfg.get("sms_service_id", "4005"))
SMS_COUNTRY    = _cfg.get("sms_country", "jpn")
SMS_SERVER     = str(_cfg.get("sms_server", "2"))

# SMS credentials - nhạy cảm (env var > user_config.json)
SMS_USERNAME = _get("sms_username", "")
SMS_PASSWORD = _get("sms_password", "")

# Proxy config
USE_PROXY              = _cfg.get("use_proxy", True)
MAX_ACCOUNTS_PER_PROXY = int(_cfg.get("max_accounts_per_proxy", 10))

# ── Secrets (baked vào binary khi build) ──────────────────────────────────
try:
    from src.secrets import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS
except ImportError:
    try:
        from secrets import GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS
    except ImportError:
        GOOGLE_SHEET_ID    = os.environ.get("NAMCO_SHEET_ID", "")
        GOOGLE_CREDENTIALS = None

# Biến cờ hiệu toàn cục để ngắt bot (Stop button)
STOP_FLAG = False
