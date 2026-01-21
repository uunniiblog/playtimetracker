import os
import datetime
import json
from pathlib import Path

class LogManager:
    def __init__(self, log_dir):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.header = "Timestamp_Start;Timestamp_End;Duration;ActiveTime;App;Title;Status;Tags\n"
        self.metadata_file = self.log_dir / ".last_played.json"

    def format_duration(self, seconds):
        """Converts seconds to H:MM:SS."""
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"

    def get_daily_file(self, date_obj):
        """
        Returns the path for logs/YYYY-MM/activity_YYYY-MM-DD.csv
        """
        month_folder = self.log_dir / date_obj.strftime('%Y-%m')
        # Create folder if missing
        month_folder.mkdir(parents=True, exist_ok=True) 
        
        return month_folder / f"activity_{date_obj.strftime('%Y-%m-%d')}.csv"

    def save_session(self, session_data, is_update=False):
        """
        Saves or updates a log entry.
        session_data: dict containing all columns
        is_update: If True, replaces the last line in the file
        """
        start_dt = session_data['start']
        log_file = self.get_daily_file(start_dt)
        
        # Prepare the line
        line = (
            f"{start_dt.strftime('%Y-%m-%d %H:%M:%S')};"
            f"{session_data['end'].strftime('%Y-%m-%d %H:%M:%S')};"
            f"{self.format_duration(session_data['duration'])};"
            f"{self.format_duration(session_data['active_time'])};"
            f"{session_data['app']};"
            f"{session_data['title']};"
            f"{session_data['status']};"
            f"{session_data['tags']}\n"
        )

        try:
            # Ensure file and header exist
            if not log_file.exists() or log_file.stat().st_size == 0:
                log_file.write_text(self.header, encoding="utf-8")

            if not is_update:
                # Append new session
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(line)
                self._update_last_played_cache(session_data['app'], session_data['title'])
            else:
                # Overwrite the last line (Periodic Save)
                content = log_file.read_text(encoding="utf-8").splitlines()
                if len(content) > 1: # Don't overwrite header
                    content[-1] = line.strip()
                    log_file.write_text("\n".join(content) + "\n", encoding="utf-8")
                else:
                    # Fallback if file was somehow cleared
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(line)
            
            return log_file
        except Exception as e:
            print(f"[LOG ERROR] {e}")
            return None

    def get_total_app_playtime(self, app_name):
        """
        Scans logs to find total playtime for a specific app.
        """
        total_seconds = 0
        try:
            # Use rglob to search inside all YYYY-MM folders
            for log_file in self.log_dir.rglob("activity_*.csv"):
                lines = log_file.read_text(encoding="utf-8").splitlines()
                for line in lines[1:]:
                    parts = line.split(";")
                    if len(parts) >= 5 and parts[4] == app_name:
                        h, m, s = map(int, parts[3].split(":"))
                        total_seconds += h * 3600 + m * 60 + s
        except Exception:
            pass
        return total_seconds

    def get_all_tracked_apps(self):
        """Returns a unique list of App (exe) names found in all daily logs."""
        apps = set()
        for log_file in self.log_dir.rglob("activity_*.csv"):
            try:
                lines = log_file.read_text(encoding="utf-8").splitlines()
                for line in lines[1:]: # Skip header
                    parts = line.split(";")
                    if len(parts) >= 5:
                        apps.add(parts[4]) # Column: App (exe)
            except Exception: continue
        return sorted(list(apps))

    def get_stats_for_app(self, app_name):
        """Calculates total seconds and daily breakdown for a specific app."""
        total_seconds = 0
        daily_data = {} # {date: total_hours_that_day}

        process = self._extract_process(app_name)

        # Recursively find all activity files
        for log_file in self.log_dir.rglob("activity_*.csv"):
            try:
                lines = log_file.read_text(encoding="utf-8").splitlines()
                for line in lines[1:]:
                    parts = line.split(";")
                    # Check if the App column (4) matches
                    if len(parts) >= 5 and parts[4] == process:
                        # 1. Parse Date from Start Timestamp
                        dt_obj = datetime.datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                        date_key = dt_obj.date()

                        # 2. Parse ActiveTime (Index 3)
                        h, m, s = map(int, parts[3].split(":"))
                        seconds = h * 3600 + m * 60 + s
                        
                        total_seconds += seconds
                        daily_data[date_key] = daily_data.get(date_key, 0) + (seconds / 3600)
            except Exception: continue

        # Sort daily data by date for the graph
        sorted_daily = dict(sorted(daily_data.items()))
        return total_seconds, sorted_daily

    def _update_last_played_cache(self, app_name, title):
        """Updates the timestamp in the hidden JSON cache."""
        cache = {}
        if self.metadata_file.exists():
            try:
                cache = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except Exception: pass
        
        # Store clean App Name as Key, but save Title inside
        cache[app_name] = {
            "time": datetime.datetime.now().isoformat(),
            "last_title": title
        }
        
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)

    def get_apps_sorted_by_latest(self):
        """Returns app names sorted by their last played timestamp."""
        if not self.metadata_file.exists():
            # Fallback to read all logs if JSON doesn't exist
            return self.get_all_tracked_apps()

        try:
            cache = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            # Sort keys by their ISO timestamp values in reverse
            sorted_apps = sorted(cache.items(), key=lambda x: x[1]['time'], reverse=True)
            return [f"{data['last_title']} - {app}" for app, data in sorted_apps]
        except Exception as e:
            print(f"[LOG ERROR] {e}")
            return self.get_all_tracked_apps()

    def get_grouped_logs_for_app(self, combined_name):
        """
        Returns an OrderedDict: { "2026-01-18": [rows], "2026-01-17": [rows] }
        """
        from collections import OrderedDict
        grouped_data = {}

        # FIX: Extract the actual exe name before searching
        target_process = self._extract_process(combined_name)

        for log_file in self.log_dir.rglob("activity_*.csv"):
            try:
                lines = log_file.read_text(encoding="utf-8").splitlines()
                if len(lines) < 2: continue
                
                # Extract date from filename (activity_YYYY-MM-DD.csv)
                date_str = log_file.stem.replace("activity_", "")
                
                day_rows = []
                for line in lines[1:]:
                    parts = line.split(";")
                    if len(parts) >= 5 and parts[4] == target_process:
                        day_rows.append(parts)
                
                if day_rows:
                    grouped_data[date_str] = day_rows
            except Exception: continue
            
        # Sort by date descending
        return OrderedDict(sorted(grouped_data.items(), reverse=True))

    def _extract_process(self, combined_name):
        """Helper to get process from title"""
        if not combined_name: return ""
        if " - " in combined_name:
            return combined_name.rsplit(" - ", 1)[-1].strip()
        return combined_name.strip()