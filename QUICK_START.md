# CS:GO Trading Bot - Quick Start Guide

## 🚀 Installation

```bash
# Clone repository
cd Csgobot

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

1. **Copy and edit config file**:
```bash
cp config.yaml my_config.yaml
# Edit my_config.yaml with your settings
```

2. **Set your API key** (optional but recommended):
```yaml
api:
  csgofloat:
    api_key: "your_api_key_here"  # Get from csgofloat.com
```

3. **Configure items to track**:
```yaml
items:
  - "AK-47 | Redline (Field-Tested)"
  - "AWP | Asiimov (Field-Tested)"
  # Add more items...
```

## 🎮 Usage

### Run Complete Analysis (Recommended)
```bash
python bot.py --full
```

This will:
1. Collect fresh market data
2. Analyze all items
3. Generate price charts
4. Run backtest simulation
5. Export reports

### Collect Data Only
```bash
python bot.py --collect
```

### Analyze & Get Recommendations
```bash
python bot.py --analyze
```

### Generate Charts
```bash
python bot.py --charts --days 30
```

### Run Backtest
```bash
python bot.py --backtest --days 60
```

### Use Custom Config
```bash
python bot.py --config my_config.yaml --full
```

### Analyze Specific Items
```bash
python bot.py --analyze --items "AK-47 | Redline (Field-Tested)" "AWP | Asiimov (Field-Tested)"
```

### Debug Mode
```bash
python bot.py --full --log-level DEBUG
```

## 📊 Understanding Output

### Trade Signals

**🟢 BUY** - Strong buy signal
- Confidence ≥ 50%
- Positive price trend
- Good profit potential

**🔴 SELL** - Strong sell signal
- Confidence ≥ 50%
- Negative price trend
- Consider taking profits

**🟡 HOLD** - Wait for better opportunity
- Mixed signals
- Low confidence

**⚪ WAIT** - Insufficient data
- Need more historical data

### Confidence Levels

- **70-100%**: Very High - Strong recommendation
- **50-70%**: High - Good recommendation
- **30-50%**: Medium - Be cautious
- **0-30%**: Low - Not recommended

## 📈 Reading Reports

### Console Output
Real-time analysis displayed in terminal with color-coded signals

### CSV Reports
Located in `reports/analysis_TIMESTAMP.csv`
- Importable into Excel/Google Sheets
- Contains all recommendations with metrics

### JSON Reports
Located in `reports/analysis_TIMESTAMP.json`
- Machine-readable format
- Full data including reasons

### HTML Reports
Located in `reports/analysis_TIMESTAMP.html`
- Open in browser for visual report
- Color-coded by confidence level

### Charts
Located in `charts/ITEMNAME_history.png`
- Price history visualization
- Trend lines
- Price ranges

## 🔧 Advanced Usage

### Scheduled Data Collection

**Linux/Mac (cron)**:
```bash
# Edit crontab
crontab -e

# Add line to run every hour
0 * * * * cd /path/to/Csgobot && /usr/bin/python3 bot.py --collect
```

**Windows (Task Scheduler)**:
Create task to run `python bot.py --collect` hourly

### Email Notifications

Configure in `config.yaml`:
```yaml
notifications:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    sender: "your_email@gmail.com"
    password: "your_app_password"  # Use app password, not regular password!
    recipients:
      - "recipient@example.com"
```

### Strategy Optimization

Run backtests with different confidence thresholds:
```python
from bot import EnhancedTradingBot

bot = EnhancedTradingBot()
bot.backtester.compare_strategies(
    items=bot.config.items_to_track,
    confidence_thresholds=[50, 60, 70, 80],
    days=60
)
```

## 🎯 Best Practices

1. **Collect data regularly**: Run `--collect` every 1-6 hours
2. **Wait for sufficient data**: Need 50+ data points for good predictions
3. **Don't over-trade**: High confidence (70%+) signals only
4. **Diversify**: Don't put all money in one item
5. **Verify manually**: Always check prices yourself before buying
6. **Start small**: Test with cheap items first
7. **Monitor trends**: Use charts to spot patterns

## ⚠️ Important Notes

- Bot **DOES NOT** make automatic purchases - only provides analysis
- Predictions are based on historical data - not guaranteed
- Always verify prices on market before trading
- CSGOFloat API has rate limits - don't spam requests
- Keep your API keys private

## 🐛 Troubleshooting

### "No data available"
- Run `python bot.py --collect` first
- Wait a few days to accumulate history

### "Rate limit" errors
- Increase `rate_limit_delay` in config
- Get API key from csgofloat.com

### "Insufficient data" warnings
- Normal for new items
- Collect more data over time

### Charts not generating
- Check `reports/` and `charts/` directories exist
- Verify matplotlib is installed

### Email not sending
- Use app password (not regular password)
- Check SMTP settings for your provider
- Gmail: Enable "Less secure apps" or use app password

## 📚 Next Steps

1. Read full [README.md](README.md) for detailed documentation
2. Check [config.yaml](config.yaml) for all available settings
3. Review exported reports in `reports/` directory
4. Analyze charts in `charts/` directory
5. Fine-tune strategy parameters in config

## 🆘 Support

Found a bug? Have a question?
- Check existing issues on GitHub
- Create new issue with details
- Include logs from `logs/` directory

Happy trading! 🎮💰
