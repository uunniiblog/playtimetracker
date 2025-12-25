from PyQt6.QtWidgets import QMainWindow, QTabWidget
from ui.tabs.tracking_tab import TrackingTab
from ui.tabs.stats_tab import StatsTab
from ui.tabs.notes_tab import NotesTab
from ui.tabs.logs_tab import LogsTab
from ui.tabs.settings_tab import SettingsTab
import config

class MainWindow(QMainWindow):
    def __init__(self, tracker_service, data_manager):
        super().__init__()
        self.tracker_service = tracker_service
        self.data_manager = data_manager

        self.setWindowTitle(f"PlayTimeTracker {config.VERSION}")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Initialize Tabs
        self.tracking_tab = TrackingTab(tracker_service, data_manager)
        self.stats_tab = StatsTab(data_manager)
        self.notes_tab = NotesTab(data_manager)
        self.logs_tab = LogsTab(data_manager)
        self.settings_tab = SettingsTab(data_manager)

        self.tabs.addTab(self.tracking_tab, "Tracking")
        self.tabs.addTab(self.stats_tab, "Statistics")
        self.tabs.addTab(self.notes_tab, "Notes")
        self.tabs.addTab(self.logs_tab, "Logs")
        self.tabs.addTab(self.settings_tab, "Settings")

    def closeEvent(self, event):
        self.tracking_tab.stop_tracking()
        event.accept()
