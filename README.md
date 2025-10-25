# MT5 Smart Money Concepts (SMC) Trading Bot

An automated trading bot for MetaTrader 5 platform implementing Smart Money Concepts strategy.

## Strategy Overview

This bot implements the powerful SMC combination:
**Order Blocks + Liquidity + Fair Value Gaps**

### Trading Logic

1. **Identify Liquidity Pools** - Find obvious highs/lows where stop losses cluster
2. **Wait for Liquidity Sweep** - Price runs these stops (false breakout)
3. **Enter at Order Block/FVG** - After liquidity grab, price returns to Order Block or fills Fair Value Gap
4. **Confirmation** - Look for rejection candles or Break of Structure (BOS) in trading direction

## Features

- **Order Block Detection**: Identifies institutional supply/demand zones
- **Liquidity Pool Identification**: Finds areas where stop losses accumulate
- **Fair Value Gap Detection**: Identifies imbalances in price action
- **Liquidity Sweep Detection**: Detects when market sweeps liquidity before reversing
- **Break of Structure (BOS)**: Confirms trend changes and trade entries
- **Risk Management**: Automatic position sizing and stop loss placement
- **MT5 Integration**: Full integration with MetaTrader 5 platform

## Installation

### Prerequisites

- Python 3.8 or higher
- MetaTrader 5 platform installed
- MT5 trading account

### Platform-Specific Setup

#### **Linux Users (MT5 on Wine)**

If you're running MT5 on Linux with Wine, use the automated installation:

```bash
chmod +x scripts/install_linux.sh
./scripts/install_linux.sh
```

Then follow the quick start:

```bash
# 1. Configure credentials
nano .env

# 2. Start MT5
./scripts/start_mt5.sh

# 3. Test connection
./scripts/test_mt5_connection.sh

# 4. Run bot
./scripts/run_bot.sh
```

**📖 For detailed Linux/Wine setup instructions, see [LINUX_SETUP.md](LINUX_SETUP.md)**

#### **Windows Users**

1. Clone the repository:
```bash
git clone <repository_url>
cd SMC_DGA
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your MT5 account:
```bash
copy .env.example .env
# Edit .env with your MT5 credentials and trading parameters
```

4. Run the bot:
```bash
python main.py
```

## Configuration

Edit `.env` file to customize:

- **MT5 Credentials**: Login, password, server
- **Trading Parameters**: Symbol, timeframe, lot size, risk percentage
- **SMC Parameters**: Order block settings, liquidity detection, FVG thresholds

## Project Structure

```
SMC_DGA/
├── main.py                      # Main bot runner
├── config.py                    # Configuration loader
├── requirements.txt             # Python dependencies
├── .env.example                # Environment template
├── README.md                    # This file
├── LINUX_SETUP.md              # Detailed Linux/Wine setup guide
├── mt5/
│   └── connection.py           # MT5 connection handler
├── strategy/
│   ├── order_blocks.py         # Order Block detection
│   ├── liquidity.py            # Liquidity pool identification
│   ├── fvg.py                 # Fair Value Gap detection
│   ├── bos.py                 # Break of Structure detection
│   └── smc_strategy.py        # Main trading strategy
├── risk/
│   └── management.py           # Risk and position management
└── scripts/                     # Helper scripts (Linux/Wine)
    ├── install_linux.sh        # Automated Linux installation
    ├── start_mt5.sh            # Start MT5 in Wine
    ├── run_bot.sh              # Run the trading bot
    ├── test_mt5_connection.sh  # Test MT5 connection
    └── stop_bot.sh             # Stop bot and MT5
```

## How It Works

### 1. Order Blocks
The bot identifies the last up or down candle before a strong market move. These represent institutional order zones.

### 2. Liquidity Pools
Swing highs and lows are tracked as liquidity pools where retail stop losses accumulate.

### 3. Fair Value Gaps (FVG)
Gaps in price action where there's minimal trading activity, often filled later.

### 4. Trade Entry Logic

**Buy Signal:**
- Liquidity sweep below a swing low (bearish liquidity grab)
- Price returns to bullish Order Block or FVG
- Bullish BOS confirms trend change
- Enter long with stop below Order Block

**Sell Signal:**
- Liquidity sweep above a swing high (bullish liquidity grab)
- Price returns to bearish Order Block or FVG
- Bearish BOS confirms trend change
- Enter short with stop above Order Block

## Risk Warning

Trading involves substantial risk of loss. This bot is for educational purposes. Always test on a demo account first and never risk more than you can afford to lose.

## License

MIT License
