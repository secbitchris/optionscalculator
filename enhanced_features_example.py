#!/usr/bin/env python3
"""
Enhanced Features Example

Demonstrates the four new enhancements:
1. IV Calculator (reverse Black-Scholes)
2. Price Adjustment scenarios
3. Mark vs Theoretical pricing
4. Greeks scaling options

Run this to see all new features in action!
"""

from option_scenario_calculator import OptionsAnalyzer

def main():
    print("=== ENHANCED OPTIONS CALCULATOR FEATURES ===\n")
    
    # Setup
    analyzer = OptionsAnalyzer('SPY')
    S = 596.22
    K = 594.00
    T = 1/252  # 1 day
    r = 0.044
    sigma = 0.132
    
    print("=== 1. IMPLIED VOLATILITY CALCULATOR ===")
    print("Calculate IV from market prices (reverse Black-Scholes)")
    
    # Example: Calculate IV from the Excel screenshot values
    market_price_call = 3.35
    market_price_put = 1.03
    
    iv_call = analyzer.implied_volatility_calculator(market_price_call, S, K, T, r, 'call')
    iv_put = analyzer.implied_volatility_calculator(market_price_put, S, K, T, r, 'put')
    
    print(f"\nCall Option (${K:.0f}):")
    print(f"  Market Price: ${iv_call['market_price']:.2f}")
    print(f"  Implied Vol: {iv_call['implied_volatility']:.1%}")
    print(f"  IV Range: {iv_call['iv_low']:.1%} - {iv_call['iv_high']:.1%}")
    print(f"  Price Range: ${iv_call['price_at_iv_low']:.2f} - ${iv_call['price_at_iv_high']:.2f}")
    
    print(f"\nPut Option (${K:.0f}):")
    print(f"  Market Price: ${iv_put['market_price']:.2f}")
    print(f"  Implied Vol: {iv_put['implied_volatility']:.1%}")
    print(f"  IV Range: {iv_put['iv_low']:.1%} - {iv_put['iv_high']:.1%}")
    print(f"  Price Range: ${iv_put['price_at_iv_low']:.2f} - ${iv_put['price_at_iv_high']:.2f}")
    
    print("\n" + "="*60 + "\n")
    
    print("=== 2. PRICE ADJUSTMENT SCENARIOS ===")
    print("Model different underlying price scenarios")
    
    # Test different price adjustments
    adjustments = [2.0, -1.5, 0.0]
    
    for adj in adjustments:
        scenario = analyzer.price_adjustment_scenario(S, adj)
        print(f"\nAdjustment: {adj:+.1f}")
        print(f"  Scenario: {scenario['scenario_type'].title()}")
        print(f"  Price: ${scenario['base_price']:.2f} → ${scenario['adjusted_price']:.2f}")
        print(f"  Change: {scenario['percentage_change']:+.1f}%")
        
        # Show option price impact
        bs_base = analyzer.black_scholes_price(S, K, T, r, sigma, 'call')
        bs_adj = analyzer.black_scholes_price(scenario['adjusted_price'], K, T, r, sigma, 'call')
        price_impact = bs_adj['price'] - bs_base['price']
        print(f"  Call Price Impact: ${price_impact:+.2f}")
    
    print("\n" + "="*60 + "\n")
    
    print("=== 3. MARK VS THEORETICAL PRICING ===")
    print("Compare theoretical Black-Scholes vs estimated market prices")
    
    # Calculate both theoretical and mark prices
    bs_result = analyzer.black_scholes_price(S, K, T, r, sigma, 'call')
    mark_info = analyzer.calculate_mark_price(bs_result['price'], S, K, 'call')
    
    print(f"\nCall Option (${K:.0f}):")
    print(f"  Theoretical Price: ${mark_info['theoretical_price']:.2f}")
    print(f"  Mark Price: ${mark_info['mark_price']:.2f}")
    print(f"  Bid: ${mark_info['bid']:.2f}")
    print(f"  Ask: ${mark_info['ask']:.2f}")
    print(f"  Spread: ${mark_info['spread']:.2f} ({mark_info['spread_percentage']:.1f}%)")
    
    # Test with different moneyness
    strikes = [590, 596, 605]  # ITM, ATM, OTM
    print(f"\nSpread Analysis by Moneyness:")
    for strike in strikes:
        bs_test = analyzer.black_scholes_price(S, strike, T, r, sigma, 'call')
        mark_test = analyzer.calculate_mark_price(bs_test['price'], S, strike, 'call')
        moneyness = S / strike
        print(f"  ${strike}: {mark_test['spread_percentage']:.1f}% spread (moneyness: {moneyness:.3f})")
    
    print("\n" + "="*60 + "\n")
    
    print("=== 4. GREEKS SCALING OPTIONS ===")
    print("Compare Greeks in different time scales (like Excel)")
    
    bs_result = analyzer.black_scholes_price(S, K, T, r, sigma, 'call')
    
    print(f"\nCall Option Greeks (${K:.0f}):")
    
    # Test all scaling options
    scalings = ['daily', 'per_minute', 'annual']
    for scaling in scalings:
        analyzer.set_greeks_scaling(scaling)
        scaled_result = analyzer.black_scholes_price(S, K, T, r, sigma, 'call')
        
        print(f"\n{scaling.upper()} scaling:")
        print(f"  Delta: {scaled_result['delta']:.4f}")
        print(f"  Gamma: {scaled_result['gamma']:.6f}")
        print(f"  Theta: {scaled_result['theta']:.6f}")
        print(f"  Vega: {scaled_result['vega']:.4f}")
        print(f"  Rho: {scaled_result['rho']:.4f}")
    
    # Reset to daily
    analyzer.set_greeks_scaling('daily')
    
    print("\n" + "="*60 + "\n")
    
    print("=== 5. COMBINED ANALYSIS EXAMPLE ===")
    print("Using multiple features together")
    
    # Configure for advanced analysis
    analyzer.update_config(
        current_price=S,
        price_adjustment=2.0,  # Bullish scenario
        mark_vs_theoretical='mark',  # Use mark pricing
        expected_moves={
            'target': 2.5,
            'breakout': 5.0,
            'conservative': 1.0
        }
    )
    analyzer.set_greeks_scaling('per_minute')  # Excel-style scaling
    
    # Run analysis
    results, summary = analyzer.analyze_options(S, T, r, sigma, 1)
    
    print(f"Analysis Summary:")
    print(f"  Base Price: ${S:.2f}")
    print(f"  Scenario: {summary.get('price_adjustment', {}).get('scenario_type', 'N/A').title()}")
    print(f"  Options Analyzed: {len(results)}")
    print(f"  Greeks Scaling: per_minute (Excel-style)")
    print(f"  Pricing Mode: mark (includes spreads)")
    
    # Show top call
    top_call = results[results['type'] == 'CALL'].iloc[0]
    print(f"\nTop Call Option:")
    print(f"  Strike: ${top_call['strike']:.0f}")
    print(f"  Mark Price: ${top_call['premium']:.2f}")
    print(f"  Theoretical: ${top_call['theoretical_price']:.2f}")
    if 'spread' in top_call:
        print(f"  Spread: ${top_call['spread']:.2f}")
    print(f"  Delta: {top_call['delta']:.4f}")
    print(f"  Theta: {top_call['theta']:.6f} (per minute)")
    print(f"  Score: {top_call['day_trade_score']:.3f}")
    
    print(f"\n=== ALL FEATURES WORKING TOGETHER! ===")
    print("The calculator now has Excel-level functionality with:")
    print("✅ Implied Volatility Calculator")
    print("✅ Price Adjustment Scenarios") 
    print("✅ Mark vs Theoretical Pricing")
    print("✅ Flexible Greeks Scaling")

if __name__ == "__main__":
    main() 