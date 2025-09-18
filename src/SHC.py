import os
import io
import base64
import random
import sys
import time
import pystray
import logging
import asyncio
import tkinter
import tkinter.messagebox
import keyboard
import threading
import configparser
from PIL import Image
from pathlib import Path
from playwright.async_api import async_playwright
from playwright.__main__ import main as playwright_main


# Global Variables
cookies_file = "storage.json"
CONFIG_FILE = 'config.ini'
config = None
config_data = None
chromium_ready = asyncio.Event()
device_counting_ready = asyncio.Event()
loop = asyncio.new_event_loop()
base_path = Path(os.path.abspath(".."))
activatable_devices_list = []
activatable_devices_cards = None
default_device = None
executable_path = None
inst = None
browser = None
context = None
page = None
shc_tray_icon = None
shc_tray_menu = None
pressed_key_list = []
current_hotkey = ""
is_hotkey_exist = False
hotkey_window = None
icon_b64 = b"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"
icon_bytes = base64.b64decode(icon_b64)
icon_buffer = io.BytesIO(icon_bytes)


# Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('debug.log'), logging.StreamHandler()]
)


# Config functions
def create_default_config():
    cfg = configparser.ConfigParser()
    cfg['CONFIG'] = {"default_device" : "", "default_device_hotkey" : ""}
    with open(CONFIG_FILE, 'w') as f:
        cfg.write(f)
def get_config():
    global config, config_data, default_device, current_hotkey
    if not os.path.exists(CONFIG_FILE):
        create_default_config()
    config_data = configparser.ConfigParser()
    config_data.read(CONFIG_FILE)
    config = config_data['CONFIG']
    default_device = config["default_device"]
    current_hotkey = config["default_device_hotkey"]
def save_config():
    global config, config_data, CONFIG_FILE
    with open(CONFIG_FILE, 'w') as f:
        config_data.write(f)


# Checking Chromium
async def check_browser():
    global executable_path, shc_tray_icon
    logging.info("Searching chromium...")
    chromium_dirs = list((base_path / "ms-playwright").glob("chromium-*"))
    if not chromium_dirs:
        shc_tray_icon.notify("Chromium doesn't found. Starting download chromium...", title="SmartHomeControl")
        logging.info("Chromium doesn't found. Starting download chromium... Please Wait.")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(base_path / "ms-playwright")
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
    if not os.path.exists(cookies_file):
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
    except Exception:
        logging.error("Timeout authorization")
        await browser.close()
        os._exit(1)
    await page.context.storage_state(path=cookies_file)
    logging.info("Cookie saved")
    await browser.close()
    await init_browser()


# Authorize with cookies
async def cookies_authorize():
    global executable_path, inst, browser, context, page
    logging.info("Cookies already existing")
    logging.info("Starting Playwright...")
    inst = await async_playwright().start()
    logging.info("Starting Chromium...")
    browser = await inst.chromium.launch(headless=True,executable_path=executable_path)
    logging.info("Adding cookies...")
    context = await browser.new_context(storage_state=cookies_file)
    logging.info("Opening new page...")
    page = await context.new_page()
    logging.info("Opening yaiot...") #yaidiot
    await page.goto("https://yandex.ru/iot", wait_until="domcontentloaded")
    await device_counting()


# Counting devices
async def device_counting():
    global executable_path, inst, browser, context, page, activatable_devices_cards, tray_icon, shc_tray_icon
    logging.info("Counting activatable devices")
    if await page.locator("xpath=//div[@class='waterfall-grid__column']").count():     # Короче здесь проверяется какой размер карточек устройств, если на странице есть элемент waterfall-grid__column, то значит размер большой(medium). Если его нет значит маленький(small). По крайней мере сейчас это работает. Возможно потом сайт переделают и все сломается 😥
        #  Finding visible cards which have text
        devices_cards = await page.locator("//div[contains(@class, 'card-item-small')]").filter(has=page.locator(
            "xpath=//div[@class='typography typography_align_center typography_color_primary typography_multi-line-clamp card-item-device-medium__text typography_header-16-m' and normalize-space(text()) != '']"
        )).filter(visible=True).all()
    else:
        devices_cards = await page.locator("//div[contains(@class, 'card-item-small')]").filter(has=page.locator(
            "xpath=//div[@class='typography typography_align_inherit typography_color_primary typography_single-line-clamp card-item-device-small__text typography_text-13-m' and normalize-space(text()) != '']"
        )).filter(visible=True).all()
    logging.info(f"All devices:{len(devices_cards)}")
    # Finding visible cards which have switch
    activatable_devices_cards = await page.locator("//div[contains(@class, 'card-item-small')]").filter(has=page.locator(
            "xpath=//div[@class='typography typography_align_inherit typography_color_primary typography_single-line-clamp card-item-device-small__text typography_text-13-m' and normalize-space(text()) != '']"
        )).filter(has=page.locator("xpath=//div[contains(@aria-label,'ключить')]")).filter(visible=True).all()
    # Printing activatable devices
    shc_tray_icon.notify(f"Activatable devices:{len(activatable_devices_cards)}", title="SmartHomeControl")
    logging.info(f"Activatable devices:{len(activatable_devices_cards)}")
    # Splitting cards on names, locations and states
    for activatable_devices_card in activatable_devices_cards:
        activatable_device_info = (await activatable_devices_card.inner_text()).splitlines()
        activatable_device_name = activatable_device_info[0]
        activatable_device_place = activatable_device_info[1] if len(activatable_device_info) > 1 else ""
        activatable_device_button = activatable_devices_card.locator("xpath=//div[contains(@aria-label, 'ключить')]")
        activatable_device_button_state = await activatable_device_button.get_attribute('aria-label')
        activatable_device_state = False if activatable_device_button_state == 'Включить' else True
        activatable_devices_list.append({
            "name":activatable_device_name,
            "location":activatable_device_place,
            "state":activatable_device_state
        })
    device_counting_ready.set()


# Activating device
async def activating_device(needed_device_name):
    global activatable_devices_cards, shc_tray_icon
    logging.info(f"Activating device: {needed_device_name}")
    if needed_device_name:
        for activatable_devices_card in activatable_devices_cards:
            if needed_device_name in await activatable_devices_card.inner_text():
                needed_device_button = activatable_devices_card.locator("xpath=//div[contains(@aria-label, 'ключить')]")
                logging.info("The device was found. Gonna click")
                await needed_device_button.click()
                for d in activatable_devices_list:
                    if d['name'] == needed_device_name:
                        logging.info(f"{needed_device_name} was {d['state']}")
                        d["state"] = not d["state"]
                        logging.info(f"{needed_device_name} {d['state']} now")
                        if d['state']:
                            shc_tray_icon.notify(f"{needed_device_name} is turning on", title="SmartHomeControl")
                        else:
                            shc_tray_icon.notify(f"{needed_device_name} is turning off", title="SmartHomeControl")
                        break
                logging.info("Was clicked")
                break
            else:
                logging.info(f"The device {needed_device_name} was not found.")


# Refreshing page
async def refresh_page(icon=None, item=None):
    global executable_path, inst, browser, context, page, activatable_devices_list, shc_tray_icon
    try:
        logging.info("Refreshing the page")
        await page.reload(wait_until="load")
        logging.info("Page is refreshed")
        shc_tray_icon.notify(f"Page is refreshed", title="SmartHomeControl")
        activatable_devices_list = []
        await device_counting()
        update_shc_icon()
    except Exception as e:
        logging.info("Can't refresh the page")


# Exiting program
async def exit_program(icon=None, item=None):
    global shc_tray_icon
    global executable_path, inst, browser, context, page
    logging.info("Closing tray icon...")
    shc_tray_icon.visible = False
    shc_tray_icon.stop()
    logging.info("Shutting the browser...")
    await browser.close()
    await inst.stop()
    logging.info("Browser was closed")
    shc_tray_icon.notify(f"Change the world. My final message. Good bye.", title="SmartHomeControl")
    logging.info("Change the world. My final message. Good bye.")
    os._exit(0)


# Hotkey functions
def make_hotkey(current_hotkey):
    global config
    keyboard.add_hotkey(
        current_hotkey,
        lambda: activate_hotkey()
    )
    config["default_device_hotkey"] = current_hotkey
    save_config()
    logging.info("Hotkey was maked")
def remove_hotkey(current_hotkey):
    keyboard.remove_hotkey(current_hotkey)
    logging.info("Hotkey removed")
def activate_hotkey():
    logging.info("Detected hotkey")
    asyncio.run_coroutine_threadsafe(activating_device(default_device), loop)


# Setting window
def settings_window(icon, item):
    global hotkey_window, current_hotkey, pressed_key_list, is_hotkey_exist
    if not hotkey_window:
        hotkey_window = tkinter.Tk()
        hotkey_window.title("SHC Settings")
        hotkey_window.eval("tk::PlaceWindow . center")
        hotkey_window.geometry("270x180")
        hotkey_window.iconphoto(True, tkinter.PhotoImage(data=icon_b64))
        hotkey_window.resizable(
            width=False,
            height=False
        )
        hotkey_frame = tkinter.Frame(
            hotkey_window
        )
        hotkey_frame.place(
            relx=0.05,
            rely=0.01,
            relwidth=0.9,
            relheight=0.9)

        def start_record():
            global pressed_key_list
            toggle_record_button.config(text="Stop record", command=lambda: stop_record())
            title.config(text="Press wanted keys \n and press stop record (max 3 keys)")
            pressed_key_list = []
            keyboard.start_recording()

        def stop_record():
            global pressed_key_list
            raw_recorded_keys = keyboard.stop_recording()
            for e in raw_recorded_keys:
                if e.event_type == "down":
                    if e.name not in pressed_key_list:
                        if len(pressed_key_list) >= 3:
                            break
                        pressed_key_list.append(e.name)
            toggle_record_button.config(text="Start record", command=lambda: start_record())
            title.config(text="Press Apply to save hotkey \n or press Start record again")
            recorded_keys.config(text=f"Pressed keys: {"+".join(pressed_key_list)}")

        def about():
            tkinter.messagebox.showinfo(
                title="SmartHomeControl",
                message="SmartHomeControl aka SHC v1.0\nAuthor: The-Real-Duke\nLicense: CC BY-NC-SA 4.0\nGithub: https://github.com/The-Real-Duke/SmartHomeControl"
            )

        def reset_current_keys():
            global pressed_key_list, current_hotkey
            if current_hotkey:
                remove_hotkey(current_hotkey)
            pressed_key_list = []
            current_hotkey = ""
            recorded_keys.config(text=f"Pressed keys: None")
            current_hotkey_label.config(text=f"Current hotkey: {current_hotkey if current_hotkey else "None"}")

        def apply_keys():
            global pressed_key_list, current_hotkey
            if not pressed_key_list:
                return None
            if is_hotkey_exist:
                remove_hotkey(current_hotkey)
            current_hotkey = "+".join(pressed_key_list)
            make_hotkey(current_hotkey)
            title.config(text="Applied. \n Press start record to set the another hotkey.")
            current_hotkey_label.config(text=f"Current hotkey: {current_hotkey}")

        apply_button = tkinter.Button(
            hotkey_frame,
            text="Apply",
            command=lambda: apply_keys()
        )
        apply_button.place(
            rely=0.6,
            relx=0,
            relwidth=0.35
        )
        about_button = tkinter.Button(
            hotkey_frame,
            text="About",
            command=lambda: about()
        )
        about_button.place(
            rely=0.8,
            relx=0,
            relwidth=0.35
        )
        toggle_record_button = tkinter.Button(
            hotkey_frame,
            text="Start record",
            command=lambda: start_record()
        )
        toggle_record_button.place(
            rely=0.4,
            relx=0,
            relwidth=0.35
        )
        title = tkinter.Label(
            hotkey_frame,
            text="Press start record to set the hotkey."
        )
        title.place(
            relheight=0.19, relwidth=1
        )
        current_hotkey_label = tkinter.Label(
            hotkey_frame,
            text=f"Current hotkey: {current_hotkey}"
        )
        current_hotkey_label.place(
            rely=0.21, relx=0.37
        )
        recorded_keys = tkinter.Label(
            hotkey_frame,
            text=f"Pressed keys: None"
        )
        recorded_keys.place(
            rely=0.42, relx=0.37
        )
        reset_button = tkinter.Button(
            hotkey_frame,
            text="Reset",
            command=lambda: reset_current_keys()
        )
        reset_button.place(
            rely=0.2,
            relx=0,
            relwidth=0.35
        )
        def on_close():
            global hotkey_window
            hotkey_window.destroy()
            hotkey_window = None
        hotkey_window.protocol("WM_DELETE_WINDOW", on_close)
        hotkey_window.mainloop()

    else:
        hotkey_window.deiconify()
        hotkey_window.lift()
        hotkey_window.focus_force()


# Hotkeys stop working after windows locks & unlocks
# https://github.com/boppreh/keyboard/issues/223
# Thanks that man 2-3-5-7
def clear_keys():
    while True:
        with keyboard._pressed_events_lock:
            for i in list(keyboard._pressed_events.keys()):
                item = keyboard._pressed_events[i]
                if time.time() - item.time > 2:
                    del keyboard._pressed_events[i]
        time.sleep(2)


#Click trigger
def shc_tray_was_clicked(icon, item):
    logging.info(f"Was clicked on tray: {item}")
    if item.text == "Activate default device":
        asyncio.run_coroutine_threadsafe(activating_device(default_device), loop)
    else:
        asyncio.run_coroutine_threadsafe(activating_device(item.text), loop)


# Default device functions
def set_default_device(icon, item):
    global default_device, config
    default_device = item.text
    config["default_device"] = default_device
    save_config()
def is_default_device(item):
    global default_device
    return item.text == default_device


# Device checking
def is_device_on(item):
    time.sleep(0.05)
    for d in activatable_devices_list:
        if d["name"] == item.text:
            return d["state"]


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
                    pystray.MenuItem(d["name"], shc_tray_was_clicked, checked=lambda item: is_device_on(item))
                    for d in activatable_devices_list)
            )
        ),
        pystray.MenuItem(
            "Select default device", pystray.Menu(
                lambda : (
                    pystray.MenuItem(d["name"], set_default_device, checked=lambda item: is_default_device(item))
                                     for d in activatable_devices_list)
                )
            ),
        pystray.MenuItem(
            "Settings", settings_window
        ),
        pystray.MenuItem(
            "Refresh Page", lambda icon, item: asyncio.run_coroutine_threadsafe(refresh_page(),loop)
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Activate default device", shc_tray_was_clicked
        )
    )


#Updating tray (for some reason works with big latency)
def update_shc_icon():
    shc_tray_icon.menu=build_shc_tray_icon()
    shc_tray_icon.visible = False
    shc_tray_icon.update_menu()
    shc_tray_icon.visible = True
    shc_tray_icon.notify("Tray rebuilt", title="SmartHomeControl")


# Build and start tray
def start_shc_icon():
    global shc_tray_icon, shc_tray_menu, activatable_devices_list
    shc_tray_icon = pystray.Icon("SmartHomeControl", icon=Image.open(icon_buffer), title="SmartHomeControl", menu=build_shc_tray_icon())
    logging.info("Starting tray")
    shc_tray_icon.run()


# Background updater each 15 min + random seconds for antibot system
async def background_updater():
    while True:
        await asyncio.sleep(3600 + random.randint(-240, 240))
        await refresh_page()

# Main
async def main():
    get_config()
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
    threading.Thread(target=clear_keys, daemon=True).start()
    asyncio.create_task(background_updater())


# This is what is this
if __name__ == "__main__":
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()