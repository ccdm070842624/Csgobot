# CS:GO Trading Bot - Android Application

<img src="https://img.shields.io/badge/Platform-Android-green.svg" alt="Platform">
<img src="https://img.shields.io/badge/Language-Kotlin-blue.svg" alt="Language">
<img src="https://img.shields.io/badge/API-24%2B-brightgreen.svg" alt="API">

Мобильное Android приложение для CS:GO Trading Bot с real-time анализом рынка и торговыми рекомендациями.

## 📱 Возможности

### ✅ Реализовано:

- **📊 Real-time мониторинг** - Отслеживание цен на предметы CS:GO
- **💡 Торговые рекомендации** - ML-based анализ с рекомендациями BUY/SELL/HOLD
- **📈 Статистика** - Общая статистика по собранным данным
- **🔍 Детальная информация** - Подробный анализ каждого предмета
- **🔐 Безопасность** - Encrypted SharedPreferences для хранения токенов
- **🔄 Pull-to-refresh** - Обновление данных свайпом вниз
- **🎨 Material Design** - Современный UI с Material Components

## 🏗️ Архитектура

```
┌─────────────────────────────────────┐
│      Android App (Kotlin)           │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   MainActivity                │  │
│  │   - Opportunities List        │  │
│  │   - Statistics                │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   ItemDetailActivity          │  │
│  │   - Recommendation Details    │  │
│  │   - Price Analysis            │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   ApiClient (Retrofit)        │  │
│  │   - Token Management          │  │
│  │   - HTTP Communication        │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
                  ↕ HTTP/JSON
┌─────────────────────────────────────┐
│    FastAPI Server (Python)          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   REST API Endpoints          │  │
│  │   - /api/recommendations/     │  │
│  │   - /api/market/price         │  │
│  │   - /api/stats/summary        │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │   TradingBot                  │  │
│  │   PriceAnalyzer               │  │
│  │   ML Models                   │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 🚀 Установка и Запуск

### 1. Backend (FastAPI Server)

#### Установите зависимости:

```bash
pip install fastapi uvicorn pydantic
```

#### Запустите API server:

```bash
cd /home/user/Csgobot
python api_server.py
```

Сервер запустится на `http://0.0.0.0:8000`

#### Проверьте работу:

```bash
curl http://localhost:8000/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "bot_initialized": true,
  "analyzer_initialized": true,
  "timestamp": "2026-01-29T..."
}
```

### 2. Android App

#### Требования:

- **Android Studio** Arctic Fox (2020.3.1) или новее
- **Android SDK** 24+ (Android 7.0+)
- **JDK** 17
- **Kotlin** 1.9.0+

#### Настройка:

1. **Откройте проект в Android Studio:**

```bash
cd android_app
# Откройте папку в Android Studio
```

2. **Настройте URL сервера:**

Откройте `app/build.gradle` и измените `API_BASE_URL`:

```gradle
defaultConfig {
    // Замените на IP адрес вашего сервера
    buildConfigField "String", "API_BASE_URL", "\"http://192.168.1.100:8000\""
}
```

**Важно:**
- Для эмулятора используйте `http://10.0.2.2:8000`
- Для реального устройства используйте LAN IP вашего компьютера (например, `http://192.168.1.100:8000`)
- Убедитесь что firewall не блокирует порт 8000

3. **Синхронизируйте Gradle:**

```
File > Sync Project with Gradle Files
```

4. **Запустите приложение:**

- Подключите Android устройство или запустите эмулятор
- Нажмите Run (▶️) в Android Studio

## 📚 API Endpoints

### Authentication

```http
POST /auth/token
```

Получить API токен для аутентификации.

**Response:**
```json
{
  "token": "eyJhbGc...",
  "expires_in": 86400
}
```

### Market Data

#### Get Item Price

```http
POST /api/market/price
Authorization: Bearer {token}

{
  "item_name": "AK-47 | Redline",
  "days": 30
}
```

**Response:**
```json
{
  "item_name": "AK-47 | Redline",
  "current_price": 25.50,
  "avg_price": 24.80,
  "min_price": 22.10,
  "max_price": 28.90,
  "data_points": 150,
  "timestamp": "2026-01-29T12:00:00"
}
```

### Recommendations

#### Get Item Recommendation

```http
POST /api/recommendations/item
Authorization: Bearer {token}

{
  "item_name": "AK-47 | Redline"
}
```

**Response:**
```json
{
  "item": "AK-47 | Redline",
  "recommendation": "BUY",
  "confidence": 85.5,
  "current_price": 25.50,
  "predicted_price": 30.20,
  "trend": "Upward",
  "reasons": [
    "Price trending upward",
    "High confidence prediction",
    "Low volatility"
  ],
  "timestamp": "2026-01-29T12:00:00"
}
```

#### Get Top Opportunities

```http
GET /api/recommendations/opportunities?limit=10&min_confidence=50
Authorization: Bearer {token}
```

**Response:**
```json
[
  {
    "item": "AK-47 | Redline",
    "confidence": 85.5,
    "recommendation": "BUY",
    "current_price": 25.50,
    "predicted_price": 30.20,
    "potential_profit": 4.70,
    "potential_percent": 18.4,
    "data_points": 150
  },
  ...
]
```

### Statistics

```http
GET /api/stats/summary
Authorization: Bearer {token}
```

**Response:**
```json
{
  "total_items": 50,
  "items_with_data": 45,
  "total_data_points": 3500,
  "coverage_percent": 90.0,
  "timestamp": "2026-01-29T12:00:00"
}
```

## 📱 Экраны приложения

### Main Screen

Главный экран с:
- 📊 Статистика (общие данные)
- 💰 Топ торговых возможностей
- 🔄 Pull-to-refresh для обновления
- ✨ Material Design UI

### Item Detail Screen

Подробная информация о предмете:
- 📈 Рекомендация (BUY/SELL/HOLD)
- 🎯 Уровень уверенности (%)
- 💵 Текущая/предсказанная/средняя цена
- 📝 Причины анализа
- 📊 Тренд

## 🔐 Безопасность

### Реализовано:

- ✅ **Token-based Authentication** - Bearer token для всех API запросов
- ✅ **Encrypted Storage** - Android EncryptedSharedPreferences для токенов
- ✅ **HTTPS Support** - Готовность к HTTPS (измените URL в build.gradle)
- ✅ **Token Expiration** - Автоматическое обновление expired токенов
- ✅ **ProGuard Ready** - Поддержка obfuscation для release builds

### Рекомендации для Production:

1. **Используйте HTTPS:**
   ```gradle
   buildConfigField "String", "API_BASE_URL", "\"https://your-domain.com\""
   ```

2. **Включите ProGuard:**
   ```gradle
   buildTypes {
       release {
           minifyEnabled true
           proguardFiles getDefaultProguardFile('proguard-android-optimize.txt')
       }
   }
   ```

3. **Добавьте Certificate Pinning:**
   ```kotlin
   val certificatePinner = CertificatePinner.Builder()
       .add("your-domain.com", "sha256/...")
       .build()
   ```

4. **Настройте OAuth2/JWT на backend**

## 🛠️ Технологии

### Android App:

- **Language:** Kotlin 1.9.0
- **UI:** Material Components 1.11.0
- **Architecture:** MVVM-ready (ViewBinding)
- **Networking:** Retrofit 2.9.0 + OkHttp 4.12.0
- **JSON:** Gson 2.10.1
- **Security:** AndroidX Security Crypto 1.1.0
- **Async:** Kotlin Coroutines 1.7.3
- **Charts:** MPAndroidChart 3.1.0 (ready for integration)

### Backend:

- **Framework:** FastAPI (Python)
- **ML:** scikit-learn, pandas, numpy
- **Database:** SQLite
- **Parser:** requests, BeautifulSoup

## 📊 Структура проекта

```
android_app/
├── app/
│   ├── build.gradle                  # App dependencies
│   └── src/
│       └── main/
│           ├── AndroidManifest.xml
│           ├── java/com/csgobot/trading/
│           │   ├── MainActivity.kt          # Main screen
│           │   ├── ItemDetailActivity.kt    # Detail screen
│           │   ├── api/
│           │   │   ├── ApiClient.kt         # Retrofit client
│           │   │   ├── TradingApi.kt        # API interface
│           │   │   └── Models.kt            # Data classes
│           │   └── adapters/
│           │       └── OpportunityAdapter.kt # RecyclerView adapter
│           └── res/
│               ├── layout/
│               │   ├── activity_main.xml
│               │   ├── activity_item_detail.xml
│               │   └── item_opportunity.xml
│               ├── values/
│               │   ├── strings.xml
│               │   ├── colors.xml
│               │   ├── themes.xml
│               │   └── bools.xml
│               └── menu/
│                   └── menu_main.xml
└── build.gradle                      # Project config
```

## 🐛 Troubleshooting

### Проблема: "Connection refused"

**Решение:**
1. Проверьте что API server запущен: `curl http://localhost:8000/health`
2. Для эмулятора используйте `http://10.0.2.2:8000`
3. Для реального устройства используйте LAN IP
4. Проверьте firewall и что порт 8000 открыт

### Проблема: "Authentication failed"

**Решение:**
1. Проверьте что API server работает
2. Очистите данные приложения и попробуйте снова
3. Проверьте логи в Android Studio Logcat

### Проблема: "No trading opportunities found"

**Решение:**
1. Проверьте что в `config.yaml` есть список предметов
2. Запустите сбор данных: `python bot.py collect`
3. Дождитесь накопления достаточно данных (минимум 10 точек на предмет)

## 🔄 Обновления и поддержка

### Планы на будущее:

- [ ] 🔔 Push notifications для новых возможностей
- [ ] 📊 Графики истории цен (MPAndroidChart integration)
- [ ] ⚙️ Settings screen для настройки URL и параметров
- [ ] 🌙 Dark mode
- [ ] 📱 Tablet UI support
- [ ] 🔄 Background sync с WorkManager
- [ ] 💾 Offline mode с кешированием
- [ ] 🌐 Поддержка нескольких языков

## 📝 Лицензия

Этот проект разработан для образовательных целей.

## 🤝 Контакты

Если у вас есть вопросы или предложения, создайте issue в репозитории.

---

**Готово к использованию! 🚀**
