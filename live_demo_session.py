#!/usr/bin/env python3
"""
Live Demo Session with Polygon.io

This script demonstrates the full system with real market data.
Securely handles API keys and provides comprehensive analysis.
"""

import os
import sys
from datetime import datetime, timedelta
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Force reload .env file
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

# Check if polygon is available
try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False
    print("⚠️  Polygon.io not installed. Install with: pip install polygon-api-client")

from option_scenario_calculator import OptionsAnalyzer

class LiveDemoSession:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.polygon_client = None
        
        if api_key and POLYGON_AVAILABLE:
            self.polygon_client = RESTClient(api_key)
            print("✅ Connected to Polygon.io")
        elif api_key:
            print("❌ Polygon.io library not available")
        else:
            print("📊 Running in offline mode with sample data")
    
    def get_current_price(self, symbol):
        """Get current price from Polygon.io or use fallback"""
        if self.polygon_client:
            try:
                # Get latest trade
                trades = self.polygon_client.get_last_trade(symbol)
                if trades:
                    price = trades.price
                    print(f"📈 Live {symbol} price: ${price:.2f}")
                    return price
            except Exception as e:
                print(f"⚠️  Error fetching live price: {e}")
        
        # Fallback prices
        fallback_prices = {
            'SPY': 604.53,
            'SPX': 6045.26
        }
        price = fallback_prices.get(symbol, 600.0)
        print(f"📊 Using fallback {symbol} price: ${price:.2f}")
        return price
    
    def estimate_iv_from_vix(self, underlying='SPY'):
        """Estimate IV from VIX or use reasonable default"""
        if self.polygon_client and underlying == 'SPY':
            try:
                # Get VIX data
                vix_trades = self.polygon_client.get_last_trade('I:VIX')
                if vix_trades:
                    vix_value = vix_trades.price
                    # Convert VIX to SPY IV (rough approximation)
                    estimated_iv = vix_value / 100
                    print(f"📊 VIX: {vix_value:.1f} → Estimated SPY IV: {estimated_iv:.1%}")
                    return estimated_iv
            except Exception as e:
                print(f"⚠️  Error fetching VIX: {e}")
        
        # Default IV estimates
        default_iv = {'SPY': 0.15, 'SPX': 0.16}
        iv = default_iv.get(underlying, 0.15)
        print(f"📊 Using default {underlying} IV: {iv:.1%}")
        return iv
    
    def run_comprehensive_demo(self, underlying='SPY', dte=7):
        """Run a comprehensive demo with all features"""
        print("=" * 80)
        print("🚀 LIVE OPTIONS ANALYSIS DEMO")
        print("=" * 80)
        
        # Get live data
        current_price = self.get_current_price(underlying)
        estimated_iv = self.estimate_iv_from_vix(underlying)
        
        # Initialize analyzer
        analyzer = OptionsAnalyzer(underlying)
        analyzer.update_config(current_price=current_price)
        
        print(f"\n📋 ANALYSIS PARAMETERS:")
        print(f"   Underlying: {underlying}")
        print(f"   Current Price: ${current_price:.2f}")
        print(f"   DTE: {dte} days")
        print(f"   Estimated IV: {estimated_iv:.1%}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Demo 1: Basic Analysis
        print(f"\n" + "="*60)
        print("📊 1. BASIC OPTIONS ANALYSIS")
        print("="*60)
        
        results, summary = analyzer.analyze_options(
            S=current_price,
            T=dte/252,
            r=0.044,
            sigma=estimated_iv,
            dte_days=dte
        )
        
        # Show top opportunities
        top_calls = results[results['type'] == 'CALL'].head(3)
        top_puts = results[results['type'] == 'PUT'].head(3)
        
        print(f"\n🔥 TOP 3 CALL OPPORTUNITIES:")
        for _, row in top_calls.iterrows():
            print(f"   ${row['strike']:.0f}: ${row['premium']:.2f} "
                  f"(Δ={row['delta']:.3f}, Score={row['day_trade_score']:.3f})")
        
        print(f"\n🔥 TOP 3 PUT OPPORTUNITIES:")
        for _, row in top_puts.iterrows():
            print(f"   ${row['strike']:.0f}: ${row['premium']:.2f} "
                  f"(Δ={row['delta']:.3f}, Score={row['day_trade_score']:.3f})")
        
        # Demo 2: IV Calculator
        print(f"\n" + "="*60)
        print("🧮 2. IMPLIED VOLATILITY CALCULATOR")
        print("="*60)
        
        # Use ATM option for IV demo
        atm_strike = round(current_price / analyzer.config['strike_increment']) * analyzer.config['strike_increment']
        atm_call = results[(results['strike'] == atm_strike) & (results['type'] == 'CALL')]
        
        if not atm_call.empty:
            market_price = atm_call.iloc[0]['premium']
            iv_result = analyzer.implied_volatility_calculator(
                market_price, current_price, atm_strike, dte/252, 0.044, 'call'
            )
            
            print(f"\n💡 ATM Call Analysis (${atm_strike:.0f}):")
            print(f"   Market Price: ${market_price:.2f}")
            print(f"   Implied Vol: {iv_result['implied_volatility']:.1%}")
            print(f"   IV Range: {iv_result['iv_low']:.1%} - {iv_result['iv_high']:.1%}")
            print(f"   Price Range: ${iv_result['price_at_iv_low']:.2f} - ${iv_result['price_at_iv_high']:.2f}")
        
        # Demo 3: Scenario Analysis
        print(f"\n" + "="*60)
        print("📈 3. PRICE SCENARIO ANALYSIS")
        print("="*60)
        
        scenarios = [
            ("Bullish", 3.0),
            ("Bearish", -2.0),
            ("Neutral", 0.0)
        ]
        
        for scenario_name, adjustment in scenarios:
            scenario_info = analyzer.price_adjustment_scenario(current_price, adjustment)
            
            # Quick analysis for this scenario
            analyzer.update_config(price_adjustment=adjustment)
            scenario_results, _ = analyzer.analyze_options(
                S=current_price, T=dte/252, r=0.044, sigma=estimated_iv, dte_days=dte
            )
            
            top_option = scenario_results.iloc[0]
            
            print(f"\n{scenario_name} Scenario ({adjustment:+.1f}):")
            print(f"   Price: ${scenario_info['base_price']:.2f} → ${scenario_info['adjusted_price']:.2f}")
            print(f"   Top Option: ${top_option['strike']:.0f} {top_option['type']} "
                  f"${top_option['premium']:.2f} (Score: {top_option['day_trade_score']:.3f})")
        
        # Reset price adjustment
        analyzer.update_config(price_adjustment=0.0)
        
        # Demo 4: Greeks Scaling
        print(f"\n" + "="*60)
        print("📐 4. GREEKS SCALING COMPARISON")
        print("="*60)
        
        if not atm_call.empty:
            print(f"\nATM Call Greeks (${atm_strike:.0f}):")
            
            for scaling in ['daily', 'per_minute', 'annual']:
                analyzer.set_greeks_scaling(scaling)
                bs_result = analyzer.black_scholes_price(
                    current_price, atm_strike, dte/252, 0.044, estimated_iv, 'call'
                )
                
                print(f"   {scaling.upper()}: "
                      f"Θ={bs_result['theta']:.6f}, "
                      f"Γ={bs_result['gamma']:.6f}, "
                      f"ν={bs_result['vega']:.4f}")
        
        # Demo 5: Save Results
        print(f"\n" + "="*60)
        print("💾 5. SAVING RESULTS")
        print("="*60)
        
        # Reset to daily scaling for saving
        analyzer.set_greeks_scaling('daily')
        analyzer.update_config(price_adjustment=0.0)
        
        final_results, final_summary = analyzer.analyze_options(
            S=current_price, T=dte/252, r=0.044, sigma=estimated_iv, dte_days=dte
        )
        
        files = analyzer.save_analysis((final_results, final_summary), f"live_demo_{underlying}")
        print(f"\n💾 Analysis saved:")
        if isinstance(files, tuple):
            print(f"   📄 CSV: {files[0]}")
            print(f"   📄 JSON: {files[1]}")
        else:
            print(f"   📄 File: {files}")
        
        print(f"\n" + "="*80)
        print("🎉 LIVE DEMO COMPLETE!")
        print("="*80)
        print(f"✅ Analyzed {len(final_results)} options")
        print(f"✅ Used {'live' if self.polygon_client else 'sample'} market data")
        print(f"✅ Demonstrated all 4 enhanced features")
        print(f"✅ Results saved to data/ directory")
        
        return final_results, final_summary

def main():
    print("🚀 LIVE OPTIONS ANALYSIS DEMO")
    print("=" * 50)
    
    # Check for API key
    api_key = None
    
    # Method 1: Command line argument
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
        print("✅ API key provided via command line")
    
    # Method 2: .env file (preferred)
    elif 'POLYGON_API_KEY' in os.environ:
        api_key = os.environ['POLYGON_API_KEY']
        if DOTENV_AVAILABLE:
            print("✅ API key loaded from .env file")
        else:
            print("✅ API key found in environment variable")
    
    # Method 3: Prompt user (but don't store)
    else:
        print("\n🔑 Polygon.io API Key Options:")
        print("   1. Create .env file: POLYGON_API_KEY=your_key_here")
        print("   2. Pass as argument: python live_demo_session.py YOUR_API_KEY")
        print("   3. Set environment: export POLYGON_API_KEY=YOUR_API_KEY")
        print("   4. Enter now (not stored): ")
        
        user_input = input("\nEnter API key (or press Enter for offline mode): ").strip()
        if user_input:
            api_key = user_input
            print("✅ API key entered")
        else:
            print("📊 Running in offline mode")
    
    # Initialize demo session
    demo = LiveDemoSession(api_key)
    
    # Run comprehensive demo
    print(f"\n🎯 Starting comprehensive demo...")
    
    try:
        # Demo with SPY
        results, summary = demo.run_comprehensive_demo('SPY', dte=7)
        
        print(f"\n🎊 Demo completed successfully!")
        print(f"   📊 Check the data/ directory for saved results")
        print(f"   🔄 Run again anytime with: python live_demo_session.py")
        
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print(f"   💡 Try running in offline mode or check your API key")

if __name__ == "__main__":
    main() 