"""
Risk Management Module
Handles position sizing, risk calculation, and trade management
"""
import MetaTrader5 as mt5


class RiskManager:
    """Manage trading risk and position sizing"""

    def __init__(self, config):
        """
        Initialize Risk Manager

        Args:
            config: Configuration object
        """
        self.config = config
        self.risk_percent = config.RISK_PERCENT
        self.max_trades = config.MAX_TRADES

    def calculate_position_size(self, account_balance, entry_price, stop_loss, symbol_info):
        """
        Calculate position size based on risk percentage

        Args:
            account_balance: Account balance in account currency
            entry_price: Entry price
            stop_loss: Stop loss price
            symbol_info: MT5 symbol information

        Returns:
            Position size in lots
        """
        # Calculate risk amount
        risk_amount = account_balance * (self.risk_percent / 100)

        # Calculate pip risk
        pip_risk = abs(entry_price - stop_loss) / symbol_info.point

        # Calculate position size
        # For forex: lot_size = risk_amount / (pip_risk * pip_value)
        # pip_value depends on account currency and pair

        # Simplified calculation (assuming standard account)
        if symbol_info.trade_contract_size > 0:
            # Calculate the value per pip for 1 lot
            pip_value = symbol_info.trade_contract_size * symbol_info.point

            # Calculate position size
            if pip_risk > 0 and pip_value > 0:
                position_size = risk_amount / (pip_risk * pip_value)
            else:
                position_size = self.config.LOT_SIZE
        else:
            position_size = self.config.LOT_SIZE

        # Round to valid lot size
        position_size = self._round_lot_size(position_size, symbol_info)

        # Apply min/max lot size limits
        position_size = max(symbol_info.volume_min, position_size)
        position_size = min(symbol_info.volume_max, position_size)

        return position_size

    def _round_lot_size(self, lot_size, symbol_info):
        """Round lot size to valid step"""
        if symbol_info.volume_step > 0:
            lot_size = round(lot_size / symbol_info.volume_step) * symbol_info.volume_step
        return round(lot_size, 2)

    def can_open_trade(self, mt5_connection, symbol):
        """
        Check if a new trade can be opened

        Args:
            mt5_connection: MT5 connection object
            symbol: Trading symbol

        Returns:
            True if trade can be opened
        """
        # Check existing positions
        positions = mt5_connection.get_positions(symbol)

        if len(positions) >= self.max_trades:
            print(f"Maximum trades ({self.max_trades}) already open")
            return False

        return True

    def calculate_risk_reward(self, entry, stop_loss, take_profit):
        """
        Calculate risk-to-reward ratio

        Args:
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Risk-reward ratio
        """
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)

        if risk > 0:
            rr_ratio = reward / risk
        else:
            rr_ratio = 0

        return rr_ratio

    def validate_trade(self, signal, symbol_info, account_balance):
        """
        Validate trade before execution

        Args:
            signal: Trade signal
            symbol_info: Symbol information
            account_balance: Account balance

        Returns:
            True if trade is valid, False otherwise
        """
        # Check if signal exists
        if not signal:
            return False

        # Check entry, SL, TP are valid
        if not all([signal.get('entry'), signal.get('stop_loss'), signal.get('take_profit')]):
            print("Invalid signal: Missing entry, SL, or TP")
            return False

        # Check risk-reward ratio
        rr = self.calculate_risk_reward(
            signal['entry'],
            signal['stop_loss'],
            signal['take_profit']
        )

        if rr < 1.5:  # Minimum 1.5:1 RR
            print(f"Risk-reward ratio too low: {rr:.2f}")
            return False

        # Check stop loss distance
        sl_distance = abs(signal['entry'] - signal['stop_loss'])
        sl_pips = sl_distance / symbol_info.point

        # Ensure SL is not too tight (min 10 pips) or too wide (max 200 pips)
        if sl_pips < 10:
            print(f"Stop loss too tight: {sl_pips:.1f} pips")
            return False

        if sl_pips > 200:
            print(f"Stop loss too wide: {sl_pips:.1f} pips")
            return False

        # Calculate position size
        position_size = self.calculate_position_size(
            account_balance,
            signal['entry'],
            signal['stop_loss'],
            symbol_info
        )

        # Ensure position size is valid
        if position_size < symbol_info.volume_min:
            print(f"Position size too small: {position_size}")
            return False

        return True

    def get_trade_summary(self, signal, position_size, account_balance):
        """
        Get trade summary for logging

        Args:
            signal: Trade signal
            position_size: Calculated position size
            account_balance: Account balance

        Returns:
            Trade summary dictionary
        """
        risk_amount = account_balance * (self.risk_percent / 100)
        potential_profit = abs(signal['take_profit'] - signal['entry']) / abs(signal['entry'] - signal['stop_loss']) * risk_amount

        return {
            'type': signal['type'],
            'entry': signal['entry'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'position_size': position_size,
            'risk_amount': risk_amount,
            'potential_profit': potential_profit,
            'risk_reward': signal['risk_reward'],
            'risk_percent': self.risk_percent
        }

    def should_close_position(self, position, current_price):
        """
        Check if position should be closed (manual trailing stop, etc.)

        Args:
            position: Open position
            current_price: Current market price

        Returns:
            True if position should be closed
        """
        # This can be extended with trailing stop logic
        # For now, let MT5 handle SL/TP
        return False

    def get_max_risk_amount(self, account_balance):
        """
        Get maximum risk amount per trade

        Args:
            account_balance: Account balance

        Returns:
            Maximum risk amount
        """
        return account_balance * (self.risk_percent / 100)
