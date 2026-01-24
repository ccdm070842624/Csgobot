import requests
import json
import time
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# ПАРСИНГ ДАННЫХ
# ============================================================================

class CSGOFloatParser:
    def __init__(self, api_key=None):
        self.base_url = "https://csgofloat.com/api/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

    def get_item_listings(self, market_hash_name, limit=50, sort_by='best_deal'):
        """Получение списка предложений для предмета"""
        url = f"{self.base_url}/listings"

        params = {
            'market_hash_name': market_hash_name,
            'limit': limit,
            'sort_by': sort_by
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)

            if response.status_code == 200:
                data = response.json()
                # FIX: Правильная структура ответа CSGOFloat API
                # API возвращает объект с ключами, а не массив напрямую
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # Проверяем разные возможные структуры
                    return data.get('data', data.get('listings', []))
                return []
            elif response.status_code == 429:
                print("⚠️  Rate limit! Подожди 60 секунд...")
                time.sleep(60)
                return None
            elif response.status_code == 401:
                print("❌ Ошибка авторизации. Проверьте API ключ")
                return None
            else:
                print(f"❌ Ошибка API: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Детали: {error_data}")
                except (json.JSONDecodeError, ValueError) as e:
                    # ERROR HANDLING FIX: Specific exception instead of bare except
                    print(f"   (Response is not JSON: {e})")
                return None

        except requests.exceptions.Timeout:
            print("⚠️  Таймаут запроса")
            return None
        except requests.exceptions.ConnectionError:
            print("❌ Ошибка соединения")
            return None
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return None


class PriceDatabase:
    def __init__(self, db_name='csgo_prices.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        """Создание таблиц БД"""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                price REAL NOT NULL,
                float_value REAL,
                paint_seed INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                UNIQUE(item_name, price, float_value, paint_seed, timestamp)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                avg_price REAL,
                min_price REAL,
                max_price REAL,
                volume INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # FIX: Добавляем индексы для ускорения запросов
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_history_item_time
            ON price_history(item_name, timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_market_stats_item_time
            ON market_stats(item_name, timestamp)
        ''')

        self.conn.commit()

    def save_listing(self, item_data):
        """Сохранение информации о предмете"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO price_history
                (item_name, price, float_value, paint_seed, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item_data.get('item_name'),
                item_data.get('price', 0),
                item_data.get('float_value'),
                item_data.get('paint_seed'),
                item_data.get('source', 'csgofloat')
            ))

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"⚠️  Ошибка сохранения в БД: {e}")
            return False

    def save_market_stats(self, item_name, stats):
        """Сохранение статистики рынка"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO market_stats
                (item_name, avg_price, min_price, max_price, volume)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item_name,
                stats.get('avg_price', 0),
                stats.get('min_price', 0),
                stats.get('max_price', 0),
                stats.get('volume', 0)
            ))

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"⚠️  Ошибка сохранения статистики: {e}")
            return False

    def get_price_history(self, item_name, days=30):
        """Получение истории цен"""
        cursor = self.conn.cursor()

        try:
            cursor.execute('''
                SELECT price, float_value, timestamp
                FROM price_history
                WHERE item_name = ?
                AND timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            ''', (item_name, days))

            return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"⚠️  Ошибка чтения из БД: {e}")
            return []

    def close(self):
        """Закрытие соединения с БД"""
        if self.conn:
            self.conn.close()
            self.conn = None  # RESOURCE LEAK FIX: Set to None after closing

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures connection is closed"""
        self.close()
        return False  # Don't suppress exceptions


def collect_market_data(api_key=None):
    """Сбор данных с CSGOFloat"""
    parser = CSGOFloatParser(api_key=api_key)
    db = PriceDatabase()

    items_to_track = [
        "AK-47 | Redline (Field-Tested)",
        "AWP | Asiimov (Field-Tested)",
        "M4A4 | Desert-Strike (Factory New)",
        "Glock-18 | Water Elemental (Minimal Wear)",
        "Desert Eagle | Kumicho Dragon (Factory New)"
    ]

    print("🔍 Начинаю сбор данных с CSGOFloat...\n")

    success_count = 0
    fail_count = 0

    for item_name in items_to_track:
        print(f"📊 Анализирую: {item_name}")

        listings = parser.get_item_listings(item_name, limit=20)

        # FIX: Проверка что listings не None и не пустой
        if listings is None:
            print(f"  ⚠️  Не удалось получить данные, пропускаю...\n")
            fail_count += 1
            time.sleep(5)
            continue

        if not listings or len(listings) == 0:
            print(f"  ⚠️  Нет предложений на рынке\n")
            fail_count += 1
            time.sleep(3)
            continue

        # FIX: Обработка разных форматов данных
        prices = []
        saved_count = 0

        for listing in listings:
            try:
                # CSGOFloat может возвращать цену в центах или долларах
                # Проверяем и нормализуем
                price_raw = listing.get('price', 0)

                # Если цена больше 1000, скорее всего в центах
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
                print(f"  ⚠️  Ошибка обработки предмета: {e}")
                continue

        # Сохраняем статистику только если есть цены
        if prices:
            stats = {
                'avg_price': sum(prices) / len(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'volume': len(prices)
            }

            if db.save_market_stats(item_name, stats):
                print(f"  💰 Средняя цена: ${stats['avg_price']:.2f}")
                print(f"  📉 Минимум: ${stats['min_price']:.2f}")
                print(f"  📈 Максимум: ${stats['max_price']:.2f}")
                print(f"  ✅ Сохранено: {saved_count} предложений\n")
                success_count += 1
        else:
            print(f"  ⚠️  Не удалось обработать цены\n")
            fail_count += 1

        # FIX: Увеличенная задержка между запросами
        time.sleep(5)

    db.close()

    print("=" * 80)
    print(f"✅ Сбор данных завершен!")
    print(f"   Успешно: {success_count} / Ошибок: {fail_count}")
    print("=" * 80 + "\n")


# ============================================================================
# АНАЛИЗ И ПРЕДСКАЗАНИЯ
# ============================================================================

class PriceAnalyzer:
    def __init__(self, db_name='csgo_prices.db'):
        self.db_name = db_name
        # FIX: Не создаем постоянное соединение, используем контекстный менеджер

    def _get_db(self):
        """Получение соединения с БД"""
        return sqlite3.connect(self.db_name)

    def get_item_dataframe(self, item_name, days=30):
        """Получение данных в виде DataFrame"""
        conn = self._get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT price, float_value, timestamp
                FROM price_history
                WHERE item_name = ?
                AND timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            ''', (item_name, days))

            data = cursor.fetchall()
        finally:
            conn.close()

        if not data:
            return None

        df = pd.DataFrame(data, columns=['price', 'float_value', 'timestamp'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        return df

    def calculate_trend(self, item_name, days=7, df=None):
        """
        Расчет тренда цен

        Args:
            item_name: Название предмета
            days: Количество дней для анализа
            df: DataFrame с данными (опционально, для избежания повторных запросов)
        """
        # PERFORMANCE FIX: Allow passing DataFrame to avoid redundant DB queries
        if df is None:
            df = self.get_item_dataframe(item_name, days)

        if df is None or len(df) < 2:
            return None

        # FIX: Группировка по дате с обработкой пустых значений
        df['date'] = df['timestamp'].dt.date
        daily_avg = df.groupby('date')['price'].mean().reset_index()

        if len(daily_avg) < 2:
            return None

        X = np.arange(len(daily_avg)).reshape(-1, 1)
        y = daily_avg['price'].values

        try:
            model = LinearRegression()
            model.fit(X, y)

            trend_slope = model.coef_[0]

            start_price = daily_avg['price'].iloc[0]
            end_price = daily_avg['price'].iloc[-1]

            # BUG FIX #1: Division by zero - validate start_price != 0
            if start_price == 0:
                print(f"⚠️  Start price is zero, cannot calculate trend")
                return None

            percent_change = ((end_price - start_price) / start_price) * 100

            return {
                'trend_slope': trend_slope,
                'percent_change': percent_change,
                'start_price': start_price,
                'end_price': end_price,
                'direction': 'UP' if trend_slope > 0 else 'DOWN',
                'strength': abs(percent_change)
            }
        except Exception as e:
            print(f"⚠️  Ошибка расчета тренда: {e}")
            return None

    def predict_future_price(self, item_name, days_ahead=7, history_days=30, df=None):
        """
        Прогнозирование будущей цены

        Args:
            item_name: Название предмета
            days_ahead: На сколько дней вперед прогноз
            history_days: Количество дней истории для обучения
            df: DataFrame с данными (опционально, для избежания повторных запросов)
        """
        # PERFORMANCE FIX: Allow passing DataFrame to avoid redundant DB queries
        if df is None:
            df = self.get_item_dataframe(item_name, history_days)

        if df is None or len(df) < 10:
            return None

        try:
            df['days_ago'] = (df['timestamp'].max() - df['timestamp']).dt.days

            X = df[['days_ago']].values
            y = df['price'].values

            # FIX: Параметры модели для лучшей производительности
            model = RandomForestRegressor(
                n_estimators=50,  # Уменьшено для скорости
                max_depth=10,
                random_state=42,
                n_jobs=-1  # Использовать все ядра
            )
            model.fit(X, y)

            future_days = np.array([[-days_ahead]])
            predicted_price = model.predict(future_days)[0]

            current_price = df['price'].iloc[-1]

            # BUG FIX #2: Division by zero - validate current_price != 0
            if current_price == 0:
                print(f"⚠️  Current price is zero, cannot calculate expected change")
                return None

            expected_change = ((predicted_price - current_price) / current_price) * 100

            # FIX: Более точная оценка уверенности
            confidence_level = 'LOW'
            if len(df) >= 200:
                confidence_level = 'HIGH'
            elif len(df) >= 50:
                confidence_level = 'MEDIUM'

            return {
                'current_price': current_price,
                'predicted_price': predicted_price,
                'expected_change_percent': expected_change,
                'days_ahead': days_ahead,
                'confidence': confidence_level,
                'data_points': len(df)
            }
        except Exception as e:
            print(f"⚠️  Ошибка прогнозирования: {e}")
            return None

    def get_buy_recommendation(self, item_name):
        """
        Получение рекомендации по покупке

        PERFORMANCE OPTIMIZATION: Fetches data once and reuses for all calculations
        """
        # PERFORMANCE FIX: Fetch data once for all calculations
        # Use 30 days for prediction (more data = better ML model)
        df = self.get_item_dataframe(item_name, 30)

        if df is None or len(df) < 10:
            return {
                'recommendation': 'WAIT',
                'reason': 'Недостаточно данных для анализа',
                'confidence': 0,
                'current_price': None,
                'predicted_price': None
            }

        # Pass df to avoid redundant DB queries
        trend = self.calculate_trend(item_name, days=7, df=df)
        prediction = self.predict_future_price(item_name, days_ahead=7, history_days=30, df=df)

        if not trend or not prediction:
            return {
                'recommendation': 'WAIT',
                'reason': 'Ошибка анализа данных',
                'confidence': 0,
                'current_price': None,
                'predicted_price': None
            }

        score = 0
        reasons = []

        # Анализ тренда
        if trend['direction'] == 'UP' and trend['strength'] > 2:
            score += 30
            reasons.append(f"Восходящий тренд (+{trend['percent_change']:.1f}%)")
        elif trend['direction'] == 'DOWN' and trend['strength'] > 2:
            score -= 30
            reasons.append(f"Нисходящий тренд ({trend['percent_change']:.1f}%)")

        # Анализ прогноза
        if prediction['expected_change_percent'] > 5:
            score += 40
            reasons.append(f"Прогноз роста на {prediction['expected_change_percent']:.1f}%")
        elif prediction['expected_change_percent'] < -5:
            score -= 40
            reasons.append(f"Прогноз падения на {prediction['expected_change_percent']:.1f}%")

        # Анализ волатильности (reuse already fetched df)
        # BUG FIX #3 & #9: Division by zero + NaN handling - need at least 2 points for std
        if df is not None and len(df) > 1:
            price_mean = df['price'].mean()

            # Check mean is not zero before division
            if price_mean > 0:
                volatility = df['price'].std() / price_mean * 100

                # Check for NaN (happens with constant prices)
                if not np.isnan(volatility):
                    if volatility > 15:
                        score -= 20
                        reasons.append(f"Высокая волатильность ({volatility:.1f}%)")
                    elif volatility < 5:
                        score += 10
                        reasons.append(f"Низкая волатильность ({volatility:.1f}%)")

        # Определение рекомендации
        if score > 30:
            recommendation = 'BUY'
        elif score < -30:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'

        confidence = min(abs(score), 100)

        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasons': reasons,
            'current_price': prediction['current_price'],
            'predicted_price': prediction['predicted_price'],
            'trend': trend,
            'data_points': prediction.get('data_points', 0)
        }

    def plot_price_history(self, item_name, days=30, save_path=None):
        """Построение графика истории цен"""
        df = self.get_item_dataframe(item_name, days)

        if df is None or len(df) == 0:
            print(f"⚠️  Нет данных для графика: {item_name}")
            return False

        # RESOURCE LEAK FIX: Use try-finally to ensure matplotlib cleanup
        try:
            df['date'] = df['timestamp'].dt.date
            daily_data = df.groupby('date').agg({
                'price': ['mean', 'min', 'max']
            }).reset_index()

            plt.figure(figsize=(12, 6))

            try:
                plt.plot(daily_data['date'], daily_data['price']['mean'],
                        marker='o', linewidth=2, label='Средняя цена', color='#2E86AB')

                plt.fill_between(daily_data['date'],
                                 daily_data['price']['min'],
                                 daily_data['price']['max'],
                                 alpha=0.3, label='Диапазон цен', color='#A23B72')

                # Линия тренда
                trend = self.calculate_trend(item_name, days)
                if trend:
                    X = np.arange(len(daily_data))
                    y = daily_data['price']['mean'].values
                    z = np.polyfit(X, y, 1)
                    p = np.poly1d(z)

                    trend_color = '#06A77D' if trend['direction'] == 'UP' else '#D81159'
                    plt.plot(daily_data['date'], p(X),
                            "--", linewidth=2, alpha=0.8,
                            color=trend_color,
                            label=f'Тренд ({trend["direction"]} {trend["percent_change"]:+.1f}%)')

                plt.xlabel('Дата', fontsize=12, fontweight='bold')
                plt.ylabel('Цена ($)', fontsize=12, fontweight='bold')
                plt.title(f'{item_name} - История цен ({days} дней)',
                         fontsize=14, fontweight='bold', pad=20)
                plt.legend(loc='best', framealpha=0.9)
                plt.grid(True, alpha=0.3, linestyle='--')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()

                if save_path:
                    plt.savefig(save_path, dpi=300, bbox_inches='tight')
                    print(f"📊 График сохранен: {save_path}")
                else:
                    # FIX: Не показываем график в CLI, только сохраняем
                    default_path = f"{item_name.replace(' ', '_').replace('|', '-')}_price_history.png"
                    plt.savefig(default_path, dpi=300, bbox_inches='tight')
                    print(f"📊 График сохранен: {default_path}")

                return True

            finally:
                # Ensure figure is closed even if error occurs
                plt.close()

        except Exception as e:
            print(f"⚠️  Ошибка построения графика: {e}")
            return False


class TradingBot:
    def __init__(self):
        self.analyzer = PriceAnalyzer()
        self.parser = CSGOFloatParser()

    def analyze_items(self, items_list):
        """Анализ списка предметов"""
        results = []

        print("🤖 Торговый бот CS:GO начал анализ...\n")
        print("=" * 80)

        for item_name in items_list:
            print(f"\n📦 Анализирую: {item_name}")

            rec = self.analyzer.get_buy_recommendation(item_name)

            emoji_map = {
                'BUY': '🟢 ПОКУПАТЬ',
                'SELL': '🔴 ПРОДАВАТЬ',
                'HOLD': '🟡 ДЕРЖАТЬ',
                'WAIT': '⚪ ЖДАТЬ'
            }

            print(f"\n{emoji_map.get(rec['recommendation'], rec['recommendation'])}")
            print(f"Уверенность: {rec['confidence']:.0f}%")

            # FIX: Проверка наличия данных
            if rec.get('current_price') is not None:
                print(f"Текущая цена: ${rec['current_price']:.2f}")
            else:
                print("Текущая цена: Нет данных")

            if rec.get('predicted_price') is not None and rec.get('current_price') is not None:
                change = rec['predicted_price'] - rec['current_price']
                print(f"Прогноз (7 дней): ${rec['predicted_price']:.2f} ({change:+.2f})")

            if rec.get('data_points'):
                print(f"Точек данных: {rec['data_points']}")

            if rec.get('reasons'):
                print("\nПричины:")
                for reason in rec['reasons']:
                    print(f"  • {reason}")
            else:
                print(f"\nПричина: {rec.get('reason', 'Нет данных')}")

            results.append({
                'item': item_name,
                'recommendation': rec['recommendation'],
                'confidence': rec['confidence'],
                'data': rec
            })

            print("-" * 80)

        return results

    def get_top_opportunities(self, results):
        """Получение топ возможностей для покупки"""
        buy_opportunities = [
            r for r in results
            if r['recommendation'] == 'BUY' and r['confidence'] > 50
        ]

        buy_opportunities.sort(key=lambda x: x['confidence'], reverse=True)

        print("\n\n🎯 ТОП ВОЗМОЖНОСТЕЙ ДЛЯ ПОКУПКИ:\n")

        if not buy_opportunities:
            print("❌ Нет сильных сигналов на покупку в данный момент")
            print("   Попробуйте собрать больше данных или проверьте позже\n")
            return

        for i, opp in enumerate(buy_opportunities[:5], 1):
            print(f"{i}. {opp['item']}")
            print(f"   Уверенность: {opp['confidence']:.0f}%")

            # BUG FIX: Division by zero - validate both is not None and > 0
            if (opp['data'].get('predicted_price') is not None and
                opp['data'].get('current_price') is not None and
                opp['data']['current_price'] > 0):
                potential = opp['data']['predicted_price'] - opp['data']['current_price']
                potential_percent = (potential / opp['data']['current_price']) * 100
                print(f"   Потенциал: +${potential:.2f} (+{potential_percent:.1f}%)")

            if opp['data'].get('data_points'):
                print(f"   Данных: {opp['data']['data_points']} точек")

            print()


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Главная функция"""
    print("=" * 80)
    print("🎮 CS:GO Trading Bot - Анализ рынка")
    print("=" * 80 + "\n")

    items = [
        "AK-47 | Redline (Field-Tested)",
        "AWP | Asiimov (Field-Tested)",
        "M4A4 | Desert-Strike (Factory New)",
        "Glock-18 | Water Elemental (Minimal Wear)",
        "Desert Eagle | Kumicho Dragon (Factory New)",
        "USP-S | Kill Confirmed (Field-Tested)"
    ]

    # Собираем данные
    print("📥 ЭТАП 1: Сбор данных с рынка\n")
    try:
        collect_market_data()  # Можно передать api_key если есть
    except Exception as e:
        print(f"❌ Критическая ошибка сбора данных: {e}")
        print("   Попробуйте позже или проверьте API ключ\n")
        return

    print("\n" + "=" * 80 + "\n")

    # Анализируем
    print("📊 ЭТАП 2: Анализ собранных данных\n")
    try:
        bot = TradingBot()
        results = bot.analyze_items(items)
        bot.get_top_opportunities(results)
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return

    # Графики
    print("\n" + "=" * 80 + "\n")
    print("📈 ЭТАП 3: Построение графиков\n")

    analyzer = PriceAnalyzer()

    # Строим графики для предметов с данными
    graphs_created = 0
    for item in items[:3]:  # Только первые 3 для примера
        if analyzer.plot_price_history(item, days=14):
            graphs_created += 1
            time.sleep(1)

    if graphs_created > 0:
        print(f"\n✅ Создано графиков: {graphs_created}")
    else:
        print("\n⚠️  Не удалось создать графики (недостаточно данных)")

    print("\n" + "=" * 80)
    print("✅ Анализ завершен!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Программа прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
