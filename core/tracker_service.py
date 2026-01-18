from PyQt6.QtCore import QObject, pyqtSignal
from core.tracker_worker import TrackerWorker
from core.tracker_bg_worker import TrackerBgWorker
from core.utils_factory import get_desktop_utils

class TrackerService(QObject):
    log_received = pyqtSignal(str)
    tracking_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.worker = None
        try:
            self.desktop_utils = get_desktop_utils()
        except RuntimeError as e:
            print(f"Critical Startup Error: {e}")
            self.desktop_utils = None

    def start_tracking(self, app_name, refresh_timer, save_interval):
        if not self.desktop_utils:
            self.log_received.emit("ERROR: Desktop utilities not initialized.")
            return
            
        # Stop existing worker if any
        if self.worker and self.worker.isRunning():
            self.stop_tracking()

        self.worker = TrackerWorker(app_name, refresh_timer, save_interval, self.desktop_utils)
        self.worker.log_message.connect(self.log_received.emit)
        self.worker.finished.connect(self.tracking_finished.emit)

        if not self.worker.is_window_open():
            self.worker.log_message.emit(f"ERROR: Window '{app_name}' not found. Start the app before tracking.")
            self.tracking_finished.emit()
            return 

        self.worker.start()

    def background_tracking(self, refresh_timer, save_interval):
        if not self.desktop_utils:
            self.log_received.emit("ERROR: Desktop utilities not initialized.")
            return

        # Stop existing worker if any
        if self.worker and self.worker.isRunning():
            self.stop_tracking()

        self.worker = TrackerBgWorker(refresh_timer, save_interval, self.desktop_utils)
        self.worker.log_message.connect(self.log_received.emit)
        self.worker.finished.connect(self.tracking_finished.emit)
        self.worker.start()    

    def stop_tracking(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
