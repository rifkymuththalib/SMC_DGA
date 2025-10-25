"""
MT5 Connection Handler
Manages connection to MetaTrader 5 platform and trading operations
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import pytz


class MT5Connection:
    """Handle MT5 connection and trading operations"""

    def __init__(self, login, password, server):
        self.login = login
        self.password = password
        self.server = server
        self.connected = False

    def connect(self):
        """Establish connection to MT5"""
        if not mt5.initialize():
            print(f"MT5 initialization failed: {mt5.last_error()}")
            return False

        if not mt5.login(self.login, password=self.password, server=self.server):
            print(f"MT5 login failed: {mt5.last_error()}")
            mt5.shutdown()
            return False

        print(f"Connected to MT5 account #{self.login}")
        self.connected = True
        return True

    def disconnect(self):
        """Close MT5 connection"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from MT5")

    def get_bars(self, symbol, timeframe, count=500):
        """
        Get historical price data

        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: MT5 timeframe constant
            count: Number of bars to retrieve

        Returns:
            pandas DataFrame with OHLCV data
        """
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        # Get bars
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)

        if rates is None or len(rates) == 0:
            print(f"Failed to get bars: {mt5.last_error()}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')

        return df

    def get_symbol_info(self, symbol):
        """Get symbol information"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"Failed to get symbol info: {mt5.last_error()}")
            return None

        return info

    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        account_info = mt5.account_info()
        if account_info is None:
            print(f"Failed to get account info: {mt5.last_error()}")
            return None

        return account_info

    def get_positions(self, symbol=None):
        """Get open positions"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()

        if positions is None:
            print(f"Failed to get positions: {mt5.last_error()}")
            return []

        return list(positions)

    def place_order(self, symbol, order_type, volume, price=None, sl=None, tp=None, comment="SMC Bot"):
        """
        Place a trading order

        Args:
            symbol: Trading symbol
            order_type: ORDER_TYPE_BUY or ORDER_TYPE_SELL
            volume: Lot size
            price: Entry price (None for market order)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment

        Returns:
            Order result
        """
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        symbol_info = self.get_symbol_info(symbol)
        if symbol_info is None:
            return None

        # Prepare request
        if price is None:
            # Market order
            if order_type == mt5.ORDER_TYPE_BUY:
                price = mt5.symbol_info_tick(symbol).ask
                trade_type = mt5.ORDER_TYPE_BUY
            else:
                price = mt5.symbol_info_tick(symbol).bid
                trade_type = mt5.ORDER_TYPE_SELL

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": trade_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
        else:
            # Pending order
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }

        # Add SL and TP if provided
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp

        # Send order
        result = mt5.order_send(request)

        if result is None:
            print(f"Order failed: {mt5.last_error()}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order failed: {result.comment}")
            return None

        print(f"Order placed successfully: {result.order}")
        return result

    def close_position(self, position):
        """Close an open position"""
        if not self.connected:
            raise ConnectionError("Not connected to MT5")

        symbol = position.symbol
        volume = position.volume
        position_type = position.type

        # Determine close order type
        if position_type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = mt5.symbol_info_tick(symbol).bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(symbol).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close position",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position: {mt5.last_error()}")
            return False

        print(f"Position closed: {position.ticket}")
        return True

    def get_timeframe_constant(self, timeframe_str):
        """Convert timeframe string to MT5 constant"""
        timeframes = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        return timeframes.get(timeframe_str, mt5.TIMEFRAME_H1)
