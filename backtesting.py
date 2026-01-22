"""Backtesting system for trading strategies"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple


class Portfolio:
    """Simulated trading portfolio"""

    def __init__(self, initial_balance: float, transaction_fee: float = 0.05):
        """
        Initialize portfolio

        Args:
            initial_balance: Starting cash balance
            transaction_fee: Transaction fee as decimal (0.05 = 5%)
        """
        self.initial_balance = initial_balance
        self.cash = initial_balance
        self.transaction_fee = transaction_fee
        self.holdings: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.equity_history: List[Tuple[datetime, float]] = []

    def buy(self, item: str, price: float, quantity: int = 1, timestamp: datetime = None):
        """
        Buy an item

        Args:
            item: Item name
            price: Purchase price
            quantity: Quantity to buy
            timestamp: Transaction timestamp

        Returns:
            True if successful, False otherwise
        """
        total_cost = price * quantity
        fee = total_cost * self.transaction_fee
        total_with_fee = total_cost + fee

        if self.cash < total_with_fee:
            return False

        self.cash -= total_with_fee

        if item in self.holdings:
            # Average the price
            old_qty = self.holdings[item]['quantity']
            old_price = self.holdings[item]['avg_price']
            new_qty = old_qty + quantity
            new_avg_price = ((old_price * old_qty) + (price * quantity)) / new_qty

            self.holdings[item]['quantity'] = new_qty
            self.holdings[item]['avg_price'] = new_avg_price
        else:
            self.holdings[item] = {
                'quantity': quantity,
                'avg_price': price,
                'purchase_date': timestamp or datetime.now()
            }

        self.trade_history.append({
            'timestamp': timestamp or datetime.now(),
            'action': 'BUY',
            'item': item,
            'price': price,
            'quantity': quantity,
            'fee': fee,
            'total': total_with_fee
        })

        return True

    def sell(self, item: str, price: float, quantity: int = 1, timestamp: datetime = None):
        """
        Sell an item

        Args:
            item: Item name
            price: Sell price
            quantity: Quantity to sell
            timestamp: Transaction timestamp

        Returns:
            True if successful, False otherwise
        """
        if item not in self.holdings or self.holdings[item]['quantity'] < quantity:
            return False

        total_revenue = price * quantity
        fee = total_revenue * self.transaction_fee
        net_revenue = total_revenue - fee

        self.cash += net_revenue

        self.holdings[item]['quantity'] -= quantity

        # Remove from holdings if quantity is 0
        if self.holdings[item]['quantity'] == 0:
            del self.holdings[item]

        self.trade_history.append({
            'timestamp': timestamp or datetime.now(),
            'action': 'SELL',
            'item': item,
            'price': price,
            'quantity': quantity,
            'fee': fee,
            'total': net_revenue
        })

        return True

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value

        Args:
            current_prices: Dictionary of current item prices

        Returns:
            Total portfolio value (cash + holdings)
        """
        holdings_value = 0

        for item, holding in self.holdings.items():
            if item in current_prices:
                holdings_value += current_prices[item] * holding['quantity']

        return self.cash + holdings_value

    def get_profit_loss(self, current_prices: Dict[str, float]) -> float:
        """Calculate profit/loss"""
        return self.get_portfolio_value(current_prices) - self.initial_balance

    def get_roi(self, current_prices: Dict[str, float]) -> float:
        """Calculate ROI percentage"""
        return (self.get_profit_loss(current_prices) / self.initial_balance) * 100


class Backtester:
    """Backtest trading strategies on historical data"""

    def __init__(self, analyzer, config):
        """
        Initialize backtester

        Args:
            analyzer: PriceAnalyzer instance
            config: Configuration instance
        """
        self.analyzer = analyzer
        self.config = config

        self.initial_balance = config.get('backtesting.initial_balance', 100.0)
        self.transaction_fee = config.get('backtesting.transaction_fee', 0.05)
        self.min_profit_threshold = config.get('backtesting.min_profit_threshold', 0.10)

    def run_backtest(
        self,
        items: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Run backtest simulation

        Args:
            items: List of items to trade
            start_date: Start date for backtesting
            end_date: End date for backtesting
            days: Number of days if dates not specified

        Returns:
            Backtest results dictionary
        """
        print("🔄 Running backtest simulation...")

        portfolio = Portfolio(self.initial_balance, self.transaction_fee)

        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=days)

        # Simulate trading
        trades_executed = 0
        buy_signals = 0
        sell_signals = 0

        for item in items:
            # Get recommendation
            rec = self.analyzer.get_buy_recommendation(item)

            if not rec or rec.get('confidence', 0) < 50:
                continue

            action = rec['recommendation']
            confidence = rec['confidence']
            current_price = rec.get('current_price')

            if not current_price or current_price <= 0:
                continue

            # Execute trades based on recommendations
            if action == 'BUY' and confidence >= self.config.get('strategy.min_buy_confidence', 50):
                # Buy signal
                if portfolio.buy(item, current_price):
                    trades_executed += 1
                    buy_signals += 1

            elif action == 'SELL' and item in portfolio.holdings:
                # Sell signal
                holding = portfolio.holdings[item]
                profit_pct = ((current_price - holding['avg_price']) / holding['avg_price'])

                # Only sell if profit meets threshold or confidence is high
                if profit_pct >= self.min_profit_threshold or confidence >= 80:
                    if portfolio.sell(item, current_price, holding['quantity']):
                        trades_executed += 1
                        sell_signals += 1

        # Calculate final results
        current_prices = {}
        for item in items:
            df = self.analyzer.get_item_dataframe(item, 7)
            if df is not None and len(df) > 0:
                current_prices[item] = df['price'].iloc[-1]

        final_value = portfolio.get_portfolio_value(current_prices)
        profit_loss = portfolio.get_profit_loss(current_prices)
        roi = portfolio.get_roi(current_prices)

        # Calculate metrics
        win_trades = sum(1 for t in portfolio.trade_history
                        if t['action'] == 'SELL' and t['total'] > 0)
        total_trades = len([t for t in portfolio.trade_history if t['action'] == 'SELL'])
        win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0

        results = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'initial_balance': self.initial_balance,
            'final_value': final_value,
            'profit_loss': profit_loss,
            'roi': roi,
            'total_trades': trades_executed,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'win_rate': win_rate,
            'remaining_cash': portfolio.cash,
            'holdings': {
                item: {
                    'quantity': holding['quantity'],
                    'avg_price': holding['avg_price'],
                    'current_value': current_prices.get(item, 0) * holding['quantity']
                }
                for item, holding in portfolio.holdings.items()
            },
            'trade_history': portfolio.trade_history
        }

        self._print_backtest_results(results)

        return results

    def _print_backtest_results(self, results: Dict[str, Any]):
        """Print backtest results to console"""
        print("\n" + "=" * 80)
        print("📊 BACKTEST RESULTS")
        print("=" * 80)

        print(f"\nPeriod: {results['start_date']} to {results['end_date']}")
        print(f"\nInitial Balance:  ${results['initial_balance']:.2f}")
        print(f"Final Value:      ${results['final_value']:.2f}")

        profit_loss = results['profit_loss']
        emoji = "💰" if profit_loss > 0 else "💸"
        print(f"{emoji} Profit/Loss:     ${profit_loss:+.2f}")

        roi = results['roi']
        print(f"ROI:              {roi:+.1f}%")

        print(f"\nTotal Trades:     {results['total_trades']}")
        print(f"Buy Signals:      {results['buy_signals']}")
        print(f"Sell Signals:     {results['sell_signals']}")
        print(f"Win Rate:         {results['win_rate']:.1f}%")

        print(f"\nRemaining Cash:   ${results['remaining_cash']:.2f}")

        if results['holdings']:
            print("\nCurrent Holdings:")
            for item, holding in results['holdings'].items():
                print(f"  • {item}")
                print(f"    Quantity: {holding['quantity']}")
                print(f"    Avg Price: ${holding['avg_price']:.2f}")
                print(f"    Current Value: ${holding['current_value']:.2f}")

        print("=" * 80 + "\n")

    def compare_strategies(
        self,
        items: List[str],
        confidence_thresholds: List[int] = [50, 60, 70, 80],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare different confidence threshold strategies

        Args:
            items: List of items to trade
            confidence_thresholds: List of confidence thresholds to test
            days: Number of days to backtest

        Returns:
            Comparison results
        """
        print("🔬 Comparing trading strategies...")

        results = {}

        for threshold in confidence_thresholds:
            # Temporarily update config
            original_threshold = self.config.get('strategy.min_buy_confidence')
            self.config.set('strategy.min_buy_confidence', threshold)

            # Run backtest
            backtest_result = self.run_backtest(items, days=days)

            results[f'threshold_{threshold}'] = {
                'threshold': threshold,
                'roi': backtest_result['roi'],
                'total_trades': backtest_result['total_trades'],
                'win_rate': backtest_result['win_rate']
            }

            # Restore original threshold
            self.config.set('strategy.min_buy_confidence', original_threshold)

        # Print comparison
        print("\n" + "=" * 80)
        print("🏆 STRATEGY COMPARISON")
        print("=" * 80)
        print(f"{'Threshold':<15} {'ROI':<15} {'Trades':<15} {'Win Rate':<15}")
        print("-" * 80)

        for key, result in results.items():
            print(f"{result['threshold']:<15} "
                  f"{result['roi']:>7.1f}%      "
                  f"{result['total_trades']:<15} "
                  f"{result['win_rate']:>7.1f}%")

        print("=" * 80 + "\n")

        return results
