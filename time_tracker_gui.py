import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTextEdit, QWidget
)
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtCore import QProcess, QDir
from PyQt6.QtGui import QPixmap, QIcon
from pathlib import Path
import os


class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker")
        self.setGeometry(100, 100, 600, 400)

        # Build the path to the icon based on the current file's location
        icon_path = Path(__file__).parent / 'icon.png'
        print(f"Icon path: {icon_path}")

        # Load the icon
        pixmap = QPixmap(str(icon_path))  # Convert the Path object to a string
        if pixmap.isNull():
            print("Failed to load icon")
        else:
            appIcon = QIcon(pixmap)
            self.setWindowIcon(appIcon)  # This sets the icon for the taskbar

        # Initialize main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Horizontal layout for combo box and refresh button
        self.combo_layout = QHBoxLayout()
        self.layout.addLayout(self.combo_layout)

        # Combo box for selecting windows
        self.window_combo = QComboBox()
        self.combo_layout.addWidget(self.window_combo)

        # Refresh button as a small icon
        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(QIcon.fromTheme("view-refresh"))  # Use a standard refresh icon
        self.refresh_button.setToolTip("Refresh Window List")
        self.refresh_button.setFixedSize(24, 24)  # Half the height of the default button
        self.refresh_button.clicked.connect(self.refresh_window_list)
        self.combo_layout.addWidget(self.refresh_button)

        # Buttons
        self.start_button = QPushButton("Start Tracking")
        self.start_button.clicked.connect(self.start_tracking)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Tracking")
        self.stop_button.clicked.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.stop_button)

        # Text output for console logs
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.layout.addWidget(self.console_output)

        # Process for running the script
        self.process = QProcess()

        # Handle process output
        self.process.readyReadStandardOutput.connect(self.update_console)
        self.process.readyReadStandardError.connect(self.update_console)

        # Initial load of the window list
        self.last_selected_window = None
        self.refresh_window_list()

    def refresh_window_list(self):
        """Refresh the list of open windows."""
        try:
            self.console_output.append("Refreshing window list...")

            # Fetch the list of open window titles
            result = subprocess.check_output(
                ["kdotool", "search", "--name", "."], text=True
            ).strip()
            window_ids = result.split("\n") if result else []
            window_titles = [
                subprocess.check_output(
                    ["kdotool", "getwindowname", window_id], text=True
                ).strip()
                for window_id in window_ids
            ]

            # Save the current selected text
            current_selection = self.window_combo.currentText()

            # Update combo box with the new list
            self.window_combo.clear()
            self.window_combo.addItems(window_titles)

            # Restore the previously selected window if still present
            if current_selection in window_titles:
                index = self.window_combo.findText(current_selection)
                self.window_combo.setCurrentIndex(index)
            else:
                # If the previously selected window is no longer available, select the first item
                self.window_combo.setCurrentIndex(0)

            # Update the last selected window
            self.last_selected_window = self.window_combo.currentText()
            self.console_output.append("Window list refreshed.")
        except subprocess.CalledProcessError as e:
            self.console_output.append(f"Failed to fetch window list: {e}")


    def start_tracking(self):
        """Start tracking the selected window."""
        selected_window = self.window_combo.currentText()
        if not selected_window:
            self.console_output.append("No window selected!")
            return

        self.last_selected_window = selected_window
        self.console_output.append(f"Starting tracking for: {selected_window}")

        # Get the absolute path of the current Python script directory
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # Get the absolute path of the track_time.sh script
        track_time_script = os.path.join(script_dir, "track_time.sh")

        # Start the script with the selected window and working directory as arguments
        self.process.start("bash", [track_time_script, selected_window, script_dir])

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_tracking(self):
        """Stop tracking."""
        if self.process.state() == QProcess.ProcessState.Running:
            self.console_output.append("Stopping tracking...")
            # Send SIGTERM to allow the script to handle cleanup
            self.process.terminate()
            # Wait for the script to finish its cleanup
            self.process.waitForFinished()
            self.console_output.append("Tracking stopped.")
        else:
            self.console_output.append("No tracking process is running.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_console(self):
        """Update console output with process logs."""
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()
        if output:
            self.console_output.append(output.strip())
        if error:
            self.console_output.append(f"ERROR: {error.strip()}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec())
