import gspread
import threading
from datetime import datetime
from google.oauth2.service_account import Credentials
import src.config as config
from src.utils.logger import get_logger

log = get_logger("google_sheets")

class GoogleSheetsManager:
    def __init__(self):
        self.lock = threading.Lock()
        
        if not config.GOOGLE_SHEET_ID:
            log.error("Thiếu GOOGLE_SHEET_ID trong config.json")
            self.client = None
            return

        cred_path = config.DATA_DIR / "credentials.json"
        if not cred_path.exists():
            log.error(f"Không tìm thấy file credentials tại {cred_path}")
            self.client = None
            return

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            credentials = Credentials.from_service_account_file(str(cred_path), scopes=scopes)
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(config.GOOGLE_SHEET_ID)
            
            # Khởi tạo các tabs (tự động tạo nếu chưa có)
            self.mails_sheet = self._get_or_create_worksheet("Mails", ["Email", "Status", "Updated At"])
            self.proxies_sheet = self._get_or_create_worksheet("Proxies", ["Proxy", "Status"])
            
            self.accounts_columns = [
                "Email", "Bandai Password", "Namco Password", "Nickname", 
                "Phone", "BNID", "Proxy Used", "Status", "Created At", "Error Details"
            ]
            self.accounts_sheet = self._get_or_create_worksheet("Accounts", self.accounts_columns)
            
            log.info("✅ Kết nối Google Sheets thành công!")
        except Exception as e:
            log.error(f"❌ Lỗi kết nối Google Sheets: {e}")
            self.client = None

    def _get_or_create_worksheet(self, title, headers):
        try:
            sheet = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            sheet = self.spreadsheet.add_worksheet(title=title, rows="1000", cols=str(len(headers)))
            sheet.append_row(headers)
            log.info(f"Tạo mới sheet {title}")
        return sheet

    def is_connected(self):
        return self.client is not None

    def get_active_proxies(self) -> list:
        if not self.is_connected():
            return []
        try:
            records = self.proxies_sheet.get_all_records()
            # Lọc các proxy có Status là ACTIVE hoặc rỗng
            proxies = [str(r.get("Proxy")).strip() for r in records if r.get("Proxy") and str(r.get("Status", "")).upper() in ["ACTIVE", ""]]
            log.info(f"Đã load {len(proxies)} proxies từ Google Sheets")
            return proxies
        except Exception as e:
            log.error(f"Lỗi đọc proxies từ Sheets: {e}")
            return []

    def _parse_email_combo(self, raw: str) -> dict:
        """Tách chuỗi combo 'email|pass|token|...' thành dict."""
        parts = raw.strip().split("|")
        result = {"email": parts[0].strip(), "raw_email": raw.strip()}
        if len(parts) >= 2 and parts[1].strip():
            result["email_password"] = parts[1].strip()
        return result

    def get_pending_emails(self, batch_size=100) -> list:
        if not self.is_connected():
            return []
        
        with self.lock:
            try:
                # Đọc toàn bộ dữ liệu (trừ header)
                all_values = self.mails_sheet.get_all_values()
                if len(all_values) <= 1:
                    return []
                
                headers = all_values[0]
                pending_emails = []
                updates = [] # Danh sách các ô cần cập nhật thành PROCESSING
                
                # Tìm index của các cột
                try:
                    email_idx = headers.index("Email")
                    status_idx = headers.index("Status")
                    updated_idx = headers.index("Updated At")
                except ValueError:
                    log.error("Sheet Mails thiếu cột Email, Status hoặc Updated At")
                    return []

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for row_idx_0_based, row in enumerate(all_values[1:]):
                    row_idx = row_idx_0_based + 2 # Do bỏ header và gspread dùng index 1-based
                    
                    raw_email = row[email_idx].strip() if len(row) > email_idx else ""
                    status = row[status_idx].strip().upper() if len(row) > status_idx else ""
                    
                    if raw_email and status in ["", "PENDING"]:
                        parsed = self._parse_email_combo(raw_email)
                        pending_emails.append(parsed)
                        
                        # Chuẩn bị dữ liệu để update hàng loạt
                        # Update Status (cột B), Update At (cột C)
                        updates.append({
                            'range': f'B{row_idx}:C{row_idx}',
                            'values': [['PROCESSING', now_str]]
                        })
                        
                        if len(pending_emails) >= batch_size:
                            break
                
                if updates:
                    self.mails_sheet.batch_update(updates)
                    log.info(f"Đã lấy {len(pending_emails)} emails và đánh dấu PROCESSING trên Sheets")
                
                return pending_emails
                
            except Exception as e:
                log.error(f"Lỗi đọc/cập nhật emails từ Sheets: {e}")
                return []

    def update_email_status(self, email: str, new_status: str):
        if not self.is_connected():
            return
        
        with self.lock:
            try:
                # Phải tìm dòng chứa email này (email ở đây có thể là raw_email)
                cell = self.mails_sheet.find(email)
                if cell:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.mails_sheet.update(f"B{cell.row}:C{cell.row}", [[new_status, now_str]])
            except gspread.exceptions.CellNotFound:
                log.warning(f"Không tìm thấy email {email} trong sheet Mails để cập nhật status")
            except Exception as e:
                log.error(f"Lỗi khi update status cho email {email}: {e}")

    def append_account(self, data: dict):
        if not self.is_connected():
            return
        
        row = []
        for col in self.accounts_columns:
            # Map tên cột CSV cũ sang tên cột Sheet nếu cần (hoặc truyền data chuẩn)
            # data thường có key dạng chữ thường: email, bandai_password...
            # Nên ta map lại
            key_map = {
                "Email": "email",
                "Bandai Password": "bandai_password",
                "Namco Password": "namco_password",
                "Nickname": "nickname",
                "Phone": "phone",
                "BNID": "bnid_user_code",
                "Proxy Used": "proxy_used",
                "Status": "status",
                "Created At": "created_at",
                "Error Details": "error_details"
            }
            key = key_map.get(col, col.lower())
            
            val = data.get(key, "")
            # Điền mặc định created_at nếu thành công
            if key == "created_at" and not val and data.get("status") == "SUCCESS":
                val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row.append(str(val))
            
        with self.lock:
            try:
                self.accounts_sheet.append_row(row)
                log.info(f"Đã ghi kết quả acc {data.get('email')} lên Google Sheets")
            except Exception as e:
                log.error(f"Lỗi khi ghi acc {data.get('email')} lên Sheets: {e}")
                # Backup vào file local nếu lỗi
                self._backup_to_local(row)
                
    def _backup_to_local(self, row: list):
        import csv
        backup_file = config.DATA_DIR / "accounts_backup.csv"
        try:
            with open(backup_file, "a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if backup_file.stat().st_size == 0:
                    writer.writerow(self.accounts_columns)
                writer.writerow(row)
            log.info(f"Đã backup acc vào {backup_file}")
        except Exception as e:
            log.error(f"Không thể ghi file backup local: {e}")
