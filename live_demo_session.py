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

    def get_live_options_chain(self, symbol, expiration_date=None, dte=7):
        """
        Get live options chain using hybrid approach (works around subscription limits)
        
        Parameters:
        symbol: Underlying symbol (SPY, SPX)
        expiration_date: Specific expiration date (YYYY-MM-DD) or None for auto
        dte: Days to expiration if expiration_date is None
        
        Returns:
        dict with options chain data
        """
        print(f"🔄 Getting options chain for {symbol} using hybrid system...")
        
        try:
            # Use hybrid system to get around subscription limitations
            from polygon_options_hybrid import PolygonOptionsHybrid
            hybrid = PolygonOptionsHybrid()
            
            # Get enhanced options chain with theoretical pricing (auto-detect market IV)
            chain_data = hybrid.get_enhanced_options_chain(symbol, dte)
            
            if not chain_data or not chain_data.get('contracts'):
                print("❌ No options data from hybrid system")
                return {}
            
            # Convert to expected format
            options_data = {
                'calls': {},
                'puts': {},
                'expiration_date': expiration_date or chain_data.get('expiration', ''),
                'underlying': symbol,
                'stock_price': chain_data.get('stock_price'),
                'dte': dte,
                'iv_used': chain_data.get('iv_used', 15.0)
            }
            
            # Process contracts into calls/puts
            for contract in chain_data['contracts']:
                strike = contract['strike']
                option_info = {
                    'ticker': contract['ticker'],
                    'strike': strike,
                    'bid': contract['bid'],
                    'ask': contract['ask'],
                    'mid': contract['mid'],
                    'theoretical_price': contract['theoretical_price'],
                    'spread': contract['ask'] - contract['bid'],
                    'contract_type': contract['type'],
                    'delta': contract['delta'],
                    'gamma': contract['gamma'],
                    'theta': contract['theta'],
                    'vega': contract['vega'],
                    'iv': contract['iv_used']
                }
                
                if contract['type'] == 'call':
                    options_data['calls'][strike] = option_info
                else:
                    options_data['puts'][strike] = option_info
            
            print(f"✅ Hybrid system: {len(options_data['calls'])} calls, {len(options_data['puts'])} puts")
            print(f"   📈 Live price: ${chain_data['stock_price']}")
            print(f"   🧮 Theoretical pricing with {chain_data['iv_used']}% IV")
            
            return options_data
            
        except Exception as e:
            print(f"❌ Error with hybrid options system: {e}")
            return {}

    def get_live_atm_straddle(self, symbol, current_price=None, dte=7):
        """
        Get live ATM straddle price from market data
        
        Parameters:
        symbol: Underlying symbol
        current_price: Current underlying price (fetched if None)
        dte: Days to expiration
        
        Returns:
        dict with live straddle information
        """
        if current_price is None:
            current_price = self.get_current_price(symbol)
        
        # Get options chain
        options_data = self.get_live_options_chain(symbol, dte=dte)
        
        if not options_data or not options_data['calls'] or not options_data['puts']:
            print("❌ No options data available")
            return {}
        
        # Find ATM strike (closest to current price)
        call_strikes = list(options_data['calls'].keys())
        atm_strike = min(call_strikes, key=lambda x: abs(x - current_price))
        
        # Get ATM call and put
        atm_call = options_data['calls'].get(atm_strike)
        atm_put = options_data['puts'].get(atm_strike)
        
        if not atm_call or not atm_put:
            print(f"❌ No ATM straddle data for strike ${atm_strike}")
            return {}
        
        # Calculate straddle metrics
        call_mid = atm_call['mid'] or (atm_call['bid'] + atm_call['ask']) / 2
        put_mid = atm_put['mid'] or (atm_put['bid'] + atm_put['ask']) / 2
        
        straddle_price = call_mid + put_mid
        straddle_expected_move = straddle_price  # Market's implied expected move
        
        return {
            'underlying': symbol,
            'current_price': current_price,
            'atm_strike': atm_strike,
            'expiration_date': options_data['expiration_date'],
            'dte': dte,
            
            # Call data
            'call_bid': atm_call['bid'],
            'call_ask': atm_call['ask'],
            'call_mid': call_mid,
            'call_spread': atm_call['spread'],
            
            # Put data  
            'put_bid': atm_put['bid'],
            'put_ask': atm_put['ask'],
            'put_mid': put_mid,
            'put_spread': atm_put['spread'],
            
            # Straddle metrics
            'straddle_price': straddle_price,
            'straddle_expected_move': straddle_expected_move,
            'breakeven_upper': atm_strike + straddle_price,
            'breakeven_lower': atm_strike - straddle_price,
            'expected_move_percentage': (straddle_expected_move / current_price) * 100,
            
            # Additional info
            'total_spread': atm_call['spread'] + atm_put['spread'],
            'straddle_cost_as_pct_of_underlying': (straddle_price / current_price) * 100
        }

    def calculate_live_expected_moves(self, symbol, dte=7):
        """
        Calculate expected moves using both live market data and IV formula
        
        Returns:
        dict comparing different calculation methods
        """
        # Get current price
        current_price = self.get_current_price(symbol)
        
        # Get estimated IV
        estimated_iv = self.estimate_iv_from_vix(symbol)
        
        # Method 1: Live straddle pricing from market
        live_straddle = self.get_live_atm_straddle(symbol, current_price, dte)
        
        # Method 2: IV formula calculation
        analyzer = OptionsAnalyzer(symbol)
        T = dte / 252
        formula_moves = analyzer.calculate_expected_move(current_price, estimated_iv, T)
        
        # Method 3: Theoretical straddle using Black-Scholes
        theoretical_straddle = analyzer.get_atm_straddle_price(current_price, T, 0.044, estimated_iv)
        
        comparison = {
            'underlying': symbol,
            'current_price': current_price,
            'dte': dte,
            'estimated_iv': estimated_iv,
            'timestamp': datetime.now().isoformat(),
            
            # Live market data
            'live_straddle_price': live_straddle.get('straddle_price'),
            'live_expected_move': live_straddle.get('straddle_expected_move'),
            'live_breakevens': {
                'upper': live_straddle.get('breakeven_upper'),
                'lower': live_straddle.get('breakeven_lower')
            } if live_straddle else None,
            
            # Formula-based
            'formula_1sigma_move': formula_moves['1_sigma'],
            'formula_2sigma_move': formula_moves['2_sigma'],
            'formula_percentage': formula_moves['percentage_1sigma'],
            
            # Theoretical straddle
            'theoretical_straddle_price': theoretical_straddle['straddle_price'],
            'theoretical_expected_move': theoretical_straddle['straddle_expected_move'],
            
            # Analysis
            'market_vs_formula_diff': abs(live_straddle.get('straddle_expected_move', 0) - formula_moves['1_sigma']) if live_straddle else None,
            'market_vs_theoretical_diff': abs(live_straddle.get('straddle_price', 0) - theoretical_straddle['straddle_price']) if live_straddle else None,
            'implied_volatility_from_market': None  # Could calculate this from market straddle price
        }
        
        return comparison

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