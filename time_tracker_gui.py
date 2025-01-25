import sys
import subprocess
import psutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QComboBox, QPushButton, QTextEdit, QWidget, QTabWidget, QLabel
)
from PyQt6.QtCore import QProcess, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from pathlib import Path
import os
import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import rcParams

class WindowListRefresher(QThread):
    update_window_list = pyqtSignal(list, dict, str)

    def run(self):
        try:
            window_titles = []
            try:
                result = subprocess.check_output(["kdotool", "search", "--name", "."], text=True).strip()
                window_ids = result.split("\n") if result else []
                for window_id in window_ids:
                    title = subprocess.check_output(["kdotool", "getwindowname", window_id], text=True).strip()
                    window_titles.append((window_id, title))
            except subprocess.CalledProcessError as e:
                self.update_window_list.emit([], {}, f"Error using kdotool: {e}")
                return

            app_icons = {}
            for proc in psutil.process_iter(attrs=["pid", "name"]):
                try:
                    process_name = proc.info["name"]
                    desktop_file = self.find_desktop_file(process_name)
                    if desktop_file and process_name not in app_icons:
                        app_icons[process_name] = self.get_icon_from_desktop_file(desktop_file) or QIcon.fromTheme("application-default-icon")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            self.update_window_list.emit(window_titles, app_icons, "Application list refreshed.")
        except Exception as e:
            self.update_window_list.emit([], {}, f"Error refreshing application list: {e}")

    def find_desktop_file(self, process_name):
        desktop_dirs = [
            "/usr/share/applications",
            str(Path.home() / ".local/share/applications"),
        ]
        for directory in desktop_dirs:
            if not os.path.isdir(directory):
                continue
            for file in os.listdir(directory):
                if file.endswith(".desktop"):
                    with open(os.path.join(directory, file), 'r') as f:
                        content = f.read()
                        if f"Exec={process_name}" in content or f"Name={process_name}" in content:
                            return os.path.join(directory, file)
        return None

    def get_icon_from_desktop_file(self, desktop_file):
        try:
            with open(desktop_file, 'r') as f:
                for line in f:
                    if line.startswith("Icon="):
                        icon_name = line.split("=")[1].strip()
                        return QIcon.fromTheme(icon_name)
        except Exception:
            pass
        return None

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Time Tracker")
        self.setGeometry(100, 100, 800, 600)

        icon_path = Path(__file__).parent / 'icon.png'
        app_icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon.fromTheme("application-default-icon")
        self.setWindowIcon(app_icon)

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

        self.setup_main_tab()
        self.setup_stats_tab()

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

        self.window_list_refresher = WindowListRefresher()
        self.window_list_refresher.update_window_list.connect(self.update_window_combo)

        self.refresh_window_list()

    def setup_stats_tab(self):
        self.app_combo = QComboBox()
        self.stats_tab_layout.addWidget(self.app_combo)

        self.total_time_label = QLabel("Total Playtime: 0 hours")
        self.stats_tab_layout.addWidget(self.total_time_label)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.stats_tab_layout.addWidget(self.canvas)

        self.app_combo.currentIndexChanged.connect(self.update_graph)

        self.load_log_files()

    def load_log_files(self):
        log_dir = Path(__file__).parent / "log"
        if not log_dir.exists():
            self.console_output.append("Log directory not found.")
            return

        self.log_files = {file.stem.replace("game_playtime_", "").replace(".log", ""): file for file in log_dir.glob("game_playtime_*.log")}
        if not self.log_files:
            self.console_output.append("No log files found.")
            return

        self.app_combo.clear()
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
            #ax.set_title(f"Daily Playtime for {app_name}") # TODO: fix japanese rendering
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

    def refresh_window_list(self):
        self.console_output.append("Refreshing application list...")
        self.refresh_button.setEnabled(False)
        self.previous_selection = self.window_combo.currentText()
        self.window_list_refresher.start()

    def update_window_combo(self, window_titles, app_icons, message):
        self.window_combo.clear()
        selected_index = 0
        for index, (window_id, title) in enumerate(window_titles):
            icon = QIcon.fromTheme("application-default-icon")
            for process_name, app_icon in app_icons.items():
                if process_name.lower() in title.lower():
                    icon = app_icon
                    break
            self.window_combo.addItem(icon, title)
            if title == self.previous_selection:
                selected_index = index
        self.window_combo.setCurrentIndex(selected_index)
        self.console_output.append(message)
        self.refresh_button.setEnabled(True)

    def start_tracking(self):
        selected_app = self.window_combo.currentText()
        if not selected_app:
            self.console_output.append("No application selected!")
            return

        self.console_output.append(f"Starting tracking for: {selected_app}")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        track_time_script = os.path.join(script_dir, "track_time.sh")
        self.process.start("bash", [track_time_script, selected_app, script_dir])
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

    def update_console(self):
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
