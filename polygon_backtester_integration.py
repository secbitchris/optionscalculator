#!/usr/bin/env python3
"""
Polygon.io Backtester Integration
================================

This module integrates the OptionsAnalyzer with Polygon.io for backtesting.
Requires: polygon-api-client, pandas, numpy

Installation:
pip install polygon-api-client pandas numpy

"""

import json
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
from polygon import RESTClient
from option_scenario_calculator import OptionsAnalyzer

class PolygonBacktester:
    """Backtester integration using Polygon.io data"""
    
    def __init__(self, api_key: str, underlying: str = 'SPY'):
        """
        Initialize with Polygon.io API key
        
        Args:
            api_key: Your Polygon.io API key
            underlying: 'SPY' or 'SPX'
        """
        self.client = RESTClient(api_key)
        self.analyzer = OptionsAnalyzer(underlying)
        self.underlying = underlying
        self.backtest_results = []
        
    def get_historical_prices(self, start_date: str, end_date: str, timespan: str = 'day') -> pd.DataFrame:
        """
        Get historical price data from Polygon.io
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            timespan: 'minute', 'hour', 'day', 'week', 'month'
        """
        try:
            aggs = self.client.get_aggs(
                ticker=self.underlying,
                multiplier=1,
                timespan=timespan,
                from_=start_date,
                to=end_date
            )
            
            data = []
            for agg in aggs:
                data.append({
                    'timestamp': pd.to_datetime(agg.timestamp, unit='ms'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('timestamp', inplace=True)
            return df
            
        except Exception as e:
            print(f"Error fetching data from Polygon: {e}")
            return pd.DataFrame()
    
    def get_options_data(self, date: str, strikes: List[float], option_type: str, dte: int) -> Dict:
        """
        Get options data from Polygon.io (requires premium subscription)
        
        Args:
            date: Date in YYYY-MM-DD format
            strikes: List of strike prices
            option_type: 'call' or 'put'
            dte: Days to expiration
        """
        # Calculate expiration date
        exp_date = pd.to_datetime(date) + timedelta(days=dte)
        exp_str = exp_date.strftime('%Y-%m-%d')
        
        options_data = {}
        
        for strike in strikes:
            # Construct option symbol (OCC format)
            if self.underlying == 'SPY':
                option_symbol = f"O:{self.underlying}{exp_date.strftime('%y%m%d')}{option_type[0].upper()}{int(strike*1000):08d}"
            else:  # SPX
                option_symbol = f"O:{self.underlying}{exp_date.strftime('%y%m%d')}{option_type[0].upper()}{int(strike*1000):08d}"
            
            try:
                # Get option quotes (requires premium)
                quotes = self.client.get_quotes(
                    ticker=option_symbol,
                    timestamp=date
                )
                
                if quotes:
                    last_quote = list(quotes)[-1]
                    options_data[strike] = {
                        'bid': last_quote.bid,
                        'ask': last_quote.ask,
                        'mid': (last_quote.bid + last_quote.ask) / 2,
                        'symbol': option_symbol
                    }
                    
            except Exception as e:
                print(f"Error fetching option data for {strike}: {e}")
                continue
        
        return options_data
    
    def calculate_implied_volatility(self, date: str, window: int = 20) -> float:
        """
        Calculate implied volatility using historical price data
        
        Args:
            date: Current date
            window: Number of days for volatility calculation
        """
        end_date = pd.to_datetime(date)
        start_date = end_date - timedelta(days=window + 5)  # Extra days for weekends
        
        prices = self.get_historical_prices(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if len(prices) < window:
            return 0.15  # Default fallback
        
        # Calculate daily returns
        returns = prices['close'].pct_change().dropna()
        
        # Annualized volatility
        volatility = returns.std() * (252 ** 0.5)
        
        return volatility
    
    def run_backtest(self, start_date: str, end_date: str, dte: int = 7, 
                    rebalance_frequency: str = 'daily') -> Dict:
        """
        Run complete backtest with options analysis
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dte: Days to expiration for options
            rebalance_frequency: 'daily', 'weekly', 'monthly'
        """
        # Get underlying price data
        price_data = self.get_historical_prices(start_date, end_date)
        
        if price_data.empty:
            return {'error': 'No price data available'}
        
        backtest_results = []
        
        # Generate rebalance dates
        rebalance_dates = self._generate_rebalance_dates(
            price_data.index, rebalance_frequency
        )
        
        for date in rebalance_dates:
            if date not in price_data.index:
                continue
                
            current_price = price_data.loc[date, 'close']
            
            # Calculate IV
            iv = self.calculate_implied_volatility(date.strftime('%Y-%m-%d'))
            
            # Update analyzer with current price
            self.analyzer.update_config(current_price=current_price)
            
            # Run options analysis
            T = dte / 252
            analysis_data = self.analyzer.analyze_options(
                S=current_price,
                T=T,
                r=0.044,  # Could make this dynamic
                sigma=iv,
                dte_days=dte,
                output_format='backtester'
            )
            
            # Add market data
            analysis_data['market_data'] = {
                'date': date.strftime('%Y-%m-%d'),
                'underlying_price': current_price,
                'implied_vol': iv,
                'dte': dte
            }
            
            backtest_results.append(analysis_data)
            
            # Rate limiting for API calls
            time.sleep(0.1)
        
        return {
            'backtest_summary': {
                'underlying': self.underlying,
                'start_date': start_date,
                'end_date': end_date,
                'total_periods': len(backtest_results),
                'dte': dte,
                'rebalance_frequency': rebalance_frequency
            },
            'results': backtest_results
        }
    
    def _generate_rebalance_dates(self, date_index: pd.DatetimeIndex, 
                                frequency: str) -> List[pd.Timestamp]:
        """Generate rebalance dates based on frequency"""
        
        if frequency == 'daily':
            return date_index.tolist()
        elif frequency == 'weekly':
            return [d for d in date_index if d.weekday() == 0]  # Mondays
        elif frequency == 'monthly':
            return [d for d in date_index if d.day == 1]  # First of month
        else:
            return date_index.tolist()
    
    def analyze_backtest_performance(self, backtest_data: Dict) -> Dict:
        """
        Analyze backtest performance metrics
        
        Args:
            backtest_data: Output from run_backtest()
        """
        if 'results' not in backtest_data:
            return {'error': 'Invalid backtest data'}
        
        results = backtest_data['results']
        performance_metrics = {
            'total_periods': len(results),
            'avg_options_analyzed': 0,
            'avg_iv': 0,
            'price_range': {'min': float('inf'), 'max': 0},
            'best_strategies': {
                'high_delta': [],
                'best_rr': [],
                'day_trade_score': []
            }
        }
        
        for result in results:
            market_data = result['market_data']
            
            # Update averages
            performance_metrics['avg_options_analyzed'] += len(result['universe'])
            performance_metrics['avg_iv'] += market_data['implied_vol']
            
            # Update price range
            price = market_data['underlying_price']
            performance_metrics['price_range']['min'] = min(
                performance_metrics['price_range']['min'], price
            )
            performance_metrics['price_range']['max'] = max(
                performance_metrics['price_range']['max'], price
            )
            
            # Collect top strategies
            rankings = result['rankings']
            for strategy in ['high_delta', 'best_rr', 'day_trade_score']:
                if strategy in rankings:
                    performance_metrics['best_strategies'][strategy].extend(
                        rankings[strategy][:3]
                    )
        
        # Calculate averages
        total_periods = len(results)
        performance_metrics['avg_options_analyzed'] /= total_periods
        performance_metrics['avg_iv'] /= total_periods
        
        # Find most frequent strikes in each strategy
        for strategy in performance_metrics['best_strategies']:
            strikes = performance_metrics['best_strategies'][strategy]
            strike_counts = pd.Series(strikes).value_counts()
            performance_metrics['best_strategies'][strategy] = strike_counts.head(5).to_dict()
        
        return performance_metrics
    
    def export_for_analysis(self, backtest_data: Dict, filename: str = None) -> str:
        """Export backtest data for further analysis"""
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"polygon_backtest_{self.underlying}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(backtest_data, f, indent=2, default=str)
        
        return filename

# Example usage function
def run_polygon_backtest_example():
    """Example of running a backtest with Polygon.io data"""
    
    # You'll need to replace this with your actual Polygon.io API key
    API_KEY = "YOUR_POLYGON_API_KEY"
    
    print("=== POLYGON.IO BACKTESTER EXAMPLE ===")
    print("Note: Replace API_KEY with your actual Polygon.io key")
    
    # Initialize backtester
    backtester = PolygonBacktester(API_KEY, 'SPY')
    
    # Run backtest (example with small date range)
    start_date = "2024-11-01"
    end_date = "2024-11-15"
    
    print(f"Running backtest from {start_date} to {end_date}")
    
    try:
        backtest_results = backtester.run_backtest(
            start_date=start_date,
            end_date=end_date,
            dte=7,
            rebalance_frequency='daily'
        )
        
        if 'error' in backtest_results:
            print(f"Error: {backtest_results['error']}")
            return
        
        # Analyze performance
        performance = backtester.analyze_backtest_performance(backtest_results)
        
        print(f"\n=== BACKTEST RESULTS ===")
        print(f"Total periods analyzed: {performance['total_periods']}")
        print(f"Average options analyzed: {performance['avg_options_analyzed']:.0f}")
        print(f"Average IV: {performance['avg_iv']:.1%}")
        print(f"Price range: ${performance['price_range']['min']:.2f} - ${performance['price_range']['max']:.2f}")
        
        print(f"\n=== MOST FREQUENT TOP STRIKES ===")
        for strategy, strikes in performance['best_strategies'].items():
            print(f"{strategy}: {list(strikes.keys())[:3]}")
        
        # Export results
        filename = backtester.export_for_analysis(backtest_results)
        print(f"\nBacktest data exported to: {filename}")
        
    except Exception as e:
        print(f"Error running backtest: {e}")
        print("Make sure you have a valid Polygon.io API key and sufficient quota")

if __name__ == "__main__":
    run_polygon_backtest_example() 