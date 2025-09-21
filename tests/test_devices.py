from src.devices import Device,DeviceManager
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import os
async def cookies_authorize():
    APPDATA_DIR = Path(os.getenv("APPDATA")) / "SHC"
    cookies_path = APPDATA_DIR / "storage.json"
    chromium_dirs = list((APPDATA_DIR / "ms-playwright").glob("chromium-*"))
    chromium_dirs.sort()
    chromium_dir = chromium_dirs[-1]
    executable_path = chromium_dir / "chrome-win" / "chrome.exe"
    print("Cookies already existing")
    print("Starting Playwright...")
    inst = await async_playwright().start()
    print("Starting Chromium...")
    browser = await inst.chromium.launch(headless=True,executable_path=executable_path)
    print("Adding cookies...")
    context = await browser.new_context(storage_state=cookies_path)
    print("Opening new page...")
    page = await context.new_page()
    print("Opening yaiot...") #yaidiot
    await page.goto("https://yandex.ru/iot", wait_until="domcontentloaded")
    dm = DeviceManager(page)
    await dm.d_count()
    print(dm.devices)
async def main():
    asyncio.create_task(cookies_authorize())
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()