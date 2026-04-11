from app.exchanges.Binance.binance_f import get_binance_current_f_price
from app.exchanges.Binance.binance_spot import get_binance_current_spot_price


AVAILABLE_COINS = {
    "binance_futures": set(),  # Binance futures will be here
    "binance_spot": set(),  # Binance spot will be here
}

PRICE_FETCHERS = {
    "binance_spot": get_binance_current_spot_price,
    "binance_futures": get_binance_current_f_price,
}
