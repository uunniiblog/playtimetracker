#!/bin/bash
# Need to install kdotool https://github.com/jinliu/kdotool
# Modify GAME_WINDOW -> It should be the Title bar name, can get the name of all current windows with this command with kdotool: for window_id in $(kdotool search --name .); do kdotool getwindowname $window_id; done
# Modify LOG_FILE to the path and name you want

# -----------------------------
# Utility Functions
# -----------------------------

is_game_focused() {
    if [ -z "$target_game_window_id" ]; then
        return 1  # No game window found
    fi
    local active_window_id
    active_window_id=$(kdotool getactivewindow)
    # Trim any whitespace
    game_window_id=$(echo "$target_game_window_id" | xargs)
    active_window_id=$(echo "$active_window_id" | xargs)

    #echo "game_window_id: $game_window_id"
    #echo "active_window_id: $active_window_id"

    if [ "$game_window_id" == "$active_window_id" ]; then
        return 0  # Game window is focused
    else
        return 1  # Game window is not focused
    fi
}

format_time() {
    local total_seconds=$1
    printf '%d:%02d:%02d\n' $((total_seconds/3600)) $((total_seconds%3600/60)) $((total_seconds%60))
}

# Function to read previous playtime from log file
load_previous_playtime() {
    if [ -f "$LOG_FILE" ]; then
        # Extract the last recorded total playtime in HH:MM:SS format (last column)
        last_time=$(tail -n 1 "$LOG_FILE" | awk -F'; ' '{print $NF}')

        # Check if the last_time value matches the HH:MM:SS format
        if [[ $last_time =~ ^([0-9]{1,3}):([0-9]{2}):([0-9]{2})$ ]]; then
            IFS=':' read -r hours minutes seconds <<< "$last_time"
            # Convert total time to seconds
            total_seconds=$(( (10#$hours * 3600) + (10#$minutes * 60) + 10#$seconds ))
            echo $total_seconds
        else
            # Return 0 if the last line is not a valid time (e.g., header line)
            echo 0
        fi
    else
        echo 0
    fi
}

# Function to find the best match for a dynamic title
find_best_log_match() {
    local current_title="$1"
    local best_match=""
    local max_match_len=0

    for filepath in "$SCRIPT_DIR/log"/game_playtime_*.log; do
        [ -e "$filepath" ] || continue  # Skip if no logs exist

        filename=$(basename -- "$filepath")
        game_name="${filename#game_playtime_}"
        game_name="${game_name%.log}"

        common_prefix=$(longest_common_prefix "$current_title" "$game_name")
        prefix_len=${#common_prefix}

        if (( prefix_len > best_prefix_len )); then
            best_match="$game_name"
            best_prefix_len=$prefix_len
        fi
    done

    if [ -n "$best_match" ]; then
        echo "$best_match"
    else
        echo "$current_title"
    fi
}

longest_common_prefix() {
    local str1="$1"
    local str2="$2"
    local i=0

    while [[ "${str1:$i:1}" == "${str2:$i:1}" && $i -lt ${#str1} && $i -lt ${#str2} ]]; do
        ((i++))
    done

    echo "${str1:0:$i}"
}

# Function to handle script termination
cleanup() {
    session_end=$(date '+%Y-%m-%d %H:%M:%S')
    # Format the session playtime in HH:MM:SS for logging
    session_playtime_log=$(format_time $session_playtime)

    # Calculate session length
    session_start_seconds=$(date -d "$session_start" +%s)
    session_end_seconds=$(date -d "$session_end" +%s)
    session_length=$((session_end_seconds - session_start_seconds))
    session_length_formatted=$(format_time $session_length)

    # File structure:
    # Time session Start; Time Session finish; Session Length; Session Playtime; Total Playtime
    # Append the session details to the log file
    echo "$session_start; $session_end; $session_length_formatted; $session_playtime_log; $(format_time $total_playtime)" >> "$LOG_FILE"

    # Output the session details to the console
    echo "Session logged: $session_start; $session_end; $session_length_formatted; $session_playtime_log; $(format_time $total_playtime)"

    # Print the path and name of the modified log file
    echo "Log file modified: $LOG_FILE"

    exit 0
}


# -----------------------------
# Main Configuration and Logic
# -----------------------------

# Check if GAME_WINDOW argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <GAME_WINDOW> <SCRIPT_DIR> [dynamic_title]"
    exit 1
fi

# Get GAME_WINDOW from the first argument
GAME_WINDOW="$1"

# Get the script directory (second argument)
SCRIPT_DIR="$2"

# Check for games with dynamic title bar
DYNAMIC_TITLE="${3:-false}"

# Resolve canonical game name
if [ "$DYNAMIC_TITLE" == "true" ]; then
    CANONICAL_GAME_NAME=$(find_best_log_match "$GAME_WINDOW" "$SCRIPT_DIR/log")
else
    CANONICAL_GAME_NAME="$GAME_WINDOW"
fi

# Log file to track playtime
LOG_FILE="$SCRIPT_DIR/log/game_playtime_$CANONICAL_GAME_NAME.log"

# Find the window ID
target_game_window_id=$(kdotool search --name "$GAME_WINDOW")

# Check if log file exists, if not, create it with column headers
if [ ! -f "$LOG_FILE" ]; then
    echo "Time session Start; Time Session finish; Session Length; Session Playtime; Total Playtime" > "$LOG_FILE"
fi

# Initialize playtime counter
total_playtime=$(load_previous_playtime)
last_log_update=$(date +%s)

# Current session playtime counter
session_playtime=0

# Show initial playtime
echo "Starting playtime: $(format_time $total_playtime)"

# Get the start time for this session
session_start=$(date '+%Y-%m-%d %H:%M:%S')

# Trap termination signals (like Ctrl+C)
trap cleanup SIGINT SIGTERM SIGHUP SIGQUIT

# -----------------------------
# Tracking Loop
# -----------------------------

while true; do
    if is_game_focused; then
        # Increment only if the game is focused
        ((total_playtime++))
        ((session_playtime++))
    fi
    # Debug console log
    # Check if it's been at least 60 seconds since the last log update
    current_time=$(date +%s)
    if (( current_time - last_log_update >= 60 )); then
        echo "Session playtime: $(format_time $session_playtime)"
        echo "Total playtime: $(format_time $total_playtime)"
        last_log_update=$current_time
    fi
    # Check every second
    sleep 1
done
