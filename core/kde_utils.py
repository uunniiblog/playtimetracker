import dbus
import time
import subprocess
import uuid
import tempfile
import os
from core.desktop_utils_interface import DesktopUtilsInterface

class KdeUtils(DesktopUtilsInterface):
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.kwin_scripting = self.bus.get_object("org.kde.KWin", "/Scripting")
        self.kwin_iface = dbus.Interface(self.kwin_scripting, "org.kde.kwin.Scripting")

        # Local cache to prevent redundant KWin calls
        self._window_cache = {} # Format: {id: {"name": str, "pid": str}}
        self._last_cache_update = 0
        self._cache_ttl = 1.0 # Cache valid for 1 second

    def _refresh_cache(self):
        """Fetches all window data from KWin in one single pass."""
        now = time.time()
        if now - self._last_cache_update < self._cache_ttl:
            return

        # JS that returns ID, PID, and Name for all windows at once
        js_code = """
        workspace.windowList().forEach(w => {
            print('DATA:' + w.internalId + '|' + w.pid + '|' + w.caption);
        });
        """

        raw_out = self._run_kwin_script(js_code)
        new_cache = {}

        for line in raw_out.splitlines():
            if "DATA:" in line:
                try:
                    parts = line.split("DATA:")[-1].split('|')
                    if len(parts) >= 3:
                        wid, pid, name = parts[0], parts[1], parts[2]
                        new_cache[wid] = {"pid": pid, "name": name}
                except: continue

        self._window_cache = new_cache
        self._last_cache_update = now

    def _run_kwin_script(self, js_code):
        """ Helper to execute JS and get journal output."""
        script_name = f"tracker-{uuid.uuid4().hex[:8]}"
        start_time = "-2s"
        temp_path = None
        script_id = -1
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
                tf.write(js_code)
                temp_path = tf.name

            script_id = self.kwin_iface.loadScript(temp_path, script_name, signature='ss')
            start_time = time.strftime('%Y-%m-%d %H:%M:%S')

            run_obj = self.bus.get_object("org.kde.KWin", f"/Scripting/Script{script_id}")
            dbus.Interface(run_obj, "org.kde.kwin.Script").run()

            # Short delay
            time.sleep(0.05)

            return subprocess.check_output([
                "journalctl", "--since", start_time, "--user",
                "-u", "plasma-kwin_wayland.service",
                "--output=cat", "-q" # -q for quiet/faster
            ], text=True)
        finally:
            if temp_path: os.remove(temp_path)
            if script_id != -1:
                try: self.kwin_iface.unloadScript(script_name)
                except: pass

    def get_active_window_id(self):
        """ Gets current KWin ID of focused window."""
        js = "print('ACT:' + workspace.activeWindow.internalId);"
        out = self._run_kwin_script(js)
        for line in reversed(out.splitlines()):
            if "ACT:" in line: return line.split("ACT:")[-1].strip()
        return None

    def get_all_window_ids(self):
        """ Gets all windows ids"""
        self._refresh_cache()
        return list(self._window_cache.keys())

    def get_window_name(self, wid):
        """ Gets name of a Window ID"""
        self._refresh_cache()
        return self._window_cache.get(wid, {}).get("name", "Unknown")

    def get_window_pid(self, wid):
        """ Gets pid of a Window ID"""
        self._refresh_cache()
        return self._window_cache.get(wid, {}).get("pid", "0")

    def find_window_id_by_title(self, target_title, dynamic=False):
        """ Gets window ID of a window name."""
        # Escaping the title for JS
        safe_title = target_title.replace('"', '\\"')
        
        # KWin Script: Filters the window list and returns the internal ID
        script = f"""
        (function() {{
            var target = "{safe_title}".toLowerCase();
            var dynamic = {str(dynamic).lower()};
            var windows = workspace.windowList();
            var foundId = null;

            for (var i = 0; i < windows.length; i++) {{
                var w = windows[i];
                
                if (!w.normalWindow) continue;
                
                var title = w.caption.toLowerCase();
                if (!title) continue;

                if (dynamic) {{
                    if (title.indexOf(target) !== -1 || 
                        target.indexOf(title) !== -1 || 
                        (title.length >= 15 && target.substring(0, 15) === title.substring(0, 15))) {{
                        foundId = w.internalId;
                        break;
                    }}
                }} else {{
                    if (w.caption === "{safe_title}") {{
                        foundId = w.internalId;
                        break;
                    }}
                }}
            }}
            print("SEARCH_RESULT:" + foundId);
        }})();
        """

        #print(f'find_window_id_by_title script: {script}')
        
        result = self._run_kwin_script(script)
        #print(f'find_window_id_by_title result {result}')
        for line in result.splitlines():
            if "SEARCH_RESULT:" in line:
                val = line.split("SEARCH_RESULT:")[1].strip()
                return val if val != "null" else None
        return None
