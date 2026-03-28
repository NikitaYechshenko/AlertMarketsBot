# 🚀 Crypto Alert Bot

Telegram bot for tracking cryptocurrency prices across multiple exchanges with instant notifications.

**Live Bot:** [@AlertMarketsBot](https://t.me/AlertMarketsBot)

## 📋 Features

- ✅ Price alerts for cryptocurrencies
- ✅ Multi-exchange support (Binance Spot, Binance Futures)
- ✅ 24/7 monitoring
- ✅ Bilingual interface (Russian/English)
- 🔜 Percentage alerts
- 🔜 Price charts

## 🛠️ Tech Stack

- **Python 3.12** — core language
- **aiogram 3.26** — Telegram Bot API
- **PostgreSQL 16** — database
- **Redis** — cache and alert queue
- **SQLAlchemy 2.0** — ORM
- **Docker & Docker Compose** — containerization

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Telegram_bot
```

### 2. Create .env file

```bash
cp .env.example .env
```

Edit `.env` and set:
- `TELEGRAM_BOT_TOKEN` — token from [@BotFather](https://t.me/BotFather)
- `DB_PASSWORD` — secure password for PostgreSQL

### 3. Launch with Docker

```bash
docker-compose up -d --build
```

### 4. Check logs

```bash
docker logs -f Alert_bot_app
```

## 📦 Project Structure

```
Telegram_bot/
├── app/
│   ├── bot/
│   │   ├── handlers/      # Command and callback handlers
│   │   ├── keyboards/     # Keyboards (inline + reply)
│   │   ├── middlewares/   # Middleware (DB sessions)
│   │   ├── services/      # Business logic
│   │   ├── states/        # FSM states
│   │   ├── i18n.py        # Localization (ru/en)
│   │   └── main.py        # Entry point
│   ├── core/              # Configuration, DB, Redis
│   ├── exchanges/         # Exchange APIs
│   ├── models/            # SQLAlchemy models
│   ├── workers/           # Workers for alert monitoring
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env
└── README.md
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# Rebuild app image
docker-compose up -d --build app

# View logs
docker logs -f Alert_bot_app

# Stop all services
docker-compose down

# Remove volume with DB data (careful!)
docker-compose down -v
```

## 🗄️ Database

PostgreSQL runs automatically in Docker. Data is persisted in the `pgdata` volume.

Migrations are created automatically on bot startup via SQLAlchemy.

## 📝 Development

### Local run (without Docker)

1. Create virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows
```

2. Install dependencies:

```bash
pip install -r app/requirements.txt
```

3. Run PostgreSQL and Redis locally or modify `.env`:

```env
DB_HOST=localhost
REDIS_HOST=localhost
```

4. Start the bot:

```bash
cd app
python -m bot.main
```

## 🌐 Localization

The bot automatically detects user language from Telegram settings.

To add new translations, edit: `app/bot/i18n.py`

## 🔧 Exchange Configuration

Supported exchanges are configured in:
- `app/exchanges/Binance/` — API clients
- `app/workers/Binance/` — monitoring workers

## 📊 Architecture

1. **Bot** — handles user commands and interactions
2. **Workers** — background tasks for monitoring alerts
3. **PostgreSQL** — stores users and alerts
4. **Redis** — caches available coins + active alert queue

## 🎮 Bot Commands

- `/start` — Start the bot and see main menu
- `/menu` — Show main menu
- `/cancel` — Cancel current operation

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_NAME` | Database name | `Alert_bot` |
| `DB_HOST` | Database host | `db` |
| `DB_PORT` | Database port | `5432` |
| `REDIS_HOST` | Redis host | `redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | — |

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

MIT

## 👤 Author

Created by [@nikitayech](https://t.me/nikitayech)

**Try the bot:** [@AlertMarketsBot](https://t.me/AlertMarketsBot)
