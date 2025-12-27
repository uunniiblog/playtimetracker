from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QTextEdit, QCheckBox
from PyQt6.QtGui import QIcon
from core.system_utils import SystemUtils

class TrackingTab(QWidget):
    def __init__(self, tracker_service, data_manager):
        super().__init__()
        self.tracker = tracker_service
        self.data = data_manager

        # Connect Signals
        self.tracker.log_received.connect(self.append_log)
        self.tracker.tracking_finished.connect(self.on_tracking_finished)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Top Bar
        top_layout = QHBoxLayout()
        self.window_combo = QComboBox()
        top_layout.addWidget(self.window_combo)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self.refresh_list)
        top_layout.addWidget(refresh_btn)
        layout.addLayout(top_layout)

        # Options
        check_layout = QHBoxLayout()
        self.wine_check = QCheckBox("Only Show Wine Processes")
        self.wine_check.stateChanged.connect(self.refresh_list)
        check_layout.addWidget(self.wine_check)

        self.dynamic_check = QCheckBox("Dynamic Title Window")
        check_layout.addWidget(self.dynamic_check)
        layout.addLayout(check_layout)

        # Controls
        self.start_btn = QPushButton("Start Tracking")
        self.start_btn.clicked.connect(self.start_tracking)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Tracking")
        self.stop_btn.clicked.connect(self.stop_tracking)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        layout.addWidget(self.console)

        # Initial Load
        self.wine_check.setChecked(bool(self.data.settings.get('ENABLE_ONLY_WINE', 0)))
        self.dynamic_check.setChecked(bool(self.data.settings.get('ENABLE_DYNAMIC_TITLE', 0)))

    def refresh_list(self):
        self.window_combo.clear()
        utils = self.tracker.desktop_utils
        windows = SystemUtils.get_window_list(utils, self.wine_check.isChecked())
        for title, _ in windows:
            self.window_combo.addItem(title)
        self.console.append("List refreshed.")

    def start_tracking(self):
        app = self.window_combo.currentText()
        if not app: return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        refresh_timer = self.data.settings.get('LOG_REFRESH_TIMER', 0)
        save_time = self.data.settings.get('LOG_PERIODIC_SAVE', 0)
        self.tracker.start_tracking(app, refresh_timer, save_time, self.dynamic_check.isChecked())

    def stop_tracking(self):
        self.console.append("Stopping tracking...")
        self.tracker.stop_tracking()

    def on_tracking_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.console.append("Tracking stopped.")

    def append_log(self, text):
        """Inserts text at console."""

        scrollbar = self.console.verticalScrollBar()
        at_bottom = scrollbar.value() == scrollbar.maximum()

        cursor = self.console.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        if self.console.toPlainText() and not self.console.toPlainText().endswith("\n"):
            cursor.insertText("\n")

        cursor.insertText(text)

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def append_partial_log(self, text):
        """Inserts text at the end of the console without a newline."""
        cursor = self.console.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(text)
        # Ensure the scrollbar stays at the bottom
        self.console.ensureCursorVisible()

    def start_tracking_with_params(self, title):
        """Programmatically starts tracking for a specific window title."""
        # Find the title in our combo box
        index = self.window_combo.findText(title)
        if index >= 0:
            self.window_combo.setCurrentIndex(index)
        else:
            # If it's not in the list, add it temporarily
            self.window_combo.addItem(title)
            self.window_combo.setCurrentText(title)
            
        self.start_tracking()
