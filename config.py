"""
Configuration loader for MT5 SMC Trading Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for bot settings"""

    # MT5 Account Settings
    MT5_LOGIN = int(os.getenv('MT5_LOGIN', 0))
    MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
    MT5_SERVER = os.getenv('MT5_SERVER', '')

    # Trading Parameters
    SYMBOL = os.getenv('SYMBOL', 'EURUSD')
    TIMEFRAME = os.getenv('TIMEFRAME', 'H1')
    LOT_SIZE = float(os.getenv('LOT_SIZE', 0.01))
    RISK_PERCENT = float(os.getenv('RISK_PERCENT', 1.0))
    MAX_TRADES = int(os.getenv('MAX_TRADES', 3))

    # Order Block Settings
    OB_MIN_BODY_PERCENT = float(os.getenv('OB_MIN_BODY_PERCENT', 60))
    OB_LOOKBACK_CANDLES = int(os.getenv('OB_LOOKBACK_CANDLES', 50))

    # Liquidity Settings
    LIQUIDITY_LOOKBACK = int(os.getenv('LIQUIDITY_LOOKBACK', 100))
    LIQUIDITY_MIN_TOUCHES = int(os.getenv('LIQUIDITY_MIN_TOUCHES', 2))

    # Fair Value Gap Settings
    FVG_MIN_SIZE_PIPS = float(os.getenv('FVG_MIN_SIZE_PIPS', 5))
    FVG_MAX_AGE_CANDLES = int(os.getenv('FVG_MAX_AGE_CANDLES', 20))

    # Break of Structure Settings
    BOS_CONFIRMATION_CANDLES = int(os.getenv('BOS_CONFIRMATION_CANDLES', 3))

    # Timeframe mapping
    TIMEFRAME_MAP = {
        'M1': 1,
        'M5': 5,
        'M15': 15,
        'M30': 30,
        'H1': 60,
        'H4': 240,
        'D1': 1440,
        'W1': 10080,
        'MN1': 43200
    }

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.MT5_LOGIN or not cls.MT5_PASSWORD or not cls.MT5_SERVER:
            raise ValueError("MT5 credentials not configured. Please set MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER in .env file")

        if cls.TIMEFRAME not in cls.TIMEFRAME_MAP:
            raise ValueError(f"Invalid timeframe: {cls.TIMEFRAME}. Must be one of {list(cls.TIMEFRAME_MAP.keys())}")

        return True
