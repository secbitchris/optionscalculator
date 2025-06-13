#!/usr/bin/env python3
"""
Integration Examples for Options Analysis
========================================

This file demonstrates how to integrate the OptionsAnalyzer with:
1. Backtesting systems
2. Live trading bots
3. Custom analysis workflows

"""

import json
import pandas as pd
from datetime import datetime, timedelta
from option_scenario_calculator import OptionsAnalyzer

class BacktesterIntegration:
    """Example integration with backtesting system"""
    
    def __init__(self, underlying='SPY'):
        self.analyzer = OptionsAnalyzer(underlying)
        self.results_history = []
    
    def daily_analysis(self, current_price, dte=7, iv=0.15, date=None):
        """Run daily options analysis for backtesting"""
        
        if date is None:
            date = datetime.now()
        
        # Update current price
        self.analyzer.update_config(current_price=current_price)
        
        # Run analysis
        T = dte / 252
        backtest_data = self.analyzer.analyze_options(
            S=current_price, 
            T=T, 
            r=0.044, 
            sigma=iv, 
            dte_days=dte,
            output_format='backtester'
        )
        
        # Add timestamp
        backtest_data['metadata']['analysis_date'] = date.strftime('%Y-%m-%d')
        
        # Store results
        self.results_history.append(backtest_data)
        
        return backtest_data
    
    def get_strategy_selections(self, strategy_name='day_trade_score', top_n=3):
        """Get top option selections for a specific strategy"""
        
        if not self.results_history:
            return []
        
        latest = self.results_history[-1]
        strategy_strikes = latest['rankings'].get(strategy_name, [])
        
        # Get detailed data for top strikes
        selections = []
        for strike in strategy_strikes[:top_n]:
            for option in latest['universe']:
                if option['strike'] == strike:
                    selections.append({
                        'strike': strike,
                        'type': option['type'],
                        'premium': option['premium'],
                        'delta': option['delta'],
                        'expected_rr': option['expected_moves']['small'],
                        'score': option['day_trade_score']
                    })
                    break
        
        return selections
    
    def export_for_backtest(self, filename=None):
        """Export results in format suitable for backtesting framework"""
        import os
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        if filename is None:
            filename = f"data/backtest_data_{self.analyzer.underlying}_{datetime.now().strftime('%Y%m%d')}.json"
        
        export_data = {
            'underlying': self.analyzer.underlying,
            'analysis_count': len(self.results_history),
            'date_range': {
                'start': self.results_history[0]['metadata']['analysis_date'] if self.results_history else None,
                'end': self.results_history[-1]['metadata']['analysis_date'] if self.results_history else None
            },
            'daily_analyses': self.results_history
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return filename

class TradingBotIntegration:
    """Example integration with live trading bot"""
    
    def __init__(self, underlying='SPY', risk_per_trade=0.02):
        self.analyzer = OptionsAnalyzer(underlying)
        self.risk_per_trade = risk_per_trade
        self.active_positions = []
        self.trading_signals = []
    
    def get_trading_signals(self, current_price, dte=7, iv=0.15, account_size=10000):
        """Generate trading signals for bot consumption"""
        
        # Update current price
        self.analyzer.update_config(current_price=current_price)
        
        # Run analysis
        T = dte / 252
        signals_data = self.analyzer.analyze_options(
            S=current_price,
            T=T,
            r=0.044,
            sigma=iv,
            dte_days=dte,
            output_format='trading_bot'
        )
        
        # Add position sizing
        for signal in signals_data['trading_signals']:
            max_risk = account_size * self.risk_per_trade
            max_contracts = int(max_risk / signal['max_loss'])
            signal['suggested_contracts'] = max(1, max_contracts)
            signal['total_cost'] = signal['premium'] * signal['suggested_contracts'] * 100
            signal['max_risk'] = signal['max_loss'] * signal['suggested_contracts'] * 100
        
        self.trading_signals = signals_data['trading_signals']
        return signals_data
    
    def filter_signals(self, min_score=0.35, max_premium=15, min_delta=0.3):
        """Filter signals based on trading criteria"""
        
        filtered = []
        for signal in self.trading_signals:
            if (signal['day_trade_score'] >= min_score and 
                signal['premium'] <= max_premium and 
                abs(signal['delta']) >= min_delta):
                filtered.append(signal)
        
        return sorted(filtered, key=lambda x: x['day_trade_score'], reverse=True)
    
    def create_order_instructions(self, filtered_signals, max_positions=3):
        """Create order instructions for trading bot"""
        
        orders = []
        for i, signal in enumerate(filtered_signals[:max_positions]):
            order = {
                'action': 'BUY_TO_OPEN',
                'symbol': signal['symbol'],
                'underlying': signal['underlying'],
                'strike': signal['strike'],
                'option_type': signal['option_type'],
                'expiration_dte': 7,  # Could be dynamic
                'quantity': signal['suggested_contracts'],
                'order_type': 'LIMIT',
                'limit_price': signal['premium'],
                'time_in_force': 'DAY',
                'metadata': {
                    'day_trade_score': signal['day_trade_score'],
                    'expected_rr': signal['small_move_rr'],
                    'max_loss': signal['max_risk'],
                    'confidence': signal['confidence']
                }
            }
            orders.append(order)
        
        return orders

class CustomAnalysisWorkflow:
    """Example custom analysis workflow"""
    
    def __init__(self):
        self.spy_analyzer = OptionsAnalyzer('SPY')
        self.spx_analyzer = OptionsAnalyzer('SPX')
    
    def comparative_analysis(self, spy_price, spx_price, dte=7, iv=0.15):
        """Compare SPY vs SPX opportunities"""
        
        T = dte / 252
        
        # Analyze both
        spy_data, spy_summary = self.spy_analyzer.analyze_options(spy_price, T, 0.044, iv, dte)
        spx_data, spx_summary = self.spx_analyzer.analyze_options(spx_price, T, 0.044, iv, dte)
        
        # Compare top opportunities
        spy_top = spy_data.head(5)
        spx_top = spx_data.head(5)
        
        comparison = {
            'analysis_date': datetime.now().isoformat(),
            'spy': {
                'price': spy_price,
                'atm_call_premium': spy_summary['atm_call_premium'],
                'atm_put_premium': spy_summary['atm_put_premium'],
                'top_opportunities': spy_top[['strike', 'type', 'premium', 'day_trade_score', 'small_move_rr']].to_dict('records')
            },
            'spx': {
                'price': spx_price,
                'atm_call_premium': spx_summary['atm_call_premium'],
                'atm_put_premium': spx_summary['atm_put_premium'],
                'top_opportunities': spx_top[['strike', 'type', 'premium', 'day_trade_score', 'small_move_rr']].to_dict('records')
            }
        }
        
        return comparison
    
    def multi_dte_analysis(self, underlying='SPY', current_price=605, dte_range=[3, 7, 14, 21]):
        """Analyze multiple DTEs for optimal selection"""
        
        analyzer = OptionsAnalyzer(underlying)
        analyzer.update_config(current_price=current_price)
        
        results = {}
        
        for dte in dte_range:
            T = dte / 252
            df, summary = analyzer.analyze_options(current_price, T, 0.044, 0.15, dte)
            
            # Get best call and put for each DTE
            best_call = df[df['type'] == 'CALL'].iloc[0]
            best_put = df[df['type'] == 'PUT'].iloc[0]
            
            results[f'{dte}dte'] = {
                'best_call': {
                    'strike': best_call['strike'],
                    'premium': best_call['premium'],
                    'delta': best_call['delta'],
                    'theta': best_call['theta'],
                    'score': best_call['day_trade_score']
                },
                'best_put': {
                    'strike': best_put['strike'],
                    'premium': best_put['premium'],
                    'delta': best_put['delta'],
                    'theta': best_put['theta'],
                    'score': best_put['day_trade_score']
                },
                'atm_call_premium': summary['atm_call_premium'],
                'atm_put_premium': summary['atm_put_premium']
            }
        
        return results

# Example usage functions
def example_backtester_usage():
    """Demonstrate backtester integration"""
    print("=== BACKTESTER INTEGRATION EXAMPLE ===")
    
    backtester = BacktesterIntegration('SPY')
    
    # Simulate 5 days of analysis
    for i in range(5):
        date = datetime.now() - timedelta(days=4-i)
        price = 605 + (i * 2)  # Simulate price changes
        
        result = backtester.daily_analysis(current_price=price, date=date)
        print(f"Day {i+1}: Analyzed {len(result['universe'])} options")
    
    # Get strategy selections
    selections = backtester.get_strategy_selections('day_trade_score', 3)
    print(f"\nTop 3 Day Trade Score selections:")
    for sel in selections:
        print(f"  ${sel['strike']} {sel['type']}: Score {sel['score']:.3f}, Premium ${sel['premium']:.2f}")
    
    # Export data
    filename = backtester.export_for_backtest()
    print(f"\nBacktest data exported to: {filename}")

def example_trading_bot_usage():
    """Demonstrate trading bot integration"""
    print("\n=== TRADING BOT INTEGRATION EXAMPLE ===")
    
    bot = TradingBotIntegration('SPY', risk_per_trade=0.02)
    
    # Get trading signals
    signals_data = bot.get_trading_signals(current_price=605, account_size=25000)
    print(f"Generated {len(signals_data['trading_signals'])} trading signals")
    
    # Filter signals
    filtered = bot.filter_signals(min_score=0.35, max_premium=15)
    print(f"Filtered to {len(filtered)} high-quality signals")
    
    # Create orders
    orders = bot.create_order_instructions(filtered, max_positions=3)
    print(f"\nGenerated {len(orders)} order instructions:")
    for order in orders:
        print(f"  {order['action']} {order['symbol']} x{order['quantity']} @ ${order['limit_price']:.2f}")

def example_custom_analysis():
    """Demonstrate custom analysis workflow"""
    print("\n=== CUSTOM ANALYSIS EXAMPLE ===")
    
    workflow = CustomAnalysisWorkflow()
    
    # Comparative analysis
    comparison = workflow.comparative_analysis(spy_price=605, spx_price=6050)
    print("SPY vs SPX Comparison:")
    print(f"  SPY ATM Call: ${comparison['spy']['atm_call_premium']:.2f}")
    print(f"  SPX ATM Call: ${comparison['spx']['atm_call_premium']:.2f}")
    
    # Multi-DTE analysis
    dte_results = workflow.multi_dte_analysis('SPY', 605)
    print("\nMulti-DTE Analysis:")
    for dte, data in dte_results.items():
        print(f"  {dte}: Best Call Score {data['best_call']['score']:.3f}, Premium ${data['best_call']['premium']:.2f}")

if __name__ == "__main__":
    # Run all examples
    example_backtester_usage()
    example_trading_bot_usage() 
    example_custom_analysis() 