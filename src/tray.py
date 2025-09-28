import time

import pystray
from PIL import Image


class TrayManager:
    def __init__(
            self,
            image,
            config,
            activate_device,
            exit_program,
            settings,
            refresh,
            dm
    ):
        self.shc_image = image
        self.config = config
        self.default_device = self.config.get_info("CONFIG", "default_device")
        self.exit_program = exit_program
        self.activate_device = activate_device
        self.settings = settings
        self.refresh = refresh
        self.dm = dm

    def _build_tray_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                "Exit", lambda icon, item: self.exit_program()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Activatable devices", pystray.Menu(
                    lambda: (
                        pystray.MenuItem(d.name, lambda icon,item: self.activate_device(item.text), checked=lambda item: self._is_device_on(item))
                        for d in self.dm.devices.values())
                )
            ),
            pystray.MenuItem(
                "Select default device", pystray.Menu(
                    lambda: (
                        pystray.MenuItem(d.name, self._set_default_device,
                                         checked=lambda item: self._is_default_device(item))
                        for d in self.dm.devices.values())
                )
            ),
            pystray.MenuItem(
                "Settings", lambda icon, item: self.settings.open()
            ),
            pystray.MenuItem(
                "Refresh Page", lambda icon, item: self.refresh()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Activate default device", lambda icon, item:self.activate_device(self.default_device)
            )
        )

    # Updating tray
    def update_tray_menu(self):
        self.shc_tray_icon.menu = self._build_tray_menu()
        self.shc_tray_icon.update_menu()
        self.make_notify("Tray rebuilt", title="SmartHomeControl")

    # Making notify if turned on
    def make_notify(self, text, title="SmartHomeControl"):
        if self.config.get_info("CONFIG", "is_notify") == "True":
            self.shc_tray_icon.notify(text, title=title)

    # Build and start tray
    def start_tray(self):
        self.shc_tray_icon = pystray.Icon("SmartHomeControl", icon=Image.open(self.shc_image), title="SmartHomeControl",
                                          menu=self._build_tray_menu())
        self.shc_tray_icon.run()

    def _set_default_device(self, icon, item):
        self.default_device = item.text
        self.config.set("CONFIG", "default_device", str(self.default_device))
        self.config.save()

    def _is_default_device(self, item):
        return item.text == self.default_device

    # Device checking
    def _is_device_on(self, item):
        time.sleep(0.05)
        for device in self.dm.devices.values():
            if device.name == item.text:
                return device.state
        return None
