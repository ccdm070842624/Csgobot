"""Export and reporting functionality for CS:GO Trading Bot"""
import os
import csv
import json
import html
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class ReportExporter:
    """Export trading data and analysis results"""

    def __init__(self, config):
        """
        Initialize exporter

        Args:
            config: Configuration instance
        """
        self.config = config
        self.export_path = config.get('reporting.export_path', 'reports/')
        self.export_formats = config.get('reporting.export_format', ['csv', 'json'])

        # Create export directory
        os.makedirs(self.export_path, exist_ok=True)

    def export_analysis_results(self, results: List[Dict[str, Any]], filename_prefix: str = 'analysis'):
        """
        Export analysis results to configured formats

        Args:
            results: List of analysis results
            filename_prefix: Prefix for output files
        """
        if not results:
            print("⚠️  No results to export")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export to CSV
        if 'csv' in self.export_formats:
            csv_file = os.path.join(self.export_path, f'{filename_prefix}_{timestamp}.csv')
            self._export_csv(results, csv_file)

        # Export to JSON
        if 'json' in self.export_formats:
            json_file = os.path.join(self.export_path, f'{filename_prefix}_{timestamp}.json')
            self._export_json(results, json_file)

        # Export to HTML
        if 'html' in self.export_formats:
            html_file = os.path.join(self.export_path, f'{filename_prefix}_{timestamp}.html')
            self._export_html(results, html_file)

    def _export_csv(self, results: List[Dict[str, Any]], filename: str):
        """Export results to CSV"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if not results:
                    return

                # Prepare flat data
                flat_results = []
                for r in results:
                    data = r.get('data', {})
                    flat_results.append({
                        'item': r.get('item'),
                        'recommendation': r.get('recommendation'),
                        'confidence': r.get('confidence'),
                        'current_price': data.get('current_price'),
                        'predicted_price': data.get('predicted_price'),
                        'expected_change_percent': data.get('expected_change_percent'),
                        'data_points': data.get('data_points'),
                        'reasons': ' | '.join(data.get('reasons', []))
                    })

                # BUG FIX #8: Additional safety check before accessing flat_results[0]
                if flat_results and len(flat_results) > 0:
                    writer = csv.DictWriter(f, fieldnames=flat_results[0].keys())
                    writer.writeheader()
                    writer.writerows(flat_results)

                    print(f"📄 CSV report exported: {filename}")

        except Exception as e:
            print(f"❌ Error exporting CSV: {e}")

    def _export_json(self, results: List[Dict[str, Any]], filename: str):
        """Export results to JSON"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'total_items': len(results),
                'results': results
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            print(f"📄 JSON report exported: {filename}")

        except Exception as e:
            print(f"❌ Error exporting JSON: {e}")

    def _export_html(self, results: List[Dict[str, Any]], filename: str):
        """Export results to HTML"""
        try:
            html_content = self._generate_html_report(results)

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"📄 HTML report exported: {filename}")

        except Exception as e:
            print(f"❌ Error exporting HTML: {e}")

    def _generate_html_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML report"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>CS:GO Trading Bot Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    border-radius: 5px;
                }}
                .summary {{
                    background-color: white;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background-color: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                th {{
                    background-color: #34495e;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                }}
                .buy {{ color: #28a745; font-weight: bold; }}
                .sell {{ color: #dc3545; font-weight: bold; }}
                .hold {{ color: #ffc107; font-weight: bold; }}
                .wait {{ color: #6c757d; font-weight: bold; }}
                .high-conf {{ background-color: #d4edda; }}
                .med-conf {{ background-color: #fff3cd; }}
                .low-conf {{ background-color: #f8d7da; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎮 CS:GO Trading Bot Analysis Report</h1>
                <p>Generated: {timestamp}</p>
            </div>

            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Total Items Analyzed:</strong> {len(results)}</p>
                <p><strong>Buy Signals:</strong> {sum(1 for r in results if r.get('recommendation') == 'BUY')}</p>
                <p><strong>Sell Signals:</strong> {sum(1 for r in results if r.get('recommendation') == 'SELL')}</p>
                <p><strong>Hold Signals:</strong> {sum(1 for r in results if r.get('recommendation') == 'HOLD')}</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Recommendation</th>
                        <th>Confidence</th>
                        <th>Current Price</th>
                        <th>Predicted Price</th>
                        <th>Expected Change</th>
                    </tr>
                </thead>
                <tbody>
        """

        for r in results:
            data = r.get('data', {})
            rec = r.get('recommendation', 'WAIT')
            conf = r.get('confidence', 0)

            # Confidence class
            conf_class = 'high-conf' if conf > 70 else 'med-conf' if conf > 40 else 'low-conf'

            # Recommendation class
            rec_class = rec.lower()

            current_price = data.get('current_price', 0)
            predicted_price = data.get('predicted_price', 0)
            expected_change = data.get('expected_change_percent', 0)

            # BUG FIX #15: HTML injection - escape user-provided content
            item_escaped = html.escape(str(r.get('item', 'Unknown')))
            rec_escaped = html.escape(str(rec))

            html += f"""
                    <tr class="{conf_class}">
                        <td>{item_escaped}</td>
                        <td class="{rec_class}">{rec_escaped}</td>
                        <td>{conf:.0f}%</td>
                        <td>${current_price:.2f}</td>
                        <td>${predicted_price:.2f}</td>
                        <td>{expected_change:+.1f}%</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        return html

    def export_backtest_results(self, backtest_data: Dict[str, Any], filename_prefix: str = 'backtest'):
        """
        Export backtesting results

        Args:
            backtest_data: Backtesting results data
            filename_prefix: Prefix for output files
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if 'json' in self.export_formats:
            json_file = os.path.join(self.export_path, f'{filename_prefix}_{timestamp}.json')
            try:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(backtest_data, f, indent=2, ensure_ascii=False)
                print(f"📄 Backtest report exported: {json_file}")
            except Exception as e:
                print(f"❌ Error exporting backtest: {e}")

    def export_price_history(self, db, item_name: str, days: int = 30):
        """
        Export price history for an item

        Args:
            db: Database instance
            item_name: Item name
            days: Number of days of history
        """
        data = db.get_price_history(item_name, days)

        if not data:
            print(f"⚠️  No price history for {item_name}")
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = item_name.replace(' ', '_').replace('|', '-')

        if 'csv' in self.export_formats:
            csv_file = os.path.join(self.export_path, f'history_{safe_name}_{timestamp}.csv')
            try:
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Price', 'Float Value', 'Timestamp'])
                    writer.writerows(data)
                print(f"📄 Price history exported: {csv_file}")
            except Exception as e:
                print(f"❌ Error exporting price history: {e}")
