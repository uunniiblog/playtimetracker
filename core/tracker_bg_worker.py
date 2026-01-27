import time
from datetime import datetime
import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal
import config
from core.kde_utils import KdeUtils

class TrackerBgWorker(QThread):
    log_message = pyqtSignal(str)

    def __init__(self, refresh_interval, save_interval, afk_timer, desktop_utils):
        super().__init__()
        self.utils = desktop_utils
        print("not implemented")
        self.utils = desktop_utils
        self.refresh_interval = refresh_interval
        self.save_interval = save_interval
        self.running = True

    def run(self):
        """Placeholder loop so the thread stays alive until stopped."""
        self.log_message.emit("Background Tracking Started (Placeholder)...")
        
        while self.running:
            # This loop keeps the thread 'isRunning()' 
            # so TrackerService.stop_tracking() works as expected
            time.sleep(1) 
            
        self.log_message.emit("Background Tracking Stopped.")

    def stop(self):
        self.running = False
