"""
Fair Value Gap (FVG) Detection
Identifies imbalances in price action where minimal trading occurred
"""
import pandas as pd
import numpy as np


class FVGDetector:
    """Detect Fair Value Gaps (imbalances)"""

    def __init__(self, min_size_pips=5, max_age=20):
        """
        Initialize FVG Detector

        Args:
            min_size_pips: Minimum gap size in pips to consider
            max_age: Maximum age in candles before FVG expires
        """
        self.min_size_pips = min_size_pips
        self.max_age = max_age

    def detect_fvgs(self, df, pip_value=0.0001):
        """
        Detect Fair Value Gaps

        A FVG forms when there's a gap between:
        - Bullish FVG: Current candle's low > Two candles ago high
        - Bearish FVG: Current candle's high < Two candles ago low

        The gap represents an imbalance that price often returns to fill.

        Args:
            df: DataFrame with OHLCV data
            pip_value: Pip size for the symbol (0.0001 for forex, 0.01 for JPY)

        Returns:
            Dictionary with bullish and bearish FVGs
        """
        bullish_fvgs = []
        bearish_fvgs = []

        if len(df) < 3:
            return {'bullish': bullish_fvgs, 'bearish': bearish_fvgs}

        df = df.copy().reset_index(drop=True)

        # Scan for FVGs
        for i in range(2, len(df)):
            candle_0 = df.iloc[i - 2]  # Two candles ago
            candle_1 = df.iloc[i - 1]  # Previous candle
            candle_2 = df.iloc[i]      # Current candle

            # Check for Bullish FVG (gap up)
            # Current low > two candles ago high
            if candle_2['low'] > candle_0['high']:
                gap_size = candle_2['low'] - candle_0['high']
                gap_size_pips = gap_size / pip_value

                if gap_size_pips >= self.min_size_pips:
                    fvg = {
                        'index': i,
                        'time': candle_2['time'],
                        'type': 'bullish',
                        'top': candle_2['low'],
                        'bottom': candle_0['high'],
                        'size': gap_size,
                        'size_pips': gap_size_pips,
                        'filled': False,
                        'partially_filled': False,
                        'fill_percent': 0,
                        'age': len(df) - i
                    }
                    bullish_fvgs.append(fvg)

            # Check for Bearish FVG (gap down)
            # Current high < two candles ago low
            if candle_2['high'] < candle_0['low']:
                gap_size = candle_0['low'] - candle_2['high']
                gap_size_pips = gap_size / pip_value

                if gap_size_pips >= self.min_size_pips:
                    fvg = {
                        'index': i,
                        'time': candle_2['time'],
                        'type': 'bearish',
                        'top': candle_0['low'],
                        'bottom': candle_2['high'],
                        'size': gap_size,
                        'size_pips': gap_size_pips,
                        'filled': False,
                        'partially_filled': False,
                        'fill_percent': 0,
                        'age': len(df) - i
                    }
                    bearish_fvgs.append(fvg)

        # Update FVG fill status
        current_price = df.iloc[-1]['close']
        bullish_fvgs = [self._update_fvg_status(fvg, current_price) for fvg in bullish_fvgs]
        bearish_fvgs = [self._update_fvg_status(fvg, current_price) for fvg in bearish_fvgs]

        return {
            'bullish': bullish_fvgs,
            'bearish': bearish_fvgs
        }

    def _update_fvg_status(self, fvg, current_price):
        """Update FVG fill status based on current price"""
        gap_size = fvg['top'] - fvg['bottom']

        if fvg['type'] == 'bullish':
            # Price needs to come back down into the gap
            if current_price <= fvg['bottom']:
                fvg['filled'] = True
                fvg['fill_percent'] = 100
            elif current_price < fvg['top']:
                fvg['partially_filled'] = True
                filled_distance = fvg['top'] - current_price
                fvg['fill_percent'] = (filled_distance / gap_size) * 100
        else:  # bearish
            # Price needs to come back up into the gap
            if current_price >= fvg['top']:
                fvg['filled'] = True
                fvg['fill_percent'] = 100
            elif current_price > fvg['bottom']:
                fvg['partially_filled'] = True
                filled_distance = current_price - fvg['bottom']
                fvg['fill_percent'] = (filled_distance / gap_size) * 100

        return fvg

    def get_valid_fvgs(self, fvgs_dict):
        """
        Get valid FVGs that are not fully filled and not expired

        Args:
            fvgs_dict: Dictionary with 'bullish' and 'bearish' FVGs

        Returns:
            Filtered FVGs
        """
        valid_bullish = [
            fvg for fvg in fvgs_dict['bullish']
            if not fvg['filled'] and fvg['age'] <= self.max_age
        ]

        valid_bearish = [
            fvg for fvg in fvgs_dict['bearish']
            if not fvg['filled'] and fvg['age'] <= self.max_age
        ]

        return {
            'bullish': valid_bullish,
            'bearish': valid_bearish
        }

    def is_price_in_fvg(self, price, fvg):
        """Check if price is within FVG zone"""
        return fvg['bottom'] <= price <= fvg['top']

    def get_nearest_fvg(self, fvgs_dict, current_price, fvg_type='both'):
        """
        Get nearest unfilled FVG to current price

        Args:
            fvgs_dict: Dictionary with FVGs
            current_price: Current market price
            fvg_type: 'bullish', 'bearish', or 'both'

        Returns:
            Nearest FVG(s)
        """
        nearest = {}

        if fvg_type in ['bullish', 'both']:
            bullish = fvgs_dict.get('bullish', [])
            unfilled_bullish = [fvg for fvg in bullish if not fvg['filled']]

            if unfilled_bullish:
                # Find nearest below current price (for potential retracement)
                below = [fvg for fvg in unfilled_bullish if fvg['top'] < current_price]
                if below:
                    nearest['bullish'] = min(below, key=lambda x: abs((x['top'] + x['bottom'])/2 - current_price))

        if fvg_type in ['bearish', 'both']:
            bearish = fvgs_dict.get('bearish', [])
            unfilled_bearish = [fvg for fvg in bearish if not fvg['filled']]

            if unfilled_bearish:
                # Find nearest above current price (for potential retracement)
                above = [fvg for fvg in unfilled_bearish if fvg['bottom'] > current_price]
                if above:
                    nearest['bearish'] = min(above, key=lambda x: abs((x['top'] + x['bottom'])/2 - current_price))

        return nearest if nearest else None

    def check_fvg_confluence(self, fvg, order_block):
        """
        Check if FVG aligns with an order block (strong confluence)

        Args:
            fvg: Fair Value Gap
            order_block: Order Block

        Returns:
            True if they overlap (confluence zone)
        """
        # Check if zones overlap
        fvg_range = (fvg['bottom'], fvg['top'])
        ob_range = (order_block['zone_bottom'], order_block['zone_top'])

        # Check for overlap
        return not (fvg_range[1] < ob_range[0] or fvg_range[0] > ob_range[1])

    def get_fvg_entry_zone(self, fvg, fill_percent=50):
        """
        Get optimal entry zone within FVG

        Args:
            fvg: Fair Value Gap
            fill_percent: Percentage of gap to wait for (50% = middle, 100% = full fill)

        Returns:
            Entry price level
        """
        gap_size = fvg['top'] - fvg['bottom']
        fill_distance = gap_size * (fill_percent / 100)

        if fvg['type'] == 'bullish':
            # Enter when price retraces into gap
            entry = fvg['top'] - fill_distance
        else:  # bearish
            # Enter when price retraces into gap
            entry = fvg['bottom'] + fill_distance

        return entry
