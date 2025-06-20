#!/usr/bin/env python3
"""
Trading Bot Integration Examples

Complete examples showing how to integrate with the Options Analysis API
for various trading strategies and use cases.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class OptionsAnalysisClient:
    """Client for Options Analysis API"""
    
    def __init__(self, base_url: str = "http://localhost:5003/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def get_market_price(self, symbol: str) -> Dict:
        """Get current market price"""
        response = self.session.get(f"{self.base_url}/market/price/{symbol}")
        return response.json()
    
    def get_market_iv(self, symbol: str) -> Dict:
        """Get current implied volatility"""
        response = self.session.get(f"{self.base_url}/market/iv/{symbol}")
        return response.json()
    
    def get_expected_moves(self, symbol: str, dte: int = 7, iv: Optional[float] = None) -> Dict:
        """Get expected price moves"""
        params = {"dte": dte}
        if iv:
            params["iv"] = iv
        response = self.session.get(f"{self.base_url}/market/expected-moves/{symbol}", params=params)
        return response.json()
    
    def analyze_options(self, symbol: str, dte: int = 7, price: Optional[float] = None, 
                       iv: Optional[float] = None, risk_free_rate: float = 4.4) -> Dict:
        """Get comprehensive options analysis"""
        data = {
            "dte": dte,
            "risk_free_rate": risk_free_rate
        }
        if price:
            data["price"] = price
        if iv:
            data["iv"] = iv
            
        response = self.session.post(f"{self.base_url}/options/analyze/{symbol}", json=data)
        return response.json()
    
    def get_best_contracts(self, symbol: str, strategy: str, dte: int = 7, 
                          max_contracts: int = 5, min_liquidity: float = 7.0,
                          risk_tolerance: str = "medium") -> Dict:
        """Get strategy-optimized contract rankings"""
        data = {
            "strategy": strategy,
            "dte": dte,
            "max_contracts": max_contracts,
            "min_liquidity": min_liquidity,
            "risk_tolerance": risk_tolerance
        }
        response = self.session.post(f"{self.base_url}/trading/best-contracts/{symbol}", json=data)
        return response.json()
    
    def quick_scan(self, symbol: str) -> Dict:
        """Get quick market scan"""
        response = self.session.get(f"{self.base_url}/trading/quick-scan/{symbol}")
        return response.json()
    
    def health_check(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()

# ============================================================================
# GAMMA SCALPING BOT EXAMPLE
# ============================================================================

class GammaScalpingBot:
    """
    Example gamma scalping bot that uses high-gamma options
    to profit from intraday price movements
    """
    
    def __init__(self, api_client: OptionsAnalysisClient):
        self.api = api_client
        self.symbol = "SPY"
        self.position = None
        self.target_gamma = 0.02  # Minimum gamma threshold
        self.max_position_size = 10  # Max contracts
        
    def scan_for_opportunities(self) -> Optional[Dict]:
        """Scan for gamma scalping opportunities"""
        print("🔍 Scanning for gamma scalping opportunities...")
        
        # Get best gamma scalp contracts
        result = self.api.get_best_contracts(
            symbol=self.symbol,
            strategy="gamma_scalp",
            dte=7,
            max_contracts=3,
            min_liquidity=8.0,
            risk_tolerance="medium"
        )
        
        if not result.get('success') or not result.get('ranked_contracts'):
            print("❌ No suitable contracts found")
            return None
        
        # Get the top-ranked contract
        best_contract = result['ranked_contracts'][0]
        contract_info = best_contract['contract']
        
        # Check if gamma meets our threshold
        if abs(contract_info['gamma']) < self.target_gamma:
            print(f"⚠️ Gamma too low: {contract_info['gamma']:.4f} < {self.target_gamma}")
            return None
        
        print(f"✅ Found opportunity: {contract_info['strike']} {contract_info['type']}")
        print(f"   Gamma: {contract_info['gamma']:.4f}")
        print(f"   Score: {best_contract['score']}")
        print(f"   Reasoning: {best_contract['reasoning']}")
        
        return best_contract
    
    def execute_trade(self, contract_info: Dict) -> bool:
        """Execute gamma scalp trade (mock implementation)"""
        print(f"📈 Executing gamma scalp trade:")
        print(f"   Strike: {contract_info['contract']['strike']}")
        print(f"   Type: {contract_info['contract']['type']}")
        print(f"   Price: ${contract_info['contract']['price']:.2f}")
        print(f"   Gamma: {contract_info['contract']['gamma']:.4f}")
        
        # Mock trade execution
        self.position = {
            "strike": contract_info['contract']['strike'],
            "type": contract_info['contract']['type'],
            "quantity": min(self.max_position_size, 5),
            "entry_price": contract_info['contract']['price'],
            "entry_time": datetime.now(),
            "gamma": contract_info['contract']['gamma']
        }
        
        print(f"✅ Position opened: {self.position['quantity']} contracts")
        return True
    
    def monitor_position(self) -> bool:
        """Monitor existing position for exit signals"""
        if not self.position:
            return False
        
        print("📊 Monitoring gamma scalp position...")
        
        # Get current market data
        price_data = self.api.get_market_price(self.symbol)
        current_price = price_data['price']
        
        # Get updated analysis
        analysis = self.api.analyze_options(self.symbol, dte=7)
        
        # Find our contract in the analysis
        our_contract = None
        for contract in analysis.get('contracts', []):
            if (contract['strike'] == self.position['strike'] and 
                contract['type'] == self.position['type']):
                our_contract = contract
                break
        
        if not our_contract:
            print("⚠️ Contract not found in analysis")
            return False
        
        current_price_option = our_contract['price']
        pnl = (current_price_option - self.position['entry_price']) * self.position['quantity'] * 100
        
        print(f"   Current option price: ${current_price_option:.2f}")
        print(f"   P&L: ${pnl:.2f}")
        print(f"   Gamma: {our_contract['gamma']:.4f}")
        
        # Exit conditions
        if pnl > 200:  # Take profit at $200
            print("✅ Taking profit!")
            return self.close_position()
        elif pnl < -100:  # Stop loss at -$100
            print("❌ Stop loss triggered!")
            return self.close_position()
        elif abs(our_contract['gamma']) < 0.01:  # Gamma too low
            print("⚠️ Gamma decay - closing position")
            return self.close_position()
        
        return True
    
    def close_position(self) -> bool:
        """Close current position"""
        if not self.position:
            return False
        
        print(f"🔄 Closing position: {self.position['quantity']} contracts")
        self.position = None
        print("✅ Position closed")
        return True
    
    def run_strategy(self, iterations: int = 5):
        """Run the gamma scalping strategy"""
        print("🚀 Starting Gamma Scalping Bot")
        print("=" * 50)
        
        for i in range(iterations):
            print(f"\n--- Iteration {i+1}/{iterations} ---")
            
            # Check API health
            health = self.api.health_check()
            if health.get('status') != 'healthy':
                print("❌ API not healthy, skipping iteration")
                continue
            
            # Monitor existing position or look for new opportunities
            if self.position:
                if not self.monitor_position():
                    continue
            else:
                opportunity = self.scan_for_opportunities()
                if opportunity:
                    self.execute_trade(opportunity)
            
            # Wait before next iteration
            print("⏳ Waiting 30 seconds...")
            time.sleep(30)
        
        # Close any remaining position
        if self.position:
            self.close_position()
        
        print("\n🏁 Gamma Scalping Bot completed")

# ============================================================================
# THETA DECAY BOT EXAMPLE
# ============================================================================

class ThetaDecayBot:
    """
    Example theta decay bot that sells premium in high IV environments
    """
    
    def __init__(self, api_client: OptionsAnalysisClient):
        self.api = api_client
        self.symbol = "SPY"
        self.positions = []
        self.min_iv = 18.0  # Minimum IV for premium selling
        self.target_dte = 7   # Target days to expiration
        
    def scan_for_premium_selling(self) -> List[Dict]:
        """Scan for theta decay opportunities"""
        print("🔍 Scanning for theta decay opportunities...")
        
        # Check IV environment
        iv_data = self.api.get_market_iv(self.symbol)
        current_iv = iv_data['iv']
        
        print(f"📊 Current IV: {current_iv:.1f}%")
        
        if current_iv < self.min_iv:
            print(f"⚠️ IV too low for premium selling: {current_iv:.1f}% < {self.min_iv}%")
            return []
        
        print("✅ High IV environment - premium selling favored")
        
        # Get best theta decay contracts
        result = self.api.get_best_contracts(
            symbol=self.symbol,
            strategy="theta_decay",
            dte=self.target_dte,
            max_contracts=5,
            min_liquidity=7.0,
            risk_tolerance="medium"
        )
        
        if not result.get('success'):
            return []
        
        opportunities = []
        for contract in result.get('ranked_contracts', []):
            contract_info = contract['contract']
            
            # Filter for good theta decay candidates
            if (abs(contract_info['theta']) > 0.05 and  # Strong theta
                abs(contract_info['moneyness']) > 2.0):  # OTM
                
                opportunities.append(contract)
                print(f"✅ Theta opportunity: {contract_info['strike']} {contract_info['type']}")
                print(f"   Theta: {contract_info['theta']:.3f}")
                print(f"   Moneyness: {contract_info['moneyness']:.1f}%")
        
        return opportunities
    
    def execute_premium_sale(self, contract_info: Dict) -> bool:
        """Execute premium selling trade (mock implementation)"""
        print(f"📉 Selling premium:")
        print(f"   Strike: {contract_info['contract']['strike']}")
        print(f"   Type: {contract_info['contract']['type']}")
        print(f"   Premium: ${contract_info['contract']['price']:.2f}")
        print(f"   Theta: {contract_info['contract']['theta']:.3f}")
        
        # Mock trade execution
        position = {
            "strike": contract_info['contract']['strike'],
            "type": contract_info['contract']['type'],
            "quantity": -5,  # Short position
            "entry_price": contract_info['contract']['price'],
            "entry_time": datetime.now(),
            "theta": contract_info['contract']['theta'],
            "target_profit": contract_info['contract']['price'] * 0.5  # 50% profit target
        }
        
        self.positions.append(position)
        print(f"✅ Premium sold: {abs(position['quantity'])} contracts")
        return True
    
    def monitor_theta_positions(self):
        """Monitor theta decay positions"""
        if not self.positions:
            return
        
        print(f"📊 Monitoring {len(self.positions)} theta positions...")
        
        # Get current analysis
        analysis = self.api.analyze_options(self.symbol, dte=self.target_dte)
        
        positions_to_close = []
        
        for i, position in enumerate(self.positions):
            # Find contract in analysis
            our_contract = None
            for contract in analysis.get('contracts', []):
                if (contract['strike'] == position['strike'] and 
                    contract['type'] == position['type']):
                    our_contract = contract
                    break
            
            if not our_contract:
                continue
            
            current_price = our_contract['price']
            pnl = (position['entry_price'] - current_price) * abs(position['quantity']) * 100
            
            print(f"   Position {i+1}: {position['strike']} {position['type']}")
            print(f"     Current price: ${current_price:.2f}")
            print(f"     P&L: ${pnl:.2f}")
            print(f"     Theta: {our_contract['theta']:.3f}")
            
            # Exit conditions
            if current_price <= position['target_profit']:
                print("     ✅ Profit target reached!")
                positions_to_close.append(i)
            elif pnl < -150:  # Stop loss
                print("     ❌ Stop loss triggered!")
                positions_to_close.append(i)
            elif our_contract.get('days_to_expiry', 7) <= 2:  # Close near expiration
                print("     ⏰ Near expiration - closing")
                positions_to_close.append(i)
        
        # Close positions (reverse order to maintain indices)
        for i in reversed(positions_to_close):
            self.close_position(i)
    
    def close_position(self, index: int) -> bool:
        """Close specific position"""
        if index >= len(self.positions):
            return False
        
        position = self.positions.pop(index)
        print(f"🔄 Closing theta position: {position['strike']} {position['type']}")
        return True
    
    def run_strategy(self, iterations: int = 10):
        """Run the theta decay strategy"""
        print("🚀 Starting Theta Decay Bot")
        print("=" * 50)
        
        for i in range(iterations):
            print(f"\n--- Iteration {i+1}/{iterations} ---")
            
            # Monitor existing positions
            self.monitor_theta_positions()
            
            # Look for new opportunities if we have capacity
            if len(self.positions) < 3:  # Max 3 positions
                opportunities = self.scan_for_premium_selling()
                for opp in opportunities[:1]:  # Take only 1 new position per iteration
                    self.execute_premium_sale(opp)
                    break
            
            print("⏳ Waiting 60 seconds...")
            time.sleep(60)
        
        # Close all remaining positions
        while self.positions:
            self.close_position(0)
        
        print("\n🏁 Theta Decay Bot completed")

# ============================================================================
# MOMENTUM TRADING BOT EXAMPLE
# ============================================================================

class MomentumTradingBot:
    """
    Example momentum bot that uses high-delta options for directional plays
    """
    
    def __init__(self, api_client: OptionsAnalysisClient):
        self.api = api_client
        self.symbol = "SPY"
        self.position = None
        self.min_delta = 0.4  # Minimum delta for momentum plays
        
    def detect_momentum(self) -> Optional[str]:
        """Detect market momentum direction"""
        print("🔍 Detecting market momentum...")
        
        # Get quick market scan
        scan = self.api.quick_scan(self.symbol)
        
        if not scan.get('success'):
            return None
        
        market_data = scan['market_snapshot']
        trend = market_data.get('trend', 'neutral')
        iv = market_data.get('iv', 15.0)
        
        print(f"📊 Market trend: {trend}")
        print(f"📊 IV: {iv:.1f}%")
        
        # Look for momentum signals in opportunities
        opportunities = scan.get('top_opportunities', [])
        momentum_signals = [opp for opp in opportunities if opp['type'] == 'momentum']
        
        if momentum_signals:
            print("✅ Momentum signals detected")
            return trend
        
        # Simple momentum detection based on IV and alerts
        alerts = scan.get('alerts', [])
        if any('momentum' in alert.lower() for alert in alerts):
            return trend
        
        if trend != 'neutral':
            return trend
        
        print("⚠️ No clear momentum detected")
        return None
    
    def find_momentum_contract(self, direction: str) -> Optional[Dict]:
        """Find best contract for momentum play"""
        print(f"🎯 Finding momentum contract for {direction} direction...")
        
        # Get best momentum contracts
        result = self.api.get_best_contracts(
            symbol=self.symbol,
            strategy="momentum",
            dte=14,  # Longer DTE for momentum
            max_contracts=3,
            min_liquidity=8.0,
            risk_tolerance="high"
        )
        
        if not result.get('success'):
            return None
        
        # Filter contracts based on direction and delta
        for contract in result.get('ranked_contracts', []):
            contract_info = contract['contract']
            delta = contract_info['delta']
            
            # For bullish momentum, want positive delta (calls or ITM puts)
            # For bearish momentum, want negative delta (puts or ITM calls)
            if direction == 'bullish' and delta > self.min_delta:
                print(f"✅ Bullish momentum contract: {contract_info['strike']} {contract_info['type']}")
                print(f"   Delta: {delta:.3f}")
                return contract
            elif direction == 'bearish' and delta < -self.min_delta:
                print(f"✅ Bearish momentum contract: {contract_info['strike']} {contract_info['type']}")
                print(f"   Delta: {delta:.3f}")
                return contract
        
        print("❌ No suitable momentum contract found")
        return None
    
    def execute_momentum_trade(self, contract_info: Dict, direction: str) -> bool:
        """Execute momentum trade"""
        print(f"🚀 Executing {direction} momentum trade:")
        print(f"   Strike: {contract_info['contract']['strike']}")
        print(f"   Type: {contract_info['contract']['type']}")
        print(f"   Price: ${contract_info['contract']['price']:.2f}")
        print(f"   Delta: {contract_info['contract']['delta']:.3f}")
        
        # Mock trade execution
        self.position = {
            "strike": contract_info['contract']['strike'],
            "type": contract_info['contract']['type'],
            "quantity": 10,
            "entry_price": contract_info['contract']['price'],
            "entry_time": datetime.now(),
            "delta": contract_info['contract']['delta'],
            "direction": direction,
            "target_profit": contract_info['contract']['price'] * 1.5  # 50% profit target
        }
        
        print(f"✅ Momentum position opened: {self.position['quantity']} contracts")
        return True
    
    def monitor_momentum_position(self) -> bool:
        """Monitor momentum position"""
        if not self.position:
            return False
        
        print("📊 Monitoring momentum position...")
        
        # Get current analysis
        analysis = self.api.analyze_options(self.symbol, dte=14)
        
        # Find our contract
        our_contract = None
        for contract in analysis.get('contracts', []):
            if (contract['strike'] == self.position['strike'] and 
                contract['type'] == self.position['type']):
                our_contract = contract
                break
        
        if not our_contract:
            return False
        
        current_price = our_contract['price']
        pnl = (current_price - self.position['entry_price']) * self.position['quantity'] * 100
        
        print(f"   Current option price: ${current_price:.2f}")
        print(f"   P&L: ${pnl:.2f}")
        print(f"   Delta: {our_contract['delta']:.3f}")
        
        # Exit conditions
        if current_price >= self.position['target_profit']:
            print("✅ Profit target reached!")
            return self.close_momentum_position()
        elif pnl < -200:  # Stop loss
            print("❌ Stop loss triggered!")
            return self.close_momentum_position()
        elif abs(our_contract['delta']) < 0.2:  # Delta too low
            print("⚠️ Delta decay - momentum lost")
            return self.close_momentum_position()
        
        return True
    
    def close_momentum_position(self) -> bool:
        """Close momentum position"""
        if not self.position:
            return False
        
        print(f"🔄 Closing momentum position: {self.position['quantity']} contracts")
        self.position = None
        print("✅ Position closed")
        return True
    
    def run_strategy(self, iterations: int = 8):
        """Run the momentum trading strategy"""
        print("🚀 Starting Momentum Trading Bot")
        print("=" * 50)
        
        for i in range(iterations):
            print(f"\n--- Iteration {i+1}/{iterations} ---")
            
            # Monitor existing position or look for new momentum
            if self.position:
                if not self.monitor_momentum_position():
                    continue
            else:
                # Detect momentum
                direction = self.detect_momentum()
                if direction and direction != 'neutral':
                    contract = self.find_momentum_contract(direction)
                    if contract:
                        self.execute_momentum_trade(contract, direction)
            
            print("⏳ Waiting 45 seconds...")
            time.sleep(45)
        
        # Close any remaining position
        if self.position:
            self.close_momentum_position()
        
        print("\n🏁 Momentum Trading Bot completed")

# ============================================================================
# MAIN EXECUTION EXAMPLES
# ============================================================================

def main():
    """Run trading bot examples"""
    print("🤖 Options Trading Bot Examples")
    print("=" * 60)
    
    # Initialize API client
    api_client = OptionsAnalysisClient()
    
    # Check API health
    health = api_client.health_check()
    print(f"📡 API Status: {health.get('status', 'unknown')}")
    
    if health.get('status') != 'healthy':
        print("❌ API not healthy - cannot run examples")
        return
    
    print("\n" + "=" * 60)
    
    # Example 1: Quick API usage
    print("📊 Quick API Usage Example:")
    price_data = api_client.get_market_price("SPY")
    iv_data = api_client.get_market_iv("SPY")
    print(f"   SPY Price: ${price_data.get('price', 0):.2f}")
    print(f"   SPY IV: {iv_data.get('iv', 0):.1f}%")
    
    # Example 2: Get best gamma scalp contracts
    print("\n🎯 Best Gamma Scalp Contracts:")
    gamma_contracts = api_client.get_best_contracts("SPY", "gamma_scalp", max_contracts=3)
    for i, contract in enumerate(gamma_contracts.get('ranked_contracts', [])[:3], 1):
        info = contract['contract']
        print(f"   {i}. {info['strike']} {info['type']} - Gamma: {info['gamma']:.4f}, Score: {contract['score']:.1f}")
    
    print("\n" + "=" * 60)
    
    # Run bot examples (uncomment to run)
    choice = input("Run bot examples? (y/n): ").lower()
    if choice == 'y':
        print("\n🤖 Running Trading Bot Examples...")
        
        # Gamma Scalping Bot
        print("\n" + "=" * 40)
        gamma_bot = GammaScalpingBot(api_client)
        gamma_bot.run_strategy(iterations=3)
        
        # Theta Decay Bot
        print("\n" + "=" * 40)
        theta_bot = ThetaDecayBot(api_client)
        theta_bot.run_strategy(iterations=3)
        
        # Momentum Trading Bot
        print("\n" + "=" * 40)
        momentum_bot = MomentumTradingBot(api_client)
        momentum_bot.run_strategy(iterations=3)
    
    print("\n✅ All examples completed!")

if __name__ == "__main__":
    main()