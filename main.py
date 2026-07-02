import asyncio
import argparse
import sys
import time
from pathlib import Path

# Thêm root path vào PYTHONPATH để import đúng các module
sys.path.append(str(Path(__file__).parent))

import src.config as config
from src.utils.logger import get_logger, add_file_handler
from src.utils.proxy_pool import ProxyPool
from src.utils.google_sheets_manager import GoogleSheetsManager
from src.core.email_reader import generate_account_email
from src.worker import RegistrationWorker

log = get_logger("main")

async def run_worker_async(worker_id, email_queue, proxy_pool, sheets_manager):
    """Bọc RegistrationWorker.run chạy không đồng bộ hoàn toàn để tránh nghẽn log."""
    worker = RegistrationWorker(
        worker_id=worker_id,
        email_queue=email_queue,
        proxy_pool=proxy_pool,
        sheets_manager=sheets_manager
    )
    # Chạy worker.run() trong thread pool của asyncio để tránh block vòng lặp sự kiện chính
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, worker.run)

async def main_async():
    parser = argparse.ArgumentParser(description="Namco Parks Auto Registration Bot")
    parser.add_argument("--workers", type=int, default=None, help="Số luồng chạy song song")
    args = parser.parse_args()

    # --- KIỂM TRA THỜI HẠN SỬ DỤNG (TIMEBOMB) ---
    import datetime
    # Hết tháng 8 có nghĩa là từ ngày 1/9/2026 trở đi sẽ không chạy được nữa
    expiry_date = datetime.date(2026, 9, 1)
    if datetime.date.today() >= expiry_date:
        print("\n" + "="*50)
        print("❌ PHẦN MỀM ĐÃ HẾT HẠN SỬ DỤNG (License Expired).")
        print("Vui lòng liên hệ quản trị viên để gia hạn.")
        print("="*50 + "\n")
        sys.exit(1)
    # --------------------------------------------

    # Khởi tạo log file
    add_file_handler(str(config.DATA_DIR / "run.log"))
    log.info("="*50)
    log.info("🔥 BẮT ĐẦU CHẠY BOT ĐĂNG KÝ NAMCO PARKS")
    log.info("="*50)

    # 1. Cấu hình số luồng
    worker_count = args.workers if args.workers is not None else config.WORKER_COUNT
    log.info(f"Số luồng (workers): {worker_count}")

    # 2. Khởi tạo GoogleSheetsManager
    sheets_manager = GoogleSheetsManager()
    if not sheets_manager.is_connected():
        log.error("Không thể kết nối Google Sheets. Dừng chương trình.")
        return

    # 3. Load proxies từ Google Sheets
    active_proxies = sheets_manager.get_active_proxies()
    proxy_pool = ProxyPool(active_proxies)

    from queue import Queue

    # 4. Vòng lặp chính: Đọc email PENDING từ Sheets và chạy
    while True:
        # Lấy từng mẻ 50 email để chạy (giảm thiểu xung đột nếu nhiều máy cùng chạy)
        emails_to_process = sheets_manager.get_pending_emails(batch_size=50)
        
        if not emails_to_process:
            log.info("✅ Không còn tài khoản nào có trạng thái PENDING/Trống trên Sheets. Hoàn tất!")
            break

        email_queue = Queue()
        for email_data in emails_to_process:
            email_queue.put(email_data)

        log.info(f"Đang xử lý mẻ {len(emails_to_process)} email...")

        # Khởi chạy các worker không đồng bộ song song
        tasks = []
        for i in range(1, worker_count + 1):
            # Truyền sheets_manager vào worker thay vì csv_writer
            tasks.append(run_worker_async(i, email_queue, proxy_pool, sheets_manager))
            # Delay nhỏ giữa các worker để tránh conflict khởi động browser
            await asyncio.sleep(2)

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            log.warning("Nhận lệnh ngắt bàn phím (Ctrl+C). Đang dừng chương trình...")
            break
            
        log.info("🔄 Hoàn thành mẻ hiện tại. Kiểm tra mẻ tiếp theo...")
        await asyncio.sleep(2)

    log.info("="*50)
    log.info("🎉 BOT ĐÃ HOÀN TẤT CHƯƠNG TRÌNH")
    log.info("="*50)

def main():
    # Buộc stdout flush liên tục
    import os
    sys.stdout.reconfigure(line_buffering=True)
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
