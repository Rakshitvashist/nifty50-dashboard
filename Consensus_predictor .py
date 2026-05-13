"""
Consensus Voting Predictor
Aggregates 400+ indicators using weighted voting to predict:
1. Direction (buy/sell/hold)
2. Confidence score
3. Price targets
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict
from sklearn.preprocessing import StandardScaler

class ConsensusPredictor:
    """
    Multi-indicator consensus voting system
    Predicts direction, confidence, and price targets
    """
    
    def __init__(self, voting_threshold: float = 0.15, confidence_levels: Dict = None):
        """
        Args:
            voting_threshold: Minimum consensus score for signal (-1 to +1)
            confidence_levels: Dict mapping confidence to thresholds
        """
        self.voting_threshold = voting_threshold
        self.confidence_levels = confidence_levels or {
            'very_high': 0.6,
            'high': 0.4,
            'medium': 0.2,
            'low': 0.0
        }
        
    def predict(self, 
                indicators_df: pd.DataFrame, 
                quality_df: pd.DataFrame,
                current_price: pd.Series,
                atr: pd.Series = None) -> pd.DataFrame:
        """
        Generate predictions using consensus voting
        
        Args:
            indicators_df: DataFrame with indicator signals (-1 to +1)
            quality_df: DataFrame with quality scores (0 to 1)
            current_price: Series with current prices
            atr: Average True Range for price target calculation
            
        Returns:
            DataFrame with predictions:
                - signal: -1 (sell), 0 (hold), 1 (buy)
                - confidence: 0-1 score
                - consensus_score: weighted average of all indicators
                - bullish_count: number of bullish indicators
                - bearish_count: number of bearish indicators
                - price_target_upper: upper price target
                - price_target_lower: lower price target
                - expected_move: expected price move percentage
        """
        print("Calculating consensus predictions...")
        
        # Replace NaN with 0 (neutral)
        indicators_clean = indicators_df.fillna(0)
        quality_clean = quality_df.fillna(0.5)
        
        # Calculate weighted consensus score
        # Formula: sum(indicator * quality) / sum(quality)
        weighted_sum = (indicators_clean * quality_clean).sum(axis=1)
        quality_sum = quality_clean.sum(axis=1)
        consensus_score = weighted_sum / (quality_sum + 1e-10)
        
        # Count bullish/bearish signals
        bullish_count = (indicators_clean > 0).sum(axis=1)
        bearish_count = (indicators_clean < 0).sum(axis=1)
        neutral_count = (indicators_clean == 0).sum(axis=1)
        
        # Generate signals based on consensus
        signals = np.zeros(len(consensus_score))
        signals[consensus_score > self.voting_threshold] = 1   # Buy
        signals[consensus_score < -self.voting_threshold] = -1  # Sell
        
        # Calculate confidence
        confidence = np.abs(consensus_score)
        
        # Classify confidence levels
        confidence_level = pd.cut(confidence, 
                                 bins=[0, 0.2, 0.4, 0.6, 1.0],
                                 labels=['low', 'medium', 'high', 'very_high'])
        
        # Calculate price targets
        if atr is not None:
            # Use ATR for dynamic price targets
            expected_move_pct = (atr / current_price) * np.abs(consensus_score)
        else:
            # Use historical volatility
            returns = current_price.pct_change()
            rolling_std = returns.rolling(20).std()
            expected_move_pct = rolling_std * np.abs(consensus_score) * 2
        
        price_target_upper = current_price * (1 + expected_move_pct)
        price_target_lower = current_price * (1 - expected_move_pct)
        
        # Adjust targets based on signal direction
        price_target_upper = np.where(signals >= 0, price_target_upper, current_price)
        price_target_lower = np.where(signals <= 0, price_target_lower, current_price)
        
        # Create results DataFrame
        results = pd.DataFrame({
            'signal': signals,
            'confidence': confidence,
            'confidence_level': confidence_level,
            'consensus_score': consensus_score,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'bullish_pct': bullish_count / indicators_clean.shape[1] * 100,
            'bearish_pct': bearish_count / indicators_clean.shape[1] * 100,
            'price_target_upper': price_target_upper,
            'price_target_lower': price_target_lower,
            'expected_move_pct': expected_move_pct * 100,
            'current_price': current_price
        }, index=indicators_df.index)
        
        print(f"✓ Generated predictions for {len(results)} periods")
        print(f"  Buy signals: {(signals == 1).sum()}")
        print(f"  Sell signals: {(signals == -1).sum()}")
        print(f"  Hold signals: {(signals == 0).sum()}")
        
        return results
    
    def get_signal_breakdown(self, 
                            indicators_df: pd.DataFrame,
                            quality_df: pd.DataFrame,
                            index: int = -1) -> pd.DataFrame:
        """
        Get detailed breakdown of indicators for a specific date
        
        Args:
            indicators_df: DataFrame with indicator signals
            quality_df: DataFrame with quality scores
            index: Index position (default: -1 for most recent)
            
        Returns:
            DataFrame with indicator breakdown sorted by contribution
        """
        indicators_clean = indicators_df.fillna(0)
        quality_clean = quality_df.fillna(0.5)
        
        # Get specific row
        indicator_values = indicators_clean.iloc[index]
        quality_values = quality_clean.iloc[index]
        
        # Calculate weighted contribution
        contribution = indicator_values * quality_values
        
        breakdown = pd.DataFrame({
            'indicator': indicator_values.index,
            'signal': indicator_values.values,
            'quality': quality_values.values,
            'contribution': contribution.values,
            'direction': ['BULLISH' if x > 0 else 'BEARISH' if x < 0 else 'NEUTRAL' 
                         for x in indicator_values.values]
        })
        
        # Sort by absolute contribution
        breakdown['abs_contribution'] = np.abs(breakdown['contribution'])
        breakdown = breakdown.sort_values('abs_contribution', ascending=False)
        breakdown = breakdown.drop('abs_contribution', axis=1)
        
        return breakdown
    
    def calculate_indicator_performance(self,
                                       indicators_df: pd.DataFrame,
                                       future_returns: pd.Series,
                                       lookback: int = 5) -> pd.DataFrame:
        """
        Calculate historical performance of each indicator
        
        Args:
            indicators_df: DataFrame with indicator signals
            future_returns: Series with future returns (shifted)
            lookback: Days to look ahead for returns
            
        Returns:
            DataFrame with performance metrics for each indicator
        """
        print(f"Calculating indicator performance (lookback={lookback} days)...")
        
        performance = []
        
        for col in indicators_df.columns:
            signal = indicators_df[col]
            
            # Remove NaN
            valid_mask = ~(signal.isna() | future_returns.isna())
            signal_clean = signal[valid_mask]
            returns_clean = future_returns[valid_mask]
            
            if len(signal_clean) < 10:
                continue
            
            # Calculate correlation with future returns
            correlation = np.corrcoef(signal_clean, returns_clean)[0, 1] if len(signal_clean) > 1 else 0
            
            # Calculate directional accuracy
            signal_direction = np.sign(signal_clean)
            return_direction = np.sign(returns_clean)
            accuracy = (signal_direction == return_direction).mean()
            
            # Calculate average return when signal is bullish/bearish
            bullish_return = returns_clean[signal_clean > 0.5].mean() if (signal_clean > 0.5).any() else 0
            bearish_return = returns_clean[signal_clean < -0.5].mean() if (signal_clean < -0.5).any() else 0
            
            # Signal frequency
            signal_frequency = (np.abs(signal_clean) > 0.5).mean()
            
            performance.append({
                'indicator': col,
                'correlation': correlation,
                'accuracy': accuracy,
                'bullish_return_avg': bullish_return,
                'bearish_return_avg': bearish_return,
                'signal_frequency': signal_frequency,
                'sharpe_proxy': correlation * np.sqrt(signal_frequency)  # Weighted by frequency
            })
        
        performance_df = pd.DataFrame(performance)
        performance_df = performance_df.sort_values('sharpe_proxy', ascending=False)
        
        print(f"✓ Calculated performance for {len(performance_df)} indicators")
        
        return performance_df
    
    def get_adaptive_weights(self,
                            performance_df: pd.DataFrame,
                            quality_df: pd.DataFrame,
                            adaptation_rate: float = 0.5) -> pd.DataFrame:
        """
        Calculate adaptive weights based on historical performance
        
        Args:
            performance_df: DataFrame from calculate_indicator_performance
            quality_df: Original quality scores
            adaptation_rate: How much to weight performance (0=ignore, 1=full)
            
        Returns:
            Updated quality DataFrame with adaptive weights
        """
        # Create mapping from performance
        perf_map = performance_df.set_index('indicator')['sharpe_proxy'].to_dict()
        
        # Normalize performance scores to 0-1
        perf_values = np.array(list(perf_map.values()))
        perf_min, perf_max = perf_values.min(), perf_values.max()
        perf_normalized = {k: (v - perf_min) / (perf_max - perf_min + 1e-10) 
                          for k, v in perf_map.items()}
        
        # Update quality scores
        adaptive_quality = quality_df.copy()
        
        for col in quality_df.columns:
            if col in perf_normalized:
                original_quality = quality_df[col].iloc[0]
                performance_quality = perf_normalized[col]
                
                # Blend original and performance-based quality
                adaptive_quality[col] = (
                    (1 - adaptation_rate) * original_quality +
                    adaptation_rate * performance_quality
                )
        
        return adaptive_quality


class PriceTargetPredictor:
    """
    Predict specific price targets and probability of hitting them
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def predict_targets(self,
                       current_price: float,
                       consensus_score: float,
                       atr: float,
                       volatility: float,
                       trend_strength: float = 0.5) -> Dict:
        """
        Calculate multiple price targets with probabilities
        
        Args:
            current_price: Current stock price
            consensus_score: Consensus score from predictor (-1 to +1)
            atr: Average True Range
            volatility: Historical volatility (std of returns)
            trend_strength: Trend strength indicator (0 to 1)
            
        Returns:
            Dict with targets and probabilities
        """
        direction = np.sign(consensus_score)
        confidence = np.abs(consensus_score)
        
        # Calculate target distances based on ATR and volatility
        # More aggressive targets when confidence is high
        target_1x = atr * (1 + confidence * 0.5)  # Conservative
        target_2x = atr * (2 + confidence)          # Moderate
        target_3x = atr * (3 + confidence * 2)      # Aggressive
        
        if direction > 0:  # Bullish
            targets = {
                'target_1': current_price + target_1x,
                'target_2': current_price + target_2x,
                'target_3': current_price + target_3x,
                'stop_loss': current_price - atr * 0.5
            }
        else:  # Bearish
            targets = {
                'target_1': current_price - target_1x,
                'target_2': current_price - target_2x,
                'target_3': current_price - target_3x,
                'stop_loss': current_price + atr * 0.5
            }
        
        # Estimate probabilities (simplified model)
        # Higher confidence + stronger trend = higher probability
        base_prob = 0.5 + confidence * 0.3 + trend_strength * 0.2
        
        probabilities = {
            'prob_target_1': min(base_prob, 0.85),
            'prob_target_2': min(base_prob * 0.7, 0.70),
            'prob_target_3': min(base_prob * 0.4, 0.50)
        }
        
        # Expected days to hit (rough estimate)
        base_days = 5
        days_estimate = {
            'days_target_1': base_days,
            'days_target_2': base_days * 2,
            'days_target_3': base_days * 4
        }
        
        return {
            **targets,
            **probabilities,
            **days_estimate,
            'direction': 'LONG' if direction > 0 else 'SHORT',
            'confidence': confidence
        }
    
    def calculate_risk_reward(self, targets: Dict, current_price: float) -> Dict:
        """Calculate risk-reward ratios"""
        stop_loss = targets['stop_loss']
        risk = abs(current_price - stop_loss)
        
        rr_ratios = {}
        for i in range(1, 4):
            target = targets[f'target_{i}']
            reward = abs(target - current_price)
            rr_ratios[f'rr_target_{i}'] = reward / risk if risk > 0 else 0
        
        return rr_ratios


if __name__ == "__main__":
    print("Consensus Predictor - Ready for use")
    print("\nExample usage:")
    print("""
    from consensus_predictor import ConsensusPredictor
    
    predictor = ConsensusPredictor(voting_threshold=0.15)
    predictions = predictor.predict(indicators_df, quality_df, prices, atr)
    """)