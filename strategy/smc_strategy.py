"""
SMC Trading Strategy
Combines Order Blocks, Liquidity, and Fair Value Gaps for trade signals
"""
from strategy.order_blocks import OrderBlockDetector
from strategy.liquidity import LiquidityDetector
from strategy.fvg import FVGDetector
from strategy.bos import BOSDetector
import pandas as pd


class SMCStrategy:
    """
    Main SMC Trading Strategy

    Strategy Logic:
    1. Identify Liquidity Pools (swing highs/lows)
    2. Wait for Liquidity Sweep (false breakout)
    3. Enter at Order Block or FVG after sweep
    4. Confirm with Break of Structure (BOS)
    """

    def __init__(self, config):
        """Initialize SMC strategy with configuration"""
        self.config = config

        # Initialize detectors
        self.ob_detector = OrderBlockDetector(
            min_body_percent=config.OB_MIN_BODY_PERCENT,
            lookback=config.OB_LOOKBACK_CANDLES
        )

        self.liq_detector = LiquidityDetector(
            lookback=config.LIQUIDITY_LOOKBACK,
            min_touches=config.LIQUIDITY_MIN_TOUCHES
        )

        self.fvg_detector = FVGDetector(
            min_size_pips=config.FVG_MIN_SIZE_PIPS,
            max_age=config.FVG_MAX_AGE_CANDLES
        )

        self.bos_detector = BOSDetector(
            confirmation_candles=config.BOS_CONFIRMATION_CANDLES
        )

    def analyze(self, df, symbol_info):
        """
        Analyze market and generate trading signals

        Args:
            df: DataFrame with OHLCV data
            symbol_info: MT5 symbol information

        Returns:
            Trading signal or None
        """
        if len(df) < 100:
            print("Insufficient data for analysis")
            return None

        # Get pip value
        pip_value = symbol_info.point * 10 if symbol_info.digits == 5 else symbol_info.point

        # 1. Detect all SMC components
        order_blocks = self.ob_detector.detect_order_blocks(df)
        liquidity_pools = self.liq_detector.find_liquidity_pools(df)
        fvgs = self.fvg_detector.detect_fvgs(df, pip_value)
        bos = self.bos_detector.detect_bos(df)

        # 2. Check for liquidity sweeps
        liquidity_sweeps = self.liq_detector.detect_liquidity_sweep(df, liquidity_pools)

        # 3. Get valid (unexpired) zones
        valid_obs = self.ob_detector.get_valid_obs(order_blocks)
        valid_fvgs = self.fvg_detector.get_valid_fvgs(fvgs)

        # Current price
        current_price = df.iloc[-1]['close']
        current_time = df.iloc[-1]['time']

        # 4. Check for trade setups
        signal = self._check_trade_setup(
            current_price=current_price,
            current_time=current_time,
            liquidity_sweeps=liquidity_sweeps,
            order_blocks=valid_obs,
            fvgs=valid_fvgs,
            bos=bos,
            symbol_info=symbol_info
        )

        # 5. Add analysis details to signal
        if signal:
            signal['analysis'] = {
                'order_blocks': order_blocks,
                'liquidity_pools': liquidity_pools,
                'fvgs': fvgs,
                'bos': bos,
                'market_structure': bos['trend'] if bos else 'unknown'
            }

        return signal

    def _check_trade_setup(self, current_price, current_time, liquidity_sweeps,
                           order_blocks, fvgs, bos, symbol_info):
        """
        Check for valid trade setup based on SMC criteria

        Perfect Setup:
        1. Liquidity sweep occurs
        2. Price returns to Order Block or FVG
        3. BOS confirms the direction
        """
        if not liquidity_sweeps:
            return None

        for sweep in liquidity_sweeps:
            # Bullish setup: Sell-side liquidity swept (low taken out)
            if sweep['direction'] == 'bullish':
                # Check for bullish order block or FVG entry
                entry_zone = self._find_bullish_entry_zone(
                    current_price, order_blocks, fvgs
                )

                if entry_zone:
                    # Confirm with bullish BOS
                    if bos and bos.get('bullish_bos'):
                        signal = self._create_buy_signal(
                            current_price=current_price,
                            current_time=current_time,
                            entry_zone=entry_zone,
                            sweep=sweep,
                            bos=bos['bullish_bos'],
                            symbol_info=symbol_info
                        )
                        return signal

            # Bearish setup: Buy-side liquidity swept (high taken out)
            elif sweep['direction'] == 'bearish':
                # Check for bearish order block or FVG entry
                entry_zone = self._find_bearish_entry_zone(
                    current_price, order_blocks, fvgs
                )

                if entry_zone:
                    # Confirm with bearish BOS
                    if bos and bos.get('bearish_bos'):
                        signal = self._create_sell_signal(
                            current_price=current_price,
                            current_time=current_time,
                            entry_zone=entry_zone,
                            sweep=sweep,
                            bos=bos['bearish_bos'],
                            symbol_info=symbol_info
                        )
                        return signal

        return None

    def _find_bullish_entry_zone(self, current_price, order_blocks, fvgs):
        """Find bullish entry zone (Order Block or FVG below current price)"""
        # Check bullish order blocks
        bullish_obs = order_blocks.get('bullish', [])
        for ob in bullish_obs:
            # OB should be below current price for retracement entry
            if ob['zone_bottom'] < current_price <= ob['zone_top']:
                return {'type': 'order_block', 'zone': ob}

        # Check bullish FVGs
        bullish_fvgs = fvgs.get('bullish', [])
        for fvg in bullish_fvgs:
            # FVG should be below current price
            if fvg['bottom'] < current_price <= fvg['top'] and not fvg['filled']:
                return {'type': 'fvg', 'zone': fvg}

        return None

    def _find_bearish_entry_zone(self, current_price, order_blocks, fvgs):
        """Find bearish entry zone (Order Block or FVG above current price)"""
        # Check bearish order blocks
        bearish_obs = order_blocks.get('bearish', [])
        for ob in bearish_obs:
            # OB should be above current price for retracement entry
            if ob['zone_bottom'] <= current_price < ob['zone_top']:
                return {'type': 'order_block', 'zone': ob}

        # Check bearish FVGs
        bearish_fvgs = fvgs.get('bearish', [])
        for fvg in bearish_fvgs:
            # FVG should be above current price
            if fvg['bottom'] <= current_price < fvg['top'] and not fvg['filled']:
                return {'type': 'fvg', 'zone': fvg}

        return None

    def _create_buy_signal(self, current_price, current_time, entry_zone,
                          sweep, bos, symbol_info):
        """Create buy signal with entry, SL, and TP"""
        zone = entry_zone['zone']

        # Entry: Current price (in the zone)
        entry = current_price

        # Stop Loss: Below the order block/FVG
        if entry_zone['type'] == 'order_block':
            sl = zone['zone_bottom'] - (10 * symbol_info.point)  # 10 pips buffer
        else:  # FVG
            sl = zone['bottom'] - (10 * symbol_info.point)

        # Take Profit: Risk-reward ratio of 2:1 or 3:1
        risk = entry - sl
        tp = entry + (risk * 2)  # 2:1 RR

        return {
            'type': 'BUY',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'time': current_time,
            'entry_zone_type': entry_zone['type'],
            'entry_zone': zone,
            'liquidity_sweep': sweep,
            'bos': bos,
            'risk_reward': 2.0,
            'reason': f"Bullish setup: Liquidity sweep + {entry_zone['type']} + BOS confirmation"
        }

    def _create_sell_signal(self, current_price, current_time, entry_zone,
                           sweep, bos, symbol_info):
        """Create sell signal with entry, SL, and TP"""
        zone = entry_zone['zone']

        # Entry: Current price (in the zone)
        entry = current_price

        # Stop Loss: Above the order block/FVG
        if entry_zone['type'] == 'order_block':
            sl = zone['zone_top'] + (10 * symbol_info.point)  # 10 pips buffer
        else:  # FVG
            sl = zone['top'] + (10 * symbol_info.point)

        # Take Profit: Risk-reward ratio of 2:1 or 3:1
        risk = sl - entry
        tp = entry - (risk * 2)  # 2:1 RR

        return {
            'type': 'SELL',
            'entry': entry,
            'stop_loss': sl,
            'take_profit': tp,
            'time': current_time,
            'entry_zone_type': entry_zone['type'],
            'entry_zone': zone,
            'liquidity_sweep': sweep,
            'bos': bos,
            'risk_reward': 2.0,
            'reason': f"Bearish setup: Liquidity sweep + {entry_zone['type']} + BOS confirmation"
        }

    def print_analysis(self, analysis):
        """Print detailed analysis"""
        if not analysis:
            return

        print("\n" + "="*60)
        print("SMC MARKET ANALYSIS")
        print("="*60)

        if 'analysis' in analysis:
            data = analysis['analysis']

            print(f"\nMarket Structure: {data['market_structure'].upper()}")

            # Order Blocks
            obs = data['order_blocks']
            print(f"\nOrder Blocks:")
            print(f"  Bullish: {len(obs['bullish'])}")
            print(f"  Bearish: {len(obs['bearish'])}")

            # Liquidity Pools
            liq = data['liquidity_pools']
            print(f"\nLiquidity Pools:")
            print(f"  Buy-side: {len(liq['buy_side'])}")
            print(f"  Sell-side: {len(liq['sell_side'])}")

            # FVGs
            fvgs = data['fvgs']
            print(f"\nFair Value Gaps:")
            print(f"  Bullish: {len(fvgs['bullish'])}")
            print(f"  Bearish: {len(fvgs['bearish'])}")

            # BOS
            bos = data['bos']
            if bos:
                if bos.get('bullish_bos'):
                    print(f"\nBullish BOS Detected!")
                if bos.get('bearish_bos'):
                    print(f"\nBearish BOS Detected!")

        # Signal
        if analysis.get('type'):
            print("\n" + "="*60)
            print(f"TRADE SIGNAL: {analysis['type']}")
            print("="*60)
            print(f"Entry: {analysis['entry']:.5f}")
            print(f"Stop Loss: {analysis['stop_loss']:.5f}")
            print(f"Take Profit: {analysis['take_profit']:.5f}")
            print(f"Risk/Reward: {analysis['risk_reward']}:1")
            print(f"Reason: {analysis['reason']}")
            print("="*60 + "\n")
