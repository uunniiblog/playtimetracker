import os
import datetime
from pathlib import Path
import config
from collections import OrderedDict

class DataManager:
    def __init__(self):
        self.settings = {'LOG_REFRESH_TIMER': 0, 'ENABLE_ONLY_WINE': 0, 'ENABLE_DYNAMIC_TITLE': 0, 'LOG_PERIODIC_SAVE': 0}
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
                        # Ensure total_seconds captures the latest cumulative value
                        total_seconds = self.parse_time(parts[4]) 
                        daily_data[date_obj] = daily_data.get(date_obj, 0) + (seconds / 3600)
                    except ValueError: continue

        return total_seconds, daily_data

    def get_log_content(self, app_name):
        """
        Parses the log file.
        """
        log_path = config.LOG_DIR / f"game_playtime_{app_name}.log"
        if not log_path.exists():
            return [], []

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            if not lines:
                return [], []

            # Parse Header
            # We strip whitespace but keep the specific separator logic
            headers = [h.strip() for h in lines[0].strip().split(";")]
            
            # Parse Rows
            data = []
            for line in lines[1:]:
                if not line.strip(): continue
                # Split by semicolon
                row_items = [item.strip() for item in line.strip().split(";")]
                # Ensure row has same number of columns as header (pad with empty if needed)
                while len(row_items) < len(headers):
                    row_items.append("")
                data.append(row_items)
                
            return headers, data
        except Exception as e:
            print(f"Error reading log: {e}")
            return [], []

    def save_log_content(self, app_name, headers, data):
        """
        Writes headers and data back to the log file.
        """
        log_path = config.LOG_DIR / f"game_playtime_{app_name}.log"
        
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                # 1. Write Header
                # Reconstruct the "; " separator style
                header_line = "; ".join(headers) + "\n"
                f.write(header_line)
                
                # 2. Write Data
                for row in data:
                    line = "; ".join(row) + "\n"
                    f.write(line)
            return True
        except Exception as e:
            print(f"Error saving log: {e}")
            return False

    def delete_log_file(self, app_name):
        """Physically deletes the .log file."""
        log_path = config.LOG_DIR / f"game_playtime_{app_name}.log"
        try:
            if log_path.exists():
                log_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
