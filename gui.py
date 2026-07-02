import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import sys
import os
import queue
import re
from pathlib import Path

# Thêm root path để import đúng
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent
else:
    ROOT_DIR = Path(__file__).parent

sys.path.insert(0, str(ROOT_DIR))

config_path = ROOT_DIR / "config.json"
env_path = ROOT_DIR / ".env"

def load_json_config():
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_json_config(data):
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read_env_use_proxy():
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("USE_PROXY="):
                    return line.strip().split("=")[1].lower() == "true"
    return True

def write_env_use_proxy(use_proxy):
    lines = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    
    found = False
    for i, line in enumerate(lines):
        if line.startswith("USE_PROXY="):
            lines[i] = f"USE_PROXY={'true' if use_proxy else 'false'}\n"
            found = True
            break
    if not found:
        lines.append(f"USE_PROXY={'true' if use_proxy else 'false'}\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

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
        self.root.geometry("600x420")
        self.root.resizable(False, False)
        
        cfg = load_json_config()
        self.limit_var = tk.StringVar(value="")
        self.workers_var = tk.StringVar(value=str(cfg.get("worker_count", 3)))
        self.headless_var = tk.BooleanVar(value=cfg.get("headless", True))
        self.proxy_var = tk.BooleanVar(value=read_env_use_proxy())
        self.browser_path_var = tk.StringVar(value=cfg.get("browser_path", ""))
        
        self.setup_ui()
        
        self.log_queue = queue.Queue()
        self.update_logs()
        
        # Override stdout/stderr so that logger outputs to GUI
        sys.stdout = TextRedirector(self.log_queue)
        sys.stderr = TextRedirector(self.log_queue)
        
    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Đường dẫn Browser (để trống = dùng mặc định):").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.browser_path_var, width=60).grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Button(frame, text="Chọn", command=self.choose_browser).grid(row=0, column=2, padx=5)
        
        # Row 1: Limit
        ttk.Label(frame, text="Số lượng chạy (0 hoặc bỏ trống = Chạy tất cả):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.limit_var, width=15).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Row 2: Worker count
        ttk.Label(frame, text="Số Worker (Luồng chạy song song):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(frame, textvariable=self.workers_var, width=15).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Row 3: Checkboxes
        chk_frame = ttk.Frame(frame)
        chk_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=10)
        ttk.Checkbutton(chk_frame, text="Chạy ngầm (Headless)", variable=self.headless_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(chk_frame, text="Dùng Proxy", variable=self.proxy_var).pack(side=tk.LEFT, padx=10)
        
        # Row 4: Start/Stop button
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.start_btn = ttk.Button(btn_frame, text="🚀 BẮT ĐẦU CHẠY", command=self.start_bot, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="🛑 DỪNG LẠI", command=self.stop_bot, width=20, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Row 5: Mini Log Listbox
        ttk.Label(frame, text="Tiến trình đang chạy:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.log_listbox = tk.Listbox(frame, height=8, bg="#f0f0f0", fg="#333", font=("Arial", 11))
        self.log_listbox.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)
        
    def choose_browser(self):
        path = filedialog.askopenfilename(title="Chọn file chạy trình duyệt (Chromium/Chrome)")
        if path:
            self.browser_path_var.set(path)
            
    def update_logs(self):
        # Các từ khoá quan trọng dành cho user-facing log
        user_keywords = [
            "🚀 Bắt đầu xử lý:",
            "✅",
            "❌",
            "⚠️",
            "🔄",
            "⏳",
            "🎉",
            "🛑",
            "🔥",
            "🚧",
            "proxy",
            "[ERROR]",
            "[WARNING]",
            "Không còn",
            "kết nối",
            "Sheets",
            "SMS",
            "HOÀN TẤT",
            "BẮT ĐẦU",
            "GIỚI HẠN",
            "Loaded",
            "balance",
            "Hoàn thành mẻ",
            "Step",
        ]
        
        while not self.log_queue.empty():
            raw_msg = self.log_queue.get()
            msg = raw_msg.strip()
            if not msg:
                continue
                
            # Trích xuất phần nội dung chính của log
            # Kiểm tra keyword trên raw_msg trước khi split (để bắt [ERROR], [WARNING])
            raw_lower = msg.lower()
            if "—" in msg:
                display_msg = msg.split("—", 1)[1].strip()
            else:
                display_msg = msg
            
            # Chỉ hiển thị các log có chứa từ khoá quan trọng (Dành cho end-user)
            check_text = raw_lower + " " + display_msg.lower()
            is_user_friendly = any(kw.lower() in check_text for kw in user_keywords)
            if not is_user_friendly:
                continue
            
            msg = display_msg
                
            self.log_listbox.insert(tk.END, "• " + msg)
            
            # Giữ lại 30 dòng mới nhất
            if self.log_listbox.size() > 30:
                self.log_listbox.delete(0)
                
            self.log_listbox.see(tk.END)
        self.root.after(50, self.update_logs)

    def save_settings(self):
        cfg = load_json_config()
        try:
            cfg["worker_count"] = int(self.workers_var.get())
        except:
            cfg["worker_count"] = 3
        cfg["headless"] = self.headless_var.get()
        cfg["browser_path"] = self.browser_path_var.get()
        save_json_config(cfg)
        write_env_use_proxy(self.proxy_var.get())

    def start_bot(self):
        import src.config as bot_config
        bot_config.STOP_FLAG = False  # Reset flag khi bắt đầu

        self.start_btn.config(state=tk.DISABLED, text="⏳ ĐANG CHẠY...")
        self.stop_btn.config(state=tk.NORMAL)
        self.log_listbox.insert(tk.END, "🚀 Đang khởi động tiến trình, vui lòng không tắt...")
        self.log_listbox.see(tk.END)
        self.save_settings()
        
        limit_val = self.limit_var.get().strip()
        limit = int(limit_val) if limit_val and limit_val.isdigit() else 0
        
        threading.Thread(target=self.run_bot_thread, args=(limit,), daemon=True).start()
        
    def stop_bot(self):
        self.stop_btn.config(state=tk.DISABLED, text="⏳ ĐANG DỪNG...")
        self.log_listbox.insert(tk.END, "🛑 Đang gửi lệnh dừng đến các worker. Vui lòng đợi...")
        self.log_listbox.see(tk.END)
        import src.config as bot_config
        bot_config.STOP_FLAG = True
        
    def run_bot_thread(self, limit):
        import importlib
        import src.config as bot_config
        
        # Reload .env and config modules to reflect changes made by GUI
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=env_path, override=True)
        importlib.reload(bot_config)
        
        import main
        sys.argv = ["gui.py"]
        if limit > 0:
            sys.argv.extend(["--limit", str(limit)])
            
        try:
            main.main()
        except SystemExit as e:
            # sys.exit() được gọi bên trong bot (vd: hết hạn, sms thiếu tiền,...)
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
