"""
MT5 SMC Trading Bot
Main entry point for the trading bot
"""
import time
import MetaTrader5 as mt5
from datetime import datetime
from config import Config
from mt5.connection import MT5Connection
from strategy.smc_strategy import SMCStrategy
from risk.management import RiskManager


class TradingBot:
    """Main trading bot class"""

    def __init__(self):
        """Initialize trading bot"""
        # Load configuration
        self.config = Config
        self.config.validate()

        # Initialize components
        self.mt5_conn = MT5Connection(
            login=self.config.MT5_LOGIN,
            password=self.config.MT5_PASSWORD,
            server=self.config.MT5_SERVER
        )

        self.strategy = SMCStrategy(self.config)
        self.risk_manager = RiskManager(self.config)

        # Bot state
        self.running = False
        self.last_signal_time = None

    def start(self):
        """Start the trading bot"""
        print("\n" + "="*60)
        print("MT5 SMC TRADING BOT")
        print("="*60)
        print(f"Symbol: {self.config.SYMBOL}")
        print(f"Timeframe: {self.config.TIMEFRAME}")
        print(f"Risk: {self.config.RISK_PERCENT}%")
        print("="*60 + "\n")

        # Connect to MT5
        if not self.mt5_conn.connect():
            print("Failed to connect to MT5. Exiting.")
            return

        print("Connected to MT5 successfully!\n")

        # Get account info
        account_info = self.mt5_conn.get_account_info()
        if account_info:
            print(f"Account Balance: {account_info.balance} {account_info.currency}")
            print(f"Account Equity: {account_info.equity} {account_info.currency}\n")

        # Main trading loop
        self.running = True
        print("Bot started. Monitoring market...\n")

        try:
            while self.running:
                self.run_cycle()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        finally:
            self.stop()

    def run_cycle(self):
        """Run one trading cycle"""
        try:
            # Get current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Get symbol info
            symbol_info = self.mt5_conn.get_symbol_info(self.config.SYMBOL)
            if not symbol_info:
                print(f"Failed to get symbol info for {self.config.SYMBOL}")
                return

            # Get historical data
            timeframe = self.mt5_conn.get_timeframe_constant(self.config.TIMEFRAME)
            df = self.mt5_conn.get_bars(
                symbol=self.config.SYMBOL,
                timeframe=timeframe,
                count=500
            )

            if df is None or len(df) == 0:
                print("Failed to get market data")
                return

            # Analyze market
            signal = self.strategy.analyze(df, symbol_info)

            # Print analysis
            if signal:
                self.strategy.print_analysis(signal)

                # Check if we can trade
                if self._can_execute_trade(signal):
                    self._execute_trade(signal, symbol_info)
            else:
                # Print periodic status
                if int(time.time()) % 300 == 0:  # Every 5 minutes
                    print(f"[{current_time}] Monitoring {self.config.SYMBOL} - No signals")

            # Monitor open positions
            self._monitor_positions()

        except Exception as e:
            print(f"Error in trading cycle: {e}")
            import traceback
            traceback.print_exc()

    def _can_execute_trade(self, signal):
        """Check if trade can be executed"""
        # Avoid duplicate signals
        if self.last_signal_time and signal.get('time'):
            if signal['time'] == self.last_signal_time:
                return False

        # Check max trades
        if not self.risk_manager.can_open_trade(self.mt5_conn, self.config.SYMBOL):
            return False

        return True

    def _execute_trade(self, signal, symbol_info):
        """Execute trade based on signal"""
        print("\n" + "="*60)
        print("EXECUTING TRADE")
        print("="*60)

        # Get account balance
        account_info = self.mt5_conn.get_account_info()
        if not account_info:
            print("Failed to get account info")
            return

        account_balance = account_info.balance

        # Validate trade
        if not self.risk_manager.validate_trade(signal, symbol_info, account_balance):
            print("Trade validation failed")
            return

        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            account_balance=account_balance,
            entry_price=signal['entry'],
            stop_loss=signal['stop_loss'],
            symbol_info=symbol_info
        )

        # Get trade summary
        trade_summary = self.risk_manager.get_trade_summary(
            signal, position_size, account_balance
        )

        # Print trade details
        print(f"\nTrade Details:")
        print(f"  Type: {trade_summary['type']}")
        print(f"  Entry: {trade_summary['entry']:.5f}")
        print(f"  Stop Loss: {trade_summary['stop_loss']:.5f}")
        print(f"  Take Profit: {trade_summary['take_profit']:.5f}")
        print(f"  Position Size: {trade_summary['position_size']:.2f} lots")
        print(f"  Risk Amount: ${trade_summary['risk_amount']:.2f}")
        print(f"  Potential Profit: ${trade_summary['potential_profit']:.2f}")
        print(f"  Risk/Reward: {trade_summary['risk_reward']:.1f}:1")

        # Place order
        order_type = mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL

        result = self.mt5_conn.place_order(
            symbol=self.config.SYMBOL,
            order_type=order_type,
            volume=position_size,
            price=None,  # Market order
            sl=signal['stop_loss'],
            tp=signal['take_profit'],
            comment="SMC Bot"
        )

        if result:
            print(f"\nTrade executed successfully!")
            print(f"Order ID: {result.order}")
            self.last_signal_time = signal.get('time')
        else:
            print("\nFailed to execute trade")

        print("="*60 + "\n")

    def _monitor_positions(self):
        """Monitor open positions"""
        positions = self.mt5_conn.get_positions(self.config.SYMBOL)

        if positions and len(positions) > 0:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{current_time}] Open Positions: {len(positions)}")

            for pos in positions:
                profit = pos.profit
                pips = pos.profit / (pos.volume * 10)  # Approximate

                print(f"  Ticket: {pos.ticket} | Type: {'BUY' if pos.type == 0 else 'SELL'} | "
                      f"Volume: {pos.volume} | Profit: ${profit:.2f} ({pips:.1f} pips)")

    def stop(self):
        """Stop the trading bot"""
        print("\nStopping bot...")
        self.running = False
        self.mt5_conn.disconnect()
        print("Bot stopped successfully")


def main():
    """Main entry point"""
    bot = TradingBot()
    bot.start()


if __name__ == "__main__":
    main()
