from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QLabel, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
from core.log_manager import LogManager
import config
from datetime import datetime

matplotlib.rcParams['font.sans-serif'] = [
    'Noto Sans CJK JP', 'WenQuanYi Micro Hei', 'IPAexGothic', 
    'Droid Sans Fallback', 'DejaVu Sans'
]
matplotlib.rcParams['axes.unicode_minus'] = False

class StatsTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.log_manager = LogManager(config.LOG_DIR)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove outer padding
        
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Create Sub-Tabs
        self.setup_individual_tab()
        self.setup_global_tab()
        self.refresh_data()

    def setup_individual_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10) # Tighten space between elements
        layout.setContentsMargins(10, 10, 10, 10)

        # Controls Row
        controls = QHBoxLayout()
        self.app_combo = QComboBox()
        self.app_combo.setMinimumHeight(30)
        self.app_combo.currentIndexChanged.connect(self.update_graph)
        controls.addWidget(self.app_combo, stretch=1)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh"))
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.clicked.connect(self.refresh_data)
        controls.addWidget(refresh_btn)
        layout.addLayout(controls)

        self.info_label = QLabel("Total Playtime: 0h 0m")
        self.info_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #3498db;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.info_label)

        # Graph Area
        self.figure, self.ax = plt.subplots(figsize=(5, 3), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=1)
        
        self.tabs.addTab(tab, "Individual App")

    def setup_global_tab(self):
        """Sub-tab showing a horizontal bar chart of most used apps."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)

        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Timeframe:"))
        self.range_combo = QComboBox()
        self.range_combo.addItems(["Today", "Last 7 Days", "Last 30 Days", "All Time"])
        self.range_combo.currentIndexChanged.connect(self.update_global_stats)
        controls.addWidget(self.range_combo, stretch=1)
        layout.addLayout(controls)

        refresh_btn = QPushButton()
        refresh_btn.setIcon(QIcon.fromTheme("view-refresh")) # Uses system icon
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setToolTip("Refresh Global Stats")
        refresh_btn.clicked.connect(self.update_global_stats) 
        controls.addWidget(refresh_btn)

        # Summary Label (Total time for all apps in period)
        self.summary_info = QLabel("Total time in period: 0h 0m")
        self.summary_info.setStyleSheet("font-size: 13px; font-weight: bold; color: #f1c40f;")
        layout.addWidget(self.summary_info)

        # Horizontal Bar Chart 
        self.global_figure, self.global_ax = plt.subplots(figsize=(6, 4), facecolor='#1e1e1e')
        self.global_canvas = FigureCanvas(self.global_figure)
        layout.addWidget(self.global_canvas, stretch=1)

        self.tabs.addTab(tab, "Global Summary")

    def refresh_data(self):
        """Populates the combo box and updates both views."""
        self.app_combo.blockSignals(True)
        self.app_combo.clear()
        apps = self.log_manager.get_apps_sorted_by_latest()
        if apps:
            self.app_combo.addItems(apps)
            self.app_combo.setCurrentIndex(0)
        self.app_combo.blockSignals(False)
        
        # Trigger updates
        self.update_graph()
        self.update_global_stats()

    def update_graph(self):
        app = self.app_combo.currentText()
        if not app:
            self.info_label.setText("Total Playtime: 0h 0m")
            self.render_canvas({}) # Clear graph
            return

        total_seconds, daily_data = self.log_manager.get_stats_for_app(app)
        print(f'total_seconds {total_seconds}')
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        self.info_label.setText(f"Total Playtime: {hours}h {minutes}m")
        
        self.render_canvas(daily_data)

    def render_canvas(self, daily_data):
        """--- FIX 3: Robust Graph Rendering ---"""
        self.ax.clear()
        
        # Set dark theme styles
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(axis='x', colors='white', labelsize=8)
        self.ax.tick_params(axis='y', colors='white', labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color('#444444')

        if daily_data:
            # Ensure dates are sorted chronologically
            sorted_dates = sorted(daily_data.keys())
            
            # Convert string dates to datetime objects if they aren't already
            plot_dates = []
            for d in sorted_dates:
                if isinstance(d, str):
                    plot_dates.append(datetime.strptime(d, '%Y-%m-%d'))
                else:
                    plot_dates.append(d)

            plot_hours = [daily_data[d] for d in sorted_dates]

            # Plot bars
            self.ax.bar(plot_dates, plot_hours, color='#3498db', width=0.6)
            
            # Formatting the X-axis for dates
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate()
        else:
            # If no data, show a message on the canvas
            self.ax.text(0.5, 0.5, "No data available", color='gray', 
                         ha='center', va='center', transform=self.ax.transAxes)

        self.canvas.draw()

    def update_global_stats(self):
        timeframe = self.range_combo.currentText()
        data = self.log_manager.get_global_summary(timeframe)

        total_seconds = sum(item[1] for item in data)
        h, m = int(total_seconds // 3600), int((total_seconds % 3600) // 60)
        self.summary_info.setText(f"Total time in period: {h}h {m}m")

        top_data = data[:15]
        top_data.reverse()

        # Format the label: "process (truncated title)"
        display_labels = []
        for app, seconds, title in top_data:
            # Clean title: remove the process name if it's already in the title
            clean_title = title.split(' — ')[0] if ' — ' in title else title
            if len(clean_title) > 30:
                clean_title = clean_title[:27] + "..."
            
            label = f"{app.upper()}\n({clean_title})"
            display_labels.append(label)

        hours = [item[1] / 3600 for item in top_data]
        self.render_global_canvas(display_labels, hours)

    def render_global_canvas(self, labels, hours):
        self.global_ax.clear()
        self.global_ax.set_facecolor('#1e1e1e')
        
        if labels:
            bars = self.global_ax.barh(labels, hours, color='#e67e22', height=0.7)
            
            # Value labels
            for bar in bars:
                width = bar.get_width()
                self.global_ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                                    f' {width:.1f}h', 
                                    va='center', color='#f1c40f', fontsize=10, fontweight='bold')

            # Give extra space for the labels on the left and the hours on the right
            max_h = max(hours) if hours else 1
            self.global_ax.set_xlim(0, max_h * 1.25)
            
            self.global_ax.tick_params(axis='y', colors='white', labelsize=8)
            self.global_ax.tick_params(axis='x', colors='#888', labelsize=8)
            
            # Subplots adjust to give left side plenty of room for "Process (Title)"
            self.global_figure.subplots_adjust(left=0.4, right=0.95, top=0.95, bottom=0.1)
        
        self.global_canvas.draw()