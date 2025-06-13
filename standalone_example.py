#!/usr/bin/env python3
"""
Standalone Options Calculator Example

This demonstrates how to use the options calculator completely locally
without any external APIs or data sources.

Requirements: numpy, pandas, scipy (all available via pip)
"""

from option_scenario_calculator import OptionsAnalyzer

def main():
    print("=== Standalone Options Analysis Example ===\n")
    
    # Example 1: Basic SPY analysis
    print("1. Basic SPY Analysis:")
    analyzer_spy = OptionsAnalyzer('SPY')
    analyzer_spy.update_config(current_price=605.0)
    
    # Analyze with 7 DTE and 15% IV
    results_spy, summary_spy = analyzer_spy.analyze_options(
        S=605.0,           # Current price
        T=7/252,           # 7 days to expiration (as fraction of year)
        r=0.044,           # 4.4% risk-free rate
        sigma=0.15,        # 15% implied volatility
        dte_days=7
    )
    
    print(f"Analyzed {len(results_spy)} SPY options")
    print(f"ATM Call Premium: ${summary_spy['atm_call_premium']:.2f}")
    print(f"ATM Put Premium: ${summary_spy['atm_put_premium']:.2f}")
    
    # Show top opportunities
    top_calls = results_spy[results_spy['type'] == 'CALL'].head(3)
    print("\nTop 3 Call Options:")
    for _, row in top_calls.iterrows():
        print(f"  ${row['strike']:.0f}: Premium ${row['premium']:.2f}, "
              f"Delta {row['delta']:.3f}, Score {row['day_trade_score']:.3f}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 2: Custom SPX analysis with earnings scenario
    print("2. Custom SPX Earnings Analysis:")
    analyzer_spx = OptionsAnalyzer('SPX')
    analyzer_spx.update_config(
        current_price=6000.0,
        expected_moves={
            'earnings_beat': 75.0,      # Big earnings move
            'earnings_miss': -50.0,     # Earnings disappointment  
            'normal_reaction': 25.0     # Typical reaction
        }
    )
    
    results_spx, summary_spx = analyzer_spx.analyze_options(
        S=6000.0,
        T=3/252,           # 3 DTE (earnings week)
        r=0.044,
        sigma=0.25,        # 25% IV (high volatility)
        dte_days=3
    )
    
    print(f"Analyzed {len(results_spx)} SPX options")
    print(f"Expected moves: {analyzer_spx.config['expected_moves']}")
    
    # Show best scoring options
    best_options = results_spx.nlargest(5, 'day_trade_score')
    print("\nTop 5 Scoring Options:")
    for _, row in best_options.iterrows():
        print(f"  ${row['strike']:.0f} {row['type']}: "
              f"Premium ${row['premium']:.2f}, Score {row['day_trade_score']:.3f}")
    
    print("\n" + "="*60 + "\n")
    
    # Example 3: Save results locally
    print("3. Saving Results:")
    csv_file, json_file = analyzer_spx.save_analysis((results_spx, summary_spx), "earnings_analysis")
    print(f"Saved CSV: {csv_file}")
    print(f"Saved JSON: {json_file}")
    
    print("\n=== Analysis Complete ===")
    print("All calculations performed locally using Black-Scholes model.")
    print("No external APIs or real-time data required!")

if __name__ == "__main__":
    main() 