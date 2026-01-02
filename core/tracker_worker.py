import time
import datetime
import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal
import config
from core.kde_utils import KdeUtils

class TrackerWorker(QThread):
    log_message = pyqtSignal(str)

    def __init__(self, app_name, refresh_interval, save_interval, desktop_utils, dynamic_title=False):
        super().__init__()

        self.utils = desktop_utils

        if dynamic_title:
            self.app_name = self.find_best_log_match(app_name)
        else:
            self.app_name = app_name

        self.target_window_id = self.utils.find_window_id_by_title(app_name, dynamic_title)
        self.refresh_interval = int(refresh_interval)
        self.save_interval = int(save_interval) * 60
        self.dynamic_title = dynamic_title
        self.running = True
        self.session_line_exists = False

        # Internal counters
        self.total_playtime = 0
        self.session_playtime = 0
        self.session_start = datetime.datetime.now()

        # Define the log file path based on the 'best match' name
        self.log_file = config.LOG_DIR / f"game_playtime_{self.app_name}.log"

    def is_window_open(self):
        """Checks if any open window matches the target window id."""
        try:
            # Get all IDs again
            all_ids = self.utils.get_all_window_ids()
            if self.target_window_id in all_ids:
                return True
            
            # Rechecks in case of game restarting
            self.target_window_id = self.utils.find_window_id_by_title(self.app_name, self.dynamic_title)
            return self.target_window_id is not None
        except Exception as e:
            self.log_message.emit(f"Error checking window status: {e}")
            return False

    def find_best_log_match(self, current_title):
        """ Logic to find if similar log file already exists """
        best_match = current_title
        max_match_len = 0

        if not config.LOG_DIR.exists():
            return current_title

        for filepath in config.LOG_DIR.glob("game_playtime_*.log"):
            game_name = filepath.name.replace("game_playtime_", "").replace(".log", "")

            # Check for common prefix
            common_prefix = os.path.commonprefix([current_title.lower(), game_name.lower()])
            prefix_len = len(common_prefix)

            # If they share a significant start (10+ chars), treat as same game
            if prefix_len > max_match_len and prefix_len >= 10:
                best_match = game_name
                max_match_len = prefix_len

        return best_match

    def is_game_focused(self):
        """ Checks if target ID is focused """
        if not self.target_window_id:
            return False

        active_id = self.utils.get_active_window_id()
        #print(f"active_id: {active_id}")
        #print(f"self.target_window_id: {self.target_window_id}")
        return str(active_id) == str(self.target_window_id)

    def run(self):
        """ Main loop logic to calculate active window focus """
        # Load previous total playtime
        self.total_playtime = self.load_previous_playtime()
        self.log_message.emit(f"Starting tracking for: {self.app_name} {self.target_window_id}")
        self.log_message.emit(f"Starting playtime: {self.format_time(self.total_playtime)}")

        last_tick = time.monotonic()
        last_log_update = last_tick
        last_save_time = last_tick

        # Check if windows exists
        last_existence_check = 0 
        window_currently_open = True

        # Accumulator for sub-second precision
        accumulator = 0.0

        while self.running:
            now = time.monotonic()
            delta = now - last_tick
            last_tick = now
            accumulator += delta

            # Existence Check (Every 4.5 seconds)
            if now - last_existence_check >= 4.5:
                is_open = self.is_window_open()
                
                if window_currently_open and not is_open:
                    self.log_message.emit(f"'{self.app_name}' closed. Waiting for restart...")
                    window_currently_open = False
                elif not window_currently_open and is_open:
                    self.log_message.emit(f"'{self.app_name}' detected again with new ID {self.target_window_id}. Resuming tracking.")
                    window_currently_open = True
                
                last_existence_check = now

            # Increment timer every second
            if accumulator >= 1.0:
                seconds_passed = int(accumulator)

                if self.is_game_focused():
                    self.total_playtime += seconds_passed
                    self.session_playtime += seconds_passed

                # Keep the fractional remainder
                accumulator -= seconds_passed

            # UI logging
            if self.refresh_interval > 0 and (now - last_log_update) >= self.refresh_interval:
                self.log_message.emit(f"Session playtime: {self.format_time(self.session_playtime)}")
                self.log_message.emit(f"Total playtime: {self.format_time(self.total_playtime)}")
                last_log_update = now

            # Periodic Save
            if self.save_interval > 0 and (now - last_save_time) >= self.save_interval:
                self.log_message.emit(f"Log file modified: {self.log_file}")
                session_end = datetime.datetime.now()
                self._persist_to_log(session_end)
                last_save_time = now

            # Small sleep to reduce CPU usage
            time.sleep(0.1)

        # Persist session on exit
        session_end = datetime.datetime.now()
        self._persist_to_log(session_end, True)

    def load_previous_playtime(self):
        """Extracts the last 'Total Playtime' column from the log file."""
        if not self.log_file.exists():
            return 0

        try:
            lines = self.log_file.read_text().strip().splitlines()
            if len(lines) < 2: return 0 # Only header present

            last_line = lines[-1].split("; ")
            if len(last_line) < 5: return 0

            time_str = last_line[4].strip()
            h, m, s = map(int, time_str.split(":"))
            return h * 3600 + m * 60 + s
        except Exception:
            return 0

    def format_time(self, seconds):
        """Converts seconds to H:MM:SS."""
        seconds = int(seconds)

        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h}:{m:02d}:{s:02d}"

    def _persist_to_log(self, session_current_end, final=False):
        """Writes current stats to the log. Overwrites the last line if session already started."""
        session_length = int((session_current_end - self.session_start).total_seconds())
        start_str = self.session_start.strftime('%Y-%m-%d %H:%M:%S')
        end_str = session_current_end.strftime('%Y-%m-%d %H:%M:%S')

        log_entry = (
            f"{start_str}; {end_str}; "
            f"{self.format_time(session_length)}; "
            f"{self.format_time(int(self.session_playtime))}; "
            f"{self.format_time(int(self.total_playtime))}\n"
        )

        try:
            # Check if we need to write the header 
            if not self.log_file.exists() or self.log_file.stat().st_size == 0:
                header = "Time session Start; Time Session finish; Session Length; Session Playtime; Total Playtime\n"
                self.log_file.write_text(header, encoding="utf-8")

            if not self.session_line_exists:
                # First time saving this session: Just append
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)
                self.session_line_exists = True
            else:
                # Session already has a line: Replace the last line
                lines = self.log_file.read_text(encoding="utf-8").splitlines()
                if lines:
                    lines[-1] = log_entry.strip() # Replace last line
                    self.log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception as e:
            self.log_message.emit(f"Save Error: {str(e)}")

        # Show data
        if(final):
            self.log_message.emit("Session logged: Time session Start; Time Session finish; Session Length; Session Playtime; Total Playtime")
            self.log_message.emit(f"Session logged: {start_str}; {end_str}; {self.format_time(session_length)}; {self.format_time(self.session_playtime)}; {self.format_time(self.total_playtime)}")
            self.log_message.emit(f"Log file modified: {self.log_file}")

    def stop(self):
        self.running = False
