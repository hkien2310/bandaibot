import asyncio
from playwright.async_api import async_playwright
import re

async def main():
    async with async_playwright() as p:
        print("Khởi động trình duyệt...")
        # Sử dụng đúng executable_path của thư viện đã cài đặt
        browser = await p.chromium.launch(
            executable_path="/Users/hoangkien/.cloakbrowser/chromium-145.0.7632.109.2/Chromium.app/Contents/MacOS/Chromium",
            headless=True
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        email = "a.t.t.j41@gmail.com" # Lấy email đã đky thành công ban nãy
        password = "Namco2025!"
        
        print("1. Đang truy cập trang đăng nhập BNID...")
        await page.goto("https://account.bandainamcoid.com/login.html", timeout=30000)
        await asyncio.sleep(2)
        
        print("2. Điền Email & Password...")
        await page.locator("input#mail, input[name='mail']").fill(email)
        await page.locator("input#mail, input[name='mail']").blur()
        await page.locator("input#pass, input[name='pass']").fill(password)
        await page.locator("input#pass, input[name='pass']").blur()
        await asyncio.sleep(1)
        await page.click("button#btn-idpw-login")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(4)
        
        print("3. Đang truy cập trang Portal Quản lý tài khoản (Nơi chứa mã BNID)...")
        await page.goto("https://account.bandainamcoid.com/portal.html", timeout=30000)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(4)
        
        print("4. Đang chụp ảnh màn hình và lấy nội dung trang...")
        await page.screenshot(path="data/debug_portal_screenshot.png")
        
        text = await page.evaluate("() => document.body ? document.body.innerText : ''")
        with open("data/debug_portal_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        print("5. Trích xuất mã BNID từ trang Portal...")
        match = re.search(r'\b(?:B\d{12}|\d{12}|\d{4}[-\s]?\d{4}[-\s]?\d{4})\b', text)
        if match:
            print(f"👉 KẾT QUẢ TÌM THẤY BNID USER CODE: {match.group(0).strip()} 👈")
        else:
            print("❌ Không tìm thấy BNID User Code!")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
