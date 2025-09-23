import os
import random
import sys
import time
import pystray
import logging
import asyncio
import threading
from PIL import Image
from pathlib import Path
from playwright.async_api import async_playwright
from playwright.__main__ import main as playwright_main
from src.config import ConfigManager
from src.devices import DeviceManager
from src.ui_settings import SettingsWindowManager

# Global Variables
if hasattr(sys, "_MEIPASS"):
    base_path = Path(sys._MEIPASS)
else:
    base_path = Path(os.path.abspath(".."))
APPDATA_DIR = Path(os.getenv("APPDATA")) / "SHC"
config = ConfigManager(APPDATA_DIR / "config.ini")
cookies_path = APPDATA_DIR / "storage.json"
chromium_ready = asyncio.Event()
device_counting_ready = asyncio.Event()
loop = asyncio.new_event_loop()
shc_image = base_path / "assets" / "icon.png"
default_device = config.get_info("CONFIG","default_device")
executable_path = None
inst = None
browser = None
context = None
page = None
dm = DeviceManager(page)
shc_tray_icon = None
shc_tray_menu = None
pressed_key_list = []
current_hotkey = ""
is_hotkey_exist = False
hotkey_window = None


# Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(APPDATA_DIR / 'debug.log'), logging.StreamHandler()]
)


# Checking Chromium
async def check_browser():
    global executable_path, shc_tray_icon
    logging.info("Searching chromium...")
    chromium_dirs = list((APPDATA_DIR / "ms-playwright").glob("chromium-*"))
    if not chromium_dirs:
        shc_tray_icon.notify("Chromium doesn't found. Starting download chromium...", title="SmartHomeControl")
        logging.info("Chromium doesn't found. Starting download chromium... Please Wait.")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(APPDATA_DIR / "ms-playwright")
        old_argv = sys.argv
        sys.argv = ["playwright", "install", "chromium", "--no-shell"]
        try:
            playwright_main()
        except SystemExit:
            pass
        shc_tray_icon.notify("Chromium downloaded", title="SmartHomeControl")
        logging.info("Chromium downloaded")
        sys.argv = old_argv
        await check_browser()
    else:
        chromium_dirs.sort()
        chromium_dir = chromium_dirs[-1]
        executable_path = chromium_dir / "chrome-win" / "chrome.exe"
        logging.info("Chromium was found")
        chromium_ready.set()


# Checking cookies
async def init_browser():
    logging.info("Chromium initialization...")
    if not os.path.exists(cookies_path):
        await first_authorize()
    else:
        await cookies_authorize()


# First Authorize
async def first_authorize():
    global executable_path, inst, browser, page, shc_tray_icon
    inst = await async_playwright().start()
    logging.info("Trying to launch Chromium...")
    browser = await inst.chromium.launch(headless=False,executable_path=executable_path)
    page = await browser.new_page()
    logging.info("First authorization. Opening login page...")
    shc_tray_icon.notify("Cookies was not found. First authorization. Opening login page...", title="SmartHomeControl")
    await page.goto("https://passport.yandex.ru/auth")
    try:
        await page.wait_for_url(lambda url: "passport.yandex.ru" not in url, timeout=180000)
        logging.info("Authorization complete.")
    except Exception as e:
        logging.error(f"Timeout authorization:{e}")
        await browser.close()
        os._exit(1)
    await page.context.storage_state(path=cookies_path)
    logging.info("Cookie saved")
    await browser.close()
    await init_browser()


# Authorize with cookies
async def cookies_authorize():
    global executable_path, inst, browser, context, page, dm
    logging.info("Cookies already existing")
    logging.info("Starting Playwright...")
    inst = await async_playwright().start()
    logging.info("Starting Chromium...")
    browser = await inst.chromium.launch(headless=True,executable_path=executable_path)
    logging.info("Adding cookies...")
    context = await browser.new_context(storage_state=cookies_path)
    logging.info("Opening new page...")
    page = await context.new_page()
    logging.info("Opening yaiot...") #yaidiot
    await page.goto("https://yandex.ru/iot", wait_until="domcontentloaded")
    dm = DeviceManager(page)
    await dm.d_count()
    device_counting_ready.set()


# Activating device
async def activating_device(needed_device_name):
    global dm
    try:
        logging.info(f"{needed_device_name} was {dm.devices[needed_device_name].state}")
        await dm.toggle(needed_device_name)
        logging.info(f"{needed_device_name} {dm.devices[needed_device_name].state} now")
        if dm.devices[needed_device_name].state:
            shc_tray_icon.notify(f"{needed_device_name} is turning on", title="SmartHomeControl")
        else:
            shc_tray_icon.notify(f"{needed_device_name} is turning off", title="SmartHomeControl")
    except Exception as e:
        logging.info(f"Click was failed. Error: {e}")


# Refreshing page
async def refresh_page(icon=None, item=None):
    global page, shc_tray_icon, dm
    try:
        logging.info("Refreshing the page")
        await page.reload(wait_until="load")
        logging.info("Page is refreshed")
        shc_tray_icon.notify(f"Page is refreshed", title="SmartHomeControl")
        await dm.d_count()
        update_shc_icon()
    except Exception as e:
        logging.info(f"Can't refresh the page:{e}")


# Exiting program
async def exit_program(icon=None, item=None):
    global shc_tray_icon
    global executable_path, inst, browser, context, page
    logging.info("Closing tray icon...")
    shc_tray_icon.notify(f"Change the world. My final message. Good bye.", title="SmartHomeControl")
    shc_tray_icon.visible = False
    shc_tray_icon.stop()
    logging.info("Shutting the browser...")
    await context.close()
    await browser.close()
    await inst.stop()
    logging.info("Browser was closed")
    await loop.stop()


#Click trigger
def shc_tray_was_clicked(icon, item):
    logging.info(f"Was clicked on tray: {item}")
    if item.text == "Activate default device":
        asyncio.run_coroutine_threadsafe(activating_device(default_device), loop)
    else:
        asyncio.run_coroutine_threadsafe(activating_device(item.text), loop)


# Default device functions
def set_default_device(icon, item):
    global default_device
    default_device = item.text
    config.set("CONFIG", "default_device", str(default_device))
    config.save()
def is_default_device(item):
    global default_device
    return item.text == default_device


# Device checking
def is_device_on(item):
    time.sleep(0.05)
    for device in dm.devices.values():
        if device.name == item.text:
            return device.state


#Bulid for tray
def build_shc_tray_icon():
    return pystray.Menu(
        pystray.MenuItem(
            "Exit", lambda icon, item: asyncio.run_coroutine_threadsafe(exit_program(),loop)
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Activatable devices", pystray.Menu(
                lambda: (
                    pystray.MenuItem(d.name, shc_tray_was_clicked, checked=lambda item: is_device_on(item))
                    for d in dm.devices.values())
            )
        ),
        pystray.MenuItem(
            "Select default device", pystray.Menu(
                lambda : (
                    pystray.MenuItem(d.name, set_default_device, checked=lambda item: is_default_device(item))
                                     for d in dm.devices.values())
                )
            ),
        pystray.MenuItem(
            "Settings", lambda icon, item: settings_window.open()
        ),
        pystray.MenuItem(
            "Refresh Page", lambda icon, item: asyncio.run_coroutine_threadsafe(refresh_page(),loop)
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Activate default device", shc_tray_was_clicked
        )
    )


#Updating tray
def update_shc_icon():
    shc_tray_icon.menu=build_shc_tray_icon()
    shc_tray_icon.update_menu()
    shc_tray_icon.notify("Tray rebuilt", title="SmartHomeControl")


# Build and start tray
def start_shc_icon():
    global shc_tray_icon, shc_tray_menu
    shc_tray_icon = pystray.Icon("SmartHomeControl", icon=Image.open(shc_image), title="SmartHomeControl", menu=build_shc_tray_icon())
    logging.info("Starting tray")
    shc_tray_icon.run()
def activating_dd():
    asyncio.run_coroutine_threadsafe(activating_device(default_device), loop)

# Background updater each 15 min + random seconds for antibot system
async def background_updater():
    while True:
        await asyncio.sleep(3600 + random.randint(-240, 240))
        await refresh_page()

settings_window = SettingsWindowManager(shc_image, config, activating_dd)
# Main
async def main():
    logging.info("Starting tray initialization...")
    threading.Thread(target=start_shc_icon, daemon=True).start()
    await asyncio.sleep(0.1)
    logging.info("Checking chromium...")
    asyncio.create_task(check_browser())
    await chromium_ready.wait()
    logging.info("Starting chromium initialization...")
    asyncio.create_task(init_browser())
    await device_counting_ready.wait()
    logging.info("Updating tray...")
    update_shc_icon()
    threading.Thread(target=SettingsWindowManager.clear_keys, daemon=True).start()
    asyncio.create_task(background_updater())


# This is what is this
if __name__ == "__main__":
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()