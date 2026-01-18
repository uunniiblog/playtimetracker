from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel
from PyQt6.QtGui import QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
from core.log_manager import LogManager
import config

class StatsTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.log_manager = LogManager(config.LOG_DIR)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        controls = QHBoxLayout()
        self.app_combo = QComboBox()
        self.app_combo.currentIndexChanged.connect(self.update_graph)
        controls.addWidget(self.app_combo)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.clicked.connect(self.refresh_data)
        controls.addWidget(refresh_btn)
        layout.addLayout(controls)

        self.info_label = QLabel("Total: 0h")
        self.info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white; margin-bottom: 0px;")
        layout.addWidget(self.info_label)

        self.figure = plt.figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=1)

        self.refresh_data()

    def refresh_data(self):
        """Updates the dropdown list with apps found in the new folder structure."""
        self.app_combo.blockSignals(True)
        self.app_combo.clear()
        
        #apps = self.log_manager.get_all_tracked_apps()
        apps = self.log_manager.get_apps_sorted_by_latest()
        self.app_combo.addItems(apps)
        self.app_combo.blockSignals(False)
        self.app_combo.setCurrentIndex(0)
        self.update_graph()

    def update_graph(self):
        """Fetches stats and renders the matplotlib graph."""
        app = self.app_combo.currentText()
        if not app:
            self.info_label.setText("Total: 0h 0m")
            return

        # Fetch data directly from the local log_manager instance
        total_seconds, daily_data = self.log_manager.get_stats_for_app(app)

        # Formatting
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        self.info_label.setText(f"Total Playtime: {hours}h {minutes}m")
        
        # ... (Rest of your matplotlib code remains the same) ...
        self.render_canvas(daily_data)

    def render_canvas(self, daily_data):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if daily_data:
            dates = list(daily_data.keys())
            plot_hours = list(daily_data.values())
            ax.bar(dates, plot_hours, color='skyblue')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            self.figure.autofmt_xdate()
        
        self.canvas.draw()