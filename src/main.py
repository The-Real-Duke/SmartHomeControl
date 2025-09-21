import os
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
from PIL import Image
from pathlib import Path
from playwright.async_api import async_playwright
from playwright.__main__ import main as playwright_main
from config import ConfigManager
from devices import DeviceManager

# Global Variables
APPDATA_DIR = Path(os.getenv("APPDATA")) / "SHC"
config = ConfigManager(APPDATA_DIR / "config.ini")
cookies_path = APPDATA_DIR / "storage.json"
chromium_ready = asyncio.Event()
device_counting_ready = asyncio.Event()
loop = asyncio.new_event_loop()
base_path = Path(os.path.abspath(".."))
shc_image = base_path / "assets" / "icon.png"
default_device = None
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
    except Exception:
        logging.error("Timeout authorization")
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
        logging.info("Can't refresh the page")


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


# Hotkey functions
def make_hotkey(current_hotkey):
    keyboard.add_hotkey(
        current_hotkey,
        lambda: activate_hotkey()
    )
    config.set("CONFIG","dd_hotkey", str(current_hotkey))
    config.save()
    logging.info("Hotkey was maked")
def remove_hotkey(current_hotkey):
    keyboard.remove_hotkey(current_hotkey)
    logging.info("Hotkey removed")
def activate_hotkey():
    logging.info("Detected hotkey")
    asyncio.run_coroutine_threadsafe(activating_device(default_device), loop)


# Setting window
def settings_window():
    global hotkey_window, current_hotkey, pressed_key_list, is_hotkey_exist
    if not hotkey_window:
        hotkey_window = tkinter.Tk()
        hotkey_window.title("SHC Settings")
        hotkey_window.eval("tk::PlaceWindow . center")
        hotkey_window.geometry("270x180")
        hotkey_window.iconphoto(True, tkinter.PhotoImage(file=shc_image))
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
            hotkey_entry.config(state='normal')
            hotkey_entry.delete(0, tkinter.END)
            hotkey_entry.config(state='readonly')
            keyboard.hook(pressed_keys)
        def pressed_keys(event):
            if len(pressed_key_list) < 3:
                if event.name not in pressed_key_list:
                    if event.event_type == "down":
                        pressed_key_list.append(event.name)
                        hotkey_entry.config(state='normal')
                        hotkey_entry.delete(0, tkinter.END)
                        hotkey_entry.insert(0, "+".join(pressed_key_list))
                        hotkey_entry.config(state='readonly')
            else:
                stop_record()
        def stop_record():
            global pressed_key_list
            keyboard.unhook_all()
            toggle_record_button.config(text="Start record", command=lambda: start_record())
            title.config(text="Press Apply to save hotkey \n or press Start record again")

        def about():
            tkinter.messagebox.showinfo(
                title="SmartHomeControl",
                message="SmartHomeControl aka SHC v1.0\nAuthor: The-Real-Duke\nLicense: CC BY-NC-SA 4.0\nSource: github.com/The-Real-Duke/SmartHomeControl"
            )

        def reset_current_keys():
            global pressed_key_list, current_hotkey
            if current_hotkey:
                remove_hotkey(current_hotkey)
            hotkey_entry.config(state='normal')
            hotkey_entry.delete(0, tkinter.END)
            hotkey_entry.config(state='readonly')
            pressed_key_list = []
            current_hotkey = ""
            recorded_keys.config(text=f"Pressed keys: None")
            current_hotkey_label.config(text=f"Current hotkey: {current_hotkey if current_hotkey else "None"}")

        def apply_keys():
            global pressed_key_list, current_hotkey
            if not pressed_key_list:
                return
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
            text=f"Pressed keys:"
        )
        recorded_keys.place(
            rely=0.35, relx=0.37
        )
        hotkey_entry = tkinter.Entry(
            hotkey_frame,
            bg="white",
            state='readonly'
        )
        hotkey_entry.place(
            rely=0.5,
            relx=0.385,
            relwidth=0.5,
            relheight=0.15)
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
    shc_tray_icon.update_menu()
    shc_tray_icon.notify("Tray rebuilt", title="SmartHomeControl")


# Build and start tray
def start_shc_icon():
    global shc_tray_icon, shc_tray_menu
    shc_tray_icon = pystray.Icon("SmartHomeControl", icon=Image.open(shc_image), title="SmartHomeControl", menu=build_shc_tray_icon())
    logging.info("Starting tray")
    shc_tray_icon.run()


# Background updater each 15 min + random seconds for antibot system
async def background_updater():
    while True:
        await asyncio.sleep(3600 + random.randint(-240, 240))
        await refresh_page()

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
    threading.Thread(target=clear_keys, daemon=True).start()
    asyncio.create_task(background_updater())


# This is what is this
if __name__ == "__main__":
    asyncio.set_event_loop(loop)
    loop.create_task(main())
    loop.run_forever()