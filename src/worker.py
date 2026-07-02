import asyncio
import traceback
import src.config as config
import csv
from queue import Queue, Empty
from src.core.browser import BrowserInstance
from src.flows.step1_connect import run_step1
from src.flows.step2_bnid_click import run_step2
from src.flows.step3_bnid_register import run_step3
from src.flows.step4_parks_profile import run_step4
from src.flows.step5_sms_verification import run_step5
from src.utils.data_gen import generate_birthday, generate_nickname, generate_password
from src.utils.logger import get_logger, set_worker_prefix
from src.utils.checkpoint import load_checkpoint, save_checkpoint, clear_checkpoint, step_done, mark_step_done

log = get_logger("worker")

class RegistrationWorker:
    def __init__(self, worker_id: int, email_queue: Queue, proxy_pool, sheets_manager):
        self.worker_id = worker_id
        self.email_queue = email_queue
        self.proxy_pool = proxy_pool
        self.sheets_manager = sheets_manager

    def run(self):
        """Hàm chạy của luồng Thread."""
        set_worker_prefix(f"Worker-{self.worker_id}")
        log.info("Worker started.")
        
        while True:
            try:
                # Lấy email từ queue, timeout 5 giây để thoát nếu hết hàng
                email_data = self.email_queue.get(timeout=5)
                email = email_data["email"]
                email_password = email_data.get("email_password", "")
                raw_email = email_data.get("raw_email", email)
            except Empty:
                log.info("Queue trống. Worker kết thúc.")
                break

            # (Không cần check CSV nữa vì get_pending_emails đã lọc rồi)
            # Load checkpoint nếu có (resume từ bước trước)
            cp = load_checkpoint(email) or {}

            # Sinh/đọc dữ liệu — dùng checkpoint nếu có để đảm bảo nhất quán
            password = cp.get("password") or generate_password(email)
            birthday = cp.get("birthday") or generate_birthday(email)
            nickname = cp.get("nickname") or generate_nickname(email)

            # Cập nhật checkpoint với dữ liệu cơ bản
            cp.update({"email": email, "password": password, "birthday": birthday, "nickname": nickname})
            save_checkpoint(email, cp)
            
            # Khởi tạo thông tin ghi kết quả ban đầu
            result_data = {
                "email": email,
                "bandai_password": password,
                "namco_password": password,
                "nickname": nickname,
                "phone": cp.get("parks_phone", ""),
                "bnid_user_code": cp.get("bnid_user_code", ""),
                "proxy_used": "",
                "status": "PROCESSING",
                "error_details": ""
            }

            # Biến cục bộ lưu trạng thái đã đăng ký BNID hay chưa để xoay tua khi lỗi proxy
            # Nếu tài khoản đã có bnid_user_code nhưng chưa đăng ký xong (vẫn chạy tiếp) -> phải đi luồng 2 (Login)
            has_bnid_local = True if cp.get("bnid_user_code") else cp.get("has_bnid", config.HAS_BNID)

            
            # Chỉ thử 1 lần cho mỗi lượt chạy. Lỗi thì chuyển sang account tiếp theo luôn.
            max_retries = 1
            success = False
            for attempt in range(1, max_retries + 1):
                proxy = None
                proxy_idx = -1
                proxy_str = "Direct"
                
                # Tìm và kiểm tra proxy sống trước khi bắt đầu flow
                import requests
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                proxy, proxy_idx = None, -1
                proxy_str = "Direct"
                if config.USE_PROXY:
                    proxy_attempts = 0
                    max_proxy_attempts = 3
                    
                    while proxy_attempts < max_proxy_attempts:
                        proxy_attempts += 1
                        proxy, proxy_idx = self.proxy_pool.get_next_proxy()
                        proxy_str = proxy["raw"] if proxy else "Direct"
                        
                        if not proxy:
                            log.error("❌ KHO PROXY ĐÃ CẠN KIỆT (CHẾT CHÙM). TẠM DỪNG TOÀN BỘ!")
                            with self.email_queue.mutex:
                                self.email_queue.queue.clear()
                            break  # Hết proxy
                            
                        log.info(f"🔄 Đang kiểm tra proxy ({proxy_attempts}/{max_proxy_attempts}): {proxy_str}...")
                        requests_proxy = proxy_str
                        # Chuyển đổi format "http://host:port:user:pass" sang "http://user:pass@host:port" cho requests
                        if proxy_str:
                            p_parts = proxy_str.replace("http://", "").replace("https://", "").split(":")
                            if len(p_parts) == 4:
                                requests_proxy = f"http://{p_parts[2]}:{p_parts[3]}@{p_parts[0]}:{p_parts[1]}"
                                
                        proxies_dict = {
                            "http": requests_proxy,
                            "https": requests_proxy
                        }
                        try:
                            r = requests.get("https://parks2.bandainamco-am.co.jp/", proxies=proxies_dict, timeout=10, verify=False)
                            r.raise_for_status()
                            log.info(f"✅ Proxy còn sống và truy cập được Namco Parks!")
                            break
                        except Exception as e:
                            log.warning(f"❌ Proxy chết ({type(e).__name__}), đổi proxy khác...")
                            self.proxy_pool.mark_failed(proxy_idx)
                            proxy = None  # Đặt lại None để báo hiệu chưa có proxy sống
                else:
                    log.info("⚠️ Chạy KHÔNG DÙNG PROXY theo cấu hình (USE_PROXY=false)")
                
                result_data["proxy_used"] = proxy_str
                
                log.info(f"🚀 [Attempt {attempt}/{max_retries}] Bắt đầu xử lý: {email} | Proxy: {proxy_str} | HasBNID: {has_bnid_local}")
                
                # Cập nhật status lên sheet Mails (dùng raw_email để match dòng trên Sheet)
                result_data["status"] = "PROCESSING"
                self.sheets_manager.update_email_status(raw_email, "PROCESSING")
                
                try:
                    if config.USE_PROXY and not proxy:
                        if len(self.proxy_pool.proxies) == 0:
                            raise Exception("KHO_PROXY_CAN_KIET")
                        else:
                            raise Exception("Không tìm được proxy sống sau 3 lần thử.")
                        
                    asyncio.run(self._process_account_async(email, password, nickname, birthday, proxy, result_data, has_bnid_local, cp, email_password))
                    # Nếu thành công
                    has_bnid_local = True
                    success = True
                    self.proxy_pool.mark_success(proxy_idx)
                    clear_checkpoint(email)  # Xóa checkpoint sau khi SUCCESS
                    break
                except Exception as e:
                    error_msg = str(e)
                    log.warning(f"⚠️ [Attempt {attempt} Thất bại] Lỗi khi xử lý {email}: {error_msg}")
                    
                    # ─── Lỗi cạn kiệt proxy ───
                    if "KHO_PROXY_CAN_KIET" in error_msg:
                        log.warning("Hoàn trả account về PENDING do proxy cạn kiệt trước khi chạy.")
                        result_data["status"] = "PENDING"
                        result_data["error_details"] = "Proxy pool cạn kiệt"
                        break

                    # ─── Phân loại lỗi: KHÔNG RETRY vs CÓ THỂ RETRY ───
                    NO_RETRY_KEYWORDS = [
                        "EMAIL_ALREADY_IN_USE",          # Email đã đăng ký rồi
                        "Email đã được sử dụng",         # Thông báo tiếng Việt
                        "KeyboardInterrupt",             # User tự tắt
                    ]
                    is_permanent = any(kw in error_msg for kw in NO_RETRY_KEYWORDS)
                    
                    if is_permanent:
                        log.error(f"🚫 Lỗi KHÔNG THỂ RETRY: {error_msg[:200]}")
                        if "EMAIL_ALREADY_IN_USE" in error_msg or "Email đã được sử dụng" in error_msg:
                            result_data["status"] = "ALREADY_REGISTERED"
                        else:
                            result_data["status"] = "ABORTED"
                        result_data["error_details"] = error_msg[:200]
                        clear_checkpoint(email) # Xóa checkpoint dọn rác ổ cứng vì không bao giờ chạy lại
                        break  # Thoát vòng retry ngay
                    
                    # ─── Lỗi CÓ THỂ RETRY ───
                    # Đánh dấu proxy chết nếu lỗi mạng
                    if "net::ERR_" in error_msg or "Target page, context or browser has been closed" in error_msg or "Timeout" in error_msg:
                        log.warning(f"   -> Lỗi mạng/trình duyệt, đánh dấu proxy chết...")
                        self.proxy_pool.mark_failed(proxy_idx)
                    
                    # Nếu đã có BNID thì lần retry tiếp sẽ đăng nhập thay vì đăng ký
                    if result_data["bnid_user_code"] != "":
                        has_bnid_local = True
                        cp["has_bnid"] = True
                        save_checkpoint(email, cp)
                        log.info("   -> Đã có BNID. Lần thử tiếp sẽ đăng nhập thay vì đăng ký.")

                    result_data["status"] = "FAILED"
                    result_data["error_details"] = error_msg[:200]
                        
                    if attempt == max_retries:
                        log.error(f"❌ Đã thử {max_retries} lần đều thất bại cho {email}")
                        break
                    else:
                        log.info("⏳ Lỗi có thể retry. Thử lại sau 2 giây...")
                        import time
                        time.sleep(2)

            # Kết quả cuối cùng — Ghi vào Google Sheets
            self.sheets_manager.update_email_status(raw_email, result_data["status"])
            self.sheets_manager.append_account(result_data)
            self.email_queue.task_done()
            log.info(f"Kết thúc xử lý tài khoản {email}\n" + "-"*50)

    async def _process_account_async(self, email, password, nickname, birthday, proxy, result_data, has_bnid_local, cp: dict, email_password: str = ""):
        """Chạy các bước đăng ký tuần tự trong cùng một event loop."""
        browser = BrowserInstance(worker_id=self.worker_id, proxy=proxy)
        try:
            page = await browser.start()

            # ═══════════════════════════════════════════════
            # CÁC BƯỚC ĐĂNG KÝ (CÓ THỂ RESUME TỪ CHECKPOINT)
            # ═══════════════════════════════════════════════

            # Step 1: Vào trang chủ + Click link đăng ký
            if 1 not in cp.get("steps_done", []):
                try:
                    await run_step1(page)
                    cp = mark_step_done(cp, 1)
                    save_checkpoint(email, cp)
                except Exception as e:
                    raise Exception(f"Lỗi Bước 1 (Vào trang chủ): {str(e).split('Call log')[0].strip()}")

            # Step 2: Click nút vàng Get BNID
            if 2 not in cp.get("steps_done", []):
                try:
                    await run_step2(page, has_bnid=has_bnid_local)
                    cp = mark_step_done(cp, 2)
                    save_checkpoint(email, cp)
                except Exception as e:
                    raise Exception(f"Lỗi Bước 2 (Click nút Get BNID): {str(e).split('Call log')[0].strip()}")

            # Step 3: Đăng ký BNID + Nhập OTP Email + Bóc BNID User Code
            if 3 not in cp.get("steps_done", []):
                try:
                    bnid_user_code = await run_step3(page, email, password, birthday, has_bnid=has_bnid_local, email_password=email_password)
                    if bnid_user_code and bnid_user_code != "ALREADY_LOGGED_IN":
                        result_data["bnid_user_code"] = bnid_user_code
                        cp["bnid_user_code"] = bnid_user_code
                    cp = mark_step_done(cp, 3, bnid_user_code=bnid_user_code if bnid_user_code else None)
                    cp["has_bnid"] = True
                    save_checkpoint(email, cp)
                    log.info(f"✅ Step 3 done — BNID: {bnid_user_code}")
                    # (Không cần append giữa chừng lên Sheets để tránh rác data)
                except Exception as e:
                    err = str(e)
                    if "Không nhận được OTP email" in err:
                        raise Exception("Lỗi Bước 3 (OTP Email): Không nhận được OTP từ Bandai Namco sau 120s.")
                    elif "EMAIL_ALREADY_IN_USE" in err:
                        raise Exception("Lỗi Bước 3 (Tạo BNID): Email đã được sử dụng.")
                    else:
                        raise Exception(f"Lỗi Bước 3 (Tạo BNID): Mạng chậm hoặc web thay đổi ({err.split('Call log')[0].strip()})")

            # Cập nhật BNID từ checkpoint nếu có
            if cp.get("bnid_user_code") and not result_data.get("bnid_user_code"):
                result_data["bnid_user_code"] = cp["bnid_user_code"]

            # Step 4: Điền Profile Namco Parks + Thuê số điện thoại
            if 4 not in cp.get("steps_done", []):
                try:
                    step4_result = await run_step4(page, email, password, nickname, birthday)
                    phone, pkey = step4_result  # run_step4 luôn trả tuple (phone, pkey)
                    
                    if phone == "ALREADY_REGISTERED":
                        log.info(f"🎉 Tài khoản {email} đã được liên kết Namco Parks và xác thực SĐT trước đó.")
                        result_data["status"] = "SUCCESS"
                        result_data["error_details"] = "Đã liên kết Namco Parks từ trước"
                        clear_checkpoint(email)
                        return  # Kết thúc sớm

                    result_data["phone"] = phone
                    cp = mark_step_done(cp, 4, parks_phone=phone, parks_pkey=pkey)
                    save_checkpoint(email, cp)
                    log.info(f"✅ Step 4 done — Phone: {phone}")
                    # (Không cần append giữa chừng)
                except Exception as e:
                    raise Exception(f"Lỗi Bước 4 (Điền Profile): {str(e).split('Call log')[0].strip()}")

            # Step 5: Xác thực SMS OTP
            if 5 not in cp.get("steps_done", []):
                phone = cp.get("parks_phone", result_data.get("phone", ""))
                pkey = cp.get("parks_pkey", "")
                try:
                    await run_step5(page, phone, pkey)
                    cp = mark_step_done(cp, 5)
                    save_checkpoint(email, cp)
                    log.info("✅ Step 5 done — SMS Verified successfully")
                except Exception as e:
                    err = str(e)
                    if "SMS_OTP_TIMEOUT" in err:
                        raise Exception(f"Lỗi Bước 5 (Xác thực SMS): Không nhận được OTP từ API (SĐT: {phone})")
                    else:
                        raise Exception(f"Lỗi Bước 5 (Xác thực SMS): {err.split('Call log')[0].strip()}")

            # ═══════════════════════════════════════════════
            # HOÀN THÀNH — Đánh dấu SUCCESS
            # ═══════════════════════════════════════════════
            result_data["status"] = "SUCCESS"

            # Lấy BNID từ portal nếu step 3 không bóc được
            if not result_data.get("bnid_user_code"):
                try:
                    log.info("🔍 Đang truy cập portal BNID để lấy User Code...")
                    await page.goto("https://account.bandainamcoid.com/portal.html", timeout=20000)
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    text = await page.evaluate("() => document.body ? document.body.innerText : ''")
                    import re
                    match = re.search(r'\b(?:B\d{12}|\d{12}|\d{4}[-\s]?\d{4}[-\s]?\d{4})\b', text)
                    if match:
                        bnid_code = match.group(0).strip()
                        log.info(f"✅ Đã lấy được BNID User Code từ Portal: {bnid_code}")
                        result_data["bnid_user_code"] = bnid_code
                        cp["bnid_user_code"] = bnid_code
                        save_checkpoint(email, cp)
                    else:
                        log.warning("⚠️ Không tìm thấy BNID User Code trên portal.")
                except Exception as e:
                    log.warning(f"⚠️ Lỗi khi lấy BNID User Code: {e}")

            log.info(f"✅ Đăng ký thành công cho tài khoản {email}")


        except Exception as e:
            # Chụp screenshot lỗi nếu trình duyệt vẫn đang chạy
            if browser and browser.context:
                try:
                    screenshot_path = f"data/error_fatal_{email.replace('+', '_')}.png"
                    if browser.context.pages:
                        await browser.context.pages[0].screenshot(path=screenshot_path)
                        log.info(f"Đã chụp screenshot lỗi fatal: {screenshot_path}")
                except Exception as se:
                    log.debug(f"Không thể chụp screenshot lỗi fatal: {se}")
            raise e
        finally:
            # Giữ browser mở để quan sát nếu KEEP_BROWSER_OPEN=true
            if config.KEEP_BROWSER_OPEN and browser and browser.context:
                log.info("⏸️  KEEP_BROWSER_OPEN=true — Giữ browser mở. Nhấn [ENTER] để đóng...")
                await asyncio.to_thread(input, "")
            # Đóng browser và xóa data
            if browser:
                await browser.close()
