from core.desktop_utils_interface import DesktopUtilsInterface

class GnomeUtils(DesktopUtilsInterface):
    def _raise_not_implemented(self):
        raise NotImplementedError("Gnome support is not yet implemented in this application.")

    def get_all_window_ids(self): self._raise_not_implemented()
    def get_window_name(self, wid): self._raise_not_implemented()
    def get_window_pid(self, wid): self._raise_not_implemented()
    def get_active_window_id(self): self._raise_not_implemented()
    def find_window_id_by_title(self, target_title): self._raise_not_implemented()
    def find_window_by_pid(self, target_pid): self._raise_not_implemented()
