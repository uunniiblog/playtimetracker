import os
import datetime
from pathlib import Path
import config
from collections import OrderedDict

class DataManager:
    def __init__(self):
        self.settings = {'LOG_REFRESH_TIMER': 0, 'ENABLE_ONLY_WINE': 0, 'ENABLE_DYNAMIC_TITLE': 0}
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

    def get_log_files(self):
        files = list(config.LOG_DIR.glob("game_playtime_*.log"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        sorted_logs = OrderedDict()
        for f in files:
            app_name = f.stem.replace("game_playtime_", "")
            sorted_logs[app_name] = f

        return sorted_logs

    def get_note(self, app_name):
        note_file = config.NOTES_DIR / f"notes_{app_name}.txt"
        return note_file.read_text(encoding='utf-8') if note_file.exists() else ""

    def save_note(self, app_name, content):
        note_file = config.NOTES_DIR / f"notes_{app_name}.txt"
        note_file.write_text(content, encoding='utf-8')

    def parse_time(self, time_str):
        try:
            parts = list(map(int, time_str.split(":")))
            return sum(x * 60 ** i for i, x in enumerate(reversed(parts)))
        except ValueError:
            return 0

    def get_stats_for_app(self, app_name):
        # Returns (Total Hours, {Date: Hours})
        log_files = self.get_log_files()
        if app_name not in log_files: return 0, {}

        daily_data = {}
        total_seconds = 0

        with open(log_files[app_name], 'r') as f:
            for line in f:
                parts = line.strip().split("; ")
                if len(parts) == 5:
                    try:
                        date_obj = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S").date()
                        seconds = self.parse_time(parts[3])
                        total_seconds = self.parse_time(parts[4]) # Last line is cumulative usually
                        daily_data[date_obj] = daily_data.get(date_obj, 0) + (seconds / 3600)
                    except ValueError: continue

        return (total_seconds / 3600), daily_data
