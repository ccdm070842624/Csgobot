#!/usr/bin/env python3
"""
CS:GO Trading Bot - Enhanced Version
Advanced market analysis with ML predictions and backtesting
"""

import argparse
import sys
import time
from pathlib import Path

# Import all modules
from config import get_config
from logger import setup_logger_from_config
from notifications import NotificationSystem
from export import ReportExporter
from backtesting import Backtester

# Import from original bot (we'll keep classes in csgo_trading_bot.py)
from csgo_trading_bot import (
    CSGOFloatParser,
    PriceDatabase,
    PriceAnalyzer,
    collect_market_data
)


class EnhancedTradingBot:
    """Enhanced trading bot with all new features"""

    def __init__(self, config_path=None):
        """
        Initialize enhanced trading bot

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = get_config(config_path)

        # Setup logger
        self.logger = setup_logger_from_config(self.config)
        self.logger.info("Initializing Enhanced CS:GO Trading Bot")

        # Initialize components
        self.parser = CSGOFloatParser(api_key=self.config.api_key)
        self.analyzer = PriceAnalyzer(db_name=self.config.db_name)
        self.notifier = NotificationSystem(self.config)
        self.exporter = ReportExporter(self.config)
        self.backtester = Backtester(self.analyzer, self.config)

        self.logger.info("All components initialized successfully")

    def collect_data(self, items=None):
        """
        Collect market data

        Args:
            items: List of items to track (uses config if None)
        """
        items = items or self.config.items_to_track

        if not items:
            self.logger.error("No items configured to track")
            return

        self.logger.info(f"Starting data collection for {len(items)} items")

        db = PriceDatabase(self.config.db_name)
        success_count = 0
        fail_count = 0

        for item_name in items:
            self.logger.info(f"Collecting data for: {item_name}")

            listings = self.parser.get_item_listings(
                item_name,
                limit=self.config.get('data_collection.listings_per_item', 20)
            )

            if listings is None:
                self.logger.warning(f"Failed to get listings for {item_name}")
                fail_count += 1
                time.sleep(self.config.get('api.csgofloat.rate_limit_delay', 5))
                continue

            if not listings:
                self.logger.warning(f"No listings found for {item_name}")
                fail_count += 1
                time.sleep(3)
                continue

            # Process listings
            prices = []
            saved_count = 0

            for listing in listings:
                try:
                    price_raw = listing.get('price', 0)
                    price = price_raw / 100 if price_raw > 1000 else price_raw

                    if price <= 0:
                        continue

                    parsed = {
                        'item_name': item_name,
                        'price': price,
                        'float_value': listing.get('float_value') or listing.get('float'),
                        'paint_seed': listing.get('paint_seed') or listing.get('paintseed'),
                        'source': 'csgofloat'
                    }

                    if db.save_listing(parsed):
                        prices.append(price)
                        saved_count += 1

                except Exception as e:
                    self.logger.debug(f"Error processing listing: {e}")
                    continue

            # Save statistics
            if prices:
                stats = {
                    'avg_price': sum(prices) / len(prices),
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'volume': len(prices)
                }

                if db.save_market_stats(item_name, stats):
                    self.logger.data_collected(item_name, saved_count, stats['avg_price'])
                    success_count += 1
            else:
                fail_count += 1

            time.sleep(self.config.get('api.csgofloat.rate_limit_delay', 5))

        db.close()

        self.logger.info(f"Data collection complete: {success_count} successful, {fail_count} failed")

    def analyze(self, items=None, export_results=True):
        """
        Analyze items and generate recommendations

        Args:
            items: List of items to analyze (uses config if None)
            export_results: Whether to export results

        Returns:
            Analysis results list
        """
        items = items or self.config.items_to_track

        if not items:
            self.logger.error("No items configured to analyze")
            return []

        self.logger.info(f"Analyzing {len(items)} items")

        results = []
        buy_signals = 0
        sell_signals = 0

        for item_name in items:
            self.logger.info(f"Analyzing: {item_name}")

            rec = self.analyzer.get_buy_recommendation(item_name)

            if rec['recommendation'] == 'BUY':
                buy_signals += 1
            elif rec['recommendation'] == 'SELL':
                sell_signals += 1

            # Send notification if meets criteria
            if rec.get('current_price'):
                self.notifier.send_trade_signal(
                    item=item_name,
                    action=rec['recommendation'],
                    confidence=rec['confidence'],
                    current_price=rec['current_price'],
                    predicted_price=rec.get('predicted_price'),
                    reasons=rec.get('reasons')
                )

                # Log trade signal
                if rec['recommendation'] in ['BUY', 'SELL']:
                    self.logger.trade_signal(
                        item=item_name,
                        action=rec['recommendation'],
                        confidence=rec['confidence'],
                        price=rec['current_price']
                    )

            # Log prediction
            if rec.get('predicted_price') and rec.get('current_price'):
                change_pct = ((rec['predicted_price'] - rec['current_price']) /
                             rec['current_price'] * 100)
                self.logger.prediction(
                    item=item_name,
                    current=rec['current_price'],
                    predicted=rec['predicted_price'],
                    change_pct=change_pct
                )

            results.append({
                'item': item_name,
                'recommendation': rec['recommendation'],
                'confidence': rec['confidence'],
                'data': rec
            })

        # Send summary
        self.notifier.send_summary(len(items), buy_signals, sell_signals)

        # Export results
        if export_results and self.config.get('reporting.export_enabled'):
            self.exporter.export_analysis_results(results)

        return results

    def generate_charts(self, items=None, days=30):
        """
        Generate price history charts

        Args:
            items: List of items (uses config if None)
            days: Number of days of history
        """
        items = items or self.config.items_to_track

        if not items:
            self.logger.warning("No items to generate charts for")
            return

        self.logger.info(f"Generating charts for {len(items)} items")

        charts_created = 0
        save_path = self.config.get('reporting.charts.save_path', 'charts/')

        for item in items:
            safe_name = item.replace(' ', '_').replace('|', '-')
            chart_file = f"{save_path}{safe_name}_history.png"

            if self.analyzer.plot_price_history(item, days=days, save_path=chart_file):
                charts_created += 1

        self.logger.info(f"Generated {charts_created} charts")

    def run_backtest(self, items=None, days=30, export_results=True):
        """
        Run backtesting simulation

        Args:
            items: List of items to backtest (uses config if None)
            days: Number of days to simulate
            export_results: Whether to export results

        Returns:
            Backtest results
        """
        items = items or self.config.items_to_track

        if not items:
            self.logger.error("No items configured for backtesting")
            return None

        self.logger.info(f"Starting backtest for {len(items)} items over {days} days")

        results = self.backtester.run_backtest(items, days=days)

        # Log results
        self.logger.backtesting_result(
            profit=results['profit_loss'],
            roi=results['roi'],
            trades=results['total_trades']
        )

        # Export results
        if export_results and self.config.get('reporting.export_enabled'):
            self.exporter.export_backtest_results(results)

        return results

    def run_full_analysis(self):
        """Run complete analysis pipeline"""
        self.logger.info("=" * 80)
        self.logger.info("Starting FULL ANALYSIS pipeline")
        self.logger.info("=" * 80)

        # Step 1: Collect data
        self.logger.info("\n📥 Step 1/4: Collecting market data")
        self.collect_data()

        # Step 2: Analyze
        self.logger.info("\n📊 Step 2/4: Analyzing items")
        results = self.analyze()

        # Step 3: Generate charts
        if self.config.get('reporting.charts.save_enabled'):
            self.logger.info("\n📈 Step 3/4: Generating charts")
            self.generate_charts(days=14)

        # Step 4: Backtest (if enabled)
        if self.config.get('backtesting.enabled'):
            self.logger.info("\n🔄 Step 4/4: Running backtest")
            self.run_backtest(days=30)

        self.logger.info("\n" + "=" * 80)
        self.logger.info("✅ FULL ANALYSIS complete!")
        self.logger.info("=" * 80)

        return results

    def get_top_opportunities(self, results=None):
        """
        Get and display top trading opportunities

        Args:
            results: Analysis results (runs new analysis if None)

        Returns:
            List of top opportunities
        """
        if results is None:
            results = self.analyze(export_results=False)

        buy_opportunities = [
            r for r in results
            if r['recommendation'] == 'BUY' and
            r['confidence'] >= self.config.min_buy_confidence
        ]

        buy_opportunities.sort(key=lambda x: x['confidence'], reverse=True)

        self.logger.info("\n🎯 TOP TRADING OPPORTUNITIES\n")

        if not buy_opportunities:
            self.logger.info("No strong buy signals found")
            return []

        for i, opp in enumerate(buy_opportunities[:5], 1):
            print(f"{i}. {opp['item']}")
            print(f"   Confidence: {opp['confidence']:.0f}%")

            if (opp['data'].get('predicted_price') and
                opp['data'].get('current_price')):
                potential = opp['data']['predicted_price'] - opp['data']['current_price']
                potential_pct = (potential / opp['data']['current_price']) * 100
                print(f"   Potential: +${potential:.2f} (+{potential_pct:.1f}%)")

            print()

        return buy_opportunities


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='CS:GO Trading Bot - Advanced Market Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full analysis
  python bot.py --full

  # Collect data only
  python bot.py --collect

  # Analyze with custom config
  python bot.py --analyze --config my_config.yaml

  # Run backtest
  python bot.py --backtest --days 60

  # Generate charts
  python bot.py --charts --days 30
        """
    )

    parser.add_argument(
        '--config', '-c',
        help='Path to configuration file',
        default=None
    )

    parser.add_argument(
        '--full', '-f',
        action='store_true',
        help='Run full analysis pipeline (collect, analyze, chart, backtest)'
    )

    parser.add_argument(
        '--collect', '-C',
        action='store_true',
        help='Collect market data only'
    )

    parser.add_argument(
        '--analyze', '-a',
        action='store_true',
        help='Analyze collected data and generate recommendations'
    )

    parser.add_argument(
        '--backtest', '-b',
        action='store_true',
        help='Run backtesting simulation'
    )

    parser.add_argument(
        '--charts', '-p',
        action='store_true',
        help='Generate price history charts'
    )

    parser.add_argument(
        '--days', '-d',
        type=int,
        default=30,
        help='Number of days for analysis/charts/backtest (default: 30)'
    )

    parser.add_argument(
        '--items', '-i',
        nargs='+',
        help='Specific items to analyze (overrides config)'
    )

    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (overrides config)'
    )

    args = parser.parse_args()

    # If no action specified, show help
    if not any([args.full, args.collect, args.analyze, args.backtest, args.charts]):
        parser.print_help()
        sys.exit(0)

    try:
        # Initialize bot
        bot = EnhancedTradingBot(config_path=args.config)

        # Override log level if specified
        if args.log_level:
            bot.config.set('logging.level', args.log_level)

        # Run requested actions
        if args.full:
            bot.run_full_analysis()

        else:
            if args.collect:
                bot.collect_data(items=args.items)

            if args.analyze:
                results = bot.analyze(items=args.items)
                bot.get_top_opportunities(results)

            if args.charts:
                bot.generate_charts(items=args.items, days=args.days)

            if args.backtest:
                bot.run_backtest(items=args.items, days=args.days)

    except KeyboardInterrupt:
        print("\n\n⚠️  Bot stopped by user")
        sys.exit(0)

    except Exception as e:
        print(f"\n\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
