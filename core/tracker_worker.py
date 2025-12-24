import time
import datetime
import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal
import config
from core.kde_utils import KdeUtils
from core.utils_factory import get_desktop_utils

class TrackerWorker(QThread):
    log_message = pyqtSignal(str)

    def __init__(self, app_name, refresh_interval, save_interval, dynamic_title=False):
        super().__init__()
        try:
            self.utils = get_desktop_utils()
        except RuntimeError as e:
            self.log_message.emit(f"ERROR: {str(e)}")
            self.stop()

        if dynamic_title:
            self.app_name = self.find_best_log_match(app_name)
        else:
            self.app_name = app_name

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
        try:
            active_id = self.utils.get_active_window_id()
            active_title = self.utils.get_window_name(active_id)

            #self.log_message.emit(f"active_title: {active_title}")
            #self.log_message.emit(f"self.app_name: {self.app_name}")

            if self.dynamic_title:
                if self.app_name.lower() in active_title.lower() or \
                   active_title.lower() in self.app_name.lower():
                    return True

                common = os.path.commonprefix([self.app_name.lower(), active_title.lower()])
                if len(common) >= 15:
                    return True

                return False

            return self.app_name == active_title
        except Exception:
            return False

    def run(self):
        # Load previous total playtime
        self.total_playtime = self.load_previous_playtime()
        self.log_message.emit(f"Starting playtime: {self.format_time(self.total_playtime)}")

        last_tick = time.monotonic()
        last_log_update = last_tick
        last_save_time = last_tick

        # Accumulator for sub-second precision
        accumulator = 0.0

        while self.running:
            now = time.monotonic()
            delta = now - last_tick
            last_tick = now

            # Accumulate elapsed time
            accumulator += delta

            # Process whole seconds only
            if accumulator >= 1.0:
                seconds_passed = int(accumulator)

                if self.is_game_focused():
                    self.total_playtime += seconds_passed
                    self.session_playtime += seconds_passed

                # Keep the fractional remainder
                accumulator -= seconds_passed

            # UI logging (also monotonic, no drift)
            if (
                self.refresh_interval > 0
                and (now - last_log_update) >= self.refresh_interval
            ):
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

    def cleanup(self):
        """Saves final session data to log file on stop."""
        session_end = datetime.datetime.now()
        session_length = int((session_end - self.session_start).total_seconds())

        start_str = self.session_start.strftime('%Y-%m-%d %H:%M:%S')
        end_str = session_end.strftime('%Y-%m-%d %H:%M:%S')
        self._persist_to_log()

        # Show data
        self.log_message.emit("Session logged: Time session Start; Time Session finish; Session Length; Session Playtime; Total Playtime")
        self.log_message.emit(f"Session logged: {start_str}; {end_str}; {self.format_time(session_length)}; {self.format_time(self.session_playtime)}; {self.format_time(self.total_playtime)}")
        self.log_message.emit(f"Log file modified: {self.log_file}")

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
