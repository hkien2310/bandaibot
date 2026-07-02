import threading
from pathlib import Path
from src.utils.logger import get_logger
from src import config

log = get_logger("proxy_pool")

class ProxyPool:
    def __init__(self, proxy_list: list):
        self.proxies = []
        self.lock = threading.Lock()
        self.index = 0
        
        # Lưu các proxy index đã hoàn thành đăng ký thành công số accounts tối đa
        self.retired_indices = set()
        # Đếm số accounts thành công cho mỗi proxy index
        self.success_counts = {} 
        
        self.load_from_list(proxy_list)

    def load_from_list(self, proxy_list: list):
        if not proxy_list:
            log.warning("Danh sách proxy trống. Chạy không dùng proxy.")
            return

        for line in proxy_list:
            parsed = self.parse_proxy_string(line)
            if parsed:
                self.proxies.append(parsed)

        log.info(f"Loaded {len(self.proxies)} proxies vào ProxyPool")

    def parse_proxy_string(self, proxy_str: str) -> dict | None:
        """
        Parse proxy string sang dict chuẩn Playwright.
        """
        try:
            if "@" in proxy_str:
                auth_part, host_part = proxy_str.split("@", 1)
                username, password = auth_part.split(":", 1)
                host, port = host_part.split(":", 1)
                return {
                    "server": f"http://{host}:{port}",
                    "username": username,
                    "password": password,
                    "raw": proxy_str
                }

            parts = proxy_str.split(":")
            if len(parts) == 2:
                return {
                    "server": f"http://{parts[0]}:{parts[1]}",
                    "raw": proxy_str
                }
            elif len(parts) == 4:
                return {
                    "server": f"http://{parts[0]}:{parts[1]}",
                    "username": parts[2],
                    "password": parts[3],
                    "raw": proxy_str
                }
            else:
                log.warning(f"Định dạng proxy không hợp lệ: {proxy_str}")
                return None
        except Exception as e:
            log.error(f"Lỗi parse proxy string '{proxy_str}': {e}")
            return None

    def get_next_proxy(self) -> tuple[dict | None, int | None]:
        """Lấy proxy tiếp theo theo cơ chế Round-robin (thread-safe).
        
        Mỗi lần gọi luôn lấy proxy khác nhau.
        Tự động bỏ qua các proxy đã đăng ký thành công đủ số lượng accounts.
        """
        if not self.proxies:
            return None, None
            
        with self.lock:
            start_index = self.index
            while True:
                curr_idx = self.index
                # Luôn dịch index sang proxy tiếp theo cho các lần gọi sau (đảm bảo đổi proxy liên tục)
                self.index = (self.index + 1) % len(self.proxies)
                
                if curr_idx not in self.retired_indices:
                    proxy = dict(self.proxies[curr_idx])
                    log.info(f"   -> Chọn proxy index={curr_idx} | {proxy.get('server')}")
                    return proxy, curr_idx
                
                # Nếu đã duyệt hết 1 vòng mà toàn bộ đã bị retired (không thể với pool 5000), reset
                if self.index == start_index:
                    log.warning(f"Tất cả proxy trong file đều đã đăng ký thành công đủ {config.MAX_ACCOUNTS_PER_PROXY} accounts! Reset pool...")
                    self.retired_indices.clear()
                    self.success_counts.clear()
                    proxy = dict(self.proxies[curr_idx])
                    return proxy, curr_idx

    def mark_success(self, proxy_index: int):
        """Ghi nhận đăng ký thành công cho proxy index."""
        if proxy_index is None:
            return
        with self.lock:
            count = self.success_counts.get(proxy_index, 0) + 1
            self.success_counts[proxy_index] = count
            log.info(f"   [Proxy Pool] Proxy index {proxy_index} đã hoàn thành đăng ký thành công {count}/{config.MAX_ACCOUNTS_PER_PROXY} accounts.")
            if count >= config.MAX_ACCOUNTS_PER_PROXY:
                log.warning(f"   [Proxy Pool] Retire proxy index {proxy_index} (Đạt giới hạn tối đa {config.MAX_ACCOUNTS_PER_PROXY} accounts).")
                self.retired_indices.add(proxy_index)

    def count(self) -> int:
        return len(self.proxies)

    def mark_failed(self, proxy_index: int):
        """Đánh dấu proxy đã chết/lỗi để không sử dụng lại nữa."""
        if proxy_index is None:
            return
        with self.lock:
            self.retired_indices.add(proxy_index)
            log.warning(f"   [Proxy Pool] Đã loại bỏ vĩnh viễn proxy index {proxy_index} vì bị lỗi kết nối.")
