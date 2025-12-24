from PyQt6.QtCore import QObject, pyqtSignal
from core.tracker_worker import TrackerWorker

class TrackerService(QObject):
    log_received = pyqtSignal(str)
    tracking_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.worker = None

    def start_tracking(self, app_name, refresh_timer, save_interval, dynamic_title=False):
        # Stop existing worker if any
        if self.worker and self.worker.isRunning():
            self.stop_tracking()

        self.worker = TrackerWorker(app_name, refresh_timer, save_interval, dynamic_title)
        self.worker.log_message.connect(self.log_received.emit)
        self.worker.finished.connect(self.tracking_finished.emit)
        self.worker.start()

    def stop_tracking(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
