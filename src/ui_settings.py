import time
import tkinter
import tkinter.messagebox
import tkinter.ttk

import keyboard


class SettingsWindowManager:
    # To avoid different keyboards layouts... I cant design better thing than that. Sorry azerty, qwertz etc. o7
    scancodes = {
        1: 'esc', 2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8',
        10: '9', 11: '0', 12: '-', 13: '=', 14: 'backspace', 15: 'tab', 16: 'q',
        17: 'w', 18: 'e', 19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i', 24: 'o',
        25: 'p', 26: '[', 27: ']', 43: '\\', 58: 'caps lock', 30: 'A', 31: 's',
        32: 'd', 33: 'f', 34: 'g', 35: 'h', 36: 'j', 37: 'k', 38: 'l', 39: ';',
        40: "'", 28: 'enter', 42: 'shift', 44: 'z', 45: 'x', 46: 'c', 47: 'v',
        48: 'b', 49: 'n', 50: 'm', 51: ',', 52: '.', 53: '/', 54: 'right shift',
        29: 'ctrl', 91: 'left windows', 56: 'alt', 57: 'space', 93: 'menu', 41: '`',
        55: 'print screen', 71: 'home', 79: 'end', 73: 'page up', 81: 'page down',
        82: 'insert', 83: 'delete'}

    def __init__(self, image, config, on_hotkey_callback):
        self.image = image
        self.window = None
        self.config = config
        self.current_hotkey = self.config.get_info("CONFIG", "dd_hotkey")
        if self.current_hotkey != "":
            self._make_hotkey()
        self.on_hotkey_callback = on_hotkey_callback
        self.pressed_key_list = []

    def open(self):
        if not self.window:
            self.window = tkinter.Tk()
            self.window.title("SHC Settings")
            self.window.eval("tk::PlaceWindow . center")
            self.window.geometry("270x180")
            self.window.iconphoto(True, tkinter.PhotoImage(file=self.image))
            self.window.resizable(
                width=False,
                height=False
            )
            self.settings_notebook = tkinter.ttk.Notebook(self.window, style="TNotebook")
            self.settings_notebook.pack(expand=True, fill="both", padx=2, pady=2)
            self.is_refreshing = tkinter.BooleanVar(value=self.config.get_info("CONFIG", "is_refreshing"))
            self.is_notify = tkinter.BooleanVar(value=self.config.get_info("CONFIG", "is_notify"))
            # Tab 1
            self.hotkey_tab = tkinter.ttk.Frame(
                self.settings_notebook
            )
            self.settings_notebook.add(self.hotkey_tab, text="Hotkey Settings")
            self.toggle_record_button = tkinter.ttk.Button(
                self.hotkey_tab,
                text="Start record",
                command=lambda: self._start_record()
            )
            self.toggle_record_button.place(
                rely=0.2,
                relx=0,
                relwidth=0.35
            )
            self.apply_button = tkinter.ttk.Button(
                self.hotkey_tab,
                text="Apply",
                command=lambda: self._apply_keys()
            )
            self.apply_button.place(
                rely=0.4,
                relx=0,
                relwidth=0.35
            )
            self.reset_button = tkinter.ttk.Button(
                self.hotkey_tab,
                text="Reset",
                command=lambda: self._reset_current_keys()
            )
            self.reset_button.place(
                rely=0.6,
                relx=0,
                relwidth=0.35
            )
            self.about_button = tkinter.ttk.Button(
                self.hotkey_tab,
                text="About",
                command=lambda: self._about()
            )
            self.about_button.place(
                rely=0.8,
                relx=0,
                relwidth=0.35
            )

            self.title = tkinter.ttk.Label(
                self.hotkey_tab,
                text="Press start record to set the hotkey.",
                anchor="center"
            )
            self.title.place(
                relheight=0.19, relwidth=1
            )
            self.current_hotkey_text = tkinter.ttk.Label(
                self.hotkey_tab,
                text=f"Current hotkey:"
            )
            self.current_hotkey_text.place(
                rely=0.25, relx=0.38
            )
            self.current_hotkey_label = tkinter.ttk.Label(
                self.hotkey_tab,
                text=f"{self.current_hotkey}"
            )
            self.current_hotkey_label.place(
                rely=0.415, relx=0.38
            )
            self.recorded_keys = tkinter.ttk.Label(
                self.hotkey_tab,
                text=f"Pressed keys:"
            )
            self.recorded_keys.place(
                rely=0.65, relx=0.38
            )
            self.hotkey_entry = tkinter.ttk.Entry(
                self.hotkey_tab,
                state='readonly'
            )
            self.hotkey_entry.place(
                rely=0.805,
                relx=0.385,
                relwidth=0.59,
                relheight=0.1525)

            # Tab 2
            self.other_tab = tkinter.ttk.Frame(
                self.settings_notebook,
                style="White.TFrame"
            )
            self.settings_notebook.add(self.other_tab, text="Other Settings")
            self.refreshing_checkbox = tkinter.ttk.Checkbutton(
                self.other_tab,
                text="Periodically refresh",
                variable=self.is_refreshing,
                command=self._checkbox_save
            )
            self.refreshing_checkbox.pack(pady=5, padx=5, anchor="w")

            self.notify_checkbox = tkinter.ttk.Checkbutton(
                self.other_tab,
                text="Notifications",
                variable=self.is_notify,
                command=self._checkbox_save
            )
            self.notify_checkbox.pack(padx=5, anchor="w")

            self.window.protocol("WM_DELETE_WINDOW", self._on_close)
            self.window.mainloop()
        else:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def _checkbox_save(self):
        self.config.set("CONFIG", "is_refreshing", f"{self.is_refreshing.get()}")
        self.config.set("CONFIG", "is_notify", f"{self.is_notify.get()}")
        self.config.save()

    def _on_close(self):
        self.window.destroy()
        self.window = None

    def _make_hotkey(self):
        keyboard.add_hotkey(
            self.current_hotkey,
            lambda: self.on_hotkey_callback(self.config.get_info("CONFIG", "default_device"))
        )
        if self.window:
            self.config.set("CONFIG", "dd_hotkey", str(self.current_hotkey))
            self.config.save()

    def _start_record(self):
        self.toggle_record_button.config(text="Stop record", command=lambda: self._stop_record())
        self.title.config(text="Press needed keys.")
        self.pressed_key_list = []
        self.hotkey_entry.config(state='normal')
        self.hotkey_entry.delete(0, tkinter.END)
        self.hotkey_entry.config(state='readonly')
        keyboard.hook(self._pressed_keys)

    def _pressed_keys(self, event):
        if len(self.pressed_key_list) < 3:
            if self.scancodes[event.scan_code] not in self.pressed_key_list:
                if event.event_type == "down":
                    self.pressed_key_list.append(self.scancodes[event.scan_code])
                    self.hotkey_entry.config(state='normal')
                    self.hotkey_entry.delete(0, tkinter.END)
                    self.hotkey_entry.insert(0, "+".join(self.pressed_key_list))
                    self.hotkey_entry.config(state='readonly')
        else:
            self._stop_record()

    def _stop_record(self):
        keyboard.unhook(self._pressed_keys)
        self.toggle_record_button.config(text="Start record", command=lambda: self._start_record())
        self.title.config(text="Press 'Apply' to save or press 'Start record' again.")

    def _reset_current_keys(self):
        if self.current_hotkey:
            self._remove_hotkey(self.current_hotkey)
        self.hotkey_entry.config(state='normal')
        self.hotkey_entry.delete(0, tkinter.END)
        self.hotkey_entry.config(state='readonly')
        self.pressed_key_list = []
        self.current_hotkey = ""
        self.config.set("CONFIG", "dd_hotkey", str(self.current_hotkey))
        self.config.save()
        self.recorded_keys.config(text=f"Pressed keys:")
        self.current_hotkey_label.config(text=f"{self.current_hotkey if self.current_hotkey else ""}")

    def _apply_keys(self):
        if not self.pressed_key_list:
            self.title.config(text="There is no pressed keys. Try again.")
            return
        if self.current_hotkey:
            self._remove_hotkey(self.current_hotkey)
        self.current_hotkey = "+".join(self.pressed_key_list)
        self._make_hotkey()
        self.title.config(text="Hotkey saved. Press 'Start record' to set another hotkey.")
        self.current_hotkey_label.config(text=f"{self.current_hotkey}")

    @staticmethod
    def _remove_hotkey(keys):
        keyboard.remove_hotkey(keys)

    @staticmethod
    def _about():
        tkinter.messagebox.showinfo(
            title="SmartHomeControl",
            message="SmartHomeControl v1.1.0\nAuthor: The-Real-Duke\nLicense: CC BY-NC-SA 4.0\nSource: github.com/The-Real-Duke/SmartHomeControl"
        )

    @staticmethod
    def clear_keys():
        while True:
            with keyboard._pressed_events_lock:
                for i in list(keyboard._pressed_events.keys()):
                    item = keyboard._pressed_events[i]
                    if time.time() - item.time > 2:
                        del keyboard._pressed_events[i]
            time.sleep(5)
