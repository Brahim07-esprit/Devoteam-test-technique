#!/bin/bash

pkill -9 -f 'realtime_analysis/realtime_analyzer.py' || true
pkill -9 -f 'python -m realtime_analysis.realtime_analyzer' || true
pkill -9 -f 'realtime_analyzer' || true

sleep 2

if pgrep -f 'realtime_analysis/realtime_analyzer.py' > /dev/null || pgrep -f 'python -m realtime_analysis.realtime_analyzer' > /dev/null; then
    echo "WARNING: Some realtime analyzer processes are still running!"
    ps aux | grep -E 'realtime_analysis/realtime_analyzer.py|python -m realtime_analysis.realtime_analyzer' | grep -v grep
else
    echo "All realtime analyzer processes have been terminated."
fi

echo "Creating empty metrics file..."
# Create an empty metrics file (just an empty array)
if [ -f "realtime_metrics.json" ]; then
    if [ ! -w "realtime_metrics.json" ]; then
        echo "File exists but is not writable. Using sudo to reset it..."
        sudo bash -c 'echo "[]" > realtime_metrics.json'
        sudo chown $USER:$USER realtime_metrics.json
    else
        echo "[]" > realtime_metrics.json
    fi
else
    echo "[]" > realtime_metrics.json
fi

file_size=$(stat -c%s "realtime_metrics.json")
file_owner=$(stat -c%U "realtime_metrics.json")
if [ "$file_size" -le 3 ]; then
    echo "Metrics file has been reset successfully."
else
    echo "WARNING: Metrics file might not be empty. Current size: $file_size bytes."
fi

if [ "$file_owner" != "$USER" ]; then
    echo "WARNING: File is owned by $file_owner, not $USER. Fixing permissions..."
    sudo chown $USER:$USER realtime_metrics.json
    echo "Permissions fixed."
fi

echo "Environment reset complete."