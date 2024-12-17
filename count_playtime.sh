#!/bin/bash
# Need to install kdotool https://github.com/jinliu/kdotool
# Modify GAME_WINDOW -> It should be the Title bar name, can get the name of all current windows with this command with kdotool: for window_id in $(kdotool search --name .); do kdotool getwindowname $window_id; done
# Modify LOG_FILE to the path and name you want


# Name of the window title to monitor
#GAME_WINDOW="ムーン・ゴースト"
GAME_WINDOW="Dies irae ～Acta est Fabula～ HD"

# Log file to track playtime
LOG_FILE="$HOME/Desktop/playtimetracker/log/game_playtime_$GAME_WINDOW.log"

# Check if log file exists, if not, create it with column headers
if [ ! -f "$LOG_FILE" ]; then
    echo "Time session Start; Time Session finish; Session Length; Session Playtime; Total Playtime" > "$LOG_FILE"
fi

is_game_focused() {
    local game_window_id
    game_window_id=$(kdotool search --name "$GAME_WINDOW")
    if [ -z "$game_window_id" ]; then
        return 1  # No game window found
    fi
    local active_window_id
    active_window_id=$(kdotool getactivewindow)
    # Trim any whitespace
    game_window_id=$(echo "$game_window_id" | xargs)
    active_window_id=$(echo "$active_window_id" | xargs)
    if [ "$game_window_id" == "$active_window_id" ]; then
        return 0  # Game window is focused
    else
        return 1  # Game window is not focused
    fi
}

# Function to convert seconds to HH:MM:SS format
#format_time() {
#    local total_seconds=$1
#    printf '%02d:%02d:%02d\n' $((total_seconds/3600)) $((total_seconds%3600/60)) $((total_seconds%60))
#}

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


# Initialize playtime counter
total_playtime=$(load_previous_playtime)
last_log_update=$(date +%s)

# Current session playtime counter
session_playtime=0

# Show initial playtime
echo "Starting playtime: $(format_time $total_playtime)"

# Get the start time for this session
session_start=$(date '+%Y-%m-%d %H:%M:%S')

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

# Trap termination signals (like Ctrl+C)
trap cleanup SIGINT SIGTERM SIGHUP SIGQUIT

# Start monitoring
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

