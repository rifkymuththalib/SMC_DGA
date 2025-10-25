#!/bin/bash
# Start MetaTrader 5 in Wine

echo "Starting MetaTrader 5..."

# Set Wine prefix (modify if using custom location)
export WINEPREFIX="$HOME/.wine"
export WINEDEBUG=-all  # Disable Wine debug messages for better performance

# MT5 installation path (modify if installed elsewhere)
MT5_PATH="$HOME/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"

# Check if MT5 exists
if [ ! -f "$MT5_PATH" ]; then
    echo "Error: MT5 not found at $MT5_PATH"
    echo "Please update MT5_PATH in this script or install MT5"
    exit 1
fi

# Check if MT5 is already running
if pgrep -f "terminal64.exe" > /dev/null; then
    echo "MT5 is already running!"
    exit 0
fi

# Start MT5
echo "Launching MT5 from: $MT5_PATH"
wine "$MT5_PATH" &

# Wait a bit for MT5 to start
sleep 5

if pgrep -f "terminal64.exe" > /dev/null; then
    echo "MT5 started successfully!"
    echo ""
    echo "IMPORTANT:"
    echo "1. Log into your MT5 account"
    echo "2. Enable 'Algo Trading' button (top toolbar - should be green)"
    echo "3. Keep this window open"
    echo ""
    echo "Then run the bot with: ./scripts/run_bot.sh"
else
    echo "Failed to start MT5"
    exit 1
fi
