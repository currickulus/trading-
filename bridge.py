import MetaTrader5 as mt5
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def connect_mt5():
    if not mt5.initialize():
        print("MT5 init failed:", mt5.last_error())
        return False
    print("MT5 connected:", mt5.terminal_info().name)
    return True

@app.route('/api/price')
def get_price():
    for sym in ["MYM", "MYMM6", "#MYM", "MYM", "MYM$", "MYMM26"]:
        tick = mt5.symbol_info_tick(sym)
        if tick:
            return jsonify({"symbol": sym, "bid": tick.bid, "ask": tick.ask, "last": tick.last, "time": tick.time})
    return jsonify({"error": "no tick"})

@app.route('/api/bars')
def get_bars():
    for sym in ["MYM", "MYMM6", "#MYM", "MYM", "MYM$", "MYMM26"]:
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 60)
        if rates is not None and len(rates) > 0:
            bars = [{"t": int(r['time']), "o": float(r['open']), "h": float(r['high']), "l": float(r['low']), "c": float(r['close']), "v": int(r['tick_volume'])} for r in rates]
            return jsonify({"symbol": sym, "bars": bars})
    return jsonify({"error": "no bars"})

@app.route('/api/symbols')
def get_symbols():
    # Get all symbols including those not in market watch
    symbols = mt5.symbols_get()
    all_names = [s.name for s in symbols] if symbols else []
    mym = [n for n in all_names if 'MYM' in n.upper() or 'DOW' in n.upper() or 'MICRO' in n.upper()]
    return jsonify({"mym_symbols": mym, "total_symbols": len(all_names), "sample": all_names[:20]})

@app.route('/api/status')
def status():
    info = mt5.terminal_info()
    return jsonify({"connected": info is not None, "broker": info.name if info else None})

if __name__ == '__main__':
    connect_mt5()
    app.run(host='0.0.0.0', port=5000, debug=False)
