import imaplib
import email
import email.utils
import re
import time
import threading
from datetime import datetime, timezone

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False

import src.config as config
from src.utils.logger import get_logger

log = get_logger("email_reader")

# IMAP servers mapping
IMAP_SERVERS = {
    "gmail.com":      ("imap.gmail.com", 993),
    "googlemail.com": ("imap.gmail.com", 993),
    "icloud.com":     ("imap.mail.me.com", 993),
    "me.com":         ("imap.mail.me.com", 993),
    "mac.com":        ("imap.mail.me.com", 993),
    "outlook.com":    ("imap-mail.outlook.com", 993),
    "hotmail.com":    ("imap-mail.outlook.com", 993),
    "live.com":       ("imap-mail.outlook.com", 993),
    "yahoo.com":      ("imap.mail.yahoo.com", 993),
}

_IMAP_LOCK = threading.Lock()
_shared_imap = None

def _get_imap_host(email_addr: str) -> tuple[str, int]:
    domain = email_addr.split("@")[-1].lower()
    return IMAP_SERVERS.get(domain, (f"imap.{domain}", 993))

def _connect() -> imaplib.IMAP4_SSL:
    """Connect to IMAP server using catch-all config."""
    host, port = _get_imap_host(config.CATCHALL_INBOX)
    log.info(f"IMAP → {host}:{port} ({config.CATCHALL_INBOX})")
    imap = imaplib.IMAP4_SSL(host, port)
    imap.login(config.CATCHALL_INBOX, config.CATCHALL_PASSWORD)
    log.info("✅ IMAP login OK")
    return imap

def _ensure_shared_imap() -> imaplib.IMAP4_SSL:
    global _shared_imap
    if _shared_imap is not None:
        try:
            _shared_imap.noop()
            return _shared_imap
        except Exception:
            try:
                _shared_imap.logout()
            except Exception:
                pass
            _shared_imap = None
    _shared_imap = _connect()
    return _shared_imap

def _get_body_text(msg) -> str:
    """Extract body text from message."""
    parts_plain, parts_html = [], []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if "attachment" in str(part.get("Content-Disposition", "")):
                continue
            try:
                charset = part.get_content_charset() or "utf-8"
                text = part.get_payload(decode=True).decode(charset, errors="ignore")
                if ctype == "text/plain":
                    parts_plain.append(text)
                elif ctype == "text/html":
                    parts_html.append(text)
            except Exception:
                continue
    else:
        try:
            charset = msg.get_content_charset() or "utf-8"
            text = msg.get_payload(decode=True).decode(charset, errors="ignore")
            if msg.get_content_type() == "text/html":
                parts_html.append(text)
            else:
                parts_plain.append(text)
        except Exception:
            pass

    if parts_plain:
        return "\n".join(parts_plain)

    html = "\n".join(parts_html)
    if _HAS_BS4:
        return BeautifulSoup(html, "lxml").get_text(separator=" ")
    return re.sub(r"<[^<]+?>", " ", html)

def _extract_otp(text: str) -> str | None:
    """Extract Bandai Namco ID OTP (6 digits) from email body."""
    # Bandai Namco ID email lists the code as "認証コード" (Verification Code) or "Confirmation Code"
    patterns = [
        r"認証コード[:\s\n**]+(\d{6})",
        r"verification code[:\s\n**]+(\d{6})",
        r"confirmation code[:\s\n**]+(\d{6})",
        r"your code[:\s\n**]+(\d{6})",
        r"\b(\d{6})\b",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return None

def _get_msg_timestamp(msg) -> float:
    try:
        dt = email.utils.parsedate_to_datetime(msg.get("Date", ""))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return time.time()

def fetch_otp_since(
    since_ts: float,
    imap: imaplib.IMAP4_SSL | None = None,
    target_email: str = "",
) -> str | None:
    """
    Search catch-all inbox for Bandai Namco ID registration OTP since since_ts.
    """
    close_after = imap is None
    if close_after:
        imap = _connect()

    try:
        # Hỗ trợ tìm kiếm cả trong INBOX và Thư rác ([Gmail]/Spam hoặc [Gmail]/Spam Mail)
        for folder in ["INBOX", "[Gmail]/Spam", "[Gmail]/Spam Mail"]:
            try:
                status, select_data = imap.select(folder)
                if status != "OK":
                    continue
            except Exception:
                continue

            uids = []
            # Search targets: id.banapassport.net or bandainamcoid.com
            for criteria in [
                ["UNSEEN", "HEADER", "FROM", "banapassport.net"],
                ["UNSEEN", "HEADER", "FROM", "bandainamcoid.com"],
                ["HEADER", "FROM", "banapassport.net"],
                ["HEADER", "FROM", "bandainamcoid.com"],
                ["UNSEEN"], # search all unseen as fallback
            ]:
                try:
                    typ, data = imap.search(None, *criteria)
                    if typ == "OK" and data[0]:
                        uids = data[0].split()
                        break
                except Exception as e:
                    log.debug(f"IMAP search criteria failed {criteria} in {folder}: {e}")
                    continue

            if not uids:
                continue

            log.debug(f"Found {len(uids)} email(s) in {folder}, checking newest first...")

            for uid in reversed(uids):
                try:
                    typ, msg_data = imap.fetch(uid, "(RFC822)")
                    if typ != "OK":
                        continue

                    raw = next(
                        (p[1] for p in msg_data if isinstance(p, tuple) and p[1]),
                        None
                    )
                    if not raw:
                        continue

                    msg = email.message_from_bytes(raw)

                    msg_ts = _get_msg_timestamp(msg)
                    if msg_ts < (since_ts - 60):  # Allow 60s clock skew
                        log.debug(f"  UID={uid.decode()} too old ({datetime.fromtimestamp(msg_ts).strftime('%H:%M:%S')}), skip")
                        continue

                    subj = msg.get("Subject", "")
                    from_hdr = msg.get("From", "")
                    to_hdr = msg.get("To", "") or ""
                    log.debug(f"  UID={uid.decode()} | From={from_hdr} | To={to_hdr} | Subject={subj!r}")

                    # Check if target email matches the To field (for alias/catch-all filtering)
                    if target_email:
                        target_lower = target_email.lower().strip()
                        to_lower = to_hdr.lower().strip()
                        # Some forwards might place target in body or other headers, but typically To is standard.
                        if target_lower not in to_lower:
                            log.debug(f"  UID={uid.decode()} To header '{to_hdr}' does not match target '{target_email}', skip")
                            continue

                    body = _get_body_text(msg)
                    otp = _extract_otp(body)

                    if otp:
                        log.info(f"✅ Found Bandai Namco ID OTP={otp} | UID={uid.decode()} | Folder={folder} | Subject={subj!r}")
                        try:
                            imap.store(uid, "+FLAGS", "\\Seen")
                        except Exception:
                            pass
                        return otp
                    else:
                        log.warning(f"  Email matches filters but failed to extract OTP | Subject={subj!r}")

                except Exception as e:
                    log.warning(f"  Error reading UID={uid.decode()} in {folder}: {e}")
                    continue

        return None

    finally:
        if close_after and imap:
            try:
                imap.logout()
            except Exception:
                pass

def get_bandai_namco_otp(
    since_ts: float | None = None,
    timeout: int = 120,
    poll_interval: int = 5,
    target_email: str = "",
) -> str | None:
    """Poll catch-all inbox for Bandai Namco ID OTP code."""
    if not config.CATCHALL_INBOX or not config.CATCHALL_PASSWORD:
        log.error("❌ CATCHALL_INBOX or CATCHALL_PASSWORD not configured!")
        return None

    if since_ts is None:
        since_ts = time.time()

    log.info(
        f"⏳ Waiting for Bandai Namco ID OTP | Inbox: {config.CATCHALL_INBOX} "
        f"| Since: {datetime.fromtimestamp(since_ts).strftime('%H:%M:%S')} "
        f"| Target: {target_email} | Timeout: {timeout}s"
    )

    deadline = time.time() + timeout
    
    # We acquire lock for each attempt to avoid blocking other threads permanently
    while time.time() < deadline:
        with _IMAP_LOCK:
            try:
                imap = _ensure_shared_imap()
                otp = fetch_otp_since(since_ts=since_ts, imap=imap, target_email=target_email)
                if otp:
                    return otp
            except Exception as e:
                log.warning(f"IMAP search error, will reconnect: {e}")
                global _shared_imap
                _shared_imap = None # Trigger reconnect next time

        remaining = int(deadline - time.time())
        if remaining <= 0:
            break
        log.debug(f"No OTP yet, retrying in {poll_interval}s (remaining {remaining}s)...")
        time.sleep(poll_interval)

    log.warning(f"⏰ Timeout {timeout}s — No OTP found for {target_email}")
    return None

def get_gmail_dot_alias(base_email: str, index: int) -> str:
    """Tạo bí danh chứa dấu chấm cho Gmail để tránh ký tự '+' bị Bandai Namco cấm."""
    username, domain = base_email.split("@", 1)
    if domain.lower() not in ["gmail.com", "googlemail.com"]:
        return base_email
    
    gaps = len(username) - 1
    if gaps <= 0:
        return base_email
        
    # Chuyển index thành chuỗi nhị phân để chèn dấu chấm tại các vị trí bit 1
    binary_str = bin(index % (2 ** gaps))[2:].zfill(gaps)
    result = []
    for i, char in enumerate(username):
        result.append(char)
        if i < gaps and binary_str[i] == '1':
            result.append('.')
    return "".join(result) + "@" + domain

def generate_account_email(account_id: int | str) -> str:
    """Generate email from catch-all domain or gmail alias."""
    prefix = config.CATCHALL_EMAIL_PREFIX or "acc"
    suffix = f"{account_id:05d}" if isinstance(account_id, int) else str(account_id)

    if config.EMAIL_MODE == "alias":
        if not config.CATCHALL_INBOX:
            raise ValueError("CATCHALL_INBOX not configured in .env")
        base, domain = config.CATCHALL_INBOX.split("@", 1)
        if domain.lower() in ["gmail.com", "googlemail.com"]:
            try:
                # Băm suffix hoặc timestamp để ra index số nguyên
                idx = int(suffix)
            except ValueError:
                idx = abs(hash(suffix))
            return get_gmail_dot_alias(config.CATCHALL_INBOX, idx)
        else:
            return f"{base}+{prefix}{suffix}@{domain}"
    else:
        if not config.CATCHALL_DOMAIN:
            raise ValueError("CATCHALL_DOMAIN not configured in .env")
        return f"{prefix}{suffix}@{config.CATCHALL_DOMAIN}"
