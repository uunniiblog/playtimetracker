import os
from core.kde_utils import KdeUtils
from core.gnome_utils import GnomeUtils

def get_desktop_utils():
    """
    Detects the current Desktop Environment.
    Returns an INSTANCE of the correct utility class.
    """
    # Get DE name and normalize to uppercase
    de = os.environ.get("XDG_CURRENT_DESKTOP", "").upper()

    print(f"Current Desktop Environment: {de}")

    if "KDE" in de:
        print("Using KdeUtils")
        return KdeUtils()
    elif "GNOME" in de:
        print("Using GnomeUtils")
        return GnomeUtils()
    else:
        # Give error if no supported DE
        raise RuntimeError(
            f"Unsupported Desktop Environment: '{de}'. "
            "This application currently only supports KDE via KWin Scripting API."
        )
