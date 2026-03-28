"""
Centralised translations / Централизованные переводы.
Usage:
    from app.bot.i18n import t, all_langs
    t("welcome", lang, name="Nikita")
    F.text.in_(all_langs("btn_alerts"))
"""

TEXTS: dict[str, dict[str, str]] = {
    # ──────────────────── RUSSIAN ─────────────────────────────────────────────
    "ru": {
        # Buttons (Reply Keyboard)
        "btn_alerts":       "📋 Мои алерты",
        "btn_new_alert":    "➕ Новый алерт",
        "btn_percent":      "📊 % Алерт",
        "btn_settings":     "⚙️ Настройки",
        "btn_about":        "ℹ️ О боте",
        "btn_lang":         "🌐 Язык",
        "btn_cancel":       "❌ Отмена",

        # Settings
        "settings_title": (
            "⚙️ <b>Настройки</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Выберите опцию:"
        ),
        "btn_back_settings": "◀️ Назад",

        # Main menu
        "menu_title": (
            "<b>🚀 Crypto Alert Bot</b>\n\n"
            "Отслеживаю цены 24/7 и мгновенно уведомляю!\n\n"
            "📋 Мои алерты\n"
            "➕ Новый алерт\n"
            "📊 % Алерт\n"
            "ℹ️ О боте"
        ),

        # Welcome
        "welcome": (
            "👋 Привет, <b>{name}</b>!\n\n"
            "Я отслеживаю цены криптовалют и уведомлю тебя,\n"
            "когда цена достигнет нужной отметки.\n\n"
            "Используй меню ниже 👇"
        ),

        # Alerts list
        "alerts_header": (
            "🔔 <b>Активные алерты</b> — {count} шт.\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Нажмите на алерт, чтобы удалить его:</i>"
        ),
        "no_alerts": (
            "📋 <b>Мои алерты</b>\n\n"
            "🔕 Активных алертов пока нет.\n"
            "Создайте свой первый алерт!"
        ),
        "all_alerts_deleted": (
            "📋 <b>Мои алерты</b>\n\n"
            "Все алерты удалены!\n"
            "Создайте новый алерт."
        ),

        # Alert creation wizard
        "alert_step1": (
            "➕ <b>Новый алерт</b> — Шаг 1/3\n\n"
            "Введите символ монеты:\n"
            "<code>BTC</code>, <code>ETH</code>, <code>SOL</code>...\n\n"
            "<i>USDT будет добавлен автоматически</i>"
        ),
        "alert_step2_found": (
            "✅ <b>Найдено!</b> — Шаг 2/3\n\n"
            "<b>{symbol}</b>\n"
            "Доступно на {count} биржах:\n"
            "{exchanges}"
        ),
        "alert_step3": (
            "🎯 <b>Укажите цену</b> — Шаг 3/3\n\n"
            "<b>{symbol}</b> • {exchange}\n"
            "Текущая цена: <code>${current_price}</code>\n\n"
            "Введите целевую цену:\n"
            "<i>Пример: 65000 или 0.5</i>"
        ),
        "alert_symbol_not_found": (
            "❌ <b>Не найдено</b>\n\n"
            "<code>{symbol}</code> недоступен.\n\n"
            "Попробуйте: BTC, ETH, SOL"
        ),
        "alert_price_invalid": (
            "❌ <b>Некорректная цена</b>\n\n"
            "Введите число:\n"
            "<code>65000</code> или <code>0.5</code>"
        ),

        # Alert created
        "alert_created": (
            "✅ <b>Алерт создан!</b>\n\n"
            "<b>{symbol}</b> • {exchange}\n"
            "Цель: <code>${target_price}</code>\n"
            "Расстояние: {distance}\n"
            "{direction_emoji} {direction}\n\n"
            "Вы получите уведомление!"
        ),

        # Delete confirmation
        "delete_confirm_title": (
            "❌ <b>Удалить алерт?</b>\n\n"
            "<b>{symbol}</b> • {exchange}\n"
            "Цель: <code>${target_price}</code>\n"
            "{direction_emoji} {direction}\n\n"
            "Вы уверены?"
        ),
        "alert_deleted": "✅ Алерт удалён!",
        "alert_not_found": "❌ Алерт не найден!",

        # Percentage alert
        "percent_coming_soon": (
            "📊 <b>Процентный алерт</b>\n\n"
            "🔧 <b>Скоро!</b>\n\n"
            "Получайте уведомления, когда цена изменится\n"
            "на определённый % от текущего значения.\n\n"
            "Пример: Алерт когда BTC ±5%"
        ),

        # About
        "about": (
            "ℹ️ <b>Crypto Alert Bot</b>\n\n"
            "<b>Возможности:</b>\n"
            "✅ Ценовые алерты\n"
            "✅ Мульти-биржа\n"
            "✅ Мониторинг 24/7\n"
            "🔜 % алерты\n"
            "🔜 Графики\n\n"
            "<b>Биржи:</b>\n"
            "{exchanges}\n"
            "Всего: ~{total_pairs} пар\n\n"
            "<b>Скоро:</b> NASDAQ, NYSE\n\n"
            "Создатель: @nikitayech"
        ),

        # Cancel
        "cancelled": "Отменено. Возврат в главное меню.",
        "nothing_to_cancel": "Нечего отменять.",

        # Buttons (Inline)
        "btn_create_first": "➕ Создать первый алерт",
        "btn_back_menu": "◀️ Назад в меню",
        "btn_yes_delete": "✅ Да, удалить",
        "btn_cancel_inline": "❌ Отмена",

        # Language
        "lang_select": "🌐 <b>Выберите язык / Select language:</b>",
        "lang_changed": "✅ Язык изменён на <b>Русский 🇷🇺</b>",

        # Errors
        "err_connection": "📡 Ошибка соединения. Попробуйте позже.",
    },

    # ──────────────────── ENGLISH ─────────────────────────────────────────────
    "en": {
        # Buttons (Reply Keyboard)
        "btn_alerts":       "📋 My Alerts",
        "btn_new_alert":    "➕ New Alert",
        "btn_percent":      "📊 % Alert",
        "btn_settings":     "⚙️ Settings",
        "btn_about":        "ℹ️ About",
        "btn_lang":         "🌐 Language",
        "btn_cancel":       "❌ Cancel",

        # Settings
        "settings_title": (
            "⚙️ <b>Settings</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose an option:"
        ),
        "btn_back_settings": "◀️ Back",

        # Main menu
        "menu_title": (
            "<b>🚀 Crypto Alert Bot</b>\n\n"
            "Track prices 24/7 and get instant notifications!\n\n"
            "📋 My Alerts\n"
            "➕ New Alert\n"
            "📊 % Alert\n"
            "ℹ️ About"
        ),

        # Welcome
        "welcome": (
            "👋 Hello, <b>{name}</b>!\n\n"
            "I track cryptocurrency prices and notify you\n"
            "when the price reaches your target.\n\n"
            "Use the menu below 👇"
        ),

        # Alerts list
        "alerts_header": (
            "🔔 <b>Active Alerts</b> — {count}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "<i>Tap an alert to delete it:</i>"
        ),
        "no_alerts": (
            "📋 <b>My Alerts</b>\n\n"
            "🔕 No active alerts yet.\n"
            "Create your first alert!"
        ),
        "all_alerts_deleted": (
            "📋 <b>My Alerts</b>\n\n"
            "All alerts deleted!\n"
            "Create a new alert."
        ),

        # Alert creation wizard
        "alert_step1": (
            "➕ <b>New Alert</b> — Step 1/3\n\n"
            "Enter coin symbol:\n"
            "<code>BTC</code>, <code>ETH</code>, <code>SOL</code>...\n\n"
            "<i>USDT will be added automatically</i>"
        ),
        "alert_step2_found": (
            "✅ <b>Found!</b> — Step 2/3\n\n"
            "<b>{symbol}</b>\n"
            "Available on {count} exchange(s):\n"
            "{exchanges}"
        ),
        "alert_step3": (
            "🎯 <b>Set Target</b> — Step 3/3\n\n"
            "<b>{symbol}</b> • {exchange}\n"
            "Current: <code>${current_price}</code>\n\n"
            "Enter your target price:\n"
            "<i>Example: 65000 or 0.5</i>"
        ),
        "alert_symbol_not_found": (
            "❌ <b>Not found</b>\n\n"
            "<code>{symbol}</code> is not available.\n\n"
            "Try: BTC, ETH, SOL"
        ),
        "alert_price_invalid": (
            "❌ <b>Invalid price</b>\n\n"
            "Enter a valid number:\n"
            "<code>65000</code> or <code>0.5</code>"
        ),

        # Alert created
        "alert_created": (
            "✅ <b>Alert Created!</b>\n\n"
            "<b>{symbol}</b> • {exchange}\n"
            "Target: <code>${target_price}</code>\n"
            "Distance: {distance}\n"
            "{direction_emoji} {direction}\n\n"
            "You'll be notified!"
        ),

        # Delete confirmation
        "delete_confirm_title": (
            "❌ <b>Delete Alert?</b>\n\n"
            "<b>{symbol}</b> • {exchange}\n"
            "Target: <code>${target_price}</code>\n"
            "{direction_emoji} {direction}\n\n"
            "Are you sure?"
        ),
        "alert_deleted": "✅ Alert deleted!",
        "alert_not_found": "❌ Alert not found!",

        # Percentage alert
        "percent_coming_soon": (
            "📊 <b>Percentage Alert</b>\n\n"
            "🔧 <b>Coming Soon!</b>\n\n"
            "Get notified when price changes\n"
            "by a certain % from current value.\n\n"
            "Example: Alert when BTC ±5%"
        ),

        # About
        "about": (
            "ℹ️ <b>Crypto Alert Bot</b>\n\n"
            "<b>Features:</b>\n"
            "✅ Price alerts\n"
            "✅ Multi-exchange\n"
            "✅ 24/7 monitoring\n"
            "🔜 % alerts\n"
            "🔜 Charts\n\n"
            "<b>Exchanges:</b>\n"
            "{exchanges}\n"
            "Total: ~{total_pairs} pairs\n\n"
            "<b>Coming:</b> NASDAQ, NYSE\n\n"
            "Created by @nikitayech"
        ),

        # Cancel
        "cancelled": "Cancelled. Returning to main menu.",
        "nothing_to_cancel": "Nothing to cancel.",

        # Buttons (Inline)
        "btn_create_first": "➕ Create First Alert",
        "btn_back_menu": "◀️ Back to Menu",
        "btn_yes_delete": "✅ Yes, Delete",
        "btn_cancel_inline": "❌ Cancel",

        # Language
        "lang_select": "🌐 <b>Выберите язык / Select language:</b>",
        "lang_changed": "✅ Language changed to <b>English 🇬🇧</b>",

        # Errors
        "err_connection": "📡 Connection error. Please try later.",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Return translated string for key in lang, with optional .format() kwargs."""
    text = TEXTS.get(lang, TEXTS["en"]).get(key) or TEXTS["en"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def all_langs(key: str) -> set[str]:
    """Return all translations for a key — used in F.text.in_(...) filters."""
    return {TEXTS[lang][key] for lang in TEXTS if key in TEXTS[lang]}
