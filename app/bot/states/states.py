from aiogram.fsm.state import State, StatesGroup


class CreateAlert(StatesGroup):
    """States for creating a price alert."""
    waiting_for_symbol = State()
    waiting_for_exchange = State()
    waiting_for_price = State()


class CreatePercentAlert(StatesGroup):
    """States for creating a percentage-based alert."""
    waiting_for_symbol = State()
    waiting_for_exchange = State()
    waiting_for_percent = State()
    waiting_for_custom_percent = State()
    waiting_for_direction = State()