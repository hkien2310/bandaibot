import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import subprocess
import sys
import queue
import re
import webbrowser
from pathlib import Path

# Thêm root path để import đúng
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).parent

sys.path.insert(0, str(ROOT_DIR))

config_path      = ROOT_DIR / "config.json"       # fixed, committed
user_config_path = ROOT_DIR / "user_config.json"  # sensitive, local only

def load_json_config():
    """Load config.json (fixed settings)"""
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def load_user_config():
    """Load user_config.json (sensitive settings - local only)"""
    if user_config_path.exists():
        try:
            with open(user_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_json_config(data):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_user_config(data):
    with open(user_config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)



def strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

class TextRedirector(object):
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def write(self, string):
        self.log_queue.put(strip_ansi(string))

    def flush(self):
        pass

class NamcoBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Namco Parks Auto Bot")
        self.root.geometry("640x560")
        self.root.resizable(False, False)

        cfg  = load_json_config()
        ucfg = load_user_config()
        self.limit_var       = tk.StringVar(value="")
        self.workers_var     = tk.StringVar(value=str(cfg.get("worker_count", 3)))
        self.headless_var    = tk.BooleanVar(value=cfg.get("headless", True))
        self.proxy_var       = tk.BooleanVar(value=cfg.get("use_proxy", True))
        self.browser_path_var = tk.StringVar(value=cfg.get("browser_path", ""))
        self.sms_user_var    = tk.StringVar(value=ucfg.get("sms_username", ""))
        self.sms_pass_var    = tk.StringVar(value=ucfg.get("sms_password", ""))

        self.setup_ui()

        self.log_queue = queue.Queue()
        self.update_logs()

        # Override stdout/stderr để logger in ra GUI
        sys.stdout = TextRedirector(self.log_queue)
        sys.stderr = TextRedirector(self.log_queue)

        # Kiểm tra và tự cài Playwright Chromium nếu chưa có
        self.root.after(300, self._check_and_install_browser)

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Đường dẫn Browser (để trống = dùng mặc định):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.browser_path_var, width=55).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Button(frame, text="Chọn", command=self.choose_browser).grid(row=0, column=2, padx=5)

        ttk.Label(frame, text="Số lượng chạy (0 hoặc bỏ trống = Chạy tất cả):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.limit_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(frame, text="Số Worker (Luồng chạy song song):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.workers_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)

        chk_frame = ttk.Frame(frame)
        chk_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=10)
        ttk.Checkbutton(chk_frame, text="Chạy ngầm (Headless)", variable=self.headless_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(chk_frame, text="Dùng Proxy", variable=self.proxy_var).pack(side=tk.LEFT, padx=10)

        # SMS credentials
        ttk.Label(frame, text="SMS Username:").grid(row=4, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=self.sms_user_var, width=30).grid(row=4, column=1, sticky=tk.W, pady=3)

        ttk.Label(frame, text="SMS Password:").grid(row=5, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=self.sms_pass_var, width=30, show="*").grid(row=5, column=1, sticky=tk.W, pady=3)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=8)

        self.start_btn = ttk.Button(btn_frame, text="🚀 BẮt ĐẦU CHẠY", command=self.start_bot, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="🛑 DỪ NG LẠI", command=self.stop_bot, width=20, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Link Google Sheet
        sheet_frame = ttk.Frame(frame)
        sheet_frame.grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        ttk.Label(sheet_frame, text="📊 Google Sheet:").pack(side=tk.LEFT)
        self.sheet_link = tk.Label(
            sheet_frame, text="(chưa cấu hình)",
            fg="#1a73e8", cursor="hand2",
            font=("Arial", 10, "underline")
        )
        self.sheet_link.pack(side=tk.LEFT, padx=5)
        self.sheet_link.bind("<Button-1>", self.open_sheet_link)
        self._update_sheet_link()

        ttk.Label(frame, text="Tiến trình đang chạy:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.log_listbox = tk.Listbox(frame, height=8, bg="#f0f0f0", fg="#333", font=("Arial", 11))
        self.log_listbox.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(9, weight=1)

    def _check_and_install_browser(self):
        """Kiểm tra Playwright Chromium, nếu chưa có thì tự cài trong background."""
        def _is_chromium_installed():
            try:
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    # Chỉ check executable path tồn tại, không mở browser
                    exe = p.chromium.executable_path
                    return Path(exe).exists()
            except Exception:
                return False

        def _install():
            self.start_btn.config(state=tk.DISABLED, text="⏳ Đang cài trình duyệt...")
            self.log_listbox.insert(tk.END, "🔧 Kiểm tra Playwright Chromium...")
            self.log_listbox.see(tk.END)

            if _is_chromium_installed():
                self.root.after(0, lambda: (
                    self.start_btn.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY"),
                    self.log_listbox.insert(tk.END, "✅ Trình duyệt sẵn sàng."),
                    self.log_listbox.see(tk.END)
                ))
                return

            # Chưa có → tự cài
            self.root.after(0, lambda: (
                self.log_listbox.insert(tk.END, "📥 Lần đầu chạy: Đang cài Chromium (~300MB), vui lòng đợi..."),
                self.log_listbox.see(tk.END)
            ))

            try:
                # Chạy playwright install chromium
                result = subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    self.root.after(0, lambda: (
                        self.log_listbox.insert(tk.END, "✅ Cài Chromium thành công! Sẵn sàng chạy bot."),
                        self.log_listbox.see(tk.END),
                        self.start_btn.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY")
                    ))
                else:
                    err = result.stderr[:200] if result.stderr else "Unknown error"
                    self.root.after(0, lambda e=err: (
                        self.log_listbox.insert(tk.END, f"❌ Cài Chromium thất bại: {e}"),
                        self.log_listbox.see(tk.END),
                        self.start_btn.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY")
                    ))
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: (
                    self.log_listbox.insert(tk.END, "⚠️ Quá thời gian cài Chromium. Kiểm tra kết nối mạng!"),
                    self.log_listbox.see(tk.END),
                    self.start_btn.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY")
                ))
            except Exception as ex:
                self.root.after(0, lambda e=str(ex): (
                    self.log_listbox.insert(tk.END, f"❌ Lỗi cài Chromium: {e}"),
                    self.log_listbox.see(tk.END),
                    self.start_btn.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY")
                ))

        threading.Thread(target=_install, daemon=True).start()

    def choose_browser(self):
        path = filedialog.askopenfilename(title="Chọn file chạy trình duyệt (Chromium/Chrome)")
        if path:
            self.browser_path_var.set(path)

    def _update_sheet_link(self):
        """Cập nhật text link sheet dựa trên google_sheet_id trong config."""
        cfg = load_json_config()
        sheet_id = cfg.get("google_sheet_id", "").strip()
        if sheet_id and sheet_id != "PASTE_YOUR_GOOGLE_SHEET_ID_HERE":
            self._sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            self.sheet_link.config(text="Mở Google Sheet ↗", fg="#1a73e8")
        else:
            self._sheet_url = ""
            self.sheet_link.config(text="(chưa cấu hình Sheet ID)", fg="#999")

    def open_sheet_link(self, event=None):
        if self._sheet_url:
            webbrowser.open(self._sheet_url)

    def update_logs(self):
        user_keywords = [
            "🚀 Bắt đầu xử lý:",
            "✅", "❌", "⚠️", "🔄", "⏳", "🎉", "🛑", "🔥", "🚧",
            "proxy", "[ERROR]", "[WARNING]",
            "Không còn", "kết nối", "Sheets", "SMS",
            "HOÀN TẤT", "BẮT ĐẦU", "GIỚI HẠN",
            "Loaded", "balance", "Hoàn thành mẻ", "Step",
        ]

        while not self.log_queue.empty():
            raw_msg = self.log_queue.get()
            msg = raw_msg.strip()
            if not msg:
                continue

            raw_lower = msg.lower()
            if "—" in msg:
                display_msg = msg.split("—", 1)[1].strip()
            else:
                display_msg = msg

            check_text = raw_lower + " " + display_msg.lower()
            is_user_friendly = any(kw.lower() in check_text for kw in user_keywords)
            if not is_user_friendly:
                continue

            self.log_listbox.insert(tk.END, "• " + display_msg)

            if self.log_listbox.size() > 30:
                self.log_listbox.delete(0)

            self.log_listbox.see(tk.END)
        self.root.after(50, self.update_logs)

    def save_settings(self):
        """Lưu toàn bộ: cài đặt cố định vào config.json, credentials vào user_config.json"""
        # config.json - chỉ lưu giá trị cố định
        cfg = load_json_config()
        try:
            cfg["worker_count"] = int(self.workers_var.get())
        except:
            cfg["worker_count"] = 3
        cfg["headless"]      = self.headless_var.get()
        cfg["browser_path"]  = self.browser_path_var.get()
        cfg["use_proxy"]     = self.proxy_var.get()
        save_json_config(cfg)

        # user_config.json - credentials nhạy cảm của client
        ucfg = load_user_config()
        ucfg["sms_username"] = self.sms_user_var.get().strip()
        ucfg["sms_password"] = self.sms_pass_var.get().strip()
        save_user_config(ucfg)

    def start_bot(self):
        # Lưu config trước
        self.save_settings()

        # Import src.config SAU KHI lưu để nó đọc giá trị mới nhất
        import importlib
        import src.config as bot_config
        importlib.reload(bot_config)

        # Reset STOP_FLAG trực tiếp trên module đang chạy
        bot_config.STOP_FLAG = False

        self.start_btn.config(state=tk.DISABLED, text="⏳ ĐANG CHẠY...")
        self.stop_btn.config(state=tk.NORMAL, text="🛑 DỪNG LẠI")
        self.log_listbox.insert(tk.END, "🚀 Đang khởi động tiến trình, vui lòng không tắt...")
        self.log_listbox.see(tk.END)

        limit_val = self.limit_var.get().strip()
        limit = int(limit_val) if limit_val and limit_val.isdigit() else 0

        threading.Thread(target=self.run_bot_thread, args=(limit,), daemon=True).start()

    def stop_bot(self):
        """Gửi lệnh dừng cho bot — set STOP_FLAG trực tiếp trên module đang chạy."""
        self.stop_btn.config(state=tk.DISABLED, text="⏳ ĐANG DỪNG...")
        self.log_listbox.insert(tk.END, "🛑 Đang gửi lệnh dừng đến các worker. Vui lòng đợi...")
        self.log_listbox.see(tk.END)

        # Import trực tiếp module đang chạy và set flag — KHÔNG reload
        import src.config as bot_config
        bot_config.STOP_FLAG = True

    def run_bot_thread(self, limit):
        import main
        sys.argv = ["gui.py"]
        if limit > 0:
            sys.argv.extend(["--limit", str(limit)])

        try:
            main.main()
        except SystemExit as e:
            code = e.code
            def update_sysexit(c=code):
                if c and c != 0:
                    self.log_listbox.insert(tk.END, f"❌ Bot thoát với mã lỗi: {c}")
                else:
                    self.log_listbox.insert(tk.END, "✅ Bot đã thoát thành công.")
                self.log_listbox.see(tk.END)
            self.root.after(0, update_sysexit)
        except Exception as e:
            def update_err(err=str(e)):
                self.log_listbox.insert(tk.END, f"❌ Lỗi: {err}")
                self.log_listbox.see(tk.END)
            self.root.after(0, update_err)
        finally:
            def update_done():
                self.start_btn.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY")
                self.stop_btn.config(state=tk.DISABLED, text="🛑 DỪNG LẠI")
                self.log_listbox.insert(tk.END, "✅ Trạng thái: Đã hoàn tất công việc!")
                self.log_listbox.see(tk.END)
            self.root.after(0, update_done)

if __name__ == "__main__":
    root = tk.Tk()
    app = NamcoBotGUI(root)
    root.mainloop()
