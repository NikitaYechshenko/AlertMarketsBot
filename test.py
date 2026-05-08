import asyncio
import websockets
import json
from datetime import datetime

async def binance_all_tickers():
    # Актуальный эндпоинт после обновления 2026 года
    url = "wss://fstream.binance.com/market/ws/!miniTicker@arr"
    
    while True:
        try:
            print(f"[{datetime.now()}] Подключение к Binance...")
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                print("Соединение установлено. Получаю данные по всем монетам...")
                
                while True:
                    data = await ws.recv()
                    tickers = json.loads(data)
                    
                    # tickers — это список словарей для каждой монеты
                    # Выведем количество монет и цену BTC для проверки
                    btc = next((item for item in tickers if item["s"] == "BTCUSDT"), None)
                    
                    print(f"Обновлено монет: {len(tickers)} | BTC: {btc['c'] if btc else 'N/A'}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("Соединение разорвано. Повторное подключение через 5 секунд...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(binance_all_tickers())
    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")