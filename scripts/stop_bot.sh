#!/bin/bash
# Stop the trading bot and MT5

echo "Stopping MT5 SMC Trading Bot..."

# Kill Python bot processes
if pgrep -f "main.py" > /dev/null; then
    pkill -f "main.py"
    echo "✓ Bot stopped"
else
    echo "Bot is not running"
fi

# Ask about stopping MT5
read -p "Stop MT5 terminal as well? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if pgrep -f "terminal64.exe" > /dev/null; then
        pkill -f "terminal64.exe"
        wineserver -k
        echo "✓ MT5 stopped"
    else
        echo "MT5 is not running"
    fi
fi

echo "Done!"
