import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import brentq
import json
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class OptionsAnalyzer:
    def __init__(self, underlying='SPY'):
        self.underlying = underlying.upper()
        self.config = self._get_default_config()
        self.greeks_scaling = 'daily'  # 'daily', 'per_minute', or 'annual'
    
    def _get_default_config(self):
        """Get default configuration based on underlying"""
        if self.underlying == 'SPY':
            return {
                'current_price': 604.53,
                'strike_increment': 2.5,
                'strike_range_width': 35,  # +/- from ATM
                'expected_moves': {
                    'target_move': 2.0,      # Primary expected move
                    'conservative': 1.0,     # Conservative scenario
                    'aggressive': 3.0        # Aggressive scenario
                },
                'min_premium': 0.05,
                'max_premium': 50.0,
                'price_adjustment': 0.0,  # Price adjustment for scenarios
                'mark_vs_theoretical': 'theoretical'  # 'theoretical' or 'mark'
            }
        else:  # SPX
            return {
                'current_price': 6045.26,
                'strike_increment': 25,
                'strike_range_width': 350,  # +/- from ATM
                'expected_moves': {
                    'target_move': 20.0,     # Primary expected move
                    'conservative': 10.0,    # Conservative scenario  
                    'aggressive': 30.0       # Aggressive scenario
                },
                'min_premium': 0.50,
                'max_premium': 500.0,
                'price_adjustment': 0.0,  # Price adjustment for scenarios
                'mark_vs_theoretical': 'theoretical'  # 'theoretical' or 'mark'
            }
    
    def update_config(self, **kwargs):
        """Update configuration parameters"""
        self.config.update(kwargs)
    
    def set_greeks_scaling(self, scaling='daily'):
        """Set Greeks scaling: 'daily', 'per_minute', or 'annual'"""
        if scaling not in ['daily', 'per_minute', 'annual']:
            raise ValueError("Scaling must be 'daily', 'per_minute', or 'annual'")
        self.greeks_scaling = scaling

    def implied_volatility_calculator(self, market_price, S, K, T, r, option_type='call'):
        """
        Calculate implied volatility from market price (reverse Black-Scholes)
        
        Parameters:
        market_price: Market price of the option
        S: Current underlying price
        K: Strike price
        T: Time to expiration (years)
        r: Risk-free rate
        option_type: 'call' or 'put'
        
        Returns:
        dict with IV and related metrics
        """
        def bs_price_diff(sigma):
            bs_result = self.black_scholes_price(S, K, T, r, sigma, option_type)
            return bs_result['price'] - market_price
        
        try:
            # Use Brent's method to find IV (typically between 0.01% and 500%)
            iv = brentq(bs_price_diff, 0.0001, 5.0, xtol=1e-6)
            
            # Calculate additional metrics
            bs_result = self.black_scholes_price(S, K, T, r, iv, option_type)
            
            # Calculate IV range for price sensitivity
            iv_high = iv * 1.1  # +10% IV
            iv_low = iv * 0.9   # -10% IV
            
            bs_high = self.black_scholes_price(S, K, T, r, iv_high, option_type)
            bs_low = self.black_scholes_price(S, K, T, r, iv_low, option_type)
            
            return {
                'implied_volatility': iv,
                'market_price': market_price,
                'theoretical_price': bs_result['price'],
                'price_difference': market_price - bs_result['price'],
                'iv_high': iv_high,
                'iv_low': iv_low,
                'price_at_iv_high': bs_high['price'],
                'price_at_iv_low': bs_low['price'],
                'vega': bs_result['vega'],
                'delta': bs_result['delta'],
                'gamma': bs_result['gamma'],
                'theta': bs_result['theta'],
                'iv_percentile': None  # Would need historical data
            }
            
        except ValueError:
            return {
                'implied_volatility': None,
                'error': 'Could not converge on IV solution',
                'market_price': market_price,
                'possible_issues': [
                    'Price may be outside reasonable bounds',
                    'Option may be deeply ITM/OTM',
                    'Very short/long time to expiration'
                ]
            }

    def price_adjustment_scenario(self, base_price, adjustment):
        """
        Apply price adjustment for scenario modeling
        
        Parameters:
        base_price: Current underlying price
        adjustment: Dollar adjustment (can be positive or negative)
        
        Returns:
        Adjusted price and scenario description
        """
        adjusted_price = base_price + adjustment
        
        scenario_type = "neutral"
        if adjustment > 0:
            scenario_type = "bullish"
        elif adjustment < 0:
            scenario_type = "bearish"
        
        return {
            'base_price': base_price,
            'adjustment': adjustment,
            'adjusted_price': adjusted_price,
            'scenario_type': scenario_type,
            'percentage_change': (adjustment / base_price) * 100
        }

    def _scale_greeks(self, greeks_dict, T):
        """Scale Greeks based on selected scaling method"""
        scaled = greeks_dict.copy()
        
        if self.greeks_scaling == 'per_minute':
            # Convert daily to per-minute
            scaled['theta'] = scaled['theta'] / (24 * 60)  # Daily to per-minute
            scaled['rho'] = scaled['rho'] / 100  # Per 100bp to per 1bp
            
        elif self.greeks_scaling == 'annual':
            # Convert to annual values
            scaled['theta'] = scaled['theta'] * 365  # Daily to annual
            scaled['vega'] = scaled['vega'] * 100  # Per 1% to per 100%
            
        # Daily is the default, no scaling needed
        
        return scaled

    def black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """Enhanced Black-Scholes with better error handling and scaling"""
        if T <= 0:
            if option_type == 'call':
                return {'price': max(S - K, 0), 'delta': 1 if S > K else 0, 'gamma': 0, 
                       'theta': 0, 'vega': 0, 'rho': 0, 'd1': 0, 'd2': 0}
            else:
                return {'price': max(K - S, 0), 'delta': -1 if S < K else 0, 'gamma': 0,
                       'theta': 0, 'vega': 0, 'rho': 0, 'd1': 0, 'd2': 0}
        
        d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            delta = norm.cdf(d1)
            rho = K * T * np.exp(-r * T) * norm.cdf(d2)
        else:
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            delta = -norm.cdf(-d1)
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2)

        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        if option_type == 'call':
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) -
                     r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) +
                     r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100

        greeks = {
            'price': price, 'delta': delta, 'gamma': gamma,
            'theta': theta, 'vega': vega, 'rho': rho, 'd1': d1, 'd2': d2
        }
        
        # Apply scaling
        return self._scale_greeks(greeks, T)

    def calculate_mark_price(self, theoretical_price, S, K, option_type, liquidity_factor=1.0):
        """
        Calculate mark price (bid/ask midpoint estimate) vs theoretical price
        
        Parameters:
        theoretical_price: Black-Scholes theoretical price
        S: Underlying price
        K: Strike price  
        option_type: 'call' or 'put'
        liquidity_factor: Adjustment for liquidity (1.0 = normal, >1.0 = wider spreads)
        
        Returns:
        dict with mark price and spread estimates
        """
        # Simple mark price model - in reality this would use market data
        moneyness = S / K if option_type == 'call' else K / S
        
        # Estimate bid-ask spread based on moneyness and liquidity
        if 0.95 <= moneyness <= 1.05:  # ATM
            spread_pct = 0.02 * liquidity_factor  # 2% spread
        elif 0.90 <= moneyness <= 1.10:  # Near money
            spread_pct = 0.03 * liquidity_factor  # 3% spread
        else:  # Far OTM/ITM
            spread_pct = 0.05 * liquidity_factor  # 5% spread
        
        spread = theoretical_price * spread_pct
        bid = theoretical_price - spread / 2
        ask = theoretical_price + spread / 2
        mark = (bid + ask) / 2  # Should equal theoretical in this simple model
        
        return {
            'theoretical_price': theoretical_price,
            'mark_price': mark,
            'bid': max(0.01, bid),  # Minimum 1 cent bid
            'ask': ask,
            'spread': spread,
            'spread_percentage': spread_pct * 100
        }

    def calculate_probability_profit(self, S, K, T, r, sigma, option_type):
        """Calculate probability of profit and other key probabilities"""
        option_price = self.black_scholes_price(S, K, T, r, sigma, option_type)['price']
        
        if option_type == 'call':
            breakeven = K + option_price
            d = (np.log(S / breakeven) + (r - sigma**2/2) * T) / (sigma * np.sqrt(T))
            prob_profit = norm.cdf(d)
            d_itm = (np.log(S / K) + (r - sigma**2/2) * T) / (sigma * np.sqrt(T))
            prob_itm = norm.cdf(d_itm)
        else:
            breakeven = K - option_price
            d = (np.log(S / breakeven) + (r - sigma**2/2) * T) / (sigma * np.sqrt(T))
            prob_profit = norm.cdf(-d)
            d_itm = (np.log(S / K) + (r - sigma**2/2) * T) / (sigma * np.sqrt(T))
            prob_itm = norm.cdf(-d_itm)
        
        return {
            'breakeven': breakeven,
            'prob_profit': prob_profit,
            'prob_itm': prob_itm,
            'premium': option_price
        }

    def generate_strike_range(self, S, dte):
        """Generate appropriate strike range based on underlying and DTE"""
        increment = self.config['strike_increment']
        width = self.config['strike_range_width']
        
        # Adjust width based on DTE (wider for longer DTE)
        dte_multiplier = max(0.5, min(2.0, dte / 7))
        adjusted_width = width * dte_multiplier
        
        # Round to nearest increment
        atm_strike = round(S / increment) * increment
        start_strike = atm_strike - adjusted_width
        end_strike = atm_strike + adjusted_width
        
        return np.arange(start_strike, end_strike + increment, increment)

    def analyze_options(self, S, T, r, sigma, dte_days, output_format='dataframe'):
        """Main analysis function with multiple output formats"""
        
        # Apply price adjustment if configured
        price_adjustment = self.config.get('price_adjustment', 0.0)
        if price_adjustment != 0.0:
            adjustment_info = self.price_adjustment_scenario(S, price_adjustment)
            S_adjusted = adjustment_info['adjusted_price']
            print(f"Price Adjustment: {adjustment_info['scenario_type'].title()} scenario, "
                  f"${adjustment_info['base_price']:.2f} → ${S_adjusted:.2f} "
                  f"({adjustment_info['percentage_change']:+.1f}%)")
        else:
            S_adjusted = S
            adjustment_info = None
        
        # Generate strike range
        strike_range = self.generate_strike_range(S_adjusted, dte_days)
        expected_moves = self.config['expected_moves']
        
        # Analyze both calls and puts
        call_df = self._generate_option_table(S_adjusted, T, r, sigma, strike_range, 'call', expected_moves)
        put_df = self._generate_option_table(S_adjusted, T, r, sigma, strike_range, 'put', expected_moves)
        
        # Combine results
        combined_df = pd.concat([call_df, put_df], ignore_index=True)
        
        # Filter by premium range
        combined_df = combined_df[
            (combined_df['premium'] >= self.config['min_premium']) & 
            (combined_df['premium'] <= self.config['max_premium'])
        ]
        
        # Prepare analysis summary
        analysis_summary = self._generate_summary(S_adjusted, T, r, sigma, dte_days, call_df, put_df, combined_df)
        if adjustment_info:
            analysis_summary['price_adjustment'] = adjustment_info
        
        # Return in requested format
        if output_format == 'json':
            return self._format_for_json(combined_df, analysis_summary)
        elif output_format == 'trading_bot':
            return self._format_for_trading_bot(combined_df, analysis_summary)
        elif output_format == 'backtester':
            return self._format_for_backtester(combined_df, analysis_summary)
        else:
            return combined_df, analysis_summary

    def _generate_option_table(self, S, T, r, sigma, strike_range, option_type, expected_moves):
        """Generate option analysis table"""
        rows = []
        
        for K in strike_range:
            bs = self.black_scholes_price(S, K, T, r, sigma, option_type)
            prob_data = self.calculate_probability_profit(S, K, T, r, sigma, option_type)
            
            # Calculate moneyness
            moneyness = S / K if option_type == 'call' else K / S
            
            # Calculate mark vs theoretical pricing
            use_mark = self.config.get('mark_vs_theoretical', 'theoretical') == 'mark'
            if use_mark:
                mark_info = self.calculate_mark_price(bs['price'], S, K, option_type)
                display_price = mark_info['mark_price']
                bid_price = mark_info['bid']
                ask_price = mark_info['ask']
                spread = mark_info['spread']
            else:
                display_price = bs['price']
                bid_price = None
                ask_price = None
                spread = None
            
            # Calculate multiple move scenarios
            move_scenarios = {}
            for move_name, move_size in expected_moves.items():
                if option_type == 'call':
                    new_price = S + move_size
                else:
                    new_price = S - abs(move_size)
                
                bs_moved = self.black_scholes_price(new_price, K, T, r, sigma, option_type)
                price_change = bs_moved['price'] - bs['price']
                rr_ratio = price_change / bs['price'] if bs['price'] > 0.01 else 0
                
                move_scenarios[f'{move_name}_change'] = price_change
                move_scenarios[f'{move_name}_rr'] = rr_ratio
            
            # Calculate day trading score
            day_trade_score = self._calculate_day_trade_score(bs, move_scenarios, prob_data, expected_moves)
            
            row = {
                'underlying': self.underlying,
                'strike': K,
                'type': option_type.upper(),
                'premium': round(display_price, 2),
                'theoretical_price': round(bs['price'], 2),
                'moneyness': round(moneyness, 4),
                'delta': round(bs['delta'], 4),
                'gamma': round(bs['gamma'], 6),
                'theta': round(bs['theta'], 6),
                'vega': round(bs['vega'], 4),
                'rho': round(bs['rho'], 4),
                'breakeven': round(prob_data['breakeven'], 2),
                'prob_profit': round(prob_data['prob_profit'], 3),
                'prob_itm': round(prob_data['prob_itm'], 3),
                'max_loss': round(display_price, 2),
                'day_trade_score': round(day_trade_score, 4),
                'greeks_scaling': self.greeks_scaling,
                **{k: round(v, 3) for k, v in move_scenarios.items()}
            }
            
            # Add mark price info if using mark pricing
            if use_mark:
                row.update({
                    'bid': round(bid_price, 2),
                    'ask': round(ask_price, 2),
                    'spread': round(spread, 2),
                    'spread_pct': round((spread / display_price) * 100, 1) if display_price > 0 else 0
                })
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        return df.sort_values('day_trade_score', ascending=False)

    def _calculate_day_trade_score(self, bs, move_scenarios, prob_data, expected_moves):
        """Calculate composite day trading score"""
        primary_move = list(expected_moves.keys())[0]
        
        score = (
            abs(bs['delta']) * 0.4 +  # Delta exposure
            move_scenarios[f'{primary_move}_rr'] * 0.3 +  # R/R ratio
            (1 / (bs['price'] + 1)) * 0.2 +  # Affordability
            prob_data['prob_itm'] * 0.1  # Probability
        )
        
        return score

    def _generate_summary(self, S, T, r, sigma, dte_days, call_df, put_df, combined_df):
        """Generate analysis summary"""
        
        # Find ATM options
        atm_call = call_df.iloc[(call_df['moneyness'] - 1.0).abs().argsort()[:1]]
        atm_put = put_df.iloc[(put_df['moneyness'] - 1.0).abs().argsort()[:1]]
        
        # Best opportunities
        best_calls = call_df.head(3)
        best_puts = put_df.head(3)
        
        summary = {
            'underlying': self.underlying,
            'current_price': S,
            'dte_days': dte_days,
            'implied_vol': sigma,
            'risk_free_rate': r,
            'total_options_analyzed': len(combined_df),
            'atm_call_premium': float(atm_call['premium'].iloc[0]) if not atm_call.empty else None,
            'atm_put_premium': float(atm_put['premium'].iloc[0]) if not atm_put.empty else None,
            'best_call_strikes': best_calls['strike'].tolist(),
            'best_put_strikes': best_puts['strike'].tolist(),
            'analysis_timestamp': datetime.now().isoformat(),
            'config_used': self.config
        }
        
        return summary

    def _format_for_json(self, df, summary):
        """Format output for JSON export"""
        return {
            'summary': summary,
            'options_data': df.to_dict('records')
        }

    def _format_for_trading_bot(self, df, summary):
        """Format output optimized for trading bot consumption"""
        
        # Filter top opportunities only
        top_calls = df[df['type'] == 'CALL'].head(5)
        top_puts = df[df['type'] == 'PUT'].head(5)
        
        trading_signals = []
        
        for _, row in pd.concat([top_calls, top_puts]).iterrows():
            signal = {
                'symbol': f"{self.underlying}{row['strike']:.0f}{row['type'][0]}",  # e.g., SPY605C
                'underlying': self.underlying,
                'strike': row['strike'],
                'option_type': row['type'],
                'premium': row['premium'],
                'delta': row['delta'],
                'day_trade_score': row['day_trade_score'],
                'prob_profit': row['prob_profit'],
                'move_scenarios': {k: v for k, v in row.items() if k.endswith('_rr')},
                'breakeven': row['breakeven'],
                'max_loss': row['max_loss'],
                'entry_signal': 'BUY' if row['day_trade_score'] > 0.3 else 'WATCH',
                'confidence': 'HIGH' if row['day_trade_score'] > 0.4 else 'MEDIUM' if row['day_trade_score'] > 0.25 else 'LOW'
            }
            trading_signals.append(signal)
        
        return {
            'metadata': {
                'underlying': self.underlying,
                'timestamp': datetime.now().isoformat(),
                'current_price': summary['current_price'],
                'signals_count': len(trading_signals)
            },
            'trading_signals': trading_signals
        }

    def _format_for_backtester(self, df, summary):
        """Format output optimized for backtesting"""
        
        # Create backtesting-friendly structure
        backtest_data = {
            'metadata': {
                'underlying': self.underlying,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'current_price': summary['current_price'],
                'dte': summary['dte_days'],
                'iv': summary['implied_vol']
            },
            'universe': [],
            'rankings': {}
        }
        
        # Add all options to universe
        for _, row in df.iterrows():
            option_data = {
                'strike': row['strike'],
                'type': row['type'],
                'premium': row['premium'],
                'delta': row['delta'],
                'gamma': row['gamma'],
                'theta': row['theta'],
                'vega': row['vega'],
                'day_trade_score': row['day_trade_score'],
                'expected_moves': {k.replace('_rr', ''): v for k, v in row.items() if k.endswith('_rr')}
            }
            backtest_data['universe'].append(option_data)
        
        # Create rankings for different strategies
        rr_columns = [col for col in df.columns if col.endswith('_rr')]
        primary_rr = rr_columns[0] if rr_columns else 'day_trade_score'
        
        backtest_data['rankings'] = {
            'high_delta': df.nlargest(10, 'delta')['strike'].tolist(),
            'best_rr': df.nlargest(10, primary_rr)['strike'].tolist(),
            'day_trade_score': df.nlargest(10, 'day_trade_score')['strike'].tolist(),
            'cheap_options': df.nsmallest(10, 'premium')['strike'].tolist()
        }
        
        return backtest_data

    def save_analysis(self, analysis_data, filename_prefix="options_analysis"):
        """Save analysis in multiple formats to data directory"""
        import os
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if isinstance(analysis_data, tuple):
            df, summary = analysis_data
            
            # Save CSV
            csv_filename = f"data/{filename_prefix}_{self.underlying}_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            
            # Save JSON summary
            json_filename = f"data/{filename_prefix}_summary_{self.underlying}_{timestamp}.json"
            with open(json_filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
                
            return csv_filename, json_filename
        else:
            # Save JSON format
            json_filename = f"data/{filename_prefix}_{self.underlying}_{timestamp}.json"
            with open(json_filename, 'w') as f:
                json.dump(analysis_data, f, indent=2, default=str)
            return json_filename

    def calculate_expected_move(self, S, sigma, T):
        """
        Calculate expected move using standard formula: Price × IV × √(T/252)
        
        Parameters:
        S: Current stock price
        sigma: Implied volatility (annual)
        T: Time to expiration (years)
        
        Returns:
        dict with expected move calculations
        """
        # Standard 1σ expected move formula
        expected_move_1sigma = S * sigma * np.sqrt(T)
        
        # Calculate different confidence intervals
        expected_moves = {
            '1_sigma': expected_move_1sigma,  # ~68% probability
            '2_sigma': expected_move_1sigma * 2,  # ~95% probability
            '0_5_sigma': expected_move_1sigma * 0.5,  # ~38% probability
            'percentage_1sigma': (expected_move_1sigma / S) * 100
        }
        
        return expected_moves

    def get_atm_straddle_price(self, S, T, r, sigma):
        """
        Calculate ATM straddle price (call + put at same strike)
        
        Parameters:
        S: Current stock price
        T: Time to expiration (years) 
        r: Risk-free rate
        sigma: Implied volatility
        
        Returns:
        dict with straddle pricing information
        """
        # Find ATM strike
        increment = self.config['strike_increment']
        atm_strike = round(S / increment) * increment
        
        # Calculate call and put prices
        call_result = self.black_scholes_price(S, atm_strike, T, r, sigma, 'call')
        put_result = self.black_scholes_price(S, atm_strike, T, r, sigma, 'put')
        
        straddle_price = call_result['price'] + put_result['price']
        
        # The straddle price approximates the expected move
        straddle_expected_move = straddle_price
        
        return {
            'atm_strike': atm_strike,
            'call_price': call_result['price'],
            'put_price': put_result['price'],
            'straddle_price': straddle_price,
            'straddle_expected_move': straddle_expected_move,
            'breakeven_upper': atm_strike + straddle_price,
            'breakeven_lower': atm_strike - straddle_price,
            'call_delta': call_result['delta'],
            'put_delta': put_result['delta'],
            'total_vega': call_result['vega'] + put_result['vega'],
            'total_theta': call_result['theta'] + put_result['theta']
        }

    def compare_expected_move_methods(self, S, T, r, sigma):
        """
        Compare different methods of calculating expected moves
        
        Returns:
        dict comparing formula vs straddle approaches
        """
        # Method 1: Standard IV formula
        formula_moves = self.calculate_expected_move(S, sigma, T)
        
        # Method 2: ATM straddle pricing
        straddle_info = self.get_atm_straddle_price(S, T, r, sigma)
        
        # Method 3: Current hardcoded moves (for comparison)
        current_moves = self.config['expected_moves']
        
        comparison = {
            'underlying_price': S,
            'iv_annual': sigma,
            'time_to_expiration_years': T,
            'time_to_expiration_days': T * 252,
            
            # Formula-based
            'formula_1sigma_move': formula_moves['1_sigma'],
            'formula_2sigma_move': formula_moves['2_sigma'],
            'formula_percentage': formula_moves['percentage_1sigma'],
            
            # Straddle-based
            'atm_strike': straddle_info['atm_strike'],
            'straddle_price': straddle_info['straddle_price'],
            'straddle_expected_move': straddle_info['straddle_expected_move'],
            'straddle_breakevens': {
                'upper': straddle_info['breakeven_upper'],
                'lower': straddle_info['breakeven_lower']
            },
            
            # Current hardcoded (for reference)
            'current_target_move': current_moves.get('target_move', 0),
            'current_conservative': current_moves.get('conservative', 0),
            'current_aggressive': current_moves.get('aggressive', 0),
            
            # Analysis
            'formula_vs_straddle_diff': abs(formula_moves['1_sigma'] - straddle_info['straddle_price']),
            'formula_vs_current_diff': abs(formula_moves['1_sigma'] - current_moves.get('target_move', 0)),
            'recommendation': 'formula' if abs(formula_moves['1_sigma'] - straddle_info['straddle_price']) < 0.5 else 'investigate'
        }
        
        return comparison

    def update_expected_moves_from_iv(self, S, T, r, sigma, use_formula=True):
        """
        Update expected moves configuration using IV-based calculations
        
        Parameters:
        S: Current stock price
        T: Time to expiration (years)
        r: Risk-free rate
        sigma: Implied volatility
        use_formula: If True, use formula; if False, use straddle pricing
        """
        if use_formula:
            moves = self.calculate_expected_move(S, sigma, T)
            primary_move = moves['1_sigma']
        else:
            straddle_info = self.get_atm_straddle_price(S, T, r, sigma)
            primary_move = straddle_info['straddle_expected_move']
        
        # Update configuration with calculated moves
        new_expected_moves = {
            'target_move': round(primary_move, 1),
            'conservative': round(primary_move * 0.5, 1),
            'aggressive': round(primary_move * 1.5, 1),
            'formula_derived': True,
            'source': 'iv_formula' if use_formula else 'straddle_pricing'
        }
        
        self.update_config(expected_moves=new_expected_moves)
        return new_expected_moves

def main():
    parser = argparse.ArgumentParser(description='Flexible Options Analysis Calculator')
    parser.add_argument('--underlying', choices=['SPY', 'SPX'], default='SPY', 
                       help='Underlying asset to analyze')
    parser.add_argument('--current-price', type=float, help='Current underlying price')
    parser.add_argument('--dte', type=int, default=8, help='Days to expiration')
    parser.add_argument('--iv', type=float, default=0.132, help='Implied volatility')
    parser.add_argument('--rate', type=float, default=0.044, help='Risk-free rate')
    parser.add_argument('--expected-moves', type=str, 
                       help='Expected moves as JSON string, e.g. \'{"target": 2.0, "conservative": 1.0}\'')
    parser.add_argument('--price-adjustment', type=float, default=0.0,
                       help='Price adjustment for scenario modeling (e.g. +2.0 for bullish, -1.5 for bearish)')
    parser.add_argument('--greeks-scaling', choices=['daily', 'per_minute', 'annual'], default='daily',
                       help='Greeks scaling: daily (default), per_minute (like Excel), or annual')
    parser.add_argument('--pricing-mode', choices=['theoretical', 'mark'], default='theoretical',
                       help='Use theoretical Black-Scholes or estimated mark prices')
    parser.add_argument('--iv-calc', type=str,
                       help='Calculate IV from market price: "strike,price,type" e.g. "605,3.35,call"')
    parser.add_argument('--output-format', choices=['dataframe', 'json', 'trading_bot', 'backtester'], 
                       default='dataframe', help='Output format')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = OptionsAnalyzer(args.underlying)
    
    # Set Greeks scaling
    analyzer.set_greeks_scaling(args.greeks_scaling)
    
    # Update configuration
    config_updates = {}
    if args.current_price:
        config_updates['current_price'] = args.current_price
    if args.price_adjustment != 0.0:
        config_updates['price_adjustment'] = args.price_adjustment
    if args.pricing_mode:
        config_updates['mark_vs_theoretical'] = args.pricing_mode
    
    # Parse custom expected moves if provided
    if args.expected_moves:
        try:
            expected_moves = json.loads(args.expected_moves)
            config_updates['expected_moves'] = expected_moves
        except json.JSONDecodeError:
            print("Error: Invalid JSON format for expected-moves")
            return
    
    if config_updates:
        analyzer.update_config(**config_updates)
    
    # Get current price from config
    S = analyzer.config['current_price']
    T = args.dte / 252
    r = args.rate
    sigma = args.iv
    
    # Handle IV calculation if requested
    if args.iv_calc:
        try:
            parts = args.iv_calc.split(',')
            if len(parts) != 3:
                raise ValueError("IV calc format: strike,price,type")
            
            iv_strike = float(parts[0])
            iv_market_price = float(parts[1])
            iv_type = parts[2].lower()
            
            print(f"\n=== IMPLIED VOLATILITY CALCULATION ===")
            iv_result = analyzer.implied_volatility_calculator(
                iv_market_price, S, iv_strike, T, r, iv_type
            )
            
            if iv_result.get('implied_volatility'):
                print(f"Market Price: ${iv_result['market_price']:.2f}")
                print(f"Strike: ${iv_strike:.0f} {iv_type.upper()}")
                print(f"Implied Volatility: {iv_result['implied_volatility']:.1%}")
                print(f"Theoretical Price: ${iv_result['theoretical_price']:.2f}")
                print(f"Price Difference: ${iv_result['price_difference']:.2f}")
                print(f"IV Range: {iv_result['iv_low']:.1%} - {iv_result['iv_high']:.1%}")
                print(f"Price Range: ${iv_result['price_at_iv_low']:.2f} - ${iv_result['price_at_iv_high']:.2f}")
            else:
                print(f"Error calculating IV: {iv_result.get('error', 'Unknown error')}")
                if 'possible_issues' in iv_result:
                    for issue in iv_result['possible_issues']:
                        print(f"  - {issue}")
            print()
            
        except (ValueError, IndexError) as e:
            print(f"Error parsing IV calculation: {e}")
            print("Format: --iv-calc 'strike,price,type' e.g. --iv-calc '605,3.35,call'")
            return
    
    print(f"\n{args.underlying} Options Analysis")
    print("=" * 60)
    print(f"Current {args.underlying} Price: ${S:.2f}")
    if args.price_adjustment != 0.0:
        print(f"Price Adjustment: {args.price_adjustment:+.2f}")
    print(f"Days to Expiration: {args.dte}")
    print(f"Implied Volatility: {sigma:.1%}")
    print(f"Expected Moves: {analyzer.config['expected_moves']}")
    print(f"Greeks Scaling: {args.greeks_scaling}")
    print(f"Pricing Mode: {args.pricing_mode}")
    print(f"Output Format: {args.output_format}")
    
    # Run analysis
    analysis_result = analyzer.analyze_options(S, T, r, sigma, args.dte, args.output_format)
    
    # Display results based on format
    if args.output_format == 'dataframe':
        df, summary = analysis_result
        
        # Display top opportunities
        calls = df[df['type'] == 'CALL'].head(5)
        puts = df[df['type'] == 'PUT'].head(5)
        
        print(f"\n=== TOP 5 CALL OPTIONS ===")
        for _, row in calls.iterrows():
            print(f"${row['strike']:.0f}: Premium ${row['premium']:.2f}, "
                  f"Delta {row['delta']:.3f}, Score {row['day_trade_score']:.3f}")
        
        print(f"\n=== TOP 5 PUT OPTIONS ===")
        for _, row in puts.iterrows():
            print(f"${row['strike']:.0f}: Premium ${row['premium']:.2f}, "
                  f"Delta {row['delta']:.3f}, Score {row['day_trade_score']:.3f}")
        
        print(f"\n=== SUMMARY ===")
        print(f"Total options analyzed: {summary['total_options_analyzed']}")
        print(f"ATM Call Premium: ${summary['atm_call_premium']:.2f}")
        print(f"ATM Put Premium: ${summary['atm_put_premium']:.2f}")
        
    elif args.output_format == 'trading_bot':
        signals = analysis_result['trading_signals']
        print(f"\n=== TRADING SIGNALS ({len(signals)} total) ===")
        for signal in signals[:10]:  # Show top 10
            print(f"{signal['symbol']}: {signal['entry_signal']} - "
                  f"Score {signal['day_trade_score']:.3f} ({signal['confidence']})")
    
    elif args.output_format == 'backtester':
        rankings = analysis_result['rankings']
        print(f"\n=== BACKTESTER RANKINGS ===")
        print(f"High Delta Strikes: {rankings['high_delta'][:5]}")
        print(f"Best R/R Strikes: {rankings['best_rr'][:5]}")
        print(f"Top Day Trade Scores: {rankings['day_trade_score'][:5]}")
    
    # Save if requested
    if args.save:
        files = analyzer.save_analysis(analysis_result)
        print(f"\nFiles saved: {files}")
    
    return analysis_result

if __name__ == "__main__":
    main()
