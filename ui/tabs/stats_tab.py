from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel
from PyQt6.QtGui import QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates

class StatsTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data = data_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
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
        layout.addWidget(self.info_label)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        self.refresh_data()

    def refresh_data(self):
        self.app_combo.blockSignals(True)
        self.app_combo.clear()
        logs = self.data.get_log_files()
        self.app_combo.addItems(logs.keys())
        self.app_combo.blockSignals(False)
        self.update_graph()

    def update_graph(self):
        app = self.app_combo.currentText()
        total, daily_data = self.data.get_stats_for_app(app)

        self.info_label.setText(f"Total: {total:.2f} hours")
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if daily_data:
            dates = list(daily_data.keys())
            hours = list(daily_data.values())
            ax.bar(dates, hours, color='skyblue')
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            self.figure.autofmt_xdate()

        self.canvas.draw()
