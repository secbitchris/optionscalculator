#!/usr/bin/env python3
"""
Excel Black-Scholes Validation

Comparing our calculator against the Excel implementation shown in the screenshot.
Excel Parameters:
- Symbol: SPY
- Underlying Price: $596.22
- Strike Price: $594.00
- Time to Expiration: 0.003968 years (approx 1 day)
- Risk-Free Rate: 4.40%
- Contract IV: 13.20%
- Price Adjustment: $2.00
- Adjusted Underlying: $598.22

Excel Results:
- CALL "Mark" Price: $3.35
- PUT "Mark" Price: $1.03
- Call Delta: 0.6822
- Put Delta: -0.3178
- Gamma: 0.0722 (call), 0.0719 (put)
- Theta: -0.0024 (per minute)
- Vega: 0.1344 (call), 0.1339 (put)
- Rho: 0.0160 (call), -0.0076 (put)
"""

from option_scenario_calculator import OptionsAnalyzer
import numpy as np

def validate_against_excel():
    print("=== Excel Black-Scholes Validation ===\n")
    
    # Excel parameters
    S = 596.22          # Underlying price
    K = 594.00          # Strike price  
    T = 0.003968        # Time to expiration (years)
    r = 0.044          # Risk-free rate (4.40%)
    sigma = 0.132      # Implied volatility (13.20%)
    
    print(f"Parameters from Excel:")
    print(f"Underlying Price (S): ${S}")
    print(f"Strike Price (K): ${K}")
    print(f"Time to Expiration (T): {T:.6f} years")
    print(f"Risk-Free Rate (r): {r:.1%}")
    print(f"Implied Volatility (σ): {sigma:.1%}")
    print()
    
    # Create analyzer
    analyzer = OptionsAnalyzer('SPY')
    
    # Calculate using our Black-Scholes implementation
    call_result = analyzer.black_scholes_price(S, K, T, r, sigma, 'call')
    put_result = analyzer.black_scholes_price(S, K, T, r, sigma, 'put')
    
    print("=== OUR CALCULATOR RESULTS ===")
    print(f"Call Price: ${call_result['price']:.2f}")
    print(f"Put Price: ${put_result['price']:.2f}")
    print(f"Call Delta: {call_result['delta']:.4f}")
    print(f"Put Delta: {put_result['delta']:.4f}")
    print(f"Call Gamma: {call_result['gamma']:.4f}")
    print(f"Put Gamma: {put_result['gamma']:.4f}")
    print(f"Call Theta: {call_result['theta']:.4f}")
    print(f"Put Theta: {put_result['theta']:.4f}")
    print(f"Call Vega: {call_result['vega']:.4f}")
    print(f"Put Vega: {put_result['vega']:.4f}")
    print(f"Call Rho: {call_result['rho']:.4f}")
    print(f"Put Rho: {put_result['rho']:.4f}")
    print()
    
    print("=== EXCEL RESULTS (from screenshot) ===")
    excel_results = {
        'call_price': 3.35,
        'put_price': 1.03,
        'call_delta': 0.6822,
        'put_delta': -0.3178,
        'call_gamma': 0.0722,
        'put_gamma': 0.0719,
        'theta': -0.0024,  # Per minute
        'call_vega': 0.1344,
        'put_vega': 0.1339,
        'call_rho': 0.0160,
        'put_rho': -0.0076
    }
    
    print(f"Call Price: ${excel_results['call_price']:.2f}")
    print(f"Put Price: ${excel_results['put_price']:.2f}")
    print(f"Call Delta: {excel_results['call_delta']:.4f}")
    print(f"Put Delta: {excel_results['put_delta']:.4f}")
    print(f"Call Gamma: {excel_results['call_gamma']:.4f}")
    print(f"Put Gamma: {excel_results['put_gamma']:.4f}")
    print(f"Theta: {excel_results['theta']:.4f} (per minute)")
    print(f"Call Vega: {excel_results['call_vega']:.4f}")
    print(f"Put Vega: {excel_results['put_vega']:.4f}")
    print(f"Call Rho: {excel_results['call_rho']:.4f}")
    print(f"Put Rho: {excel_results['put_rho']:.4f}")
    print()
    
    print("=== COMPARISON & DIFFERENCES ===")
    
    # Calculate differences
    call_price_diff = abs(call_result['price'] - excel_results['call_price'])
    put_price_diff = abs(put_result['price'] - excel_results['put_price'])
    call_delta_diff = abs(call_result['delta'] - excel_results['call_delta'])
    put_delta_diff = abs(put_result['delta'] - excel_results['put_delta'])
    
    print(f"Call Price Difference: ${call_price_diff:.3f}")
    print(f"Put Price Difference: ${put_price_diff:.3f}")
    print(f"Call Delta Difference: {call_delta_diff:.4f}")
    print(f"Put Delta Difference: {put_delta_diff:.4f}")
    print()
    
    # Check if differences are reasonable (within typical rounding/calculation differences)
    tolerance = 0.05  # 5 cents for prices, 0.005 for Greeks
    greek_tolerance = 0.005
    
    print("=== VALIDATION STATUS ===")
    print(f"Call Price: {'✅ PASS' if call_price_diff <= tolerance else '❌ FAIL'} (diff: ${call_price_diff:.3f})")
    print(f"Put Price: {'✅ PASS' if put_price_diff <= tolerance else '❌ FAIL'} (diff: ${put_price_diff:.3f})")
    print(f"Call Delta: {'✅ PASS' if call_delta_diff <= greek_tolerance else '❌ FAIL'} (diff: {call_delta_diff:.4f})")
    print(f"Put Delta: {'✅ PASS' if put_delta_diff <= greek_tolerance else '❌ FAIL'} (diff: {put_delta_diff:.4f})")
    
    print("\n=== ANALYSIS ===")
    if call_price_diff > tolerance or put_price_diff > tolerance:
        print("⚠️ Significant pricing differences detected.")
        print("Possible causes:")
        print("- Different dividend yield assumptions")
        print("- Different day count conventions")
        print("- Excel using different precision")
        print("- Price adjustment factor in Excel ($2.00)")
    else:
        print("✅ Results are very close to Excel implementation!")
        print("Minor differences likely due to:")
        print("- Rounding differences")
        print("- Calculation precision")
        print("- Day count methodology")
    
    print(f"\nNote: Excel shows 'Price Adjustment' of $2.00 and 'Adjusted Underlying' of $598.22")
    print(f"This might explain pricing differences if Excel is using the adjusted price.")
    
    # Test with adjusted price
    print(f"\n=== TESTING WITH EXCEL'S ADJUSTED PRICE ($598.22) ===")
    S_adjusted = 598.22
    call_adj = analyzer.black_scholes_price(S_adjusted, K, T, r, sigma, 'call')
    put_adj = analyzer.black_scholes_price(S_adjusted, K, T, r, sigma, 'put')
    
    print(f"Adjusted Call Price: ${call_adj['price']:.2f} (Excel: ${excel_results['call_price']:.2f})")
    print(f"Adjusted Put Price: ${put_adj['price']:.2f} (Excel: ${excel_results['put_price']:.2f})")
    
    adj_call_diff = abs(call_adj['price'] - excel_results['call_price'])
    adj_put_diff = abs(put_adj['price'] - excel_results['put_price'])
    
    print(f"Adjusted Call Difference: ${adj_call_diff:.3f}")
    print(f"Adjusted Put Difference: ${adj_put_diff:.3f}")
    
    if adj_call_diff < call_price_diff and adj_put_diff < put_price_diff:
        print("✅ Using adjusted price gives closer results!")
        print("Excel likely applies the $2.00 price adjustment before calculation.")

if __name__ == "__main__":
    validate_against_excel() 