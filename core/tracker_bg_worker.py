import time
import config
from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
from core.system_utils import SystemUtils
from core.log_manager import LogManager

class TrackerBgWorker(QThread):
    log_message = pyqtSignal(str)

    def __init__(self, refresh_interval, save_interval, afk_timer, desktop_utils):
        super().__init__()
        self.utils = desktop_utils
        
        # Configuration
        self.refresh_interval = int(refresh_interval)
        self.save_interval = int(save_interval) * 60
        self.afk_timer = int(afk_timer) * 60
        self.start_tracking_threshold = 5
        
        self.running = True
        self.logger = LogManager(config.LOG_DIR)

        # Current Session State
        self.current_wid = None  # Cache the ID to detect changes cheaply
        self.current_process = None
        self.current_title = None
        self.session_start = None
        self.session_playtime = 0
        self.session_line_exists = False
        
        # AFK State
        self.was_afk = False

    def log(self, message):
        print(f"[BG] {message}")

    def run(self):
        self.log(f"Background Tracking Started. AFK Threshold: {self.afk_timer}s")

        if self.afk_timer > 0:
            SystemUtils.start_afk_daemon(self.afk_timer)

        last_tick = time.monotonic()
        last_log_update = last_tick
        last_save_time = last_tick
        last_window_check = 0
        accumulator = 0.0

        # Initial detection
        self._detect_switch()

        while self.running:
            now = time.monotonic()
            delta = now - last_tick
            last_tick = now
            accumulator += delta

            # AFK Logic 
            is_afk, _ = SystemUtils.get_afk_status()

            if is_afk and not self.was_afk:
                self.log("Status: AFK (Paused)")
                if self.afk_timer > 0:
                    # Subtract the threshold time that leaked into the session
                    self.session_playtime = max(0, self.session_playtime - self.afk_timer)
                    self._trigger_log_save() 
                self.was_afk = True
            elif not is_afk and self.was_afk:
                self.log("Status: Resumed")
                self.was_afk = False

            # Window Switch Detection
            if now - last_window_check >= 1.0:
                self._detect_switch()
                last_window_check = now

            # Increment timer every second if focused and not AFK
            if accumulator >= 1.0:
                seconds_passed = int(accumulator)
                accumulator -= seconds_passed

                if self.current_process and not is_afk:
                    self.session_playtime += seconds_passed
            
            # UI logging
            #if self.refresh_interval > 0 and (now - last_log_update) >= self.refresh_interval and not is_afk:
            #    print(f"Session playtime: {self.logger.format_duration(self.session_playtime)}")
            #    last_log_update = now

            # Autosave
            if self.save_interval > 0 and (now - last_save_time) >= self.save_interval:
                if self.current_process and not is_afk:
                    self._trigger_log_save()
                    last_save_time = now

            time.sleep(0.1)

        SystemUtils.stop_afk_daemon()
        if self.current_process:
            self._trigger_log_save(is_final=True)
        self.log("Background Tracking Stopped.")

    def _detect_switch(self):
        """
        Check if active window has changed.
        Initialize session for new process
        """
        try:
            active_wid = self.utils.get_active_window_id()
            
            # if no change do nothing
            if not active_wid or active_wid == self.current_wid:
                return

            # Logic when Switched tabs
            
            # Save the previous session
            if self.current_process:
                self._trigger_log_save(is_final=True)

            # Get data from new window
            pid = self.utils.get_window_pid(active_wid)
            if not pid:
                # If we can't get a PID just reset tracking
                self.current_wid = active_wid
                self.current_process = None
                return

            process_name = SystemUtils.get_app_name_from_pid(pid)
            _, title = self.utils.find_window_by_pid(pid)
            
            # For sub processes without title
            if not title: title = "Unknown"

            # Initialize new session state
            self.current_wid = active_wid
            self.current_process = process_name
            self.current_title = title
            self.session_start = datetime.now()
            self.session_playtime = 0
            self.session_line_exists = False
            
            self.log(f"Switched to: {title} ({process_name})")

        except Exception as e:
            self.log(f"Tracking Error: {e}")
            pass

    def _trigger_log_save(self, is_final=False):
        if not self.current_process: return

        if self.session_playtime < self.start_tracking_threshold:
            return

        now = datetime.now()
        wall_duration = int((now - self.session_start).total_seconds())

        session_data = {
            'start': self.session_start,
            'end': now,
            'duration': wall_duration,
            'active_time': self.session_playtime,
            'app': self.current_process,
            'title': self.current_title,
            'status': "Background",
            'tags': ""
        }

        self.logger.save_session(session_data, is_update=self.session_line_exists)
        self.session_line_exists = True

        readable = self.logger.format_duration(self.session_playtime)
        self.log(f"Saved: {self.current_process} - Time: {readable}")

    def stop(self):
        self.running = False
        