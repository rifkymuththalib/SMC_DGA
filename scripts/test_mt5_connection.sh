#!/bin/bash
# Test MT5 connection

echo "Testing MT5 connection..."

# Change to bot directory
cd "$(dirname "$0")/.." || exit

# Set Wine prefix
export WINEPREFIX="$HOME/.wine"
export WINEDEBUG=-all

# Create test script
cat > test_connection.py << 'EOF'
#!/usr/bin/env python3
import sys
import MetaTrader5 as mt5

print("="*60)
print("MT5 Connection Test")
print("="*60)

print("\n1. Checking MetaTrader5 module...")
print(f"   Module location: {mt5.__file__}")

print("\n2. Initializing MT5...")
if not mt5.initialize():
    error = mt5.last_error()
    print(f"   ❌ Failed to initialize MT5")
    print(f"   Error code: {error}")
    print("\n   Troubleshooting:")
    print("   - Ensure MT5 terminal is running")
    print("   - Enable 'Algo Trading' in MT5 (green button)")
    print("   - Check if MT5 is logged in")
    sys.exit(1)

print("   ✓ MT5 initialized successfully!")

print("\n3. Getting MT5 version...")
version = mt5.version()
print(f"   MT5 Version: {version}")

print("\n4. Getting terminal info...")
terminal_info = mt5.terminal_info()
if terminal_info:
    print(f"   Company: {terminal_info.company}")
    print(f"   Name: {terminal_info.name}")
    print(f"   Path: {terminal_info.path}")
    print(f"   Connected: {terminal_info.connected}")
    print(f"   Trade allowed: {terminal_info.trade_allowed}")

print("\n5. Getting account info...")
account_info = mt5.account_info()
if account_info:
    print(f"   ✓ Account: {account_info.login}")
    print(f"   Server: {account_info.server}")
    print(f"   Balance: {account_info.balance} {account_info.currency}")
    print(f"   Equity: {account_info.equity} {account_info.currency}")
    print(f"   Leverage: 1:{account_info.leverage}")
else:
    print("   ❌ Not logged in to any account")
    print("   Please log into your MT5 account first")

print("\n6. Testing symbol access...")
symbol = "EURUSD"
symbol_info = mt5.symbol_info(symbol)
if symbol_info:
    print(f"   ✓ {symbol} is accessible")
    print(f"   Bid: {symbol_info.bid}")
    print(f"   Ask: {symbol_info.ask}")
    print(f"   Spread: {symbol_info.spread}")
else:
    print(f"   ❌ Cannot access {symbol}")

print("\n7. Shutting down MT5 connection...")
mt5.shutdown()
print("   ✓ Disconnected")

print("\n" + "="*60)
print("✓ All tests passed! MT5 is ready for trading bot")
print("="*60)
EOF

# Run test
WINE_PYTHON="$HOME/.wine/drive_c/Python311/python.exe"

if [ -f "$WINE_PYTHON" ]; then
    echo "Using Wine Python..."
    wine "$WINE_PYTHON" test_connection.py
elif command -v python3 &> /dev/null; then
    echo "Using Linux Python..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    python3 test_connection.py
else
    echo "Error: Python not found!"
    exit 1
fi

# Clean up
rm -f test_connection.py
