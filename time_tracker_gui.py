import sys
import subprocess
import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTextEdit, QWidget, QTabWidget, QLabel, QCheckBox, QSpinBox
)
from PyQt6.QtCore import QProcess, QThread, Qt
from PyQt6.QtGui import QIcon
from pathlib import Path
import os
import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import rcParams
from PyQt6.QtWidgets import QTextEdit
import matplotlib.font_manager as fm
import warnings
import matplotlib.font_manager as fm

class TimeTrackerApp(QMainWindow):

    version = 'v2025-05-25'
    git_url = 'https://github.com/uunniiblog/playtimetracker'
    settings_file = Path(__file__).parent / "settings.ini"
    log_dir = Path(__file__).parent / "log"
    notes_dir = Path(__file__).parent / "notes"
    settings = {
        'LOG_REFRESH_TIMER': None,
        'ENABLE_ONLY_WINE': None,
        'ENABLE_DYNAMIC_TITLE': None
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.main_tab = QWidget()
        self.main_tab_layout = QVBoxLayout()
        self.main_tab.setLayout(self.main_tab_layout)
        self.tab_widget.addTab(self.main_tab, "Tracking")

        self.stats_tab = QWidget()
        self.stats_tab_layout = QVBoxLayout()
        self.stats_tab.setLayout(self.stats_tab_layout)
        self.tab_widget.addTab(self.stats_tab, "Statistics")

        self.notes_tab = QWidget()
        self.notes_tab_layout = QVBoxLayout()
        self.notes_tab.setLayout(self.notes_tab_layout)
        self.tab_widget.addTab(self.notes_tab, "Notes")

        self.settings_tab = QWidget()
        self.settings_tab_layout = QVBoxLayout()
        self.settings_tab.setLayout(self.settings_tab_layout)
        self.tab_widget.addTab(self.settings_tab, "Settings")

        self.setup_main_tab()
        self.setup_stats_tab()
        self.setup_notes_tab()
        self.setup_config_tab()

        #self.refresh_window_list()


    def setup_main_tab(self):
        self.combo_layout = QHBoxLayout()
        self.main_tab_layout.addLayout(self.combo_layout)

        self.window_combo = QComboBox()
        self.combo_layout.addWidget(self.window_combo)

        self.refresh_button = QPushButton()
        self.refresh_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_button.setToolTip("Refresh Application List")
        self.refresh_button.setFixedSize(24, 24)
        self.refresh_button.clicked.connect(self.refresh_window_list)
        self.combo_layout.addWidget(self.refresh_button)

        self.checkbox_layout = QHBoxLayout()

        # "Only Show Wine Processes" checkbox
        self.only_show_wine_checkbox = QCheckBox("Only Show Wine Processes")
        self.only_show_wine_checkbox.setChecked(False)
        self.only_show_wine_checkbox.stateChanged.connect(self.refresh_window_list)
        self.checkbox_layout.addWidget(self.only_show_wine_checkbox)

        # "Dynamic title" checkbox
        self.dynamic_title_checkbox = QCheckBox("Game with Dynamic Title Window")
        self.dynamic_title_checkbox.setChecked(False)
        self.checkbox_layout.addWidget(self.dynamic_title_checkbox)

        self.main_tab_layout.addLayout(self.checkbox_layout)

        self.start_button = QPushButton("Start Tracking")
        self.start_button.clicked.connect(self.start_tracking)
        self.main_tab_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Tracking")
        self.stop_button.clicked.connect(self.stop_tracking)
        self.stop_button.setEnabled(False)
        self.main_tab_layout.addWidget(self.stop_button)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.main_tab_layout.addWidget(self.console_output)

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.update_console)
        self.process.readyReadStandardError.connect(self.update_console)

    def setup_stats_tab(self):
        self.app_combo = QComboBox()
        self.stats_tab_layout.addWidget(self.app_combo)

        # Create refresh button and set the style (same as the existing one)
        self.refresh_stats_button = QPushButton()
        self.refresh_stats_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_stats_button.setToolTip("Refresh Statistics")
        self.refresh_stats_button.setFixedSize(24, 24)
        self.refresh_stats_button.clicked.connect(self.refresh_stats)

        # Add the refresh button next to the combo box
        stats_combo_layout = QHBoxLayout()
        stats_combo_layout.addWidget(self.app_combo)
        stats_combo_layout.addWidget(self.refresh_stats_button)
        self.stats_tab_layout.addLayout(stats_combo_layout)

        self.total_time_label = QLabel("Total Playtime: 0 hours")
        self.stats_tab_layout.addWidget(self.total_time_label)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.stats_tab_layout.addWidget(self.canvas)

        self.app_combo.currentIndexChanged.connect(self.update_graph)
        self.load_log_files()

    def setup_notes_tab(self):
        self.notes_combo = QComboBox()
        self.notes_tab_layout.addWidget(self.notes_combo)

        # Create refresh button and set the style (same as the existing one)
        self.refresh_notes_button = QPushButton()
        self.refresh_notes_button.setIcon(QIcon.fromTheme("view-refresh"))
        self.refresh_notes_button.setToolTip("Refresh Statistics")
        self.refresh_notes_button.setFixedSize(24, 24)
        self.refresh_notes_button.clicked.connect(self.refresh_notes)

        # Add the refresh button next to the combo box
        notes_combo_layout = QHBoxLayout()
        notes_combo_layout.addWidget(self.notes_combo)
        notes_combo_layout.addWidget(self.refresh_notes_button)
        self.notes_tab_layout.addLayout(notes_combo_layout)

        # Text field to show Notes
        self.notes_output = QTextEdit()
        self.notes_output.setReadOnly(False)
        self.notes_tab_layout.addWidget(self.notes_output)
        self.notes_output.textChanged.connect(self.on_notes_text_changed)

        # Save button
        self.save_note_button = QPushButton("Save Note")
        self.save_note_button.clicked.connect(self.save_note)
        self.notes_tab_layout.addWidget(self.save_note_button)

        # Status label for "Note saved" message
        self.note_status_label = QLabel("")
        self.notes_tab_layout.addWidget(self.note_status_label)

        self.notes_combo.currentIndexChanged.connect(self.update_notes)
        self.load_notes_files_combo()

    def setup_config_tab(self):
        self.settings_about_label = QLabel(
            f"PlayTimeTracker {self.version}\n{self.git_url}")
        self.settings_about_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        # Text with settings
        self.settings_text = QTextEdit()
        self.settings_text.setReadOnly(False)
        self.settings_text.textChanged.connect(self.on_about_text_changed)

        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)

        # Status label for "Settings saved" message
        self.settings_status_label = QLabel("")

        # Add widgets to layout
        self.settings_tab_layout.addWidget(self.settings_about_label)
        self.settings_tab_layout.addWidget(self.settings_text)
        self.settings_tab_layout.addWidget(self.save_button)
        self.settings_tab_layout.addWidget(self.settings_status_label)

        self.load_settings()

    def save_settings(self):
        with open(self.settings_file, "w", encoding="utf-8") as f:
            f.write(self.settings_text.toPlainText())
            self.settings_status_label.setText(f"Settings Saved.")

            # Overwrite current settings
            content = self.settings_text.toPlainText()
            for line in content.splitlines():
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = map(str.strip, line.split('=', 1))
                    if key in self.settings:
                        try:
                            self.settings[key] = int(value)
                        except ValueError:
                            self.settings[key] = value  # fallback to raw string

    def load_settings(self):
        with open(self.settings_file, 'r') as f:
            content = f.read()
            # Load file into the text editor
            self.settings_text.append(content)

            # Read Settings
            for line in content.splitlines():
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = map(str.strip, line.split('=', 1))
                    if key in self.settings:
                        try:
                            self.settings[key] = int(value)
                        except ValueError:
                            self.settings[key] = value  # fallback to raw string

            # Load settings
            print(f"Settings loaded: {self.settings}")
            self.console_output.append(f"\nPlayTimeTracker {self.version}\n")
            self.only_show_wine_checkbox.setChecked(bool(self.settings.get('ENABLE_ONLY_WINE', 0)))
            self.dynamic_title_checkbox.setChecked(bool(self.settings.get('ENABLE_DYNAMIC_TITLE', 0)))
            if self.settings.get('ENABLE_ONLY_WINE') == 0:
                self.refresh_window_list()

    def on_about_text_changed(self):
        self.settings_status_label.setText("")


    """Check if the process is running under Wine or Proton based on the PID."""
    def is_wine_or_proton(self, pid):
        try:
            # Check the environment variables for the process (works for both normal and gamescope)
            env_result = subprocess.check_output(f"cat /proc/{pid}/environ", shell=True, text=True)

            #log_message = f"Processing PID {pid}, env: {env_result}"
            #self.console_output.append(log_message)

            # Check if the process is running under Wine or Proton
            is_wine = "WINEPREFIX" in env_result
            is_proton = "STEAM_COMPAT_DATA_PATH" in env_result or "PROTON_HOME" in env_result

            result = is_wine or is_proton

            # Log the detection result
            #result_message = f"PID {pid} - Wine: {is_wine}, Proton: {is_proton}"
            #self.console_output.append(result_message)

            return result
        except Exception as e:
            # If there's an error, log it and return False
            cmdline_result = subprocess.check_output(f"cat /proc/{pid}/cmdline", shell=True, text=True)
            error_message = f"Error checking PID {pid}, cmdline: {cmdline_result.strip()} : {e}"
            self.console_output.append(error_message)  # Display in the console output
            return False

    def refresh_window_list_sync(self, only_show_wine=False):
        try:
            window_titles = []
            try:
                result = subprocess.check_output(["kdotool", "search", "--name", "."], text=True).strip()
                window_ids = result.split("\n") if result else []
                for window_id in window_ids:
                    title = subprocess.check_output(["kdotool", "getwindowname", window_id], text=True).strip()
                    # Get the process ID associated with the window
                    pid_result = subprocess.check_output(["kdotool", "getwindowpid", window_id], text=True).strip()
                    pid = int(pid_result) if pid_result else None
                    is_wine = False
                    if only_show_wine and pid:
                        # Check if the application is running under Wine or Proton
                        is_wine = self.is_wine_or_proton(pid)


                    # Only add to the list if checkbox is checked and it's a Wine process or if it's unchecked (add all)
                    if only_show_wine and is_wine:
                        window_titles.append((window_id, title, is_wine))
                    elif not only_show_wine:
                        window_titles.append((window_id, title, is_wine))

            except subprocess.CalledProcessError as e:
                return [], {}, f"Error using kdotool: {e}"

            return window_titles, {}, "Application list refreshed."
        except Exception as e:
            return [], {}, f"Error refreshing application list: {e}"

    def refresh_window_list(self):
        self.console_output.append("Refreshing application list...")
        self.refresh_button.setEnabled(False)
        self.previous_selection = self.window_combo.currentText()

        # Check if the checkbox is checked
        only_show_wine = self.only_show_wine_checkbox.isChecked()

        window_titles, app_icons, message = self.refresh_window_list_sync(only_show_wine)
        self._update_window_combo(window_titles, app_icons, message)
        self.refresh_button.setEnabled(True)

    def _update_window_combo(self, window_titles, app_icons, message):
        self.window_combo.clear()
        selected_index = 0
        for index, (window_id, title, _) in enumerate(window_titles):
            self.window_combo.addItem(title)
            if title == self.previous_selection:
                selected_index = index
        self.window_combo.setCurrentIndex(selected_index)
        self.console_output.append(message)

    def start_tracking(self):
        selected_app = self.window_combo.currentText()
        if not selected_app:
            self.console_output.append("No application selected!")
            return

        dynamic_titles = self.dynamic_title_checkbox.isChecked()
        script_dir = os.path.dirname(os.path.realpath(__file__))
        track_time_script = os.path.join(script_dir, "track_time.sh")

        args = [track_time_script, selected_app, script_dir, str(self.settings.get('LOG_REFRESH_TIMER', 0))]
        if dynamic_titles:
            args.append("true")  # Add the dynamic title flag

        self.console_output.append(f"Starting tracking for: {selected_app}")
        self.process.start("bash", args)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_tracking(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.console_output.append("Stopping tracking...")
            self.process.terminate()
            self.process.waitForFinished()
            self.console_output.append("Tracking stopped.")
        else:
            self.console_output.append("No tracking process is running.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle cleanup when the window is closed."""
        print("Closing event triggered")
        if self.process.state() == QProcess.ProcessState.Running:
            print("Stopping tracking before exit...")
            self.process.terminate()
            self.process.waitForFinished()
            print("Tracking stopped.")

        event.accept()  # Accept the close event to proceed with closing

    def update_console(self):
        output = self.process.readAllStandardOutput().data().decode()
        error = self.process.readAllStandardError().data().decode()
        if output:
            self.console_output.append(output.strip())
        if error:
            self.console_output.append(f"ERROR: {error.strip()}")

    def refresh_stats(self):
        # Recalculate everything to show updated hours
        self.load_log_files()  # Reload the log files
        self.update_graph()  # Update the graph with new data

    def load_log_files(self):
        if not self.log_dir.exists():
            self.console_output.append("Log directory not found.")
            return

        self.log_files = {file.stem.replace("game_playtime_", "").replace(".log", ""): file for file in self.log_dir.glob("game_playtime_*.log")}

        if not self.log_files:
            self.console_output.append("No log files found.")
            return

        self.app_combo.clear()
        self.app_combo.addItem("Global")  # Global option at the top
        sorted_files = sorted(self.log_files.items(), key=lambda x: os.path.getmtime(x[1]), reverse=True)

        for app_name, file_path in sorted_files:
            self.app_combo.addItem(app_name)

        if sorted_files:
            self.app_combo.setCurrentIndex(0)
            self.update_graph()

    def update_graph(self):
        app_name = self.app_combo.currentText()
        if not app_name:
            return

        if app_name == "Global":
            self.generate_global_graph()
        else:
            self.generate_app_graph(app_name)

    def refresh_notes(self):
        self.load_notes_files_combo()
        self.note_status_label.setText("")

    def load_notes_files_combo(self):
        # Get list of apps from log folder first
        # Then create or update in notes folder .txt for each app
        if not self.log_dir.exists():
            self.console_output.append("Log directory not found.")
            return
        self.log_files = {file.stem.replace("game_playtime_", "").replace(".log", ""): file for file in self.log_dir.glob("game_playtime_*.log")}
        if not self.log_files:
            self.console_output.append("No app with logs found.")
            return

        self.notes_combo.clear()

        # Sort by last tracked
        sorted_files = sorted(self.log_files.items(), key=lambda x: os.path.getmtime(x[1]), reverse=True)
        for app_name, file_path in sorted_files:
            self.notes_combo.addItem(app_name)

        if sorted_files:
            self.notes_combo.setCurrentIndex(0)
            self.update_notes()

    def update_notes(self):
        if not self.notes_dir.exists():
            self.notes_output.append("Notes directory not found.")
            return

        # Search if notes file for game exist already
        self.notes_files = {file.stem.replace("notes_", "").replace(".txt", ""): file for file in self.notes_dir.glob("notes_*.txt")}
        app_combo = self.notes_combo.currentText()
        note_found = False
        for app_note, file_path in self.notes_files.items():
            if app_combo.strip() == app_note.strip():
                note_found = True
                with file_path.open("r", encoding="utf-8") as f:
                    self.notes_output.setPlainText(f.read())
                break

        if not note_found:
            self.notes_output.clear()

    def save_note(self):
        app_name = self.notes_combo.currentText().strip()
        note_file = self.notes_dir / f"notes_{app_name}.txt"
        with note_file.open("w", encoding="utf-8") as f:
            # Save all text from notes_output
            f.write(self.notes_output.toPlainText())

        # Show message saved
        self.note_status_label.setText(f"Note saved for {app_name}.")

    def on_notes_text_changed(self):
        self.note_status_label.setText("")

    def generate_global_graph(self):
        total_playtimes = {}
        max_playtime = 100  # Default max value for Y-axis
        total_global_playtime = 0  # Variable to store sum of all playtimes

        for app_name, log_file in self.log_files.items():
            with open(log_file, 'r') as file:
                lines = file.readlines()
                if not lines:
                    continue
                last_line = lines[-1].strip().split("; ")
                if len(last_line) >= 5:
                    try:
                        total_playtime = self.parse_time(last_line[4]) / 3600  # Convert to hours
                        total_playtimes[app_name] = total_playtime
                        max_playtime = max(max_playtime, total_playtime)
                        total_global_playtime += total_playtime
                    except ValueError:
                        continue

        self.total_time_label.setText(f"Total Playtime: {total_global_playtime:.2f} hours")
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # 🔹 Define a list of fallback fonts (first available one will be used)
        fallback_fonts = ["Noto Serif CJK JP", "Noto Sans CJK JP", "IPAPMincho", "TakaoPGothic", "Yu Gothic", "Arial Unicode MS"]
        available_fonts = set(f.name for f in fm.fontManager.ttflist)
        selected_font = next((font for font in fallback_fonts if font in available_fonts), None)

        if selected_font:
            plt.rcParams["font.family"] = selected_font
            plt.rcParams["font.sans-serif"] = selected_font

        if total_playtimes:
            apps = list(total_playtimes.keys())
            playtimes = list(total_playtimes.values())

            ax.bar(apps, playtimes, color="skyblue")
            ax.set_xlabel("Game")
            ax.set_ylabel("Total Playtime (hours)")
            ax.set_ylim(0, max(100, max_playtime))  # Set Y-axis from 0 to 100 or max value

            # 🔹 Rotate X-axis labels for better readability
            ax.set_xticklabels(apps, rotation=30, ha="right", fontsize=10,
                               fontname=selected_font if selected_font else "sans-serif")

            # 🔹 Adjust bottom padding to avoid cutting game names
            plt.subplots_adjust(bottom=0.40)  # Increase padding at the bottom

            # 🔹 Resize dynamically based on number of entries (with more height)
            if len(apps) > 10:
                self.figure.set_size_inches(len(apps) * 0.5, 7)
            else:
                self.figure.set_size_inches(max(6, len(apps) * 0.5), 7)

        else:
            ax.text(0.5, 0.5, "No valid data to display", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12, color="red")

        self.canvas.draw()


    def generate_app_graph(self, app_name):
        log_file = self.log_files.get(app_name)
        if not log_file:
            return

        daily_playtime = {}
        total_playtime = 0

        with open(log_file, 'r') as file:
            for line in file:
                columns = line.strip().split("; ")
                if len(columns) == 5:
                    try:
                        date = datetime.datetime.strptime(columns[0], "%Y-%m-%d %H:%M:%S")
                        playtime = self.parse_time(columns[3]) / 3600  # Convert to hours
                        total_playtime = self.parse_time(columns[4]) / 3600
                        day = date.date()
                        if day not in daily_playtime:
                            daily_playtime[day] = 0
                        daily_playtime[day] += playtime
                    except ValueError:
                        continue

        self.total_time_label.setText(f"Total Playtime: {total_playtime:.2f} hours")
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if daily_playtime:
            days = list(daily_playtime.keys())
            hours = list(daily_playtime.values())
            ax.bar(days, hours, color="skyblue")
            ax.set_xlabel("Date")
            ax.set_ylabel("Playtime (hours)")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d, %Y"))
            self.figure.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "No valid data to display", transform=ax.transAxes,
                    ha="center", va="center", fontsize=12, color="red")

        self.canvas.draw()

    def parse_time(self, time_str):
        time_parts = list(map(int, time_str.split(":")))
        return sum(x * 60 ** i for i, x in enumerate(reversed(time_parts)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec())
