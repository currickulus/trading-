import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Initialize MT5 connection
def initialize_mt5():
    print("Attempting to initialize MT5...")
    if not mt5.initialize():
        error_code, error_msg = mt5.last_error()
        print(f"MT5 initialization failed, error code: {error_code}, message: {error_msg}")
        return False
    print("MT5 initialized successfully")
    return True

# Login to AMP Futures MT5 demo account
def login_mt5(account, password, server):
    print(f"Attempting to log in to account {account} on server {server}...")
    if not mt5.login(account, password=password, server=server):
        error_code, error_msg = mt5.last_error()
        print(f"Login failed, error code: {error_code}, message: {error_msg}")
        mt5.shutdown()
        return False
    print(f"Logged in to account {account}")
    return True

# Check if MT5 connection is active
def check_mt5_connection():
    if not mt5.terminal_info():
        print("MT5 connection lost. Attempting to reconnect...")
        if not mt5.initialize():
            print("Reconnection failed. Please check MT5 terminal.")
            return False
    return True

# Check if the market is open (Micro E-mini Dow futures schedule)
def is_market_open():
    now = datetime.now(timezone.utc)
    now_et = now.astimezone(ZoneInfo("America/New_York"))  # Eastern Time
    day_of_week = now_et.weekday()  # 0 = Monday, 4 = Friday, 6 = Sunday
    hour = now_et.hour
    minute = now_et.minute
    
    # Market is open Sunday 6:00 PM ET to Friday 5:00 PM ET, with a daily break 5:00 PM to 6:00 PM ET
    if day_of_week == 4 and hour >= 17:  # Friday after 5:00 PM ET
        return False
    if day_of_week == 5:  # Saturday
        return False
    if day_of_week == 6 and (hour < 18 or (hour == 18 and minute < 0)):  # Sunday before 6:00 PM ET
        return False
    if hour == 17 and 0 <= minute < 0:  # Daily break 5:00 PM to 6:00 PM ET
        return False
    
    return True

# Fetch 5-minute bar data
def get_market_data(symbol, lookback=1440):
    if not mt5.symbol_select(symbol, True):
        print(f"Symbol {symbol} not available. Check if MYMM25 is still active or if the contract has rolled over.")
        return None
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, lookback)
    if rates is None or len(rates) == 0:
        print("Failed to retrieve market data. Market may be closed or no new data available.")
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

# Calculate probabilities for each candle using a rolling window and volume weighting
def calculate_probabilities_for_candles(df, window=100):
    if df is None or len(df) == 0:
        return df
    
    df['buy_prob'] = 0.0
    df['sell_prob'] = 0.0
    df['change'] = (df['close'] - df['open']) / df['open'] * 100  # Calculate percentage change
    
    if 'tick_volume' in df.columns and df['tick_volume'].sum() > 0:
        df['volume_weight'] = df['tick_volume'] / df['tick_volume'].max()
    else:
        df['volume_weight'] = 1.0
    
    for i in range(len(df)):
        start_idx = max(0, i - window + 1)
        temp_df = df.iloc[start_idx:i+1]
        
        total_weight = temp_df['volume_weight'].sum()
        if total_weight > 0:
            buy_weight = temp_df[temp_df['change'] > 0].apply(
                lambda x: x['volume_weight'] * abs(x['change']), axis=1
            ).sum()
            sell_weight = temp_df[temp_df['change'] < 0].apply(
                lambda x: x['volume_weight'] * abs(x['change']), axis=1
            ).sum()
            
            total_change_weight = buy_weight + sell_weight
            if total_change_weight > 0:
                df.at[i, 'buy_prob'] = (buy_weight / total_change_weight) * 100
                df.at[i, 'sell_prob'] = (sell_weight / total_change_weight) * 100
            else:
                df.at[i, 'buy_prob'] = 50.0  # Neutral if no significant movement
                df.at[i, 'sell_prob'] = 50.0
        else:
            df.at[i, 'buy_prob'] = 50.0
            df.at[i, 'sell_prob'] = 50.0
    
    return df

# Update the scrollable table with new data
def update_table(root, tree, symbol, lookback, window, last_timestamp, status_label, update_interval=10000):
    try:
        # Check if market is open
        if not is_market_open():
            now_et = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
            status_label.config(text=f"Status: Market closed until Sunday 6:00 PM ET (Current: {now_et.strftime('%H:%M:%S')})")
            root.after(update_interval, update_table, root, tree, symbol, lookback, window, last_timestamp, status_label, update_interval)
            return
        
        # Check MT5 connection
        if not check_mt5_connection():
            status_label.config(text="Status: MT5 connection lost")
            root.after(update_interval, update_table, root, tree, symbol, lookback, window, last_timestamp, status_label, update_interval)
            return
        
        df = get_market_data(symbol, lookback)
        if df is None or len(df) == 0:
            status_label.config(text="Status: No new data (market may be closed)")
            root.after(update_interval, update_table, root, tree, symbol, lookback, window, last_timestamp, status_label, update_interval)
            return
        
        df = calculate_probabilities_for_candles(df, window)
        new_last_timestamp = df['time'].iloc[-1]
        
        print(f"Latest candle timestamp: {new_last_timestamp}")
        
        if last_timestamp is None or new_last_timestamp > last_timestamp:
            for item in tree.get_children():
                tree.delete(item)
            
            for index, row in df.iterrows():
                tree.insert('', 'end', values=(
                    row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    f"{row['open']:.2f}",
                    f"{row['high']:.2f}",
                    f"{row['low']:.2f}",
                    f"{row['close']:.2f}",
                    f"{row['tick_volume']}",
                    f"{row['buy_prob']:.2f}",
                    f"{row['sell_prob']:.2f}"
                ))
            
            print(f"Table updated at {datetime.now()} with {len(df)} candles")
            status_label.config(text=f"Status: Updated at {datetime.now().strftime('%H:%M:%S')}")
            last_timestamp = new_last_timestamp
        else:
            print(f"No new data at {datetime.now()}. Last candle: {last_timestamp}")
            status_label.config(text=f"Status: No new data (last: {last_timestamp.strftime('%H:%M:%S')})")
        
    except Exception as e:
        print(f"Error updating table: {e}")
        status_label.config(text=f"Status: Error - {str(e)}")
    
    root.after(update_interval, update_table, root, tree, symbol, lookback, window, last_timestamp, status_label, update_interval)

def main():
    # AMP Futures MT5 demo account details
    account = 1521612
    password = "Z*Fi1eLo"
    server = "AMPGlobalUSA-Demo"
    symbol = "MYMM25"
    lookback = 1440
    window = 100
    update_interval = 10000

    # Initialize and login
    if not initialize_mt5():
        return
    if not login_mt5(account, password, server):
        return

    # Fetch initial market data
    df = get_market_data(symbol, lookback)
    if df is None:
        print("No data retrieved. Exiting...")
        mt5.shutdown()
        return

    # Calculate initial probabilities
    df = calculate_probabilities_for_candles(df, window)
    if df is None or len(df) == 0:
        print("No data to display. Exiting...")
        mt5.shutdown()
        return

    # Create GUI
    root = tk.Tk()
    root.title("Micro E-mini Dow Historical Probabilities (Live)")
    root.geometry("900x600")

    # Status label
    status_label = tk.Label(root, text="Status: Initializing...", font=("Arial", 10))
    status_label.pack(pady=5)

    # Create a frame for the table
    table_frame = ttk.Frame(root)
    table_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Create a Treeview widget (table)
    columns = ('Time', 'Open', 'High', 'Low', 'Close', 'Tick Volume', 'Buy Prob (%)', 'Sell Prob (%)')
    tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

    # Set column headings
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor='center')

    # Add a scrollbar
    scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    tree.pack(fill='both', expand=True)

    # Insert initial data into the table
    for index, row in df.iterrows():
        tree.insert('', 'end', values=(
            row['time'].strftime('%Y-%m-%d %H:%M:%S'),
            f"{row['open']:.2f}",
            f"{row['high']:.2f}",
            f"{row['low']:.2f}",
            f"{row['close']:.2f}",
            f"{row['tick_volume']}",
            f"{row['buy_prob']:.2f}",
            f"{row['sell_prob']:.2f}"
        ))

    last_timestamp = df['time'].iloc[-1]
    print(f"Initial last timestamp: {last_timestamp}")

    # Start continuous updates
    root.after(update_interval, update_table, root, tree, symbol, lookback, window, last_timestamp, status_label, update_interval)

    # Handle window close
    def on_closing():
        mt5.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start GUI
    try:
        root.mainloop()
    except KeyboardInterrupt:
        mt5.shutdown()
        print("Program terminated")

if __name__ == "__main__":
    main()