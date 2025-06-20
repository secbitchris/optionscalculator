#!/usr/bin/env python3
"""
Test API Integration

Quick test script to demonstrate the Options Analysis API
for trading bot integration.
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoints():
    """Test all major API endpoints"""
    base_url = "http://localhost:5004/api/v1"
    
    print("🧪 Testing Options Analysis API Integration")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1. 🏥 Health Check")
    try:
        response = requests.get(f"{base_url}/health")
        health = response.json()
        print(f"   Status: {health.get('status', 'unknown')}")
        print(f"   Services: {health.get('services', {})}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Market Price
    print("\n2. 💰 Market Price")
    try:
        response = requests.get(f"{base_url}/market/price/SPY")
        price_data = response.json()
        print(f"   SPY Price: ${price_data.get('price', 0):.2f}")
        print(f"   Source: {price_data.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Market IV
    print("\n3. 📊 Market Implied Volatility")
    try:
        response = requests.get(f"{base_url}/market/iv/SPY")
        iv_data = response.json()
        print(f"   SPY IV: {iv_data.get('iv', 0):.1f}%")
        print(f"   Source: {iv_data.get('source', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Expected Moves
    print("\n4. 📈 Expected Moves")
    try:
        response = requests.get(f"{base_url}/market/expected-moves/SPY?dte=7")
        moves_data = response.json()
        if moves_data.get('success'):
            moves = moves_data['expected_moves']
            print(f"   7-day Expected Move: ±${moves.get('one_std', 0):.2f}")
            print(f"   68% Range: ${moves['price_ranges']['68_percent'][0]:.2f} - ${moves['price_ranges']['68_percent'][1]:.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Options Analysis
    print("\n5. 🎯 Options Analysis")
    try:
        payload = {
            "dte": 7,
            "risk_free_rate": 4.4
        }
        response = requests.post(f"{base_url}/options/analyze/SPY", json=payload)
        analysis = response.json()
        if analysis.get('success'):
            print(f"   Total Contracts: {analysis['summary']['total_contracts']}")
            print(f"   Current Price: ${analysis['analysis_params']['price']:.2f}")
            print(f"   IV: {analysis['analysis_params']['iv']:.1f}%")
            
            # Show top 3 contracts
            print("   Top 3 Contracts:")
            for i, contract in enumerate(analysis['contracts'][:3], 1):
                print(f"     {i}. {contract['strike']} {contract['type']} - ${contract['price']:.2f}")
                print(f"        Delta: {contract['delta']:.3f}, Gamma: {contract['gamma']:.4f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Best Contracts for Strategy
    print("\n6. 🏆 Best Contracts (Gamma Scalp)")
    try:
        payload = {
            "strategy": "gamma_scalp",
            "dte": 7,
            "max_contracts": 3,
            "min_liquidity": 6.0,
            "risk_tolerance": "medium"
        }
        response = requests.post(f"{base_url}/trading/best-contracts/SPY", json=payload)
        best_contracts = response.json()
        if best_contracts.get('success'):
            print(f"   Strategy: {best_contracts['strategy']}")
            for contract in best_contracts['ranked_contracts']:
                info = contract['contract']
                print(f"   Rank {contract['rank']}: {info['strike']} {info['type']} (Score: {contract['score']:.1f})")
                print(f"     Price: ${info['price']:.2f}, Gamma: {info['gamma']:.4f}")
                print(f"     Reasoning: {contract['reasoning']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: Quick Market Scan
    print("\n7. ⚡ Quick Market Scan")
    try:
        response = requests.get(f"{base_url}/trading/quick-scan/SPY")
        scan = response.json()
        if scan.get('success'):
            snapshot = scan['market_snapshot']
            print(f"   Price: ${snapshot['price']:.2f}")
            print(f"   IV: {snapshot['iv']:.1f}%")
            print(f"   Volatility Regime: {snapshot['volatility_regime']}")
            
            print("   Top Opportunities:")
            for opp in scan.get('top_opportunities', [])[:2]:
                print(f"     {opp['type']}: {opp['strike']} {opp['option_type']} (Score: {opp['score']:.1f})")
                print(f"       {opp['quick_reason']}")
            
            if scan.get('alerts'):
                print("   Alerts:")
                for alert in scan['alerts']:
                    print(f"     • {alert}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API Integration Test Complete!")
    return True

def demo_trading_bot_workflow():
    """Demonstrate a simple trading bot workflow"""
    print("\n🤖 Trading Bot Workflow Demo")
    print("=" * 60)
    
    base_url = "http://localhost:5004/api/v1"
    
    # Step 1: Market Analysis
    print("\n📊 Step 1: Market Analysis")
    try:
        scan_response = requests.get(f"{base_url}/trading/quick-scan/SPY")
        scan = scan_response.json()
        
        if scan.get('success'):
            snapshot = scan['market_snapshot']
            print(f"   Market Conditions:")
            print(f"   • Price: ${snapshot['price']:.2f}")
            print(f"   • IV: {snapshot['iv']:.1f}% ({snapshot['volatility_regime']} regime)")
            
            # Decision logic
            if snapshot['iv'] > 20:
                strategy = "theta_decay"
                print(f"   🎯 Strategy Selected: Premium Selling (High IV)")
            else:
                strategy = "gamma_scalp"
                print(f"   🎯 Strategy Selected: Gamma Scalping (Low IV)")
        else:
            print("   ❌ Market scan failed")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 2: Contract Selection
    print(f"\n🎯 Step 2: Contract Selection ({strategy})")
    try:
        payload = {
            "strategy": strategy,
            "dte": 7,
            "max_contracts": 2,
            "min_liquidity": 7.0,
            "risk_tolerance": "medium"
        }
        response = requests.post(f"{base_url}/trading/best-contracts/SPY", json=payload)
        contracts = response.json()
        
        if contracts.get('success') and contracts.get('ranked_contracts'):
            best_contract = contracts['ranked_contracts'][0]
            info = best_contract['contract']
            
            print(f"   Selected Contract:")
            print(f"   • Strike: {info['strike']} {info['type']}")
            print(f"   • Price: ${info['price']:.2f}")
            print(f"   • Greeks: Δ={info['delta']:.3f}, Γ={info['gamma']:.4f}, Θ={info['theta']:.3f}")
            print(f"   • Liquidity Score: {info['liquidity_score']:.1f}/10")
            print(f"   • Selection Score: {best_contract['score']:.1f}")
            print(f"   • Reasoning: {best_contract['reasoning']}")
            
            # Mock trade execution
            print(f"\n📈 Step 3: Trade Execution (SIMULATED)")
            print(f"   Action: BUY 5 contracts of {info['strike']} {info['type']}")
            print(f"   Cost: ${info['price'] * 5 * 100:.2f}")
            print(f"   Max Risk: ${info['price'] * 5 * 100:.2f}")
            
        else:
            print("   ❌ No suitable contracts found")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Risk Management
    print(f"\n🛡️ Step 4: Risk Management Setup")
    print(f"   • Stop Loss: 50% of premium paid")
    print(f"   • Profit Target: 25% gain")
    print(f"   • Time Stop: Close 1 day before expiration")
    print(f"   • Position Size: 5 contracts (manageable risk)")
    
    print("\n" + "=" * 60)
    print("✅ Trading Bot Workflow Demo Complete!")

if __name__ == "__main__":
    print("🚀 Options Analysis API Integration Test")
    print("Starting API service test...")
    
    # Test all endpoints
    success = test_api_endpoints()
    
    if success:
        # Demo trading bot workflow
        demo_trading_bot_workflow()
        
        print(f"\n🎉 Integration test successful!")
        print(f"📖 See API_DOCUMENTATION.md for complete endpoint reference")
        print(f"🤖 See trading_bot_examples.py for full bot implementations")
    else:
        print(f"\n❌ Integration test failed - check API service") 