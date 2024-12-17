# Playtime Tracker for Wayland KDE

<img src="https://i.imgur.com/4gQrikS.png" alt="Alt text" width="70%"/>

This tool tracks game window focus time and displays playtime statistics using a lightweight server and a playtime logger script.

This should work in any environment where kdotool does.

---

## 1. Prerequisites

Ensure the following tools are installed on your system:

- **Python 3** (to run the web server)
- **kdotool** (to track window focus): [kdotool GitHub repository](https://github.com/jinliu/kdotool)

---

## 2. Setting Up

### Step 1: Update the Script

Open `count_playtime.sh` and configure the following variables:

```bash
# Set the title of the game window to monitor (case-sensitive)
GAME_WINDOW="Your_Game_Window_Title"
```

#### How to Find Your Game Window Title:
Run this command to list all current window titles:
```bash
for window_id in $(kdotool search --name .); do kdotool getwindowname $window_id; done
```

Look for the title of the game window and update `GAME_WINDOW` in the script.

---

## 3. Running the Tracker

### Step 1: Start the Playtime Tracker Script

Run the `count_playtime.sh` script:
```bash
./count_playtime.sh
```

- The script will monitor the window focus and log playtime into the specified `.log` file.
- Press `Ctrl+C` to stop tracking. A session summary will be appended to the log file.

---

## 4. Viewing Playtime Statistics

### Step 1: Start the Local Web Server

Run the following Python 3 command to serve the HTML file:

```bash
cd /path/to/your/html/file
python3 -m http.server 8000
```

This will start a web server at `http://localhost:8000`.

### Step 2: Open the website

1. Open a web browser (Firefox, Chrome, etc.).
2. Navigate to:
   ```
   http://localhost:8000
   ```
3. The application will automatically load all `.log` files from the configured `log` directory and display:
   - A list of applications (based on log filenames).
   - A bar graph showing daily playtime statistics.
   - Total playtime and session efficiency details.

---

## 5. Notes

- **Game Window Title**: Make sure the game title in `GAME_WINDOW` matches the window's actual name.
- **Log Files**: Log files are stored as `game_playtime_<GameName>.log` in the `log` folder.
- **Server**: The Python server must remain running to view the stats.

---
disclaimer: 90% of this was done by chatgpt
