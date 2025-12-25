import subprocess
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

    @abstractmethod
    def find_window_by_pid(self, target_pid): pass

    @staticmethod
    def get_process_environ(pid):
        """Standard for all Linux DEs, get enviroment vars of process"""
        try:
            environ_path = Path(f"/proc/{pid}/environ")
            return environ_path.read_text() if environ_path.exists() else ""
        except Exception:
            return ""
    @staticmethod
    def get_pid_by_name(process_name):
        """
        Extracts the filename and searches the process list.
        Matches the logic needed for Wine/Proton backslashes.
        """
        import os
        filename = os.path.basename(process_name)
        my_pid = str(os.getpid()) # Get the PID of the tracker itself
        
        try:
            # -f: search full command line
            output = subprocess.check_output(["pgrep", "-f", filename], text=True)
            pids = output.strip().splitlines()
            
            # Filter out our own PID so we don't track ourselves
            valid_pids = [p for p in pids if p != my_pid]
            
            if not valid_pids:
                return None

            # Priority 1: Look for the process with the Windows-style backslash (The Game)
            for pid in reversed(valid_pids):
                try:
                    cmdline = Path(f"/proc/{pid}/cmdline").read_text()
                    if "\\" in cmdline:
                        return pid
                except: continue

            # Priority 2: Return the newest process that isn't us
            return valid_pids[-1]
        except Exception:
            return None
