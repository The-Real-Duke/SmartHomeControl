import configparser
from pathlib import Path


class ConfigManager:
    def __init__(self, path="config.ini"):
        self.path = Path(path)
        self.data = configparser.ConfigParser()
        if self.path.exists():
            self.data.read(self.path)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.data["CONFIG"] = {
                "default_device": "",
                "dd_hotkey": "",
                "is_refreshing": "True",
                "is_notify": "True"
            }
            self.save()

    def get_info(self, section, option, fallback=None):
        return self.data.get(section, option, fallback=fallback)

    def set(self, section, option, value):
        if section not in self.data:
            self.data[section] = {}
        self.data[section][option] = value
        self.save()

    def save(self):
        with open(self.path, 'w') as f:
            self.data.write(f)
