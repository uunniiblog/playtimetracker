import os
from PyQt6.QtCore import QObject, QTimer
from core.system_utils import SystemUtils

class CliController(QObject):
    def __init__(self, main_window, tracker_service, data_manager):
        super().__init__()
        self.window = main_window
        self.tracker = tracker_service
        self.data = data_manager
        self.auto_timer = None
        self.target_process = None

    def handle_args(self, args):
        if args.background:
            print("Launching in Background Mode...")

            refresh = self.data.settings.get('REFRESH_INTERVAL', 5)
            save = self.data.settings.get('SAVE_INTERVAL', 60)
            afk = self.data.settings.get('AFK_TIMER', 0)

            self.tracker.background_tracking(refresh, save, afk)
            return

        if args.target:
            self.start_auto_tracking(args.target)

    def start_auto_tracking(self, process_path):
        self.target_process = os.path.basename(process_path)
        self.window.tracking_tab.append_log(f"Auto-tracking enabled for: {self.target_process}")        
        self.window.tracking_tab.append_log("Waiting")
        print(f"Auto-tracking enabled for: {self.target_process}")
        print("Waiting", end="")

        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self._attempt_auto_launch)
        self.auto_timer.start(2000)

    def _attempt_auto_launch(self):
        utils = self.tracker.desktop_utils
        pid = SystemUtils.get_pid_by_name(self.target_process)
        
        if not pid:
            print(".", end="", flush=True)
            self.window.tracking_tab.append_partial_log(".")
            return 

        print(f"Detected PID: {pid}. Looking for KWin window...")
        self.window.tracking_tab.append_log(f"Detected PID: {pid}. Looking for KWin window...")
        
        wid, title = utils.find_window_by_pid(pid)
        
        if wid and title:
            self.auto_timer.stop()
            self.window.tracking_tab.append_log(f"Success! Found Window: {title}")
            print(f"Success! Found Window: {title}")
            self.window.tracking_tab.start_tracking_with_params(title)