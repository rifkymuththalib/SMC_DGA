"""
Liquidity Pool Detection
Identifies liquidity pools at swing highs and lows where stop losses cluster
"""
import pandas as pd
import numpy as np
from scipy.signal import argrelextrema


class LiquidityDetector:
    """Detect liquidity pools and sweeps"""

    def __init__(self, lookback=100, min_touches=2):
        """
        Initialize Liquidity Detector

        Args:
            lookback: Number of candles to analyze for liquidity
            min_touches: Minimum touches to confirm a liquidity level
        """
        self.lookback = lookback
        self.min_touches = min_touches

    def find_liquidity_pools(self, df):
        """
        Find liquidity pools at swing highs and lows

        Liquidity pools form at:
        - Swing highs: Buy stop orders cluster above
        - Swing lows: Sell stop orders cluster below

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with buy-side and sell-side liquidity pools
        """
        if len(df) < self.lookback:
            return {'buy_side': [], 'sell_side': []}

        df = df.copy().reset_index(drop=True)

        # Find swing highs and lows
        swing_highs = self._find_swing_highs(df)
        swing_lows = self._find_swing_lows(df)

        # Build liquidity pools
        buy_side_liquidity = []  # Above swing highs
        sell_side_liquidity = []  # Below swing lows

        # Process swing highs (buy-side liquidity above)
        for high in swing_highs:
            pool = {
                'index': high['index'],
                'time': high['time'],
                'price': high['price'],
                'type': 'buy_side',  # Stops above this level
                'touches': high['touches'],
                'swept': False,
                'age': len(df) - high['index']
            }
            buy_side_liquidity.append(pool)

        # Process swing lows (sell-side liquidity below)
        for low in swing_lows:
            pool = {
                'index': low['index'],
                'time': low['time'],
                'price': low['price'],
                'type': 'sell_side',  # Stops below this level
                'touches': low['touches'],
                'swept': False,
                'age': len(df) - low['index']
            }
            sell_side_liquidity.append(pool)

        return {
            'buy_side': buy_side_liquidity,
            'sell_side': sell_side_liquidity
        }

    def _find_swing_highs(self, df, order=5):
        """
        Find swing highs in the data

        Args:
            df: DataFrame with price data
            order: Number of candles on each side to confirm swing

        Returns:
            List of swing high points
        """
        # Find local maxima
        high_indices = argrelextrema(df['high'].values, np.greater, order=order)[0]

        swing_highs = []
        for idx in high_indices:
            if idx >= len(df) - self.lookback and idx < len(df):
                # Count how many times this level was touched
                touches = self._count_touches(df, df.iloc[idx]['high'], 'high', idx)

                if touches >= self.min_touches:
                    swing_highs.append({
                        'index': idx,
                        'time': df.iloc[idx]['time'],
                        'price': df.iloc[idx]['high'],
                        'touches': touches
                    })

        return swing_highs

    def _find_swing_lows(self, df, order=5):
        """
        Find swing lows in the data

        Args:
            df: DataFrame with price data
            order: Number of candles on each side to confirm swing

        Returns:
            List of swing low points
        """
        # Find local minima
        low_indices = argrelextrema(df['low'].values, np.less, order=order)[0]

        swing_lows = []
        for idx in low_indices:
            if idx >= len(df) - self.lookback and idx < len(df):
                # Count how many times this level was touched
                touches = self._count_touches(df, df.iloc[idx]['low'], 'low', idx)

                if touches >= self.min_touches:
                    swing_lows.append({
                        'index': idx,
                        'time': df.iloc[idx]['time'],
                        'price': df.iloc[idx]['low'],
                        'touches': touches
                    })

        return swing_lows

    def _count_touches(self, df, level, price_type='high', start_idx=0, tolerance=0.0002):
        """
        Count how many times price touched a level

        Args:
            df: DataFrame
            level: Price level to check
            price_type: 'high' or 'low'
            start_idx: Starting index
            tolerance: Price tolerance (0.02% by default)

        Returns:
            Number of touches
        """
        touches = 0
        threshold = level * tolerance

        for i in range(max(0, start_idx - 20), min(len(df), start_idx + 20)):
            if abs(df.iloc[i][price_type] - level) <= threshold:
                touches += 1

        return touches

    def detect_liquidity_sweep(self, df, liquidity_pools, lookback_candles=5):
        """
        Detect if liquidity was swept (false breakout)

        A liquidity sweep occurs when:
        - Price breaks above buy-side liquidity (swing high)
        - Price breaks below sell-side liquidity (swing low)
        - Then quickly reverses (false breakout)

        Args:
            df: DataFrame with recent price data
            liquidity_pools: Dictionary with liquidity pools
            lookback_candles: Number of recent candles to check

        Returns:
            Dictionary with sweep information
        """
        if len(df) < lookback_candles:
            return None

        recent_candles = df.tail(lookback_candles)
        sweeps = []

        # Check buy-side liquidity sweeps (price breaks high then reverses down)
        for pool in liquidity_pools.get('buy_side', []):
            if pool['swept']:
                continue

            # Check if recent price broke above the liquidity level
            broke_above = recent_candles['high'].max() > pool['price']

            if broke_above:
                # Check for reversal (close back below the level)
                current_close = df.iloc[-1]['close']
                if current_close < pool['price']:
                    pool['swept'] = True
                    sweeps.append({
                        'type': 'buy_side_sweep',
                        'direction': 'bearish',  # Swept high, expect down move
                        'level': pool['price'],
                        'time': df.iloc[-1]['time'],
                        'pool': pool
                    })

        # Check sell-side liquidity sweeps (price breaks low then reverses up)
        for pool in liquidity_pools.get('sell_side', []):
            if pool['swept']:
                continue

            # Check if recent price broke below the liquidity level
            broke_below = recent_candles['low'].min() < pool['price']

            if broke_below:
                # Check for reversal (close back above the level)
                current_close = df.iloc[-1]['close']
                if current_close > pool['price']:
                    pool['swept'] = True
                    sweeps.append({
                        'type': 'sell_side_sweep',
                        'direction': 'bullish',  # Swept low, expect up move
                        'level': pool['price'],
                        'time': df.iloc[-1]['time'],
                        'pool': pool
                    })

        return sweeps if len(sweeps) > 0 else None

    def get_nearest_liquidity(self, liquidity_pools, current_price, side='both'):
        """
        Get nearest liquidity pool to current price

        Args:
            liquidity_pools: Dictionary with liquidity pools
            current_price: Current market price
            side: 'buy_side', 'sell_side', or 'both'

        Returns:
            Nearest liquidity pool(s)
        """
        nearest = {}

        if side in ['buy_side', 'both']:
            buy_side = liquidity_pools.get('buy_side', [])
            if buy_side:
                # Find nearest above current price
                above = [p for p in buy_side if p['price'] > current_price and not p['swept']]
                if above:
                    nearest['buy_side'] = min(above, key=lambda x: abs(x['price'] - current_price))

        if side in ['sell_side', 'both']:
            sell_side = liquidity_pools.get('sell_side', [])
            if sell_side:
                # Find nearest below current price
                below = [p for p in sell_side if p['price'] < current_price and not p['swept']]
                if below:
                    nearest['sell_side'] = min(below, key=lambda x: abs(x['price'] - current_price))

        return nearest if nearest else None
