from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from app.bot.i18n import t


# ═══════════════════════════════════════════════════════════════════
#                      CALLBACK DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

class MenuCallback(CallbackData, prefix="menu"):
    action: str


class AlertCallback(CallbackData, prefix="alert"):
    action: str
    alert_id: int = 0


class ExchangeCallback(CallbackData, prefix="exchange"):
    exchange: str


class PercentCallback(CallbackData, prefix="percent"):
    action: str
    value: int = 0


class LangCallback(CallbackData, prefix="lang"):
    lang: str


# ═══════════════════════════════════════════════════════════════════
#                    REPLY KEYBOARD (BOTTOM BUTTONS)
# ═══════════════════════════════════════════════════════════════════

def get_main_reply_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Persistent bottom keyboard with main menu options."""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text=t("btn_alerts", lang)),
        KeyboardButton(text=t("btn_new_alert", lang))
    )
    builder.row(
        KeyboardButton(text=t("btn_percent", lang)),
        KeyboardButton(text=t("btn_settings", lang))
    )

    return builder.as_markup(resize_keyboard=True, is_persistent=True)


def get_cancel_reply_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Cancel button at the bottom during alert creation."""
    builder = ReplyKeyboardBuilder()

    builder.row(
        KeyboardButton(text=t("btn_cancel", lang))
    )

    return builder.as_markup(resize_keyboard=True, is_persistent=True)


# ═══════════════════════════════════════════════════════════════════
#                         MAIN MENU (INLINE)
# ═══════════════════════════════════════════════════════════════════

def get_main_menu(lang: str = "en") -> InlineKeyboardMarkup:
    """Modern main menu with 4 options."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_alerts", lang),
            callback_data=MenuCallback(action="my_alerts").pack()
        ),
        InlineKeyboardButton(
            text=t("btn_new_alert", lang),
            callback_data=MenuCallback(action="new_alert").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_percent", lang),
            callback_data=MenuCallback(action="percent_alert").pack()
        ),
        InlineKeyboardButton(
            text=t("btn_about", lang),
            callback_data=MenuCallback(action="about").pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                      MY ALERTS MENU
# ═══════════════════════════════════════════════════════════════════

def format_price_short(price: float) -> str:
    """Format price for display in buttons."""
    if price >= 1000:
        return f"{price:,.0f}"
    elif price >= 1:
        return f"{price:.2f}"
    elif price >= 0.01:
        return f"{price:.4f}"
    else:
        return f"{price:.6f}"


def get_alerts_list_keyboard(alerts: list, lang: str = "en") -> InlineKeyboardMarkup:
    """
    Generates keyboard with user alerts.
    Format: 🗑 TICKER | Exchange | → price
    """
    builder = InlineKeyboardBuilder()

    for alert in alerts:
        price_str = format_price_short(float(alert.target_price))
        exchange_display = alert.exchange.replace("_", " ").title()

        direction_emoji = "📈" if alert.direction == "ABOVE" else "📉"

        alert_text = f"🗑 {alert.symbol} | {exchange_display} | {direction_emoji} ${price_str}"

        builder.row(
            InlineKeyboardButton(
                text=alert_text,
                callback_data=AlertCallback(action="delete", alert_id=alert.id).pack()
            )
        )

    return builder.as_markup()


def get_empty_alerts_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard when user has no alerts - empty (no buttons)."""
    builder = InlineKeyboardBuilder()
    return builder.as_markup()


def get_confirm_delete_keyboard(alert_id: int, lang: str = "en") -> InlineKeyboardMarkup:
    """Confirmation keyboard for deleting an alert. Cancel left, Yes Delete right."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel_inline", lang),
            callback_data=MenuCallback(action="my_alerts").pack()
        ),
        InlineKeyboardButton(
            text=t("btn_yes_delete", lang),
            callback_data=AlertCallback(action="confirm_delete", alert_id=alert_id).pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                      NEW ALERT KEYBOARDS
# ═══════════════════════════════════════════════════════════════════

def get_exchange_keyboard(exchanges: list[dict], lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for selecting exchange."""
    builder = InlineKeyboardBuilder()

    exchange_emojis = {
        "binance_spot": "🟡",
        "binance_futures": "🟠",
        "bybit": "🔵",
        "kucoin": "🟢",
    }

    for exchange in exchanges:
        emoji = exchange_emojis.get(exchange["data"], "📊")
        display_text = f"{emoji} {exchange['name']}"

        builder.row(
            InlineKeyboardButton(
                text=display_text,
                callback_data=ExchangeCallback(exchange=exchange["data"]).pack()
            )
        )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel_inline", lang),
            callback_data=MenuCallback(action="main_menu").pack()
        )
    )

    return builder.as_markup()


def get_cancel_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Simple cancel keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_cancel_inline", lang),
            callback_data=MenuCallback(action="main_menu").pack()
        )
    )

    return builder.as_markup()


def get_alert_created_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard shown after alert creation."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_new_alert", lang),
            callback_data=MenuCallback(action="new_alert").pack()
        ),
        InlineKeyboardButton(
            text=t("btn_alerts", lang),
            callback_data=MenuCallback(action="my_alerts").pack()
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data=MenuCallback(action="main_menu").pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                    PERCENTAGE ALERT KEYBOARDS
# ═══════════════════════════════════════════════════════════════════

def get_percent_selection_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for selecting percentage change threshold."""
    builder = InlineKeyboardBuilder()

    percentages = [1, 2, 3, 5, 10, 15, 20, 25]

    row = []
    for percent in percentages:
        row.append(
            InlineKeyboardButton(
                text=f"{percent}%",
                callback_data=PercentCallback(action="select", value=percent).pack()
            )
        )
        if len(row) == 4:
            builder.row(*row)
            row = []

    if row:
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(
            text="✏️ Custom %",
            callback_data=PercentCallback(action="custom").pack()
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data=MenuCallback(action="main_menu").pack()
        )
    )

    return builder.as_markup()


def get_percent_direction_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for selecting direction of percentage change."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text="📈 Up",
            callback_data=PercentCallback(action="direction_up").pack()
        ),
        InlineKeyboardButton(
            text="📉 Down",
            callback_data=PercentCallback(action="direction_down").pack()
        ),
        InlineKeyboardButton(
            text="↕️ Both",
            callback_data=PercentCallback(action="direction_both").pack()
        )
    )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data=MenuCallback(action="percent_alert").pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                         SETTINGS KEYBOARD
# ═══════════════════════════════════════════════════════════════════

def get_settings_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for Settings menu with Language and About options."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_lang", lang),
            callback_data=MenuCallback(action="language").pack()
        ),
        InlineKeyboardButton(
            text=t("btn_about", lang),
            callback_data=MenuCallback(action="about").pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                         LANGUAGE KEYBOARD
# ═══════════════════════════════════════════════════════════════════

def get_language_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for language selection."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data=LangCallback(lang="ru").pack()),
        InlineKeyboardButton(text="🇬🇧 English", callback_data=LangCallback(lang="en").pack())
    )

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back_settings", lang),
            callback_data=MenuCallback(action="settings").pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                         ABOUT KEYBOARD
# ═══════════════════════════════════════════════════════════════════

def get_about_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for About section."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back_settings", lang),
            callback_data=MenuCallback(action="settings").pack()
        )
    )

    return builder.as_markup()


# ═══════════════════════════════════════════════════════════════════
#                      BACK BUTTON
# ═══════════════════════════════════════════════════════════════════

def get_back_to_menu_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Simple back to menu keyboard."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=t("btn_back_menu", lang),
            callback_data=MenuCallback(action="main_menu").pack()
        )
    )

    return builder.as_markup()
