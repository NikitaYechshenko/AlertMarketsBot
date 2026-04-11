# 🚀 Crypto Alert Bot

**Telegram bot for monitoring cryptocurrency prices on Binance with instant notifications.**

📱 **Try it:** [@AlertMarketsBot](https://t.me/AlertMarketsBot)

## ⚡ Features

- Real-time cryptocurrency prices
- Binance monitoring (Spot & Futures)
- Advanced notifications
- Russian/English support

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.12 + aiogram 3.26 |
| **Database** | PostgreSQL 16 |
| **Cache** | Redis |
| **Deploy** | Docker Compose |
| **ORM** | SQLAlchemy 2.0 |

## 🔍 How It Works

1. User creates an alert via the bot (price X for cryptocurrency Y)
2. **Worker** monitors prices on Binance API in the background (~5 sec intervals)
3. Redis caches available coins (fast, saves API requests)
4. When an alert triggers → notification in Telegram
5. PostgreSQL stores users and their alerts

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone <repo-url> && cd Telegram_bot

# 2. Set environment variables
cp .env.example .env
# Add TELEGRAM_BOT_TOKEN from @BotFather

# 3. Run with Docker
docker-compose up -d --build

# 4. View logs
docker logs -f Alert_bot_app
```

## 📂 Project Structure

```
app/
├── bot/              # Handlers, keyboards, FSM
├── workers/          # Background monitoring tasks
├── exchanges/        # Binance API clients
├── models/           # DB models (SQLAlchemy)
└── core/             # Config, DB, Redis
```

## 🎮 Bot Commands

- `/start` — main menu
- `/menu` — return to menu
- `/cancel` — cancel

---

**Author:** [@nikitayech](https://t.me/nikitayech)
