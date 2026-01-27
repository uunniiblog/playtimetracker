import sys
import ctypes
import ctypes.util
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.tracker_service import TrackerService
from core.data_manager import DataManager
from core.cli_handler import CliHandler
from core.cli_controller import CliController

def main():
    set_process_name("PlayTimeTracker")
    cli = CliHandler()
    args = cli.parse()
    
    app = QApplication(sys.argv)

    data_manager = DataManager()
    tracker_service = TrackerService()
    window = MainWindow(tracker_service, data_manager)

    controller = CliController(window, tracker_service, data_manager)
    controller.handle_args(args)

    if not args.background:
        window.show()
    sys.exit(app.exec())

def set_process_name(name):
    libc = ctypes.CDLL(ctypes.util.find_library('c'))
    byte_name = name.encode('utf-8')[:15]
    libc.prctl(15, byte_name, 0, 0, 0)

if __name__ == "__main__":
    main()