# Примеры использования CS:GO Trading Bot

## 🎯 Базовые примеры

### 1. Простой анализ
```bash
# Запуск полного анализа с дефолтными настройками
python bot.py --full
```

### 2. Только сбор данных
```bash
# Собрать данные для накопления истории
python bot.py --collect

# Запускайте это каждые 1-6 часов для лучшей точности
```

### 3. Анализ без сбора данных
```bash
# Анализировать уже собранные данные
python bot.py --analyze
```

## 🔧 Продвинутые примеры

### 4. Кастомная конфигурация
```bash
# Создайте свой конфиг
cp config.yaml my_strategy.yaml

# Отредактируйте параметры
nano my_strategy.yaml

# Используйте кастомный конфиг
python bot.py --config my_strategy.yaml --full
```

### 5. Анализ конкретных предметов
```bash
# Анализ только выбранных предметов
python bot.py --analyze --items \
  "AK-47 | Redline (Field-Tested)" \
  "AWP | Asiimov (Field-Tested)"
```

### 6. Бэктестинг на разные периоды
```bash
# Бэктест на 30 дней
python bot.py --backtest --days 30

# Бэктест на 90 дней (больше данных = точнее)
python bot.py --backtest --days 90
```

### 7. Генерация графиков
```bash
# Графики за последние 14 дней
python bot.py --charts --days 14

# Графики за месяц
python bot.py --charts --days 30
```

### 8. Debug режим
```bash
# Показать детальную информацию
python bot.py --full --log-level DEBUG
```

## 🐍 Программные примеры

### 9. Python скрипт - Базовый анализ
```python
from bot import EnhancedTradingBot

# Инициализация бота
bot = EnhancedTradingBot()

# Сбор данных
bot.collect_data()

# Анализ
results = bot.analyze()

# Показать лучшие возможности
top = bot.get_top_opportunities(results)
```

### 10. Python - Кастомные предметы
```python
from bot import EnhancedTradingBot

bot = EnhancedTradingBot()

# Свой список предметов
my_items = [
    "AK-47 | Vulcan (Factory New)",
    "M4A4 | Howl (Field-Tested)",
    "AWP | Dragon Lore (Minimal Wear)"
]

# Собрать данные только для этих предметов
bot.collect_data(items=my_items)

# Анализ
results = bot.analyze(items=my_items, export_results=True)
```

### 11. Python - Бэктестинг
```python
from bot import EnhancedTradingBot

bot = EnhancedTradingBot()

# Простой бэктест
results = bot.run_backtest(days=60)

print(f"ROI: {results['roi']:.1f}%")
print(f"Profit: ${results['profit_loss']:.2f}")
print(f"Win Rate: {results['win_rate']:.1f}%")
```

### 12. Python - Сравнение стратегий
```python
from bot import EnhancedTradingBot

bot = EnhancedTradingBot()

# Сравнить разные пороги уверенности
comparison = bot.backtester.compare_strategies(
    items=bot.config.items_to_track,
    confidence_thresholds=[50, 60, 70, 80],
    days=60
)

# Найти лучшую стратегию
best = max(comparison.values(), key=lambda x: x['roi'])
print(f"Best threshold: {best['threshold']} with ROI: {best['roi']:.1f}%")
```

### 13. Python - Экспорт конкретных данных
```python
from bot import EnhancedTradingBot
from csgo_trading_bot import PriceDatabase

bot = EnhancedTradingBot()

# Экспорт истории цен для предмета
db = PriceDatabase()
bot.exporter.export_price_history(
    db=db,
    item_name="AK-47 | Redline (Field-Tested)",
    days=30
)
db.close()
```

### 14. Python - Кастомная стратегия
```python
from bot import EnhancedTradingBot

class AggressiveBot(EnhancedTradingBot):
    def __init__(self):
        super().__init__()
        # Более агрессивная стратегия
        self.config.set('strategy.min_buy_confidence', 40)
        self.config.set('strategy.volatility_threshold', 20)

# Использование
aggressive_bot = AggressiveBot()
results = aggressive_bot.run_full_analysis()
```

### 15. Python - Только топ возможности
```python
from bot import EnhancedTradingBot

bot = EnhancedTradingBot()

# Быстрый анализ только для поиска возможностей
results = bot.analyze(export_results=False)

# Получить топ 3 возможности
top_3 = bot.get_top_opportunities(results)[:3]

for i, opp in enumerate(top_3, 1):
    print(f"{i}. {opp['item']} - Confidence: {opp['confidence']:.0f}%")
```

## 🔄 Автоматизация

### 16. Cron - Ежечасный сбор данных (Linux/Mac)
```bash
# Откройте crontab
crontab -e

# Добавьте строку (каждый час)
0 * * * * cd /path/to/Csgobot && /usr/bin/python3 bot.py --collect >> /tmp/csgo_collect.log 2>&1

# Или каждые 6 часов
0 */6 * * * cd /path/to/Csgobot && /usr/bin/python3 bot.py --collect
```

### 17. Cron - Ежедневный полный анализ
```bash
# Каждый день в 9:00
0 9 * * * cd /path/to/Csgobot && /usr/bin/python3 bot.py --full

# Отправка результатов на email (если настроено)
0 9 * * * cd /path/to/Csgobot && /usr/bin/python3 bot.py --analyze
```

### 18. Python скрипт - Автоматический мониторинг
```python
import time
from bot import EnhancedTradingBot

def monitor_loop(interval_hours=6):
    """Непрерывный мониторинг рынка"""
    bot = EnhancedTradingBot()

    while True:
        try:
            print(f"\n{'='*60}")
            print(f"Starting analysis cycle...")
            print(f"{'='*60}\n")

            # Сбор данных
            bot.collect_data()

            # Анализ
            results = bot.analyze()

            # Показать топ возможности
            top = bot.get_top_opportunities(results)

            # Если есть сильные сигналы (80%+), дополнительное уведомление
            strong_signals = [r for r in top if r['confidence'] >= 80]
            if strong_signals:
                print("\n🚨 STRONG BUY SIGNALS DETECTED! 🚨")
                for signal in strong_signals:
                    print(f"  • {signal['item']} - {signal['confidence']:.0f}%")

            # Ждать следующего цикла
            print(f"\nSleeping for {interval_hours} hours...")
            time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            time.sleep(300)  # Wait 5 minutes on error

if __name__ == "__main__":
    monitor_loop(interval_hours=6)
```

### 19. Python - Email отчеты
```python
from bot import EnhancedTradingBot

# Настройте email в config.yaml сначала
bot = EnhancedTradingBot()

# Включить email уведомления
bot.config.set('notifications.email.enabled', True)

# Анализ с отправкой email для сильных сигналов
results = bot.analyze()

# Email будут отправлены автоматически для сигналов с confidence >= 70%
```

## 📊 Примеры конфигурации

### 20. Консервативная стратегия
```yaml
# conservative_config.yaml
strategy:
  min_buy_confidence: 70  # Только очень уверенные сигналы
  volatility_threshold: 10  # Избегать волатильных предметов
  trend_strength_threshold: 3.0  # Сильные тренды

backtesting:
  min_profit_threshold: 0.15  # 15% минимум прибыли
```

### 21. Агрессивная стратегия
```yaml
# aggressive_config.yaml
strategy:
  min_buy_confidence: 40  # Принимать больше рисков
  volatility_threshold: 25  # Допускать высокую волатильность
  trend_strength_threshold: 1.0  # Слабые тренды OK

backtesting:
  min_profit_threshold: 0.05  # 5% минимум прибыли
```

### 22. Дневная торговля
```yaml
# daytrading_config.yaml
strategy:
  trend_days: 3  # Короткие тренды
  prediction_days_ahead: 1  # Краткосрочные прогнозы

data_collection:
  collection_interval: 1800  # Каждые 30 минут
```

## 🎓 Обучающие примеры

### 23. Первый запуск - Пошаговый
```bash
# Шаг 1: Установка
pip install -r requirements.txt

# Шаг 2: Проверка конфигурации
cat config.yaml

# Шаг 3: Первый сбор данных (будет мало данных)
python bot.py --collect

# Шаг 4: Подождать несколько часов, собрать еще раз
# (Запустите это 3-4 раза в течение дня)

# Шаг 5: Первый анализ
python bot.py --analyze

# Шаг 6: Полный анализ с графиками
python bot.py --full
```

### 24. Тестирование на исторических данных
```python
from bot import EnhancedTradingBot

bot = EnhancedTradingBot()

# Собрать данные несколько дней
print("Collecting data... Run this daily for a week")
bot.collect_data()

# После недели данных
print("\nRunning backtest on collected data...")
results = bot.run_backtest(days=7)

# Оценить результаты
if results['roi'] > 10:
    print("✅ Strategy looks profitable!")
else:
    print("⚠️  Strategy needs adjustment")
```

## 🔍 Отладка и тестирование

### 25. Debug конкретного предмета
```python
from csgo_trading_bot import PriceAnalyzer
import pandas as pd

analyzer = PriceAnalyzer()

item = "AK-47 | Redline (Field-Tested)"

# Получить данные
df = analyzer.get_item_dataframe(item, days=30)
print(f"\nData points: {len(df)}")
print(df.head())

# Тренд
trend = analyzer.calculate_trend(item, days=7)
print(f"\nTrend: {trend}")

# Прогноз
prediction = analyzer.predict_future_price(item, days_ahead=7)
print(f"\nPrediction: {prediction}")

# Рекомендация
rec = analyzer.get_buy_recommendation(item)
print(f"\nRecommendation: {rec['recommendation']} ({rec['confidence']:.0f}%)")
```

### 26. Проверка API подключения
```python
from csgo_trading_bot import CSGOFloatParser

parser = CSGOFloatParser(api_key="your_api_key")  # или None

# Тест запроса
test_item = "AK-47 | Redline (Field-Tested)"
listings = parser.get_item_listings(test_item, limit=5)

if listings:
    print(f"✅ API working! Got {len(listings)} listings")
    print(f"First listing: ${listings[0].get('price', 0)/100:.2f}")
else:
    print("❌ API not working. Check your API key or connection")
```

## 💡 Полезные команды

```bash
# Посмотреть логи
tail -f logs/trading_bot.log

# Очистить старые данные (будьте осторожны!)
rm csgo_prices.db

# Посмотреть размер БД
ls -lh csgo_prices.db

# Экспорт всей БД в CSV (SQLite)
sqlite3 csgo_prices.db ".mode csv" ".output all_data.csv" "SELECT * FROM price_history;"

# Посмотреть последние отчеты
ls -lt reports/ | head -5

# Открыть последний HTML отчет в браузере (Mac)
open $(ls -t reports/*.html | head -1)

# Linux
xdg-open $(ls -t reports/*.html | head -1)

# Граф ики
ls -lt charts/

# Проверить установленные пакеты
pip list | grep -E "pandas|numpy|sklearn|matplotlib|yaml"
```

---

💡 **Совет**: Начните с простых примеров (1-3), затем переходите к продвинутым (10-15), и наконец автоматизируйте (16-19)
