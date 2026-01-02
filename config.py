import os
from pathlib import Path

VERSION = 'v2026-01-02'
GIT_URL = 'https://github.com/uunniiblog/playtimetracker'

# Paths
BASE_DIR = Path(__file__).parent.resolve()
SCRIPT_DIR = BASE_DIR
SETTINGS_FILE = BASE_DIR / "settings.ini"
LOG_DIR = BASE_DIR / "log"
NOTES_DIR = BASE_DIR / "notes"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
NOTES_DIR.mkdir(parents=True, exist_ok=True)
