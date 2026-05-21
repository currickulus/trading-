import MetaTrader5 as mt5
import datetime
import time
import csv
import os
import subprocess

MT5_PATH = "C:\\Program Files\\AMP Global (USA) MT5 Exchange-Traded Futures Only\\terminal64.exe"
SYMBOL = "@MYM"
OUTPUT = "C:\\Users\\thoma\\mym_live.csv"
CURRICKULUS = "x@192.168.0.48"
REMOTE_PATH = "/home/x/trading/mym_bars_sorted.csv"

def is_market_hours():
    now = datetime.datetime.utcnow()
    wd = now.weekday()
    h = now.hour
    # Sun 22:00 - Fri 21:00 UTC (CME Globex)
    if wd == 5: return False  # Saturday always closed
    if wd == 6 and h < 22: return False  # Sunday before open
    if wd == 4 and h >= 21: return False  # Friday after close
    return True

def load_existing():
    seen = set()
    if os.path.exists(OUTPUT):
        with open(OUTPUT, 'r') as f:
            for line in f:
                ts = line.split(',')[0].strip()
                if ts:
                    seen.add(ts)
    return seen

def run():
    print("MYM Collector starting...")
    mt5.initialize(MT5_PATH)
    seen = load_existing()
    print(f"Loaded {len(seen)} existing bars")

    while True:
        if not is_market_hours():
            print("Market closed, sleeping 5min...")
            mt5.shutdown()
            time.sleep(300)
            mt5.initialize(MT5_PATH)
            seen = load_existing()
            continue

        bars = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M1, 1, 50)
        if bars is None:
            print("No bars returned, retrying...")
            time.sleep(30)
            continue

        new_bars = []
        for b in bars:
            dt = datetime.datetime.fromtimestamp(b[0]).strftime('%Y-%m-%d %H:%M:%S')
            if dt not in seen:
                new_bars.append([dt, b[1], b[2], b[3], b[4], b[5]])
                seen.add(dt)

        if new_bars:
            with open(OUTPUT, 'a', newline='') as f:
                w = csv.writer(f)
                for bar in new_bars:
                    w.writerow(bar)
            print(f"Added {len(new_bars)} bars, total seen: {len(seen)}")

            # SCP to currickulus
            try:
                subprocess.run([
                    "scp", OUTPUT,
                    f"{CURRICKULUS}:{REMOTE_PATH}"
                ], timeout=30, capture_output=True)
                print("Synced to currickulus")
            except Exception as e:
                print(f"SCP failed: {e}")

        time.sleep(60)

if __name__ == '__main__':
    run()