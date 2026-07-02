import asyncio
import time
import random
import re
import os
from playwright.async_api import async_playwright
import src.config as config
from src.core.email_reader import get_bandai_namco_otp

async def take_snapshot(page, step_name):
    print(f"📸 Đang chụp ảnh và lấy DOM cho bước: {step_name}")
    # Chụp ảnh
    await page.screenshot(path=f"data/step_{step_name}.png", full_page=True)
    # Lấy DOM
    text = await page.evaluate("() => document.body ? document.body.innerText : ''")
    with open(f"data/step_{step_name}_dom.txt", "w", encoding="utf-8") as f:
        f.write(text)
    # Tìm xem có mã BNID trên DOM không
    match = re.search(r'\b(?:B\d{12}|\d{12}|\d{4}[-\s]?\d{4}[-\s]?\d{4})\b', text)
    if match:
        print(f"   => KẾT QUẢ: 🎯 TÌM THẤY MÃ BNID '{match.group(0).strip()}' TRÊN MÀN HÌNH NÀY!")
    else:
        print(f"   => KẾT QUẢ: ❌ Không có mã BNID trên màn hình này.")

async def main():
    email = "a.t.t.t.j.41@gmail.com" # Email mới
    password = "Namco2025!"
    
    print(f"🚀 Bắt đầu test luồng đăng ký step-by-step với email: {email}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/Users/hoangkien/.cloakbrowser/chromium-145.0.7632.109.2/Chromium.app/Contents/MacOS/Chromium",
            headless=False
        )
        context = await browser.new_context()
        page = await context.new_page()
        since_ts = time.time()
        
        # Bước 1: Vào trang connect
        await page.goto("https://parks2.bandainamco-am.co.jp/ext/bandainamco_id_connect.html", timeout=30000)
        await asyncio.sleep(2)
        await take_snapshot(page, "1_trang_connect")
        
        # Xử lý cookie banner nếu có
        try:
            cookie_btn = await page.wait_for_selector("button#cookie-accept, button.cookie-accept, button.onetrust-accept-btn-handler", timeout=3000)
            if cookie_btn:
                await cookie_btn.click()
                await asyncio.sleep(1)
        except:
            pass

        # Bước 2: Bấm Get BNID
        btn = await page.wait_for_selector("img[alt='バンダイナムコIDを取得'], img[src*='btn_get_id'], a:has(img[alt='バンダイナムコIDを取得'])", timeout=15000)
        await btn.click()
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(3)
        await take_snapshot(page, "2_trang_dien_email_pass")
        
        # Bước 3: Điền Email/Pass
        await page.locator("input#mail").fill(email)
        await page.locator("input#mail").blur()
        await page.locator("input#pass").fill(password)
        await page.locator("input#pass").blur()
        
        # Tick checkbox
        cbs = await page.query_selector_all("input[type='checkbox']")
        for cb in cbs:
            await cb.evaluate("el => { if (!el.checked) el.click(); }")
            
        await asyncio.sleep(1)
        await page.click("button#btn-idpw-next")
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(5)
        await take_snapshot(page, "3_trang_dien_ngay_sinh")
        
        # Bước 4: Điền ngày sinh
        try:
            # Country
            sel = await page.query_selector("select#country")
            if sel: await sel.evaluate("el => { el.value = 'JP'; el.dispatchEvent(new Event('change', {bubbles: true})); }")
            # DOB
            await page.locator("input#id_month").evaluate("el => { el.value = '1'; el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }")
            await page.locator("input#id_day").evaluate("el => { el.value = '1'; el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }")
            await page.locator("input#id_year").evaluate("el => { el.value = '1990'; el.dispatchEvent(new Event('input', {bubbles: true})); el.dispatchEvent(new Event('change', {bubbles: true})); }")
            
            cbs = await page.query_selector_all("input[type='checkbox']")
            for cb in cbs:
                await cb.evaluate("el => { if (!el.checked) el.click(); }")
                
            await asyncio.sleep(1)
            await page.click("button#btn-agree-b")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(5)
            await take_snapshot(page, "4_trang_nhap_otp")
            
        except Exception as e:
            print(f"Lỗi khi điền thông tin: {e}")
            await browser.close()
            return
            
        # Bước 5: Chờ OTP
        print("Đang chờ mã OTP từ email...")
        email_otp = get_bandai_namco_otp(since_ts=since_ts, timeout=120, target_email=email)
        if not email_otp:
            print("❌ KHÔNG NHẬN ĐƯỢC OTP! Khả năng Bandai đã chặn gửi mã về email này.")
            await browser.close()
            return
            
        print(f"✅ OTP: {email_otp}. Đang điền...")
        await page.locator("input[name='authenticationCode']").fill(str(email_otp))
        await page.locator("input[name='authenticationCode']").blur()
        await asyncio.sleep(1)
        await page.click("button[type='submit']")
        
        # BƯỚC QUAN TRỌNG: Màn hình ngay sau khi submit OTP!
        await asyncio.sleep(2) # Chờ 2 giây (Lúc nó đang redirect)
        await take_snapshot(page, "5_ngay_sau_khi_submit_otp_2s")
        
        await asyncio.sleep(3) # Chờ thêm 3 giây
        await take_snapshot(page, "6_ngay_sau_khi_submit_otp_5s")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
