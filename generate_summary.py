import pandas as pd
import glob
import os
import json
from datetime import datetime

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
                
            symbol = os.path.basename(file_path).split('_')[0]
            
            # Get latest row
            latest = df.iloc[-1]
            
            # Calculate Consensus Score
            # We look for columns like 'price_above_sma', 'macd_*_cross', 'rsi_*_oversold', etc.
            indicator_cols = [c for c in df.columns if any(x in c for x in ['above', 'cross', 'signal', 'supertrend', 'oversold', 'overbought'])]
            
            if indicator_cols:
                # Average the normalized indicators (-1 to +1)
                consensus = df[indicator_cols].iloc[-1].mean()
            else:
                consensus = 0.0
                
            # Get historical data for chart (last 100 days)
            chart_data = []
            hist_df = df.tail(100)
            for _, row in hist_df.iterrows():
                chart_data.append({
                    "time": row['date'],
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume'])
                })
            
            summary.append({
                "symbol": symbol,
                "company": latest.get('company', symbol),
                "industry": latest.get('industry', 'Unknown'),
                "price": float(latest['close']),
                "change": float(latest['close'] - df.iloc[-2]['close']) if len(df) > 1 else 0.0,
                "consensus": float(consensus),
                "indicators": {
                    "rsi": float(latest.get('rsi_14', 50)),
                    "macd": float(latest.get('macd_12_26_histogram', 0)),
                    "supertrend": float(latest.get('supertrend_10_3', 0))
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
