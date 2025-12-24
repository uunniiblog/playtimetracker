import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.tracker_service import TrackerService
from core.data_manager import DataManager

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Initialize Core Logic
    data_manager = DataManager()
    tracker_service = TrackerService()

    # Initialize UI and inject logic
    window = MainWindow(tracker_service, data_manager)
    window.show()

    sys.exit(app.exec())
