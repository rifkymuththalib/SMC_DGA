#!/bin/bash
# Installation script for Linux with Wine

set -e

echo "="*60
echo "MT5 SMC Trading Bot - Linux Installation"
echo "="*60

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "Cannot detect Linux distribution"
    exit 1
fi

echo ""
echo "Detected OS: $OS"
echo ""

# Function to install Wine
install_wine() {
    echo "Installing Wine..."
    case $OS in
        ubuntu|debian|linuxmint)
            sudo dpkg --add-architecture i386
            sudo apt update
            sudo apt install -y wine64 wine32 winetricks wget
            ;;
        fedora)
            sudo dnf install -y wine winetricks wget
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm wine winetricks wget
            ;;
        *)
            echo "Unsupported distribution. Please install Wine manually."
            exit 1
            ;;
    esac
}

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "Wine is not installed."
    read -p "Install Wine? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_wine
    else
        echo "Wine is required. Exiting."
        exit 1
    fi
fi

echo "✓ Wine version: $(wine --version)"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python3..."
    case $OS in
        ubuntu|debian|linuxmint)
            sudo apt install -y python3 python3-venv python3-pip
            ;;
        fedora)
            sudo dnf install -y python3 python3-pip
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm python python-pip
            ;;
    esac
fi

echo "✓ Python version: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate venv and install dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Check if MT5 is installed in Wine
MT5_PATH="$HOME/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe"

if [ ! -f "$MT5_PATH" ]; then
    echo ""
    echo "MetaTrader 5 not found in Wine."
    echo ""
    echo "Options:"
    echo "1. Download and install MT5 now"
    echo "2. Skip (install manually later)"
    read -p "Choose (1/2): " -n 1 -r
    echo

    if [[ $REPLY == "1" ]]; then
        echo "Downloading MT5 installer..."
        wget -O /tmp/mt5setup.exe https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

        echo "Installing MT5 in Wine..."
        echo "(Follow the installation wizard)"
        wine /tmp/mt5setup.exe

        # Wait for installation
        echo "Waiting for installation to complete..."
        sleep 5
    fi
fi

# Install Wine dependencies for MT5
echo ""
echo "Installing Wine dependencies for MT5..."
export WINEDEBUG=-all
winetricks -q dotnet48 vcrun2019 corefonts 2>/dev/null || true
echo "✓ Wine dependencies installed"

# Install Python in Wine
WINE_PYTHON="$HOME/.wine/drive_c/Python311/python.exe"

if [ ! -f "$WINE_PYTHON" ]; then
    echo ""
    echo "Python not found in Wine."
    read -p "Install Python in Wine? (Recommended) (y/n) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Downloading Python for Windows..."
        wget -O /tmp/python-installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

        echo "Installing Python in Wine..."
        echo "(Make sure to check 'Add Python to PATH' in the installer)"
        wine /tmp/python-installer.exe

        # Wait for installation
        sleep 5

        # Install Python packages in Wine
        if [ -f "$WINE_PYTHON" ]; then
            echo "Installing Python packages in Wine..."
            wine "$WINE_PYTHON" -m pip install MetaTrader5 pandas numpy scipy python-dotenv pytz
            echo "✓ Wine Python packages installed"
        fi
    fi
fi

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x scripts/*.sh
echo "✓ Scripts are executable"

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env configuration file..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your MT5 credentials:"
    echo "   nano .env"
fi

# Summary
echo ""
echo "="*60
echo "✓ Installation Complete!"
echo "="*60
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your MT5 account:"
echo "   nano .env"
echo ""
echo "2. Start MT5:"
echo "   ./scripts/start_mt5.sh"
echo ""
echo "3. Test the connection:"
echo "   ./scripts/test_mt5_connection.sh"
echo ""
echo "4. Run the bot:"
echo "   ./scripts/run_bot.sh"
echo ""
echo "For detailed instructions, see: LINUX_SETUP.md"
echo "="*60
