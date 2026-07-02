import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path="/Users/hoangkien/.cloakbrowser/chromium-145.0.7632.109.2/Chromium.app/Contents/MacOS/Chromium",
            headless=False
        )
        page = await browser.new_page()
        print("Navigating to Namco Parks connect URL...")
        await page.goto("https://parks2.bandainamco-am.co.jp/ext/bandainamco_id_connect.html", wait_until="networkidle")
        
        # Dump all links and buttons
        print("\n--- Links on page ---")
        links = await page.query_selector_all("a")
        for i, link in enumerate(links):
            text = (await link.inner_text()).strip()
            href = await link.get_attribute("href")
            print(f"Link {i}: Text='{text}', href='{href}'")
            
        print("\n--- Buttons on page ---")
        buttons = await page.query_selector_all("button, input[type='button'], input[type='submit']")
        for i, btn in enumerate(buttons):
            text = (await btn.inner_text()).strip() or await btn.get_attribute("value")
            print(f"Button {i}: Text='{text}'")

        # Let's navigate directly to the signup.html page to avoid popup/new tab handling issues
        signup_url = "https://account.bandainamcoid.com/signup.html?client_id=namcoparks_onlinestore&redirect_uri=https%3A%2F%2Fparks2.bandainamco-am.co.jp%2Fmember_regist_new.html"
        print(f"\nNavigating directly to: {signup_url}")
        await page.goto(signup_url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        print(f"Current URL: {page.url}")
        
        # Print elements on registration page
        print("\n--- Inputs on signup page ---")
        inputs = await page.query_selector_all("input")
        for i, inp in enumerate(inputs):
            name = await inp.get_attribute("name")
            inp_id = await inp.get_attribute("id")
            inp_class = await inp.get_attribute("class")
            inp_type = await inp.get_attribute("type")
            placeholder = await inp.get_attribute("placeholder")
            print(f"Input {i}: name='{name}', id='{inp_id}', class='{inp_class}', type='{inp_type}', placeholder='{placeholder}'")

        print("\n--- Buttons on signup page ---")
        reg_buttons = await page.query_selector_all("button, input[type='submit'], [class*='btn']")
        for i, btn in enumerate(reg_buttons):
            text = (await btn.inner_text()).strip() or await btn.get_attribute("value")
            btn_type = await btn.get_attribute("type")
            btn_class = await btn.get_attribute("class")
            print(f"Button {i}: Text='{text}', type='{btn_type}', class='{btn_class}'")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
