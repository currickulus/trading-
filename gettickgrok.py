import os
import time
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve login credentials from .env
MT5_LOGIN = int(os.getenv("MT5_LOGIN"))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")

# Initialize MetaTrader 5 connection
def connect_to_mt5():
    if not mt5.initialize(login=MT5_LOGIN, server=MT5_SERVER, password=MT5_PASSWORD):
        print("Failed to initialize MT5, error code:", mt5.last_error())
        return False
    print("Connected to MetaTrader 5")
    return True

# Function to decode tick flags for buy/sell identification
def buy_or_sell(flag):
    # MetaTrader 5 flags: 32 for buy-initiated, 64 for sell-initiated
    if flag & 32 and flag & 64:
        return "both"
    elif flag & 32:
        return "buy"
    elif flag & 64:
        return "sell"
    return "unknown"

# Function to fetch and process real-time tick data
def get_realtime_volume(symbol, duration_seconds=60):
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select symbol {symbol}")
        return None

    # Get the current time for the tick range
    utc_to = datetime.now()
    utc_from = utc_to - pd.Timedelta(seconds=duration_seconds)

    # Fetch tick data
    ticks = mt5.copy_ticks_range(symbol, utc_from, utc_to, mt5.COPY_TICKS_TRADE)
    if ticks is None or len(ticks) == 0:
        print(f"No tick data retrieved for {symbol}")
        return None

    # Convert to DataFrame
    ticks_df = pd.DataFrame(ticks)
    ticks_df['time'] = pd.to_datetime(ticks_df['time'], unit='s')
    
    # Decode buy/sell from flags
    ticks_df['trade_type'] = ticks_df['flags'].apply(buy_or_sell)
    
    # Calculate buy and sell volumes
    buy_volume = ticks_df[ticks_df['trade_type'] == 'buy']['volume'].sum()
    sell_volume = ticks_df[ticks_df['trade_type'] == 'sell']['volume'].sum()
    
    return {
        'symbol': symbol,
        'buy_volume': buy_volume,
        'sell_volume': sell_volume,
        'last_update': ticks_df['time'].iloc[-1] if not ticks_df.empty else utc_to
    }

def main():
    # Connect to MT5
    if not connect_to_mt5():
        return

    # Symbol to monitor (e.g., EURUSD)
    symbol = "EURUSD"  # Change to your desired symbol
    poll_interval = 5  # Seconds between updates

    try:
        while True:
            # Fetch real-time volume data
            volume_data = get_realtime_volume(symbol)
            if volume_data:
                print(f"[{volume_data['last_update']}] {symbol} - "
                      f"Buy Volume: {volume_data['buy_volume']}, "
                      f"Sell Volume: {volume_data['sell_volume']}")
            else:
                print(f"[{datetime.now()}] No data for {symbol}")

            # Wait before fetching again
            time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\nStopped by user")
    finally:
        mt5.shutdown()
        print("Disconnected from MetaTrader 5")

if __name__ == "__main__":
    main()