#!/bin/bash
# Run the MT5 SMC Trading Bot

echo "Starting MT5 SMC Trading Bot..."

# Change to bot directory
cd "$(dirname "$0")/.." || exit

# Check if MT5 is running
if ! pgrep -f "terminal64.exe" > /dev/null; then
    echo "Warning: MT5 terminal is not running!"
    echo "Starting MT5 first..."
    ./scripts/start_mt5.sh
    sleep 10
fi

# Set Wine prefix
export WINEPREFIX="$HOME/.wine"
export WINEDEBUG=-all

# Wine Python path (modify if installed elsewhere)
WINE_PYTHON="$HOME/.wine/drive_c/Python311/python.exe"

# Check which Python to use
if [ -f "$WINE_PYTHON" ]; then
    echo "Using Wine Python: $WINE_PYTHON"
    wine "$WINE_PYTHON" main.py
elif command -v python3 &> /dev/null; then
    echo "Using Linux Python: $(which python3)"
    # Activate venv if exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python3 main.py
else
    echo "Error: Python not found!"
    echo "Please install Python in Wine or on Linux"
    exit 1
fi
