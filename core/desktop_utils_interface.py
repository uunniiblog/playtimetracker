from abc import ABC, abstractmethod
from pathlib import Path

class DesktopUtilsInterface(ABC):
    @abstractmethod
    def get_all_window_ids(self): pass

    @abstractmethod
    def get_window_name(self, wid): pass

    @abstractmethod
    def get_window_pid(self, wid): pass

    @abstractmethod
    def get_active_window_id(self): pass

    @abstractmethod
    def find_window_id_by_title(self, target_title, dynamic): pass

    @staticmethod
    def get_process_environ(pid):
        """Standard for all Linux DEs, get enviroment vars of process"""
        try:
            environ_path = Path(f"/proc/{pid}/environ")
            return environ_path.read_text() if environ_path.exists() else ""
        except Exception:
            return ""
