# Running MT5 SMC Trading Bot on Linux with Wine

This guide explains how to run the MT5 trading bot on Linux when MetaTrader 5 is installed via Wine.

## Prerequisites

- Linux system (Ubuntu/Debian/Fedora/Arch)
- Wine installed
- Python 3.8 or higher
- MetaTrader 5 installed in Wine

---

## Step 1: Install Wine (if not already installed)

### Ubuntu/Debian:
```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine64 wine32 winetricks
```

### Fedora:
```bash
sudo dnf install wine winetricks
```

### Arch Linux:
```bash
sudo pacman -S wine winetricks
```

Verify Wine installation:
```bash
wine --version
```

---

## Step 2: Install MetaTrader 5 in Wine

### Method 1: Using installer
```bash
# Download MT5 installer
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

# Run installer with Wine
wine mt5setup.exe
```

### Method 2: Using Winetricks
```bash
winetricks mt5
```

The default MT5 installation path in Wine is:
```
~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe
```

---

## Step 3: Configure Wine for MT5

1. **Run Wine configuration:**
```bash
winecfg
```

2. **Set Windows version to Windows 10** (in Applications tab)

3. **Install required Windows components:**
```bash
winetricks dotnet48
winetricks vcrun2019
winetricks corefonts
```

---

## Step 4: Install Python and Bot Dependencies

### Install Python packages:
```bash
# Install Python virtual environment
sudo apt install python3 python3-venv python3-pip  # Ubuntu/Debian
# OR
sudo dnf install python3 python3-pip  # Fedora
# OR
sudo pacman -S python python-pip  # Arch

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install bot dependencies
pip install -r requirements.txt
```

---

## Step 5: Configure MetaTrader5 Python Library for Wine

The MetaTrader5 Python library needs special configuration to work with Wine on Linux.

### Option A: Using Wine Python (Recommended)

This method runs Python inside Wine to access MT5 directly.

1. **Install Python in Wine:**
```bash
# Download Python installer for Windows
wget https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

# Install Python in Wine
wine python-3.11.9-amd64.exe
```

2. **Install Python packages in Wine Python:**
```bash
# Find Wine Python path
WINE_PYTHON="$HOME/.wine/drive_c/Python311/python.exe"

# Install packages
wine $WINE_PYTHON -m pip install MetaTrader5 pandas numpy scipy python-dotenv pytz
```

3. **Run the bot with Wine Python:**
```bash
wine $HOME/.wine/drive_c/Python311/python.exe main.py
```

### Option B: Using Linux Python with Wine Bridge (Advanced)

This is more complex and may have compatibility issues.

1. **Set Wine prefix environment variable:**
```bash
export WINEPREFIX="$HOME/.wine"
```

2. **Find MT5 terminal path:**
```bash
export MT5_PATH="$HOME/.wine/drive_c/Program Files/MetaTrader 5"
```

3. **Run the bot:**
```bash
python3 main.py
```

---

## Step 6: Configure the Bot

1. **Copy environment template:**
```bash
cp .env.example .env
```

2. **Edit .env file:**
```bash
nano .env
```

Add your MT5 credentials:
```env
# MT5 Account Configuration
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Trading Parameters
SYMBOL=EURUSD
TIMEFRAME=H1
LOT_SIZE=0.01
RISK_PERCENT=1.0
MAX_TRADES=3
```

---

## Step 7: Start MT5 Terminal

**Important:** MT5 terminal must be running before starting the bot!

### Start MT5 manually:
```bash
wine "$HOME/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
```

Or use the helper script (after creating it):
```bash
./scripts/start_mt5.sh
```

### Keep MT5 running:
- Log into your account
- Enable "Algo Trading" button (top toolbar)
- Leave the terminal window open

---

## Step 8: Run the Trading Bot

### Using Wine Python (Option A):
```bash
wine "$HOME/.wine/drive_c/Python311/python.exe" main.py
```

### Using Linux Python (Option B):
```bash
source venv/bin/activate
python3 main.py
```

---

## Troubleshooting

### Issue 1: "Failed to initialize MT5"

**Solution:**
- Ensure MT5 terminal is running in Wine
- Check if "Algo Trading" is enabled in MT5 (green button in toolbar)
- Verify MT5 terminal path

### Issue 2: "MetaTrader5 module not found"

**Solution:**
```bash
# For Wine Python
wine "$HOME/.wine/drive_c/Python311/python.exe" -m pip install MetaTrader5

# For Linux Python
pip install MetaTrader5
```

### Issue 3: Connection refused or timeout

**Solution:**
- Check internet connection
- Verify broker server address
- Check firewall settings:
```bash
sudo ufw allow out 443/tcp
sudo ufw allow out 80/tcp
```

### Issue 4: Wine crashes or freezes

**Solution:**
```bash
# Kill Wine processes
wineserver -k

# Restart Wine
wine "$HOME/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
```

### Issue 5: Can't find MT5 terminal

**Solution:**
```bash
# Find MT5 installation
find ~/.wine -name "terminal64.exe"

# Update path in start script
```

---

## Running Bot as a Service (Background)

### Using systemd:

1. **Create service file:**
```bash
sudo nano /etc/systemd/system/mt5-bot.service
```

2. **Add configuration:**
```ini
[Unit]
Description=MT5 SMC Trading Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/SMC_DGA
Environment="DISPLAY=:0"
ExecStart=/usr/bin/wine /home/your_username/.wine/drive_c/Python311/python.exe main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Enable and start service:**
```bash
sudo systemctl enable mt5-bot
sudo systemctl start mt5-bot
sudo systemctl status mt5-bot
```

### Using screen (simpler):

```bash
# Start MT5 in screen
screen -S mt5
wine "$HOME/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"
# Detach: Ctrl+A, then D

# Start bot in another screen
screen -S bot
wine "$HOME/.wine/drive_c/Python311/python.exe" main.py
# Detach: Ctrl+A, then D

# Reattach later
screen -r bot
```

---

## Performance Tips

1. **Use lightweight desktop environment** (XFCE, LXDE) to reduce overhead
2. **Disable Wine debugging:**
```bash
export WINEDEBUG=-all
```

3. **Increase Wine performance:**
```bash
# Edit Wine registry
wine regedit

# Set HKEY_CURRENT_USER\Software\Wine\Direct3D\MaxVersionGL to 30000
```

4. **Monitor resource usage:**
```bash
htop
```

---

## Alternative: Using VPS with Windows

If Wine causes issues, consider:
1. **Rent a Windows VPS** (cheaper, more reliable)
2. Run MT5 natively on Windows
3. Run bot on Windows
4. Access via RDP from Linux

Popular VPS providers:
- Vultr (Windows VPS from $6/month)
- Contabo (Windows VPS from €5/month)
- AWS Lightsail

---

## Testing the Setup

Run this test to verify MT5 connection:

```python
# test_mt5.py
import MetaTrader5 as mt5

print("Initializing MT5...")
if not mt5.initialize():
    print("Failed:", mt5.last_error())
else:
    print("Success!")
    print("Version:", mt5.version())
    mt5.shutdown()
```

Run test:
```bash
wine "$HOME/.wine/drive_c/Python311/python.exe" test_mt5.py
```

---

## Support

If you encounter issues:
1. Check Wine logs: `wine --verbose`
2. Check MT5 logs: `~/.wine/drive_c/Program Files/MetaTrader 5/Logs/`
3. Test MT5 works manually before running bot
4. Ensure "Algo Trading" is enabled in MT5

---

## Quick Start Script

For convenience, use the provided scripts:

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Start MT5
./scripts/start_mt5.sh

# Run bot
./scripts/run_bot.sh
```
