import numpy as np
import pandas as pd
from scipy.stats import norm
import json
import argparse
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class OptionsAnalyzer:
    def __init__(self, underlying='SPY'):
        self.underlying = underlying.upper()
        self.config = self._get_default_config()
    
    def _get_default_config(self):
        """Get default configuration based on underlying"""
        if self.underlying == 'SPY':
            return {
                'current_price': 604.53,
                'strike_increment': 2.5,
                'strike_range_width': 35,  # +/- from ATM
                'expected_moves': {
                    'small_move': 1.25,
                    'medium_move': 2.50,
                    'large_move': 4.00,
                    'conservative': 0.75
                },
                'min_premium': 0.05,
                'max_premium': 50.0
            }
        else:  # SPX
            return {
                'current_price': 6045.26,
                'strike_increment': 25,
                'strike_range_width': 350,  # +/- from ATM
                'expected_moves': {
                    'small_move': 12.5,
                    'medium_move': 25.0,
                    'large_move': 40.0,
                    'conservative': 7.5
                },
                'min_premium': 0.50,
                'max_premium': 500.0
            }
    
    def update_config(self, **kwargs):
        """Update configuration parameters"""
        self.config.update(kwargs)
    
    def black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """Enhanced Black-Scholes with better error handling"""
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

        return {
            'price': price, 'delta': delta, 'gamma': gamma,
            'theta': theta, 'vega': vega, 'rho': rho, 'd1': d1, 'd2': d2
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
        
        # Generate strike range
        strike_range = self.generate_strike_range(S, dte_days)
        expected_moves = self.config['expected_moves']
        
        # Analyze both calls and puts
        call_df = self._generate_option_table(S, T, r, sigma, strike_range, 'call', expected_moves)
        put_df = self._generate_option_table(S, T, r, sigma, strike_range, 'put', expected_moves)
        
        # Combine results
        combined_df = pd.concat([call_df, put_df], ignore_index=True)
        
        # Filter by premium range
        combined_df = combined_df[
            (combined_df['premium'] >= self.config['min_premium']) & 
            (combined_df['premium'] <= self.config['max_premium'])
        ]
        
        # Prepare analysis summary
        analysis_summary = self._generate_summary(S, T, r, sigma, dte_days, call_df, put_df, combined_df)
        
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
                'premium': round(bs['price'], 2),
                'moneyness': round(moneyness, 4),
                'delta': round(bs['delta'], 4),
                'gamma': round(bs['gamma'], 6),
                'theta': round(bs['theta'], 3),
                'vega': round(bs['vega'], 3),
                'rho': round(bs['rho'], 3),
                'breakeven': round(prob_data['breakeven'], 2),
                'prob_profit': round(prob_data['prob_profit'], 3),
                'prob_itm': round(prob_data['prob_itm'], 3),
                'max_loss': round(bs['price'], 2),
                'day_trade_score': round(day_trade_score, 4),
                **{k: round(v, 3) for k, v in move_scenarios.items()}
            }
            
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
                'small_move_rr': row['small_move_rr'],
                'medium_move_rr': row['medium_move_rr'],
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
                'expected_moves': {
                    'small': row['small_move_rr'],
                    'medium': row['medium_move_rr'],
                    'large': row['large_move_rr']
                }
            }
            backtest_data['universe'].append(option_data)
        
        # Create rankings for different strategies
        backtest_data['rankings'] = {
            'high_delta': df.nlargest(10, 'delta')['strike'].tolist(),
            'best_rr': df.nlargest(10, 'small_move_rr')['strike'].tolist(),
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

def main():
    parser = argparse.ArgumentParser(description='Options Analysis for Day Trading')
    parser.add_argument('--underlying', choices=['SPY', 'SPX'], default='SPY', 
                       help='Underlying asset to analyze')
    parser.add_argument('--current-price', type=float, help='Current underlying price')
    parser.add_argument('--dte', type=int, default=8, help='Days to expiration')
    parser.add_argument('--iv', type=float, default=0.132, help='Implied volatility')
    parser.add_argument('--rate', type=float, default=0.044, help='Risk-free rate')
    parser.add_argument('--output-format', choices=['dataframe', 'json', 'trading_bot', 'backtester'], 
                       default='dataframe', help='Output format')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = OptionsAnalyzer(args.underlying)
    
    # Update price if provided
    if args.current_price:
        analyzer.update_config(current_price=args.current_price)
    
    # Get current price from config
    S = analyzer.config['current_price']
    T = args.dte / 252
    r = args.rate
    sigma = args.iv
    
    print(f"\n{args.underlying} Options Day Trading Analysis")
    print("=" * 60)
    print(f"Current {args.underlying} Price: ${S:.2f}")
    print(f"Days to Expiration: {args.dte}")
    print(f"Implied Volatility: {sigma:.1%}")
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
