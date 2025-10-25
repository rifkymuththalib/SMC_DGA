# Quick Start Guide - Linux with Wine

This is a quick reference for running the MT5 SMC Trading Bot on Linux.

## Prerequisites

- Linux (Ubuntu, Debian, Fedora, or Arch)
- Wine installed
- Internet connection

## Installation (One-Time Setup)

### 1. Run the automated installer:

```bash
chmod +x scripts/install_linux.sh
./scripts/install_linux.sh
```

This will:
- Install Wine (if needed)
- Install Python3 and dependencies
- Set up virtual environment
- Install MT5 in Wine (optional)
- Install Wine Python (recommended)
- Configure everything automatically

### 2. Configure your MT5 credentials:

```bash
nano .env
```

Update these values:
```env
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

SYMBOL=EURUSD
TIMEFRAME=H1
RISK_PERCENT=1.0
```

Save with `Ctrl+O`, exit with `Ctrl+X`

## Daily Usage

### Step 1: Start MT5

```bash
./scripts/start_mt5.sh
```

**Important:**
1. Log into your MT5 account
2. Click the "Algo Trading" button (top toolbar) - it should turn GREEN
3. Keep the MT5 window open

### Step 2: Test Connection (Optional but Recommended)

```bash
./scripts/test_mt5_connection.sh
```

If you see "✓ All tests passed!" you're ready to trade!

### Step 3: Run the Bot

```bash
./scripts/run_bot.sh
```

The bot will:
- Connect to MT5
- Monitor the market
- Analyze price action using SMC
- Execute trades when conditions are met
- Print detailed analysis to console

### Step 4: Stop the Bot (when done)

Press `Ctrl+C` in the bot terminal, or run:

```bash
./scripts/stop_bot.sh
```

## Troubleshooting

### Problem: "Failed to initialize MT5"

**Solutions:**
```bash
# 1. Make sure MT5 is running
./scripts/start_mt5.sh

# 2. Check if "Algo Trading" is enabled (green button in MT5)

# 3. Restart Wine
wineserver -k
./scripts/start_mt5.sh

# 4. Test connection
./scripts/test_mt5_connection.sh
```

### Problem: "MT5 not found"

**Solution:**
```bash
# Find MT5 installation
find ~/.wine -name "terminal64.exe"

# Update path in scripts/start_mt5.sh
nano scripts/start_mt5.sh
# Edit MT5_PATH variable
```

### Problem: Scripts won't run

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Problem: Wine crashes or freezes

**Solution:**
```bash
# Kill all Wine processes
wineserver -k
killall wine wineserver

# Restart
./scripts/start_mt5.sh
```

### Problem: "Module MetaTrader5 not found"

**Solution:**
```bash
# If using Wine Python
wine "$HOME/.wine/drive_c/Python311/python.exe" -m pip install MetaTrader5

# If using Linux Python
source venv/bin/activate
pip install MetaTrader5
```

## Running in Background

### Using screen (Recommended):

```bash
# Start MT5 in screen session
screen -S mt5
./scripts/start_mt5.sh
# Press Ctrl+A, then D to detach

# Start bot in another screen session
screen -S bot
./scripts/run_bot.sh
# Press Ctrl+A, then D to detach

# Reattach to bot screen later to check status
screen -r bot

# List all screens
screen -ls
```

### Using tmux:

```bash
# Start MT5
tmux new -s mt5
./scripts/start_mt5.sh
# Press Ctrl+B, then D to detach

# Start bot
tmux new -s bot
./scripts/run_bot.sh
# Press Ctrl+B, then D to detach

# Reattach
tmux attach -t bot

# List sessions
tmux ls
```

## Monitoring the Bot

### Check if running:

```bash
# Check bot process
pgrep -f "main.py"

# Check MT5 process
pgrep -f "terminal64.exe"
```

### View logs in real-time:

The bot prints all output to the console. To see it:

```bash
# If using screen
screen -r bot

# If using tmux
tmux attach -t bot
```

## Important Notes

✅ **Always test on demo account first!**

✅ **Monitor the bot regularly** - don't leave it completely unattended

✅ **MT5 must be running** before starting the bot

✅ **"Algo Trading" must be enabled** (green button in MT5)

✅ **Internet connection required** for both MT5 and bot

✅ **Check your risk settings** in `.env` file

## File Locations

- **Bot files**: `~/SMC_DGA/`
- **Wine prefix**: `~/.wine/`
- **MT5 in Wine**: `~/.wine/drive_c/Program Files/MetaTrader 5/`
- **MT5 logs**: `~/.wine/drive_c/Program Files/MetaTrader 5/Logs/`
- **Config file**: `~/SMC_DGA/.env`

## Useful Commands

```bash
# View bot configuration
cat .env

# Edit configuration
nano .env

# Check Wine Python
wine "$HOME/.wine/drive_c/Python311/python.exe" --version

# Check Linux Python
python3 --version

# View running processes
htop

# Check disk space
df -h

# Check MT5 logs
tail -f "$HOME/.wine/drive_c/Program Files/MetaTrader 5/Logs/"*.log
```

## Getting Help

1. **Read detailed guide**: `LINUX_SETUP.md`
2. **Test connection**: `./scripts/test_mt5_connection.sh`
3. **Check MT5 logs**: Look in Wine MT5 directory
4. **Verify credentials**: Double-check `.env` file

## Strategy Summary

The bot uses Smart Money Concepts (SMC):

1. 📍 **Finds liquidity pools** at swing highs/lows
2. 💥 **Waits for liquidity sweep** (false breakout)
3. 🎯 **Enters at Order Block or FVG** after sweep
4. ✅ **Confirms with Break of Structure** (BOS)

Default risk: **1% per trade** | Risk/Reward: **2:1**

---

**Happy Trading! 🚀**

*Remember: Past performance does not guarantee future results. Trade responsibly!*
