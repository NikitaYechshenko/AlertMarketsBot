AVAILABLE_COINS = {
    "binance_futures": set(),  # Binance futures will be here
    "binance_spot": set(),  # Binance spot will be here
}

URLS = {
    "binance_spot": "https://www.binance.com/en/futures/{symbol}",
    "binance_futures": "https://www.binance.com/en/delivery/{symbol}",
}
