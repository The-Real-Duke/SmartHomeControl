import time
import tkinter
import tkinter.messagebox
import keyboard

class SettingsWindowManager:
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
            self.hotkey_frame = tkinter.Frame(
                self.window
            )
            self.hotkey_frame.place(
                relx=0.05,
                rely=0.01,
                relwidth=0.9,
                relheight=0.9)
            self.apply_button = tkinter.Button(
                self.hotkey_frame,
                text="Apply",
                command=lambda: self._apply_keys()
            )
            self.apply_button.place(
                rely=0.6,
                relx=0,
                relwidth=0.35
            )
            self.about_button = tkinter.Button(
                self.hotkey_frame,
                text="About",
                command=lambda: self._about()
            )
            self.about_button.place(
                rely=0.8,
                relx=0,
                relwidth=0.35
            )
            self.toggle_record_button = tkinter.Button(
                self.hotkey_frame,
                text="Start record",
                command=lambda: self._start_record()
            )
            self.toggle_record_button.place(
                rely=0.4,
                relx=0,
                relwidth=0.35
            )
            self.title = tkinter.Label(
                self.hotkey_frame,
                text="Press start record to set the hotkey."
            )
            self.title.place(
                relheight=0.19, relwidth=1
            )
            self.current_hotkey_label = tkinter.Label(
                self.hotkey_frame,
                text=f"Current hotkey: {self.current_hotkey}"
            )
            self.current_hotkey_label.place(
                rely=0.21, relx=0.37
            )
            self.recorded_keys = tkinter.Label(
                self.hotkey_frame,
                text=f"Pressed keys:"
            )
            self.recorded_keys.place(
                rely=0.35, relx=0.37
            )
            self.hotkey_entry = tkinter.Entry(
                self.hotkey_frame,
                bg="white",
                state='readonly'
            )
            self.hotkey_entry.place(
                rely=0.5,
                relx=0.385,
                relwidth=0.5,
                relheight=0.15)
            self.reset_button = tkinter.Button(
                self.hotkey_frame,
                text="Reset",
                command=lambda: self._reset_current_keys()
            )
            self.reset_button.place(
                rely=0.2,
                relx=0,
                relwidth=0.35
            )
            self.window.protocol("WM_DELETE_WINDOW", self._on_close)
            self.window.mainloop()
        else:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def _on_close(self):
        self.window.destroy()
        self.window = None

    def _make_hotkey(self):
        keyboard.add_hotkey(
            self.current_hotkey,
            lambda: self.on_hotkey_callback()
        )
        if self.window:
            self.config.set("CONFIG", "dd_hotkey", str(self.current_hotkey))
            self.config.save()

    def _start_record(self):
        self.toggle_record_button.config(text="Stop record", command=lambda: self._stop_record())
        self.title.config(text="Press wanted keys \n and press stop record (max 3 keys)")
        self.pressed_key_list = []
        self.hotkey_entry.config(state='normal')
        self.hotkey_entry.delete(0, tkinter.END)
        self.hotkey_entry.config(state='readonly')
        keyboard.hook(self._pressed_keys)

    def _pressed_keys(self, event):
        if len(self.pressed_key_list) < 3:
            if event.name not in self.pressed_key_list:
                if event.event_type == "down":
                    self.pressed_key_list.append(event.name)
                    self.hotkey_entry.config(state='normal')
                    self.hotkey_entry.delete(0, tkinter.END)
                    self.hotkey_entry.insert(0, "+".join(self.pressed_key_list))
                    self.hotkey_entry.config(state='readonly')
        else:
            self._stop_record()

    def _stop_record(self):
        keyboard.unhook(self._pressed_keys)
        self.toggle_record_button.config(text="Start record", command=lambda: self._start_record())
        self.title.config(text="Press Apply to save hotkey \n or press Start record again")

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
        self.current_hotkey_label.config(text=f"Current hotkey: {self.current_hotkey if self.current_hotkey else ""}")

    def _apply_keys(self):
        if not self.pressed_key_list:
            return
        if self.current_hotkey:
            self._remove_hotkey(self.current_hotkey)
        self.current_hotkey = "+".join(self.pressed_key_list)
        self._make_hotkey()
        self.title.config(text="Applied. \n Press start record to set the another hotkey.")
        self.current_hotkey_label.config(text=f"Current hotkey: {self.current_hotkey}")
        print(self.current_hotkey)

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