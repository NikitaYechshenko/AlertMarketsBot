# 🚀 Crypto Alert Bot

**Telegram bot для мониторинга цен криптовалют на Binance с мгновенными уведомлениями.**

📱 **Попробить:** [@AlertMarketsBot](https://t.me/AlertMarketsBot)

## ⚡ Что умеет

- Цены криптовалют в реал-тайме
- Мониторинг Binance (Spot & Futures)
- Расширенные уведомления
- Русский/Английский

## 🛠️ Технологии

| Компонент | Технология |
|-----------|-----------|
| **Backend** | Python 3.12 + aiogram 3.26 |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis |
| **Deploy** | Docker Compose |
| **ORM** | SQLAlchemy 2.0 |

## 🔍 Как работает

1. Пользователь создаёт алерт через бота (цена X для криптовалюты Y)
2. **Worker** в фоне мониторит цены на Binance API каждые ~5 сек
3. Redis кэширует доступные монеты (быстро, экономит API-запросы)
4. При срабатывании алерта → уведомление в Telegram
5. PostgreSQL хранит пользователей и их алерты

## 🚀 Быстрый старт

```bash
# 1. Клонирование
git clone <repo-url> && cd Telegram_bot

# 2. Переменные окружения
cp .env.example .env
# Вставить TELEGRAM_BOT_TOKEN от @BotFather

# 3. Запуск в Docker
docker-compose up -d --build

# 4. Логи
docker logs -f Alert_bot_app
```

## 📂 Структура

```
app/
├── bot/              # Handlers, keyboards, FSM
├── workers/          # Фоновые задачи мониторинга
├── exchanges/        # Binance API clients
├── models/           # DB models (SQLAlchemy)
└── core/             # Config, DB, Redis
```

## 🎮 Команды бота

- `/start` — главное меню
- `/menu` — вернуться в меню
- `/cancel` — отмена

---

**Автор:** [@nikitayech](https://t.me/nikitayech)
