import os
import json
import shutil
from pathlib import Path
from dotenv import load_dotenv

import sys

# Xác định ROOT_DIR (thư mục gốc)
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    ROOT_DIR = Path(__file__).parent.parent
    BUNDLE_DIR = ROOT_DIR

def _extract_if_missing(rel_path: str):
    """Extract file từ bundle ra cạnh exe nếu chưa có."""
    dest = ROOT_DIR / rel_path
    src = BUNDLE_DIR / rel_path
    if not dest.exists() and src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dest))

# Lần đầu chạy: tự tạo config files cạnh exe
if getattr(sys, 'frozen', False):
    _extract_if_missing("config.json")
    _extract_if_missing(".env")
    _extract_if_missing("data/credentials.json")

# Load .env
ENV_FILE = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_FILE)

# Load config.json
CONFIG_FILE = ROOT_DIR / "config.json"
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        _json_config = json.load(f)
else:
    _json_config = {}

# Paths
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Email config
EMAIL_MODE = os.getenv("EMAIL_MODE", "alias")
CATCHALL_INBOX = os.getenv("CATCHALL_INBOX", "")
CATCHALL_PASSWORD = os.getenv("CATCHALL_PASSWORD", "")
CATCHALL_DOMAIN = os.getenv("CATCHALL_DOMAIN", "")
CATCHALL_EMAIL_PREFIX = os.getenv("CATCHALL_EMAIL_PREFIX", "acc")

# SMS config
SMS_ENABLED = os.getenv("SMS_ENABLED", "true").lower() == "true"
SMS_BASE_URL = os.getenv("SMS_BASE_URL", "https://northdinhjpn.online")
SMS_USERNAME = os.getenv("SMS_USERNAME", "")
SMS_PASSWORD = os.getenv("SMS_PASSWORD", "")
SMS_SERVICE_ID = os.getenv("SMS_SERVICE_ID", "1017")
SMS_COUNTRY = os.getenv("SMS_COUNTRY", "jpn")
SMS_SERVER = os.getenv("SMS_SERVER", "2")

# Proxy config
USE_PROXY = os.getenv("USE_PROXY", "true").lower() == "true"
MAX_ACCOUNTS_PER_PROXY = int(os.getenv("MAX_ACCOUNTS_PER_PROXY", "5"))

# Config from JSON
BROWSER_PATH = _json_config.get("browser_path", "")
HEADLESS = _json_config.get("headless", False)
HAS_BNID = _json_config.get("has_bnid", False)
GOOGLE_SHEET_ID = _json_config.get("google_sheet_id", "")
WORKER_COUNT = _json_config.get("worker_count", 1)
EMAIL_OTP_TIMEOUT = _json_config.get("email_otp_timeout", 120)
SMS_OTP_TIMEOUT = _json_config.get("sms_otp_timeout", 300)
DEFAULT_PASSWORD = _json_config.get("default_password", "Namco2025!")
DEFAULT_GENDER = _json_config.get("default_gender", "回答しない")
DEFAULT_PREFECTURE = _json_config.get("default_prefecture", "東京都")
# Giữ browser mở sau khi xong để debug (set false để tự đóng trong production)
KEEP_BROWSER_OPEN = _json_config.get("keep_browser_open", False)

# Biến cờ hiệu toàn cục để ngắt bot (Stop button)
STOP_FLAG = False
