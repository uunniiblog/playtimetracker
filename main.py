import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.tracker_service import TrackerService
from core.data_manager import DataManager
from core.cli_handler import CliHandler
from core.cli_controller import CliController

def main():
    cli = CliHandler()
    args = cli.parse()
    
    app = QApplication(sys.argv)

    data_manager = DataManager()
    tracker_service = TrackerService()
    window = MainWindow(tracker_service, data_manager)

    controller = CliController(window, tracker_service)
    controller.handle_args(args)

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()