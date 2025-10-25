"""
Order Block Detection
Identifies institutional order blocks (supply and demand zones)
"""
import pandas as pd
import numpy as np


class OrderBlockDetector:
    """Detect order blocks in price data"""

    def __init__(self, min_body_percent=60, lookback=50):
        """
        Initialize Order Block Detector

        Args:
            min_body_percent: Minimum candle body percentage (60-80% recommended)
            lookback: Number of candles to look back for order blocks
        """
        self.min_body_percent = min_body_percent
        self.lookback = lookback

    def detect_order_blocks(self, df):
        """
        Detect bullish and bearish order blocks

        An order block is the last opposite candle before a strong move:
        - Bullish OB: Last down candle before strong up move
        - Bearish OB: Last up candle before strong down move

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with bullish and bearish order blocks
        """
        bullish_obs = []
        bearish_obs = []

        # Ensure we have enough data
        if len(df) < self.lookback + 10:
            return {'bullish': bullish_obs, 'bearish': bearish_obs}

        # Calculate candle properties
        df = df.copy()
        df['body'] = abs(df['close'] - df['open'])
        df['range'] = df['high'] - df['low']
        df['body_percent'] = (df['body'] / df['range']) * 100

        # Identify strong candles (large body)
        df['is_strong'] = df['body_percent'] >= self.min_body_percent

        # Bullish and bearish candles
        df['is_bullish'] = df['close'] > df['open']
        df['is_bearish'] = df['close'] < df['open']

        # Look for order blocks in recent data
        for i in range(len(df) - self.lookback, len(df) - 5):
            if i < 1:
                continue

            # Check for bullish order block
            # Last bearish candle before bullish movement
            if df.iloc[i]['is_bearish'] and df.iloc[i]['is_strong']:
                # Check if followed by bullish candles
                next_candles = df.iloc[i+1:i+4]
                if len(next_candles) > 0 and next_candles['is_bullish'].sum() >= 2:
                    # Verify the move broke above the OB high
                    if next_candles['high'].max() > df.iloc[i]['high']:
                        ob = {
                            'index': i,
                            'time': df.iloc[i]['time'],
                            'type': 'bullish',
                            'high': df.iloc[i]['high'],
                            'low': df.iloc[i]['low'],
                            'open': df.iloc[i]['open'],
                            'close': df.iloc[i]['close'],
                            'zone_top': df.iloc[i]['high'],
                            'zone_bottom': df.iloc[i]['low'],
                            'touched': False,
                            'age': len(df) - i
                        }
                        bullish_obs.append(ob)

            # Check for bearish order block
            # Last bullish candle before bearish movement
            if df.iloc[i]['is_bullish'] and df.iloc[i]['is_strong']:
                # Check if followed by bearish candles
                next_candles = df.iloc[i+1:i+4]
                if len(next_candles) > 0 and next_candles['is_bearish'].sum() >= 2:
                    # Verify the move broke below the OB low
                    if next_candles['low'].min() < df.iloc[i]['low']:
                        ob = {
                            'index': i,
                            'time': df.iloc[i]['time'],
                            'type': 'bearish',
                            'high': df.iloc[i]['high'],
                            'low': df.iloc[i]['low'],
                            'open': df.iloc[i]['open'],
                            'close': df.iloc[i]['close'],
                            'zone_top': df.iloc[i]['high'],
                            'zone_bottom': df.iloc[i]['low'],
                            'touched': False,
                            'age': len(df) - i
                        }
                        bearish_obs.append(ob)

        # Filter out overlapping order blocks (keep most recent)
        bullish_obs = self._filter_overlapping_obs(bullish_obs)
        bearish_obs = self._filter_overlapping_obs(bearish_obs)

        return {
            'bullish': bullish_obs,
            'bearish': bearish_obs
        }

    def _filter_overlapping_obs(self, obs_list):
        """Remove overlapping order blocks, keeping the most recent"""
        if len(obs_list) <= 1:
            return obs_list

        # Sort by index (most recent first)
        obs_list.sort(key=lambda x: x['index'], reverse=True)

        filtered = []
        for ob in obs_list:
            # Check if it overlaps with any already filtered OB
            overlaps = False
            for filtered_ob in filtered:
                if self._zones_overlap(ob, filtered_ob):
                    overlaps = True
                    break

            if not overlaps:
                filtered.append(ob)

        return filtered

    def _zones_overlap(self, ob1, ob2):
        """Check if two order block zones overlap"""
        return not (ob1['zone_top'] < ob2['zone_bottom'] or ob1['zone_bottom'] > ob2['zone_top'])

    def is_price_in_ob(self, price, order_block):
        """Check if price is within order block zone"""
        return order_block['zone_bottom'] <= price <= order_block['zone_top']

    def get_valid_obs(self, obs_dict, max_age=50):
        """
        Get valid order blocks that haven't expired

        Args:
            obs_dict: Dictionary with 'bullish' and 'bearish' order blocks
            max_age: Maximum age in candles

        Returns:
            Filtered order blocks
        """
        valid_bullish = [ob for ob in obs_dict['bullish'] if ob['age'] <= max_age]
        valid_bearish = [ob for ob in obs_dict['bearish'] if ob['age'] <= max_age]

        return {
            'bullish': valid_bullish,
            'bearish': valid_bearish
        }

    def mark_ob_touched(self, order_block, current_price):
        """Mark order block as touched if price entered the zone"""
        if self.is_price_in_ob(current_price, order_block):
            order_block['touched'] = True
            return True
        return False
