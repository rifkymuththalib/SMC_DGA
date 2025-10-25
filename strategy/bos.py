"""
Break of Structure (BOS) Detection
Identifies trend changes and structure breaks in price action
"""
import pandas as pd
import numpy as np


class BOSDetector:
    """Detect Break of Structure (BOS) and Change of Character (ChoCh)"""

    def __init__(self, confirmation_candles=3):
        """
        Initialize BOS Detector

        Args:
            confirmation_candles: Number of candles to confirm BOS
        """
        self.confirmation_candles = confirmation_candles

    def detect_bos(self, df, lookback=50):
        """
        Detect Break of Structure

        BOS occurs when:
        - Bullish BOS: Price breaks above previous swing high (uptrend confirmed)
        - Bearish BOS: Price breaks below previous swing low (downtrend confirmed)

        Args:
            df: DataFrame with OHLCV data
            lookback: Number of candles to analyze

        Returns:
            Dictionary with BOS signals
        """
        if len(df) < lookback:
            return None

        df = df.copy().reset_index(drop=True)

        # Get recent data
        recent_df = df.tail(lookback)

        # Find swing points
        swing_highs = self._find_swing_highs(recent_df)
        swing_lows = self._find_swing_lows(recent_df)

        # Check for recent BOS
        bullish_bos = self._check_bullish_bos(df, swing_highs)
        bearish_bos = self._check_bearish_bos(df, swing_lows)

        result = {
            'bullish_bos': bullish_bos,
            'bearish_bos': bearish_bos,
            'trend': self._determine_trend(df, swing_highs, swing_lows)
        }

        return result

    def _find_swing_highs(self, df, order=3):
        """Find swing high points"""
        from scipy.signal import argrelextrema

        high_indices = argrelextrema(df['high'].values, np.greater, order=order)[0]

        swing_highs = []
        for idx in high_indices:
            if idx < len(df):
                swing_highs.append({
                    'index': df.index[idx],
                    'price': df.iloc[idx]['high'],
                    'time': df.iloc[idx]['time']
                })

        return sorted(swing_highs, key=lambda x: x['index'])

    def _find_swing_lows(self, df, order=3):
        """Find swing low points"""
        from scipy.signal import argrelextrema

        low_indices = argrelextrema(df['low'].values, np.less, order=order)[0]

        swing_lows = []
        for idx in low_indices:
            if idx < len(df):
                swing_lows.append({
                    'index': df.index[idx],
                    'price': df.iloc[idx]['low'],
                    'time': df.iloc[idx]['time']
                })

        return sorted(swing_lows, key=lambda x: x['index'])

    def _check_bullish_bos(self, df, swing_highs):
        """
        Check for bullish Break of Structure

        Occurs when price breaks above a previous swing high
        """
        if len(swing_highs) == 0:
            return None

        # Get most recent swing high
        last_swing_high = swing_highs[-1]

        # Check if recent price broke above it
        recent_candles = df.tail(self.confirmation_candles)
        broke_above = recent_candles['high'].max() > last_swing_high['price']

        if broke_above:
            # Confirm with close above
            closes_above = (recent_candles['close'] > last_swing_high['price']).sum()

            if closes_above >= 1:
                return {
                    'confirmed': True,
                    'break_level': last_swing_high['price'],
                    'break_time': df.iloc[-1]['time'],
                    'strength': closes_above / self.confirmation_candles
                }

        return None

    def _check_bearish_bos(self, df, swing_lows):
        """
        Check for bearish Break of Structure

        Occurs when price breaks below a previous swing low
        """
        if len(swing_lows) == 0:
            return None

        # Get most recent swing low
        last_swing_low = swing_lows[-1]

        # Check if recent price broke below it
        recent_candles = df.tail(self.confirmation_candles)
        broke_below = recent_candles['low'].min() < last_swing_low['price']

        if broke_below:
            # Confirm with close below
            closes_below = (recent_candles['close'] < last_swing_low['price']).sum()

            if closes_below >= 1:
                return {
                    'confirmed': True,
                    'break_level': last_swing_low['price'],
                    'break_time': df.iloc[-1]['time'],
                    'strength': closes_below / self.confirmation_candles
                }

        return None

    def _determine_trend(self, df, swing_highs, swing_lows):
        """
        Determine current trend based on swing points

        Uptrend: Higher highs and higher lows
        Downtrend: Lower highs and lower lows
        """
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'unknown'

        # Check last two swing highs
        recent_highs = swing_highs[-2:]
        higher_high = recent_highs[1]['price'] > recent_highs[0]['price']

        # Check last two swing lows
        recent_lows = swing_lows[-2:]
        higher_low = recent_lows[1]['price'] > recent_lows[0]['price']

        # Determine trend
        if higher_high and higher_low:
            return 'uptrend'
        elif not higher_high and not higher_low:
            return 'downtrend'
        else:
            return 'ranging'

    def detect_choch(self, df, lookback=50):
        """
        Detect Change of Character (ChoCh)

        ChoCh is an early sign of trend change:
        - In uptrend: Failure to make higher high
        - In downtrend: Failure to make lower low

        Args:
            df: DataFrame with price data
            lookback: Number of candles to analyze

        Returns:
            ChoCh signal if detected
        """
        if len(df) < lookback:
            return None

        df = df.copy().reset_index(drop=True)
        recent_df = df.tail(lookback)

        swing_highs = self._find_swing_highs(recent_df)
        swing_lows = self._find_swing_lows(recent_df)

        trend = self._determine_trend(df, swing_highs, swing_lows)

        choch = None

        if trend == 'uptrend' and len(swing_lows) >= 2:
            # Check for lower low (ChoCh in uptrend)
            recent_lows = swing_lows[-2:]
            if recent_lows[1]['price'] < recent_lows[0]['price']:
                choch = {
                    'type': 'bearish_choch',
                    'previous_trend': 'uptrend',
                    'level': recent_lows[1]['price'],
                    'time': recent_lows[1]['time']
                }

        elif trend == 'downtrend' and len(swing_highs) >= 2:
            # Check for higher high (ChoCh in downtrend)
            recent_highs = swing_highs[-2:]
            if recent_highs[1]['price'] > recent_highs[0]['price']:
                choch = {
                    'type': 'bullish_choch',
                    'previous_trend': 'downtrend',
                    'level': recent_highs[1]['price'],
                    'time': recent_highs[1]['time']
                }

        return choch

    def is_bos_confirmed(self, bos_signal, current_candle):
        """
        Check if BOS remains valid

        Args:
            bos_signal: BOS signal to check
            current_candle: Current candle data

        Returns:
            True if BOS is still valid
        """
        if bos_signal is None:
            return False

        return bos_signal.get('confirmed', False)

    def get_market_structure(self, df, lookback=100):
        """
        Analyze overall market structure

        Args:
            df: DataFrame with price data
            lookback: Number of candles to analyze

        Returns:
            Market structure analysis
        """
        if len(df) < lookback:
            lookback = len(df)

        recent_df = df.tail(lookback).copy().reset_index(drop=True)

        swing_highs = self._find_swing_highs(recent_df)
        swing_lows = self._find_swing_lows(recent_df)

        trend = self._determine_trend(df, swing_highs, swing_lows)

        structure = {
            'trend': trend,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'last_swing_high': swing_highs[-1] if swing_highs else None,
            'last_swing_low': swing_lows[-1] if swing_lows else None
        }

        return structure
