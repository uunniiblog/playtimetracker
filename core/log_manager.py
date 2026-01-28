import os
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta

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

    def get_stats_for_app(self, combined_name):
        """Returns total_seconds and a dict of {date: hours} for the individual graph."""
        total_seconds = 0
        daily_data = {}

        # Extract actual process name
        target_process = self._extract_process(combined_name)
        if not target_process:
            return 0, {}

        for log_file in self.log_dir.rglob("activity_*.csv"):
            try:
                with open(log_file, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        # Match the process name column
                        if row.get('App') == target_process:
                            active_time_str = row.get('ActiveTime', '0:0:0')
                            seconds = self._duration_to_seconds(active_time_str)
                            total_seconds += seconds

                            # Group by date for the graph
                            try:
                                date_str = row['Timestamp_Start'].split(' ')[0]
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                                daily_data[date_obj] = daily_data.get(date_obj, 0) + (seconds / 3600)
                            except (KeyError, ValueError):
                                continue
            except Exception as e:
                print(f"[LOG ERROR] Error reading {log_file}: {e}")
                continue

        return total_seconds, daily_data

    def _update_last_played_cache(self, app_name, title):
        """Updates the timestamp in the hidden JSON cache."""
        cache = {}
        if self.metadata_file.exists():
            try:
                cache = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except Exception: pass
        
        # Store clean App Name as Key, but save Title inside
        cache[app_name] = {
            "time": datetime.now().isoformat(),
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

    def _duration_to_seconds(self, duration_str):
        """Converts H:M:S string (e.g. '0:01:12' or '01:02:03') to total seconds."""
        if not duration_str or duration_str == "None":
            return 0
        try:
            parts = list(map(int, duration_str.split(':')))
            if len(parts) == 3: # H:M:S
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2: # M:S
                return parts[0] * 60 + parts[1]
            return 0
        except (ValueError, TypeError):
            return 0

    def get_global_summary(self, timeframe="All Time"):
        """Aggregates all apps for the summary table across all folders."""
        summary = {} # {app_name: seconds}
        titles = {}  # {app_name: latest_title}
        now = datetime.now()
        
        start_filter = None
        if timeframe == "Today":
            start_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif timeframe == "Last 7 Days":
            start_filter = now - timedelta(days=7)
        elif timeframe == "Last 30 Days":
            start_filter = now - timedelta(days=30)

        for log_file in self.log_dir.rglob("activity_*.csv"):
            try:
                with log_file.open(mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        start_dt = datetime.strptime(row['Timestamp_Start'], '%Y-%m-%d %H:%M:%S')
                        if start_filter and start_dt < start_filter:
                            continue
                        
                        app = row.get('App')
                        if not app: continue
                        
                        seconds = self._duration_to_seconds(row.get('ActiveTime', '0:0:0'))
                        summary[app] = summary.get(app, 0) + seconds
                        # Keep the most recent title found
                        titles[app] = row.get('Title', '')
            except Exception: continue

        # Return list of tuples: (app_name, total_seconds, latest_title)
        sorted_data = sorted(summary.items(), key=lambda x: x[1], reverse=True)
        return [(app, seconds, titles.get(app, "")) for app, seconds in sorted_data]