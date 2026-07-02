"""
Checkpoint utility — lưu/đọc trạng thái sau từng step để resume khi retry.

File: data/checkpoints/<email_sanitized>.json
Schema:
{
    "email": "...",
    "password": "...",
    "nickname": "...",
    "birthday": "...",
    "completed_steps": [1, 2, 3],   # step nào đã xong
    "bnid_user_code": "...",         # sau step 3
    "parks_phone": "...",            # sau step 4
    "parks_pkey": "...",             # sau step 4
    "parks_member_id": "...",        # sau step 5
    "status": "STEP3_DONE" | "STEP4_DONE" | "SUCCESS" | ...
}
"""

import json
import os
import re
from src.utils.logger import get_logger

log = get_logger("checkpoint")

CHECKPOINT_DIR = "data/checkpoints"


def _email_to_filename(email: str) -> str:
    """Chuyển email thành tên file an toàn."""
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", email)
    return os.path.join(CHECKPOINT_DIR, f"{safe}.json")


def load_checkpoint(email: str) -> dict | None:
    """Đọc checkpoint hiện tại của email. Trả về None nếu chưa có."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = _email_to_filename(email)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.info(f"[Checkpoint] Load: {email} | Steps done: {data.get('completed_steps', [])}")
        return data
    except Exception as e:
        log.warning(f"[Checkpoint] Lỗi đọc checkpoint {path}: {e}")
        return None


def save_checkpoint(email: str, data: dict) -> None:
    """Ghi checkpoint. data phải chứa ít nhất 'completed_steps'."""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = _email_to_filename(email)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"[Checkpoint] Saved: {email} | Steps done: {data.get('completed_steps', [])}")
    except Exception as e:
        log.warning(f"[Checkpoint] Lỗi ghi checkpoint {path}: {e}")


def clear_checkpoint(email: str) -> None:
    """Xóa checkpoint sau khi hoàn thành (SUCCESS)."""
    path = _email_to_filename(email)
    if os.path.exists(path):
        os.remove(path)
        log.info(f"[Checkpoint] Cleared: {email}")


def step_done(cp: dict, step: int) -> bool:
    """Kiểm tra step đã hoàn thành chưa."""
    return step in cp.get("completed_steps", [])


def mark_step_done(cp: dict, step: int, **kwargs) -> dict:
    """Đánh dấu step hoàn thành và cập nhật dữ liệu vào checkpoint."""
    if "completed_steps" not in cp:
        cp["completed_steps"] = []
    if step not in cp["completed_steps"]:
        cp["completed_steps"].append(step)
    cp.update(kwargs)
    return cp
