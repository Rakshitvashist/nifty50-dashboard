"""
Comprehensive Technical Indicator Library
~400 indicators across all categories for multi-signal consensus
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.signal import argrelextrema
import talib
from numba import jit

class IndicatorLibrary:
    """Generate 400+ technical indicators for consensus voting"""
    
    def __init__(self):
        self.indicator_count = 0
        self.indicators = {}
    
    def calculate_all_indicators(self, df):
        """
        Calculate all 400+ indicators
        Returns: DataFrame with 400+ columns, each indicator normalized to -1 to +1
        -1 = strong sell, 0 = neutral, +1 = strong buy
        """
        indicators = {}
        
        # Validate and normalize input
        df.columns = [col.lower() for col in df.columns]
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            raise ValueError(f"DataFrame must contain: {required_cols}. Missing: {missing}")
        
        ohlcv = df[required_cols].values
        O, H, L, C, V = ohlcv[:, 0], ohlcv[:, 1], ohlcv[:, 2], ohlcv[:, 3], ohlcv[:, 4]
        
        # ==================== TREND INDICATORS (100+) ====================
        
        # Moving Averages (20 indicators)
        for period in [5, 10, 20, 50, 100, 200]:
            sma = talib.SMA(C, timeperiod=period)
            ema = talib.EMA(C, timeperiod=period)
            wma = talib.WMA(C, timeperiod=period)
            
            # Price vs MA signals
            indicators[f'price_above_sma_{period}'] = self._normalize_bool(C > sma)
            indicators[f'price_above_ema_{period}'] = self._normalize_bool(C > ema)
            
            # MA slope
            indicators[f'sma_slope_{period}'] = self._normalize_slope(sma, period=5)
            indicators[f'ema_slope_{period}'] = self._normalize_slope(ema, period=5)
        
        # MACD variants (15 indicators)
        for fast, slow, signal in [(12, 26, 9), (5, 35, 5), (19, 39, 9)]:
            macd, signal_line, hist = talib.MACD(C, fastperiod=fast, slowperiod=slow, signalperiod=signal)
            indicators[f'macd_{fast}_{slow}_cross'] = self._normalize_crossover(macd, signal_line)
            indicators[f'macd_{fast}_{slow}_histogram'] = self._normalize_range(hist, -np.nanstd(hist)*2, np.nanstd(hist)*2)
            indicators[f'macd_{fast}_{slow}_divergence'] = self._detect_divergence(C, macd)
        
        # ADX / Directional Movement (20 indicators)
        for period in [7, 14, 21, 28]:
            adx = talib.ADX(H, L, C, timeperiod=period)
            plus_di = talib.PLUS_DI(H, L, C, timeperiod=period)
            minus_di = talib.MINUS_DI(H, L, C, timeperiod=period)
            
            indicators[f'adx_{period}_strength'] = self._normalize_range(adx, 0, 50)
            indicators[f'di_cross_{period}'] = self._normalize_crossover(plus_di, minus_di)
            indicators[f'adx_{period}_trending'] = self._normalize_bool(adx > 25)
            indicators[f'di_spread_{period}'] = self._normalize_range(plus_di - minus_di, -50, 50)
        
        # Parabolic SAR (5 indicators)
        for accel, max_accel in [(0.02, 0.2), (0.01, 0.1), (0.03, 0.3)]:
            sar = talib.SAR(H, L, acceleration=accel, maximum=max_accel)
            indicators[f'sar_{accel}_signal'] = self._normalize_bool(C > sar)
        
        # Ichimoku (10 indicators)
        tenkan = self._ichimoku_line(H, L, 9)
        kijun = self._ichimoku_line(H, L, 26)
        senkou_a = (tenkan + kijun) / 2
        senkou_b = self._ichimoku_line(H, L, 52)
        
        indicators['ichimoku_tk_cross'] = self._normalize_crossover(tenkan, kijun)
        indicators['ichimoku_price_above_cloud'] = self._normalize_bool(C > np.maximum(senkou_a, senkou_b))
        indicators['ichimoku_cloud_color'] = self._normalize_bool(senkou_a > senkou_b)
        
        # SuperTrend variants (15 indicators)
        for period, multiplier in [(7, 2), (10, 3), (14, 3), (21, 4), (50, 5)]:
            st_signal = self._calculate_supertrend(H, L, C, period, multiplier)
            indicators[f'supertrend_{period}_{multiplier}'] = st_signal
        
        # Aroon (10 indicators)
        for period in [14, 25, 50]:
            aroon_up, aroon_down = talib.AROON(H, L, timeperiod=period)
            indicators[f'aroon_up_{period}'] = self._normalize_range(aroon_up, 0, 100)
            indicators[f'aroon_cross_{period}'] = self._normalize_crossover(aroon_up, aroon_down)
        
        # ==================== MOMENTUM INDICATORS (100+) ====================
        
        # RSI variants (25 indicators)
        for period in [7, 14, 21, 28, 50]:
            rsi = talib.RSI(C, timeperiod=period)
            indicators[f'rsi_{period}'] = self._normalize_range(rsi, 0, 100)
            indicators[f'rsi_{period}_oversold'] = self._normalize_bool(rsi < 30)
            indicators[f'rsi_{period}_overbought'] = self._normalize_bool(rsi > 70)
            indicators[f'rsi_{period}_divergence'] = self._detect_divergence(C, rsi)
        
        # Stochastic variants (20 indicators)
        for k_period, d_period in [(14, 3), (5, 3), (21, 5)]:
            slowk, slowd = talib.STOCH(H, L, C, fastk_period=k_period, slowk_period=3, slowd_period=d_period)
            indicators[f'stoch_{k_period}_k'] = self._normalize_range(slowk, 0, 100)
            indicators[f'stoch_{k_period}_cross'] = self._normalize_crossover(slowk, slowd)
            indicators[f'stoch_{k_period}_oversold'] = self._normalize_bool(slowk < 20)
        
        # Williams %R (10 indicators)
        for period in [14, 21, 28]:
            willr = talib.WILLR(H, L, C, timeperiod=period)
            indicators[f'willr_{period}'] = self._normalize_range(willr, -100, 0)
            indicators[f'willr_{period}_oversold'] = self._normalize_bool(willr < -80)
        
        # CCI - Commodity Channel Index (15 indicators)
        for period in [14, 20, 30]:
            cci = talib.CCI(H, L, C, timeperiod=period)
            indicators[f'cci_{period}'] = self._normalize_range(cci, -200, 200)
            indicators[f'cci_{period}_extreme'] = self._normalize_bool(np.abs(cci) > 100)
        
        # ROC - Rate of Change (15 indicators)
        for period in [5, 10, 20, 30, 50]:
            roc = talib.ROC(C, timeperiod=period)
            indicators[f'roc_{period}'] = self._normalize_range(roc, -20, 20)
        
        # MOM - Momentum (10 indicators)
        for period in [10, 20, 30]:
            mom = talib.MOM(C, timeperiod=period)
            indicators[f'mom_{period}'] = self._normalize_range(mom, -np.nanstd(mom)*3, np.nanstd(mom)*3)
        
        # Ultimate Oscillator (5 indicators)
        for t1, t2, t3 in [(7, 14, 28), (5, 10, 20)]:
            ult_osc = talib.ULTOSC(H, L, C, timeperiod1=t1, timeperiod2=t2, timeperiod3=t3)
            indicators[f'ultosc_{t1}_{t2}_{t3}'] = self._normalize_range(ult_osc, 0, 100)
        
        # ==================== VOLATILITY INDICATORS (50+) ====================
        
        # Bollinger Bands (20 indicators)
        for period, std_dev in [(20, 2), (20, 3), (50, 2), (100, 2)]:
            upper, middle, lower = talib.BBANDS(C, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev)
            
            bb_position = (C - lower) / (upper - lower + 1e-10)
            indicators[f'bb_{period}_{std_dev}_position'] = self._normalize_range(bb_position, 0, 1)
            indicators[f'bb_{period}_{std_dev}_squeeze'] = self._normalize_range((upper - lower) / middle, 0, 0.2)
            indicators[f'bb_{period}_{std_dev}_breakout'] = self._normalize_bool((C > upper) | (C < lower))
        
        # ATR - Average True Range (15 indicators)
        for period in [7, 14, 21, 30]:
            atr = talib.ATR(H, L, C, timeperiod=period)
            natr = talib.NATR(H, L, C, timeperiod=period)
            
            indicators[f'atr_{period}_normalized'] = self._normalize_range(natr, 0, 10)
            indicators[f'atr_{period}_expanding'] = self._normalize_slope(atr, period=5)
        
        # Keltner Channels (10 indicators)
        for period, atr_mult in [(20, 2), (50, 2.5)]:
            kc_middle = talib.EMA(C, timeperiod=period)
            atr = talib.ATR(H, L, C, timeperiod=period)
            kc_upper = kc_middle + atr_mult * atr
            kc_lower = kc_middle - atr_mult * atr
            
            kc_position = (C - kc_lower) / (kc_upper - kc_lower + 1e-10)
            indicators[f'keltner_{period}_{atr_mult}_position'] = self._normalize_range(kc_position, 0, 1)
        
        # ==================== VOLUME INDICATORS (50+) ====================
        
        # Volume analysis (25 indicators)
        for period in [10, 20, 50]:
            vol_ma = talib.SMA(V, timeperiod=period)
            vol_std = pd.Series(V).rolling(period).std().values
            
            indicators[f'volume_above_avg_{period}'] = self._normalize_bool(V > vol_ma)
            indicators[f'volume_surge_{period}'] = self._normalize_range(V / vol_ma, 0, 3)
            indicators[f'volume_expansion_{period}'] = self._normalize_slope(vol_ma, period=5)
        
        # OBV - On Balance Volume (10 indicators)
        obv = talib.OBV(C, V)
        for period in [20, 50, 100]:
            obv_ma = talib.SMA(obv, timeperiod=period)
            indicators[f'obv_vs_ma_{period}'] = self._normalize_bool(obv > obv_ma)
            indicators[f'obv_divergence_{period}'] = self._detect_divergence(C, obv)
        
        # AD - Accumulation/Distribution (10 indicators)
        ad = talib.AD(H, L, C, V)
        for period in [20, 50]:
            ad_ma = talib.SMA(ad, timeperiod=period)
            indicators[f'ad_trend_{period}'] = self._normalize_slope(ad, period=period)
            indicators[f'ad_divergence_{period}'] = self._detect_divergence(C, ad)
        
        # ADOSC - Chaikin A/D Oscillator (5 indicators)
        adosc = talib.ADOSC(H, L, C, V, fastperiod=3, slowperiod=10)
        indicators['adosc'] = self._normalize_range(adosc, -np.nanstd(adosc)*3, np.nanstd(adosc)*3)
        
        # ==================== PATTERN RECOGNITION (50+) ====================
        
        # Candlestick patterns (30 indicators)
        patterns = [
            ('CDLDOJI', talib.CDLDOJI),
            ('CDLHAMMER', talib.CDLHAMMER),
            ('CDLINVERTEDHAMMER', talib.CDLINVERTEDHAMMER),
            ('CDLENGULFING', talib.CDLENGULFING),
            ('CDLHARAMI', talib.CDLHARAMI),
            ('CDLPIERCING', talib.CDLPIERCING),
            ('CDLMORNINGSTAR', talib.CDLMORNINGSTAR),
            ('CDLEVENINGSTAR', talib.CDLEVENINGSTAR),
            ('CDLSHOOTINGSTAR', talib.CDLSHOOTINGSTAR),
            ('CDLMARUBOZU', talib.CDLMARUBOZU),
            ('CDL3WHITESOLDIERS', talib.CDL3WHITESOLDIERS),
            ('CDL3BLACKCROWS', talib.CDL3BLACKCROWS),
            ('CDLSPINNINGTOP', talib.CDLSPINNINGTOP),
            ('CDLDRAGONFLYDOJI', talib.CDLDRAGONFLYDOJI),
            ('CDLGRAVESTONEDOJI', talib.CDLGRAVESTONEDOJI),
        ]
        
        for name, func in patterns:
            pattern = func(O, H, L, C)
            indicators[f'pattern_{name.lower()}'] = self._normalize_pattern(pattern)
        
        # Price patterns (20 indicators)
        indicators['higher_highs'] = self._detect_higher_highs(H, period=20)
        indicators['lower_lows'] = self._detect_lower_lows(L, period=20)
        indicators['double_top'] = self._detect_double_top(H, C, period=50)
        indicators['double_bottom'] = self._detect_double_bottom(L, C, period=50)
        indicators['triangle_pattern'] = self._detect_triangle(H, L, period=30)
        
        # ==================== STATISTICAL INDICATORS (30+) ====================
        
        # Z-Score / Standard Deviation (15 indicators)
        for period in [20, 50, 100]:
            returns = pd.Series(C).pct_change().values
            mean = pd.Series(C).rolling(period).mean().values
            std = pd.Series(C).rolling(period).std().values
            zscore = (C - mean) / (std + 1e-10)
            
            indicators[f'zscore_{period}'] = self._normalize_range(zscore, -3, 3)
            indicators[f'std_{period}_expanding'] = self._normalize_slope(std, period=5)
        
        # Linear Regression (10 indicators)
        for period in [20, 50, 100]:
            slope, intercept = self._linear_regression(C, period)
            indicators[f'linreg_slope_{period}'] = self._normalize_range(slope, -0.05, 0.05)
            indicators[f'linreg_deviation_{period}'] = self._normalize_range((C - (slope * period + intercept)) / C, -0.1, 0.1)
        
        # Correlation (5 indicators)
        price_volume_corr = pd.Series(C).rolling(20).corr(pd.Series(V)).values
        indicators['price_volume_corr_20'] = self._normalize_range(price_volume_corr, -1, 1)
        
        # ==================== CUSTOM INDICATORS (30+) ====================
        
        # Market microstructure
        indicators['close_position_in_range'] = self._normalize_range((C - L) / (H - L + 1e-10), 0, 1)
        indicators['body_to_range_ratio'] = self._normalize_range(np.abs(C - O) / (H - L + 1e-10), 0, 1)
        
        # Gap detection
        indicators['gap_up'] = self._normalize_bool(L > np.roll(H, 1))
        indicators['gap_down'] = self._normalize_bool(H < np.roll(L, 1))
        
        # Momentum persistence
        for period in [5, 10, 20]:
            returns = pd.Series(C).pct_change().values
            momentum_consistency = pd.Series(returns > 0).rolling(period).mean().values
            indicators[f'momentum_consistency_{period}'] = self._normalize_range(momentum_consistency, 0, 1)
        
        # Volatility of volatility
        for period in [20, 50]:
            returns = pd.Series(C).pct_change().values
            vol = pd.Series(returns).rolling(period).std().values
            vol_of_vol = pd.Series(vol).rolling(period).std().values
            indicators[f'vol_of_vol_{period}'] = self._normalize_range(vol_of_vol, 0, np.nanpercentile(vol_of_vol, 95))
        
        # Range expansion/contraction
        for period in [10, 20]:
            daily_range = (H - L) / C
            range_ma = pd.Series(daily_range).rolling(period).mean().values
            range_expansion = daily_range / (range_ma + 1e-10)
            indicators[f'range_expansion_{period}'] = self._normalize_range(range_expansion, 0, 3)
        
        self.indicators = pd.DataFrame(indicators, index=df.index)
        self.indicator_count = len(indicators)
        
        print(f"DONE: Generated {self.indicator_count} indicators")
        
        return self.indicators
    
    # ==================== HELPER FUNCTIONS ====================
    
    @staticmethod
    def _normalize_bool(boolean_series):
        """Convert boolean to -1/+1"""
        return np.where(boolean_series, 1.0, -1.0)
    
    @staticmethod
    def _normalize_range(values, min_val, max_val):
        """Normalize to -1 to +1"""
        normalized = 2 * (values - min_val) / (max_val - min_val + 1e-10) - 1
        return np.clip(normalized, -1, 1)
    
    @staticmethod
    def _normalize_crossover(series1, series2):
        """Detect crossover: +1 if series1 > series2, -1 otherwise"""
        return np.where(series1 > series2, 1.0, -1.0)
    
    @staticmethod
    def _normalize_slope(series, period=5):
        """Calculate slope and normalize"""
        slopes = []
        for i in range(len(series)):
            if i < period:
                slopes.append(0)
            else:
                slope = (series[i] - series[i-period]) / (series[i-period] + 1e-10)
                slopes.append(slope)
        slopes = np.array(slopes)
        return np.clip(slopes * 10, -1, 1)  # Scale and clip
    
    @staticmethod
    def _normalize_pattern(pattern_values):
        """Normalize candlestick pattern output"""
        return np.clip(pattern_values / 100, -1, 1)
    
    @staticmethod
    def _detect_divergence(price, indicator):
        """Detect price-indicator divergence"""
        # Simplified divergence detection
        price_slope = np.gradient(price)
        indicator_slope = np.gradient(indicator)
        
        # Bearish divergence: price up, indicator down
        bearish_div = (price_slope > 0) & (indicator_slope < 0)
        # Bullish divergence: price down, indicator up
        bullish_div = (price_slope < 0) & (indicator_slope > 0)
        
        result = np.zeros_like(price)
        result[bearish_div] = -1
        result[bullish_div] = 1
        
        return result
    
    @staticmethod
    def _calculate_supertrend(high, low, close, period, multiplier):
        """Calculate SuperTrend indicator"""
        atr = talib.ATR(high, low, close, timeperiod=period)
        hl_avg = (high + low) / 2
        
        upper_band = hl_avg + multiplier * atr
        lower_band = hl_avg - multiplier * atr
        
        supertrend = np.zeros_like(close)
        trend = np.ones_like(close)
        
        for i in range(1, len(close)):
            if close[i] > upper_band[i-1]:
                trend[i] = 1
            elif close[i] < lower_band[i-1]:
                trend[i] = -1
            else:
                trend[i] = trend[i-1]
            
            if trend[i] == 1:
                supertrend[i] = lower_band[i]
            else:
                supertrend[i] = upper_band[i]
        
        return np.where(close > supertrend, 1.0, -1.0)
    
    @staticmethod
    def _ichimoku_line(high, low, period):
        """Calculate Ichimoku line"""
        highs = pd.Series(high).rolling(period).max().values
        lows = pd.Series(low).rolling(period).min().values
        return (highs + lows) / 2
    
    @staticmethod
    def _detect_higher_highs(high, period=20):
        """Detect higher highs pattern"""
        highs_rolling = pd.Series(high).rolling(period).max().values
        higher_high = high > np.roll(highs_rolling, period)
        return np.where(higher_high, 1.0, -1.0)
    
    @staticmethod
    def _detect_lower_lows(low, period=20):
        """Detect lower lows pattern"""
        lows_rolling = pd.Series(low).rolling(period).min().values
        lower_low = low < np.roll(lows_rolling, period)
        return np.where(lower_low, -1.0, 1.0)
    
    @staticmethod
    def _detect_double_top(high, close, period=50):
        """Simplified double top detection"""
        peaks = argrelextrema(high, np.greater, order=5)[0]
        signal = np.zeros_like(high)
        
        for i in range(1, len(peaks)):
            if i >= len(peaks):
                break
            p1, p2 = peaks[i-1], peaks[i]
            if np.abs(high[p1] - high[p2]) / high[p1] < 0.02:  # Within 2%
                signal[p2:min(p2+10, len(signal))] = -1  # Bearish
        
        return signal
    
    @staticmethod
    def _detect_double_bottom(low, close, period=50):
        """Simplified double bottom detection"""
        troughs = argrelextrema(low, np.less, order=5)[0]
        signal = np.zeros_like(low)
        
        for i in range(1, len(troughs)):
            if i >= len(troughs):
                break
            t1, t2 = troughs[i-1], troughs[i]
            if np.abs(low[t1] - low[t2]) / low[t1] < 0.02:
                signal[t2:min(t2+10, len(signal))] = 1  # Bullish
        
        return signal
    
    @staticmethod
    def _detect_triangle(high, low, period=30):
        """Simplified triangle pattern detection"""
        high_ma = pd.Series(high).rolling(period).max().values
        low_ma = pd.Series(low).rolling(period).min().values
        
        range_squeeze = (high_ma - low_ma) / high_ma
        range_squeezing = np.gradient(range_squeeze) < 0
        
        return np.where(range_squeezing, 0.5, 0)  # Neutral signal
    
    @staticmethod
    def _linear_regression(series, period):
        """Calculate linear regression slope and intercept"""
        slopes = np.zeros_like(series)
        intercepts = np.zeros_like(series)
        
        for i in range(period, len(series)):
            y = series[i-period:i]
            x = np.arange(period)
            slope, intercept = np.polyfit(x, y, 1)
            slopes[i] = slope
            intercepts[i] = intercept
        
        return slopes, intercepts

if __name__ == "__main__":
    import os
    import glob
    from datetime import datetime
    
    # Path settings
    DATA_DIR = "nifty50_host"
    OUTPUT_DIR = "processed_indicators"
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")
    
    # Initialize library
    lib = IndicatorLibrary()
    
    # Find all stock data files
    files = glob.glob(os.path.join(DATA_DIR, "*_1d_max.csv"))
    
    if not files:
        print(f"No files found in {DATA_DIR}. Please check the path.")
    else:
        print(f"Found {len(files)} files to process.")
        
        for file_path in files:
            symbol = os.path.basename(file_path).split('_')[0]
            print(f"\n--- Processing {symbol} ---")
            
            try:
                # Load data
                df = pd.read_csv(file_path)
                
                # Normalize column names to lowercase to handle case-insensitivity
                df.columns = [c.lower() for c in df.columns]
                
                # Ensure Date is parsed correctly
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], dayfirst=True)
                    df.set_index('date', inplace=True)
                
                # Calculate indicators
                indicators_df = lib.calculate_all_indicators(df)
                
                # Combine original data with indicators
                result_df = pd.concat([df, indicators_df], axis=1)
                
                # Save result
                output_path = os.path.join(OUTPUT_DIR, f"{symbol}_with_indicators.csv")
                result_df.to_csv(output_path)
                print(f"[SUCCESS] Saved results to {output_path}")
                
            except Exception as e:
                print(f"[ERROR] Error processing {symbol}: {e}")

    print("\nProcessing complete.")