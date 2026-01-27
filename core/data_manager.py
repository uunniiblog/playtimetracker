import os
import datetime
from pathlib import Path
import config
from collections import OrderedDict

class DataManager:
    def __init__(self):
        self.settings = {'LOG_REFRESH_TIMER': 0, 'ENABLE_ONLY_WINE': 0, 'LOG_PERIODIC_SAVE': 0, 'AFK_TIMER': 0}
        self.load_settings()

    def load_settings(self):
        if config.SETTINGS_FILE.exists():
            content = config.SETTINGS_FILE.read_text()
            for line in content.splitlines():
                if '=' in line and not line.strip().startswith('#'):
                    key, val = map(str.strip, line.split('=', 1))
                    if key in self.settings:
                        try:
                            self.settings[key] = int(val)
                        except ValueError:
                            self.settings[key] = val

    def save_settings_text(self, text):
        config.SETTINGS_FILE.write_text(text, encoding='utf-8')
        self.load_settings()

    def get_note(self, app_name):
        note_file = config.NOTES_DIR / f"notes_{app_name}.txt"
        return note_file.read_text(encoding='utf-8') if note_file.exists() else ""

    def save_note(self, app_name, content):
        note_file = config.NOTES_DIR / f"notes_{app_name}.txt"
        note_file.write_text(content, encoding='utf-8')
