from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.bot.states.states import CreateAlert, CreatePercentAlert
from app.bot.i18n import t, all_langs
from app.bot.keyboards import (
    MenuCallback,
    AlertCallback,
    ExchangeCallback,
    PercentCallback,
    LangCallback,
    get_main_menu,
    get_main_reply_keyboard,
    get_cancel_reply_keyboard,
    get_alerts_list_keyboard,
    get_empty_alerts_keyboard,
    get_confirm_delete_keyboard,
    get_exchange_keyboard,
    get_alert_created_keyboard,
    get_percent_selection_keyboard,
    get_percent_direction_keyboard,
    get_settings_keyboard,
    get_language_keyboard,
    get_about_keyboard,
    get_back_to_menu_keyboard,
)
import app.bot.services.alert_serv as alert_serv
from app.core.globals import AVAILABLE_COINS
from app.core.redis_db import redis_client

alert = Router()


# ═══════════════════════════════════════════════════════════════════
#                         HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def get_user_by_telegram_id(telegram_id: int, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).filter(User.telegram_id == telegram_id))
    return result.scalars().first()


def format_price(price: float) -> str:
    """Format price with appropriate decimal places."""
    if price >= 1:
        return f"{price:,.2f}"
    elif price >= 0.01:
        return f"{price:.4f}"
    else:
        return f"{price:.8f}"


def calculate_percentage_diff(current: float, target: float) -> float:
    """Calculate percentage difference between current and target price."""
    if current == 0:
        return 0
    return ((target - current) / current) * 100


def parse_price_input(text: str, current_price: float) -> float:
    """
    Parse user input and return calculated target price.
    Supports absolute prices and percentage changes.

    Formats:
    - Absolute: "65000", "0.5", "$65,000.50"
    - Percent: "-5%", "+20%", "-5", "+20"

    Returns:
        target_price: calculated price

    Raises ValueError if input is invalid.
    """
    original_text = text.strip()

    # Check if it's percentage (contains % symbol or starts with +/-)
    is_percent = "%" in original_text or (original_text and original_text[0] in "+-")

    # Clean input: remove spaces, $, %, and commas (thousand separators)
    clean = original_text.replace(" ", "").replace("$", "").replace("%", "").replace(",", "")

    if not clean:
        raise ValueError("Empty input")

    try:
        if is_percent:
            # Parse as percentage
            percent_value = float(clean)

            # Validate range: -99 to +99
            if percent_value < -99 or percent_value > 99:
                raise ValueError("Percentage must be between -99% and +99%")

            # Calculate target price
            target_price = current_price * (1 + percent_value / 100)
            return target_price
        else:
            # Parse as absolute price
            target_price = float(clean)

            # Validate it's positive
            if target_price <= 0:
                raise ValueError("Price must be positive")

            return target_price
    except ValueError:
        raise ValueError("Invalid price format")


async def get_user_lang(telegram_id: int) -> str:
    """Get user language from Redis, default to 'en'."""
    lang = await redis_client.get(f"lang:{telegram_id}")
    return lang if lang else "en"


async def set_user_lang(telegram_id: int, lang: str):
    """Save user language to Redis."""
    await redis_client.set(f"lang:{telegram_id}", lang)


# ═══════════════════════════════════════════════════════════════════
#                         MAIN MENU
# ═══════════════════════════════════════════════════════════════════

@alert.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    """Main entry point - shows the main menu with reply keyboard."""
    await state.clear()
    telegram_id = message.from_user.id

    # Check if user exists, if not - redirect to registration
    user = await get_user_by_telegram_id(telegram_id, session)
    if not user:
        from app.bot.services.user_serv import register_user
        await register_user(
            telegram_id=telegram_id,
            session=session,
            telegram_username=message.from_user.username
        )

    # Auto-detect language from Telegram on first visit
    existing_lang = await redis_client.get(f"lang:{telegram_id}")
    if not existing_lang:
        tg_lang = message.from_user.language_code or ""
        lang = "ru" if tg_lang.startswith("ru") else "en"
        await set_user_lang(telegram_id, lang)
    else:
        lang = existing_lang

    name = message.from_user.first_name or "User"

    await message.answer(
        t("welcome", lang, name=name),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )


@alert.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    """Show main menu via /menu command."""
    await state.clear()
    lang = await get_user_lang(message.from_user.id)

    await message.answer(
        t("menu_title", lang),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════
#                    REPLY KEYBOARD HANDLERS
# ═══════════════════════════════════════════════════════════════════

@alert.message(F.text.in_(all_langs("btn_alerts")))
async def reply_my_alerts(message: Message, session: AsyncSession, state: FSMContext):
    """Handle My Alerts button from reply keyboard."""
    await state.clear()
    lang = await get_user_lang(message.from_user.id)

    alerts = await alert_serv.get_all_active_alerts(
        telegram_id=message.from_user.id,
        session=session
    )

    if not alerts:
        await message.answer(
            t("no_alerts", lang),
            reply_markup=get_empty_alerts_keyboard(lang),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            t("alerts_header", lang, count=len(alerts)),
            reply_markup=get_alerts_list_keyboard(alerts, lang),
            parse_mode="HTML"
        )


@alert.message(F.text.in_(all_langs("btn_new_alert")))
async def reply_new_alert(message: Message, state: FSMContext):
    """Handle New Alert button from reply keyboard."""
    lang = await get_user_lang(message.from_user.id)
    await state.set_state(CreateAlert.waiting_for_symbol)

    await message.answer(
        t("alert_step1", lang),
        reply_markup=get_cancel_reply_keyboard(lang),
        parse_mode="HTML"
    )


@alert.message(F.text.in_(all_langs("btn_percent")))
async def reply_percent_alert(message: Message, state: FSMContext):
    """Handle Percentage Alert button from reply keyboard."""
    lang = await get_user_lang(message.from_user.id)
    await state.set_state(CreatePercentAlert.waiting_for_symbol)

    await message.answer(
        t("percent_coming_soon", lang),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )
    await state.clear()


@alert.message(F.text.in_(all_langs("btn_about")))
async def reply_about(message: Message, state: FSMContext):
    """Handle About button from reply keyboard."""
    await state.clear()
    lang = await get_user_lang(message.from_user.id)

    # Gather exchange statistics
    exchanges_info = []
    total_pairs = 0
    for exchange_name, coins in AVAILABLE_COINS.items():
        display_name = exchange_name.replace("_", " ").title()
        coin_count = len(coins)
        total_pairs += coin_count
        exchanges_info.append(f"• {display_name} — {coin_count} pairs")

    exchanges_text = "\n".join(exchanges_info) if exchanges_info else "No exchanges"

    await message.answer(
        t("about", lang, exchanges=exchanges_text, total_pairs=total_pairs),
        reply_markup=get_about_keyboard(lang),
        parse_mode="HTML"
    )


@alert.message(F.text.in_(all_langs("btn_settings")))
async def reply_settings(message: Message, state: FSMContext):
    """Handle Settings button from reply keyboard."""
    await state.clear()
    lang = await get_user_lang(message.from_user.id)

    await message.answer(
        t("settings_title", lang),
        reply_markup=get_settings_keyboard(lang),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════
#                   SETTINGS & LANGUAGE CALLBACKS
# ═══════════════════════════════════════════════════════════════════

@alert.callback_query(MenuCallback.filter(F.action == "settings"))
async def show_settings(callback: CallbackQuery, state: FSMContext):
    """Show settings menu."""
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)

    await callback.message.edit_text(
        t("settings_title", lang),
        reply_markup=get_settings_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()


@alert.callback_query(MenuCallback.filter(F.action == "language"))
async def show_language(callback: CallbackQuery):
    """Show language selection."""
    lang = await get_user_lang(callback.from_user.id)

    await callback.message.edit_text(
        t("lang_select", lang),
        reply_markup=get_language_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@alert.callback_query(LangCallback.filter())
async def change_language(callback: CallbackQuery, callback_data: LangCallback):
    """Change user language."""
    new_lang = callback_data.lang
    await set_user_lang(callback.from_user.id, new_lang)

    await callback.answer(t("lang_changed", new_lang), show_alert=False)

    # Show settings with new language
    await callback.message.edit_text(
        t("settings_title", new_lang),
        reply_markup=get_settings_keyboard(new_lang),
        parse_mode="HTML"
    )

    # Update reply keyboard with new language
    await callback.message.answer(
        t("menu_title", new_lang),
        reply_markup=get_main_reply_keyboard(new_lang),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════
#                   INLINE MENU CALLBACKS
# ═══════════════════════════════════════════════════════════════════

@alert.callback_query(MenuCallback.filter(F.action == "main_menu"))
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu."""
    await state.clear()
    lang = await get_user_lang(callback.from_user.id)

    await callback.message.edit_text(
        t("menu_title", lang),
        reply_markup=get_main_menu(lang),
        parse_mode="HTML"
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════
#                         CANCEL HANDLERS
# ═══════════════════════════════════════════════════════════════════

@alert.message(Command("cancel"), StateFilter("*"))
async def cancel_command_handler(message: Message, state: FSMContext):
    """Allows the user to cancel any process via /cancel."""
    lang = await get_user_lang(message.from_user.id)
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            t("nothing_to_cancel", lang),
            reply_markup=get_main_reply_keyboard(lang)
        )
        return

    await state.clear()
    await message.answer(
        t("cancelled", lang),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )


@alert.message(F.text.in_(all_langs("btn_cancel")))
async def cancel_button_handler(message: Message, state: FSMContext):
    """Handle Cancel button from reply keyboard."""
    lang = await get_user_lang(message.from_user.id)
    await state.clear()
    await message.answer(
        t("cancelled", lang),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════
#                         MY ALERTS (INLINE)
# ═══════════════════════════════════════════════════════════════════

@alert.callback_query(MenuCallback.filter(F.action == "my_alerts"))
async def show_my_alerts(callback: CallbackQuery, session: AsyncSession):
    """Display user's active alerts with delete buttons."""
    lang = await get_user_lang(callback.from_user.id)


    alerts = await alert_serv.get_all_active_alerts(
        telegram_id=callback.from_user.id,
        session=session
    )

    if alerts is None:
        await callback.message.edit_text(
            t("user_not_found use /start", lang),
            reply_markup=get_main_menu(lang),
            parse_mode="HTML"
        )
        await callback.answer()
        return
    

    if len(alerts) == 0:
        await callback.message.edit_text(
            t("no_alerts", lang),
            reply_markup=get_empty_alerts_keyboard(lang),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            t("alerts_header", lang, count=len(alerts)),
            reply_markup=get_alerts_list_keyboard(alerts, lang),
            parse_mode="HTML"
        )
    await callback.answer()


@alert.callback_query(AlertCallback.filter(F.action == "delete"))
async def confirm_delete_alert(callback: CallbackQuery, callback_data: AlertCallback, session: AsyncSession):
    """Ask for confirmation before deleting alert."""
    lang = await get_user_lang(callback.from_user.id)
    alert_obj = await alert_serv.get_alert_by_id(callback_data.alert_id, session)

    if not alert_obj:
        await callback.answer(t("alert_not_found", lang), show_alert=True)
        return

    price_str = format_price(float(alert_obj.target_price))
    exchange_display = alert_obj.exchange.replace("_", " ").title()
    direction_emoji = "📈" if alert_obj.direction == "ABOVE" else "📉"
    direction_text = "above" if alert_obj.direction == "ABOVE" else "below"

    await callback.message.edit_text(
        t("delete_confirm_title", lang,
          symbol=alert_obj.symbol,
          exchange=exchange_display,
          target_price=price_str,
          direction_emoji=direction_emoji,
          direction=direction_text),
        reply_markup=get_confirm_delete_keyboard(callback_data.alert_id, lang),
        parse_mode="HTML"
    )
    await callback.answer()


@alert.callback_query(AlertCallback.filter(F.action == "confirm_delete"))
async def delete_alert(callback: CallbackQuery, callback_data: AlertCallback, session: AsyncSession):
    """Delete alert and return to alerts list."""
    lang = await get_user_lang(callback.from_user.id)
    await alert_serv.delete_alert(callback_data.alert_id, session)

    # Get remaining alerts to show updated list
    alerts = await alert_serv.get_all_active_alerts(
        telegram_id=callback.from_user.id,
        session=session
    )

    await callback.answer(t("alert_deleted", lang), show_alert=False)

    if not alerts:
        await callback.message.edit_text(
            t("all_alerts_deleted", lang),
            reply_markup=get_empty_alerts_keyboard(lang),
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            t("alerts_header", lang, count=len(alerts)),
            reply_markup=get_alerts_list_keyboard(alerts, lang),
            parse_mode="HTML"
        )


# ═══════════════════════════════════════════════════════════════════
#                         NEW ALERT CREATION
# ═══════════════════════════════════════════════════════════════════

@alert.callback_query(MenuCallback.filter(F.action == "new_alert"))
async def start_new_alert(callback: CallbackQuery, state: FSMContext):
    """Start new alert creation process."""
    lang = await get_user_lang(callback.from_user.id)
    await state.set_state(CreateAlert.waiting_for_symbol)

    await callback.message.edit_text(
        t("alert_step1", lang),
        parse_mode="HTML"
    )
    await callback.answer()


@alert.message(CreateAlert.waiting_for_symbol)
async def process_symbol(message: Message, state: FSMContext):
    """Process coin symbol and show exchange selection."""
    lang = await get_user_lang(message.from_user.id)

    # Check if user pressed cancel
    if message.text in all_langs("btn_cancel"):
        await state.clear()
        await message.answer(
            t("cancelled", lang),
            reply_markup=get_main_reply_keyboard(lang),
            parse_mode="HTML"
        )
        return

    user_input = message.text.strip().upper()
    symbol = f"{user_input}USDT" if not user_input.endswith("USDT") else user_input

    available_markets = await alert_serv.find_exchanges_for_symbol(symbol)

    if not available_markets:
        await message.answer(
            t("alert_symbol_not_found", lang, symbol=symbol),
            reply_markup=get_cancel_reply_keyboard(lang),
            parse_mode="HTML"
        )
        return

    await state.update_data(chosen_symbol=symbol)
    await state.set_state(CreateAlert.waiting_for_exchange)

    exchanges_list = "\n".join([f"• {ex['name']}" for ex in available_markets])

    await message.answer(
        t("alert_step2_found", lang,
          symbol=symbol,
          count=len(available_markets),
          exchanges=exchanges_list),
        reply_markup=get_exchange_keyboard(available_markets, lang),
        parse_mode="HTML"
    )


@alert.callback_query(CreateAlert.waiting_for_exchange, ExchangeCallback.filter())
async def process_exchange_selection(callback: CallbackQuery, callback_data: ExchangeCallback, state: FSMContext):
    """Save exchange and ask for target price."""
    lang = await get_user_lang(callback.from_user.id)
    selected_exchange = callback_data.exchange

    user_data = await state.get_data()
    symbol = user_data.get("chosen_symbol")

    current_price = await alert_serv.get_current_price(symbol, selected_exchange)

    await state.update_data(exchange=selected_exchange, current_price=current_price)
    await state.set_state(CreateAlert.waiting_for_price)

    display_name = selected_exchange.replace("_", " ").title()

    await callback.message.edit_text(
        t("alert_step3", lang,
          symbol=symbol,
          exchange=display_name,
          current_price=format_price(current_price)),
        parse_mode="HTML"
    )
    await callback.answer()


@alert.message(CreateAlert.waiting_for_price)
async def process_price(message: Message, state: FSMContext, session: AsyncSession):
    """Validate price and create alert."""
    lang = await get_user_lang(message.from_user.id)

    # Check if user pressed cancel
    if message.text in all_langs("btn_cancel"):
        await state.clear()
        await message.answer(
            t("cancelled", lang),
            reply_markup=get_main_reply_keyboard(lang),
            parse_mode="HTML"
        )
        return

    # Get current state data first (to access current_price for percent calculations)
    data = await state.get_data()
    symbol = data.get("chosen_symbol")
    exchange = data.get("exchange")
    current_price = data.get("current_price")

    # Parse user input - supports both absolute prices and percentages
    try:
        target_price = parse_price_input(message.text, current_price)
    except ValueError:
        await message.answer(
            t("alert_price_invalid", lang),
            reply_markup=get_cancel_reply_keyboard(lang),
            parse_mode="HTML"
        )
        return

    direction = "ABOVE" if target_price > current_price else "BELOW"

    user = await get_user_by_telegram_id(message.from_user.id, session)

    if not user:
        await message.answer(
            "❌ Error: User not found. Please restart with /start",
            reply_markup=get_main_reply_keyboard(lang),
            parse_mode="HTML"
        )
        await state.clear()
        return

    try:
        alert_db_obj = await alert_serv.post_alert_to_database(
            user_id=user.id,
            symbol=symbol,
            exchange=exchange,
            direction=direction,
            target_price=target_price,
            session=session
        )
    except ValueError as e:
        await message.answer(
            f"❌ Error creating alert: {str(e)}",
            reply_markup=get_cancel_reply_keyboard(lang),
            parse_mode="HTML"
        )
        await state.clear()
        return

    await alert_serv.put_alert_in_redis(
        user_id=user.id,
        telegram_id=message.from_user.id,
        symbol=symbol,
        exchange=exchange,
        target_price=target_price,
        direction=direction,
        alert_id=alert_db_obj.id
    )

    display_exchange = exchange.replace("_", " ").title()
    direction_emoji = "📈" if direction == "ABOVE" else "📉"
    direction_text = "above" if direction == "ABOVE" else "below"

    # Calculate percentage difference
    diff_percent = calculate_percentage_diff(current_price, target_price)
    diff_sign = "+" if diff_percent > 0 else ""
    distance = f"{diff_sign}{diff_percent:.2f}%"

    await message.answer(
        t("alert_created", lang,
          symbol=symbol,
          exchange=display_exchange,
          target_price=format_price(target_price),
          distance=distance,
          direction_emoji=direction_emoji,
          direction=direction_text),
        reply_markup=get_main_reply_keyboard(lang),
        parse_mode="HTML"
    )

    await state.clear()


# ═══════════════════════════════════════════════════════════════════
#                            ABOUT
# ═══════════════════════════════════════════════════════════════════

@alert.callback_query(MenuCallback.filter(F.action == "about"))
async def show_about(callback: CallbackQuery):
    """Show bot information and exchange statistics."""
    lang = await get_user_lang(callback.from_user.id)

    # Gather exchange statistics
    exchanges_info = []
    total_pairs = 0

    for exchange_name, coins in AVAILABLE_COINS.items():
        display_name = exchange_name.replace("_", " ").title()
        coin_count = len(coins)
        total_pairs += coin_count
        exchanges_info.append(f"• {display_name} — {coin_count} pairs")

    exchanges_text = "\n".join(exchanges_info) if exchanges_info else "No exchanges"

    await callback.message.edit_text(
        t("about", lang, exchanges=exchanges_text, total_pairs=total_pairs),
        reply_markup=get_about_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()
