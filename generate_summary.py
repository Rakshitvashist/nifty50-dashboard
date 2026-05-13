import pandas as pd
import glob
import os
import json
from datetime import datetime
import talib
import numpy as np

def generate_summary():
    data_dir = "processed_indicators"
    output_file = os.path.join("dashboard", "public", "summary.json")
    
    # Ensure dashboard/public exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    files = glob.glob(os.path.join(data_dir, "*_with_indicators.csv"))
    summary = []
    
    print(f"Aggregating data from {len(files)} files...")
    
    for file_path in files:
        try:
            # Read only last 100 rows for charts and latest indicators
            # We read everything first to get headers and index properly
            df = pd.read_csv(file_path)
            if df.empty:
                continue
                
            # Get latest row and handle NaNs
            df = df.fillna(0)
            
            # Calculate Raw Indicators for display
            C = df['close'].values
            H = df['high'].values
            L = df['low'].values
            V = df['volume'].values
            
            raw_rsi = talib.RSI(C, timeperiod=14)[-1]
            macd, macdsignal, macdhist = talib.MACD(C, fastperiod=12, slowperiod=26, signalperiod=9)
            raw_macd = macdhist[-1]
            raw_adx = talib.ADX(H, L, C, timeperiod=14)[-1]
            upper, middle, lower = talib.BBANDS(C, timeperiod=20, nbdevup=2, nbdevdn=2)
            raw_bb_pos = (C[-1] - lower[-1]) / (upper[-1] - lower[-1] + 1e-10)
            raw_atr = talib.ATR(H, L, C, timeperiod=14)[-1]
            
            latest = df.iloc[-1]
            symbol = os.path.basename(file_path).split('_')[0]
            
            # Calculate Consensus Score
            indicator_cols = [c for c in df.columns if any(x in c for x in ['above', 'cross', 'signal', 'supertrend', 'oversold', 'overbought'])]
            
            if indicator_cols:
                consensus = df[indicator_cols].iloc[-1].mean()
            else:
                consensus = 0.0
                
            # Get historical data for chart (last 100 days)
            chart_data = []
            hist_df = df.tail(100)
            for _, row in hist_df.iterrows():
                chart_data.append({
                    "time": str(row['date']),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume'])
                })
            
            summary.append({
                "symbol": symbol,
                "company": str(latest.get('company', symbol)),
                "industry": str(latest.get('industry', 'Unknown')),
                "price": float(latest['close']),
                "change": float(latest['close'] - df.iloc[-2]['close']) if len(df) > 1 else 0.0,
                "consensus": float(consensus),
                "indicators": {
                    "rsi": float(raw_rsi if not np.isnan(raw_rsi) else 50),
                    "macd": float(raw_macd if not np.isnan(raw_macd) else 0),
                    "supertrend": float(latest.get('supertrend_10_3', 0)),
                    "adx": float(raw_adx if not np.isnan(raw_adx) else 0),
                    "bb_pos": float(raw_bb_pos if not np.isnan(raw_bb_pos) else 0.5),
                    "atr": float(raw_atr if not np.isnan(raw_atr) else 0),
                    "volume_surge": float(latest.get('volume_surge_20', 1.0)),
                    "zscore": float(latest.get('zscore_20', 0)),
                    "linreg_slope": float(latest.get('linreg_slope_20', 0))
                },
                "history": chart_data
            })
            
            print(f"[SUCCESS] Processed {symbol}")
            
        except Exception as e:
            print(f"[ERROR] Error processing {file_path}: {e}")
            
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
        
    print(f"\nSummary generated: {output_file}")

if __name__ == "__main__":
    generate_summary()
