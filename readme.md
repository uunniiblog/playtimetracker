# Playtime Tracker for Wayland KDE

<img src="https://i.imgur.com/NfhVWQB.jpeg" alt="Alt text" width="70%"/>

<img src="https://i.imgur.com/tr1i6vX.jpeg" alt="Alt text" width="70%"/>

This tool tracks game window focus time for more accurate playing time stats. This ensures time is only counted when the window is actually active.

Works on KDE Plasma 6 Wayland.

---

## 1. Prerequisites

Ensure the following tools are installed on your system:

- **Python 3.10+**
- **PyQt6**
- **Systemd** (Used for KWin log parsing)
- **dbus-python** (Used or KWin calls)

---

## 2. Open the python application

```bash
git clone https://github.com/uunniiblog/playtimetracker.git
cd playtimetracker
python main.py 
```

Cli Options

```bash
usage: main.py [-h] [-v] [target]

PlayTimeTracker - A game time tracking utility for KDE Wayland 6.

positional arguments:
  target         The .exe or process name to track automatically (Requires more testing still). If omitted, the GUI launches normally.

options:
  -h, --help     show this help message and exit
  -v, --version  Show the application version and exit.
```
   
For a shortcut you can make a .desktop file with the icon you want:

```bash
#!/usr/bin/env xdg-open
[Desktop Entry]
Name=Time Tracker
Comment=Track playtime for your apps
Exec=/usr/bin/python3 /home/user/Documents/playtimetracker/main.py
Icon=utilities-system-monitor
Terminal=false
Type=Application
Categories=Utility;
```

and place it in: ~/.local/share/applications/ (KDE) to get a shortcut in the application launcher

## 3. Notes

- **Log Files**: Log files are stored as `game_playtime_<GameName>.log` in the `log` folder if wanted to be seen manually.
- **Notes files** Notes are stored as `notes_<GameName>.txt` in the `notes` folder. It requires a game to have been tracked before to make a note.

This application communicates with KWin via D-Bus. It loads a temporary JavaScript script into the compositor to query window states. If you encounter issues with window detection, ensure that KWin scripting is not disabled in your system settings.

