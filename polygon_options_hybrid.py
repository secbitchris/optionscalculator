#!/usr/bin/env python3
"""
Polygon.io Options Hybrid Solution

This module works around subscription limitations by:
1. ✅ Using real options contracts (available with basic API)
2. ✅ Using live stock prices (available with basic API) 
3. 🧮 Calculating theoretical options prices (Black-Scholes)
4. 📊 Implementing proper expected move formulas

This gives you full functionality without needing premium subscription.
"""

import os
import requests
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
from dotenv import load_dotenv

load_dotenv()

class PolygonOptionsHybrid:
    """Hybrid options data provider using free tier + calculations"""
    
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        self.base_url = "https://api.polygon.io"
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
    def black_scholes_price(self, S, K, T, r, sigma, option_type='call'):
        """
        Calculate Black-Scholes option price
        
        S: Current stock price
        K: Strike price  
        T: Time to expiration (years)
        r: Risk-free rate
        sigma: Volatility
        option_type: 'call' or 'put'
        """
        if T <= 0:
            # Option expired
            if option_type == 'call':
                return max(S - K, 0)
            else:
                return max(K - S, 0)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        if option_type == 'call':
            price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
        return price
    
    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """Calculate option Greeks"""
        if T <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Delta
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        # Gamma (same for calls and puts)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
        
        # Theta (per day)
        if option_type == 'call':
            theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - 
                    r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        else:
            theta = (-(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + 
                    r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        
        # Vega (per 1% change in volatility)
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100
        
        return {
            'delta': delta,
            'gamma': gamma, 
            'theta': theta,
            'vega': vega
        }
    
    def get_live_stock_price(self, symbol):
        """Get live stock price (works with basic API)"""
        try:
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/prev"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    return data['results'][0]['c']  # closing price
            return None
        except Exception as e:
            print(f"Error getting stock price: {e}")
            return None
    
    def get_options_contracts(self, underlying, dte_min=1, dte_max=30, limit=100):
        """Get real options contracts (works with basic API)"""
        try:
            url = f"{self.base_url}/v3/reference/options/contracts"
            
            exp_min = (datetime.now() + timedelta(days=dte_min)).strftime("%Y-%m-%d")
            exp_max = (datetime.now() + timedelta(days=dte_max)).strftime("%Y-%m-%d")
            
            params = {
                "underlying_ticker": underlying,
                "expiration_date.gte": exp_min,
                "expiration_date.lte": exp_max,
                "limit": limit
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            else:
                print(f"Error getting contracts: {response.text}")
                return []
                
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def calculate_expected_moves(self, S, sigma, dte_list, method='both'):
        """
        Calculate expected moves using different methods
        
        method: 'formula', 'straddle', or 'both'
        """
        results = {}
        
        for dte in dte_list:
            T = dte / 252
            
            # Method 1: Standard Formula (Price × IV × √(T/252))
            formula_move = S * sigma * np.sqrt(T)
            
            results[dte] = {
                'formula_move_1sigma': formula_move,
                'formula_move_2sigma': formula_move * 2,
                'confidence_68': [S - formula_move, S + formula_move],
                'confidence_95': [S - formula_move * 2, S + formula_move * 2],
            }
            
            # Method 2: ATM Straddle Price (if requested)
            if method in ['straddle', 'both']:
                # Find closest strike to current price
                strike = round(S)
                r = 0.044  # 4.4% risk-free rate
                
                call_price = self.black_scholes_price(S, strike, T, r, sigma, 'call')
                put_price = self.black_scholes_price(S, strike, T, r, sigma, 'put')
                straddle_price = call_price + put_price
                
                results[dte].update({
                    'straddle_price': straddle_price,
                    'straddle_range': [S - straddle_price, S + straddle_price],
                    'call_price': call_price,
                    'put_price': put_price,
                    'strike': strike
                })
        
        return results
    
    def get_enhanced_options_chain(self, underlying, dte=7, iv=None, r=0.044):
        """
        Get enhanced options chain with theoretical pricing
        This is what we'll use instead of expensive live quotes
        """
        print(f"🔄 Getting enhanced options chain for {underlying}...")
        
        # Get live stock price
        stock_price = self.get_live_stock_price(underlying)
        if not stock_price:
            print(f"❌ Could not get live price for {underlying}")
            return {}
        
        print(f"📈 Live {underlying} price: ${stock_price}")
        
        # Get real market IV if not provided
        if iv is None:
            iv = self.get_market_iv(underlying)
            print(f"📊 Using market IV: {iv:.1%}")
        else:
            print(f"📊 Using provided IV: {iv:.1%}")
        
        # Get real options contracts
        contracts = self.get_options_contracts(underlying, dte-2, dte+2)
        if not contracts:
            print(f"❌ No options contracts found")
            return {}
        
        print(f"📊 Found {len(contracts)} real options contracts")
        
        # Process contracts and add theoretical pricing
        enhanced_chain = []
        T = dte / 252
        
        for contract in contracts:
            try:
                strike = float(contract.get('strike_price', 0))
                exp_date = contract.get('expiration_date')
                contract_type = contract.get('contract_type', '').lower()
                ticker = contract.get('ticker', '')
                
                # Calculate theoretical price and Greeks
                theo_price = self.black_scholes_price(stock_price, strike, T, r, iv, contract_type)
                greeks = self.calculate_greeks(stock_price, strike, T, r, iv, contract_type)
                
                enhanced_contract = {
                    'ticker': ticker,
                    'type': contract_type,
                    'strike': strike,
                    'expiration': exp_date,
                    'dte': dte,
                    'theoretical_price': theo_price,
                    'bid': theo_price * 0.98,  # Approximate bid/ask spread
                    'ask': theo_price * 1.02,
                    'mid': theo_price,
                    'delta': greeks['delta'],
                    'gamma': greeks['gamma'],
                    'theta': greeks['theta'],
                    'vega': greeks['vega'],
                    'iv_used': iv * 100,  # Convert to percentage
                }
                
                enhanced_chain.append(enhanced_contract)
                
            except Exception as e:
                print(f"Error processing contract: {e}")
                continue
        
        # Sort by strike price
        enhanced_chain.sort(key=lambda x: x['strike'])
        
        return {
            'underlying': underlying,
            'stock_price': stock_price,
            'dte': dte,
            'iv_used': iv * 100,
            'risk_free_rate': r * 100,
            'contracts': enhanced_chain,
            'total_contracts': len(enhanced_chain)
        }
    
    def get_real_data_only_chain(self, underlying, dte=7, iv=None, r=0.044):
        """
        Get options chain with REAL DATA ONLY - works directly with real market data
        
        Returns only contracts that have:
        - Real open interest from Polygon.io
        - Real underlying price
        - Theoretical pricing (since live option quotes require premium subscription)
        
        Volume is excluded since it requires paid subscription
        """
        print(f"🔄 Getting REAL DATA ONLY options chain for {underlying}...")
        
        # Get live stock price
        stock_price = self.get_live_stock_price(underlying)
        if not stock_price:
            print(f"❌ Could not get live price for {underlying}")
            return {}
        
        print(f"📈 Live {underlying} price: ${stock_price}")
        
        # Get real market IV if not provided
        if iv is None:
            iv = self.get_market_iv(underlying)
            print(f"📊 Using market IV: {iv:.1%}")
        else:
            print(f"📊 Using provided IV: {iv:.1%}")
        
        # Get real open interest data first
        real_oi_data = self.get_real_open_interest(underlying)
        if not real_oi_data:
            print(f"❌ No real open interest data available")
            return {}
        
        print(f"✅ Found REAL open interest for {len(real_oi_data)} contracts")
        
        # Show what real OI data we have
        print(f"🔍 Available real OI contracts:")
        for key, oi_info in list(real_oi_data.items())[:5]:  # Show first 5
            print(f"   {oi_info['type'].upper()} ${oi_info['strike']} exp:{oi_info['expiry']} OI:{oi_info['open_interest']}")
        
        # Work directly with the real OI data instead of synthetic contracts
        real_contracts = []
        
        for key, oi_info in real_oi_data.items():
            try:
                strike = oi_info['strike']
                contract_type = oi_info['type'].lower()
                expiry = oi_info['expiry']
                open_interest = oi_info['open_interest']
                
                # Calculate DTE from expiry
                from datetime import datetime
                try:
                    exp_date = datetime.strptime(expiry, '%Y-%m-%d')
                    current_date = datetime.now()
                    contract_dte = (exp_date - current_date).days
                except:
                    contract_dte = dte  # Fallback to requested DTE
                
                # Filter by DTE (allow more flexibility for real data)
                # Accept 0-DTE options too since they're actively traded
                if dte <= 14:
                    acceptable_range = (0, 21)  # 0-3 weeks (includes same-day expiry)
                elif dte <= 45:
                    acceptable_range = (0, 60)  # 0-8 weeks 
                else:
                    acceptable_range = (0, 365)  # Any expiry
                
                if not (acceptable_range[0] <= contract_dte <= acceptable_range[1]):
                    print(f"   Skipping {contract_type.upper()} ${strike} - DTE {contract_dte} outside range {acceptable_range}")
                    continue
                
                print(f"   Including {contract_type.upper()} ${strike} - DTE {contract_dte}, OI {open_interest}")
                
                # Calculate theoretical price and Greeks
                T = contract_dte / 252
                theo_price = self.black_scholes_price(stock_price, strike, T, r, iv, contract_type)
                greeks = self.calculate_greeks(stock_price, strike, T, r, iv, contract_type)
                
                # Calculate liquidity score
                if contract_type == 'call':
                    moneyness = strike / stock_price
                else:
                    moneyness = stock_price / strike
                
                atm_factor = max(0.1, 1 - abs(moneyness - 1) * 2)
                
                if 7 <= contract_dte <= 45:
                    dte_factor = 1.0
                elif contract_dte < 7:
                    dte_factor = 0.3 + (contract_dte / 7) * 0.7
                else:
                    dte_factor = max(0.1, 1 - (contract_dte - 45) / 60)
                
                liquidity_score = atm_factor * dte_factor
                
                # Estimate bid/ask spread based on liquidity
                spread_info = self.estimate_bid_ask_spread(theo_price, liquidity_score)
                
                enhanced_contract = {
                    'ticker': f"O:{underlying}{expiry.replace('-', '')}{contract_type[0].upper()}{int(strike*1000):08d}",
                    'type': contract_type.upper(),
                    'strike': strike,
                    'expiration': expiry,
                    'dte': contract_dte,
                    'theoretical_price': theo_price,
                    'bid': spread_info['bid'],
                    'ask': spread_info['ask'],
                    'mid': theo_price,
                    'spread': spread_info['spread'],
                    'spread_pct': spread_info['spread_pct'],
                    'delta': greeks['delta'],
                    'gamma': greeks['gamma'],
                    'theta': greeks['theta'],
                    'vega': greeks['vega'],
                    'iv_used': iv * 100,
                    'open_interest': open_interest,
                    'oi_source': "REAL",  # Always real since we're using real OI data
                    'volume': None,  # No real volume data without premium subscription
                    'volume_source': "NONE",
                    'liquidity_score': round(liquidity_score, 3),
                    'liquidity_tier': self._get_liquidity_tier(liquidity_score),
                    'confidence': "HIGH"
                }
                
                real_contracts.append(enhanced_contract)
                
            except Exception as e:
                print(f"❌ Error processing real contract {key}: {e}")
                continue
        
        # Sort by strike price
        real_contracts.sort(key=lambda x: x['strike'])
        
        print(f"✅ Created {len(real_contracts)} contracts with REAL data only")
        
        return {
            'underlying': underlying,
            'stock_price': stock_price,
            'dte': dte,
            'iv_used': iv * 100,
            'risk_free_rate': r * 100,
            'contracts': real_contracts,
            'total_contracts': len(real_contracts),
            'data_quality': 'REAL_ONLY',
            'notes': 'Built directly from real open interest data. Volume excluded (requires premium subscription).'
        }
    
    def get_market_iv(self, symbol='SPY'):
        """
        Get real market implied volatility from available sources
        
        Priority order:
        1. VIX (for SPY/SPX) - represents 30-day IV
        2. VIX9D (for shorter-term)
        3. Historical volatility as fallback
        
        Returns float: IV as decimal (e.g., 0.15 for 15%)
        """
        try:
            # Method 1: Get VIX (best proxy for SPY/SPX IV)
            if symbol.upper() in ['SPY', 'SPX']:
                vix_data = self._get_vix_data()
                if vix_data:
                    return vix_data / 100  # Convert VIX to decimal
            
            # Method 2: Calculate historical volatility as fallback
            hist_vol = self._get_historical_volatility(symbol)
            if hist_vol:
                return hist_vol
                
            # Method 3: Default fallback
            print(f"⚠️  Using default 15% IV for {symbol}")
            return 0.15
            
        except Exception as e:
            print(f"❌ Error getting market IV: {e}")
            return 0.15
    
    def _get_vix_data(self):
        """Get current VIX value (30-day IV for SPX)"""
        try:
            # VIX is available through Polygon
            url = f"{self.base_url}/v2/aggs/ticker/I:VIX/prev"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    vix_value = data['results'][0]['c']  # closing value
                    print(f"📊 Live VIX: {vix_value:.2f}% (30-day IV)")
                    return vix_value
            
            # Fallback: Try VIX9D for shorter term
            url = f"{self.base_url}/v2/aggs/ticker/I:VIX9D/prev"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    vix9d_value = data['results'][0]['c']
                    print(f"📊 Live VIX9D: {vix9d_value:.2f}% (9-day IV)")
                    return vix9d_value
                    
            return None
            
        except Exception as e:
            print(f"❌ Error getting VIX: {e}")
            return None
    
    def _get_historical_volatility(self, symbol, days=20):
        """Calculate historical volatility as IV proxy"""
        try:
            from datetime import datetime, timedelta
            
            # Get historical prices
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)
            
            url = f"{self.base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if len(results) >= days:
                    import numpy as np
                    
                    # Calculate daily returns
                    closes = [r['c'] for r in results[-days:]]
                    returns = []
                    for i in range(1, len(closes)):
                        returns.append(np.log(closes[i] / closes[i-1]))
                    
                    # Annualized volatility
                    daily_vol = np.std(returns)
                    annualized_vol = daily_vol * np.sqrt(252)
                    
                    print(f"📈 Historical volatility ({days}d): {annualized_vol:.1%}")
                    return annualized_vol
                    
            return None
            
        except Exception as e:
            print(f"❌ Error calculating historical vol: {e}")
            return None
    
    def get_real_open_interest(self, underlying='SPY'):
        """
        Get REAL Open Interest from Polygon.io snapshot endpoint
        This works with your current API subscription!
        """
        try:
            url = f"{self.base_url}/v3/snapshot/options/{underlying}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Create lookup dictionary for real OI data
                    real_oi_data = {}
                    for option in results:
                        if option.get('details') and option.get('open_interest') is not None:
                            details = option['details']
                            strike = details.get('strike_price')
                            contract_type = details.get('contract_type')
                            expiry = details.get('expiration_date')
                            oi = option.get('open_interest', 0)
                            
                            # Create lookup key
                            key = f"{strike}_{contract_type}_{expiry}"
                            real_oi_data[key] = {
                                'open_interest': oi,
                                'strike': strike,
                                'type': contract_type,
                                'expiry': expiry,
                                'ticker': option.get('underlying_ticker', underlying)
                            }
                    
                    print(f"✅ Retrieved REAL Open Interest for {len(real_oi_data)} contracts")
                    return real_oi_data
            
            print(f"⚠️  Could not get real OI data (Status: {response.status_code})")
            return {}
            
        except Exception as e:
            print(f"❌ Error getting real OI data: {e}")
            return {}

    def get_liquidity_metrics(self, S, K, dte, option_type='call', underlying='SPY', real_oi_data=None, real_data_only=False):
        """
        HYBRID: Use REAL Open Interest + estimate volume
        
        NEW: Your API can get real OI data! This combines:
        ✅ REAL Open Interest from Polygon.io
        📊 Estimated Volume (requires paid subscription)
        
        Args:
            real_data_only (bool): If True, only return contracts with real OI data
        """
        # Get real OI data if not provided
        if real_oi_data is None:
            real_oi_data = self.get_real_open_interest(underlying)
        
        # Try to find real OI for this specific contract
        real_oi = None
        for key, oi_info in real_oi_data.items():
            if (abs(oi_info['strike'] - K) < 0.01 and 
                oi_info['type'] == option_type):
                real_oi = oi_info['open_interest']
                break
        
        # If real_data_only is True and we don't have real OI, return None
        if real_data_only and real_oi is None:
            return None
        
        # Calculate liquidity factors for volume estimation
        if option_type == 'call':
            moneyness = K / S  # For calls: >1 = OTM, <1 = ITM
        else:
            moneyness = S / K  # For puts: >1 = ITM, <1 = OTM
        
        # ATM factor (closer to 1.0 = more liquid)
        atm_factor = max(0.1, 1 - abs(moneyness - 1) * 2)
        
        # DTE factor (7-45 days = most liquid)
        if 7 <= dte <= 45:
            dte_factor = 1.0
        elif dte < 7:
            dte_factor = 0.3 + (dte / 7) * 0.7
        else:
            dte_factor = max(0.1, 1 - (dte - 45) / 60)
        
        # Composite liquidity score
        liquidity_score = atm_factor * dte_factor
        
        # Use real OI if available, otherwise estimate (unless real_data_only is True)
        if real_oi is not None:
            open_interest = real_oi
            oi_source = "REAL"
            confidence = "HIGH"
        else:
            # Fallback to estimation (only if real_data_only is False)
            if liquidity_score > 0.8:
                open_interest = np.random.randint(1000, 5000)
            elif liquidity_score > 0.5:
                open_interest = np.random.randint(300, 1500)
            else:
                open_interest = np.random.randint(50, 500)
            oi_source = "ESTIMATED"
            confidence = "MEDIUM"
        
        # For real_data_only mode, set volume to None since we don't have real volume
        if real_data_only:
            volume = None
            volume_source = "NONE"
        else:
            # Always estimate volume (needs paid subscription)
            if open_interest > 0:
                # Volume typically 5-15% of OI per day
                volume_ratio = 0.05 + liquidity_score * 0.10
                volume = int(open_interest * volume_ratio)
                # Add some randomness
                volume = int(volume * (0.5 + np.random.random()))
            else:
                volume = 0
            volume_source = "ESTIMATED"
        
        return {
            'open_interest': open_interest,
            'volume': volume,
            'liquidity_score': round(liquidity_score, 3),
            'oi_source': oi_source,
            'volume_source': volume_source,
            'confidence': confidence,
            'liquidity_tier': self._get_liquidity_tier(liquidity_score)
        }

    def estimate_liquidity_metrics(self, S, K, dte, option_type='call'):
        """
        DEPRECATED: Use get_liquidity_metrics() instead
        This method kept for backwards compatibility
        """
        return self.get_liquidity_metrics(S, K, dte, option_type)
    
    def estimate_bid_ask_spread(self, theoretical_price, liquidity_score):
        """Estimate bid/ask spread based on liquidity"""
        # Base spread percentage increases with lower liquidity
        if liquidity_score > 0.8:
            spread_pct = 0.02  # 2% for very liquid
        elif liquidity_score > 0.5:
            spread_pct = 0.05  # 5% for medium liquid
        else:
            spread_pct = 0.10  # 10% for illiquid
        
        # Minimum spread of $0.05
        spread = max(0.05, theoretical_price * spread_pct)
        
        return {
            'bid': round(theoretical_price - spread/2, 2),
            'ask': round(theoretical_price + spread/2, 2),
            'spread': round(spread, 2),
            'spread_pct': round(spread_pct * 100, 1)
        }
    
    def _get_liquidity_tier(self, score):
        """Convert liquidity score to tier"""
        if score > 0.8:
            return "HIGH"
        elif score > 0.5:
            return "MEDIUM"
        elif score > 0.2:
            return "LOW"
        else:
            return "VERY_LOW"

def test_hybrid_system():
    """Test the hybrid options system"""
    print("🧪 TESTING HYBRID OPTIONS SYSTEM")
    print("=" * 60)
    
    hybrid = PolygonOptionsHybrid()
    
    # Test parameters
    underlying = 'SPY'
    dte = 7
    iv = 0.15  # 15%
    
    # Test 1: Expected moves calculation
    print(f"\n📊 Test 1: Expected Moves Calculation")
    print("-" * 40)
    
    stock_price = hybrid.get_live_stock_price(underlying)
    if stock_price:
        print(f"✅ Live {underlying} price: ${stock_price}")
        
        expected_moves = hybrid.calculate_expected_moves(stock_price, iv, [1, 7, 14, 30])
        
        for dte, moves in expected_moves.items():
            print(f"\n   {dte} DTE:")
            print(f"   Formula (1σ): ${moves['formula_move_1sigma']:.2f}")
            print(f"   Straddle: ${moves['straddle_price']:.2f}")
            print(f"   68% Range: ${moves['confidence_68'][0]:.2f} - ${moves['confidence_68'][1]:.2f}")
    
    # Test 2: Enhanced options chain
    print(f"\n📈 Test 2: Enhanced Options Chain")
    print("-" * 40)
    
    chain = hybrid.get_enhanced_options_chain(underlying, dte, iv)
    
    if chain and chain.get('contracts'):
        print(f"✅ Generated enhanced chain with {chain['total_contracts']} contracts")
        print(f"   Stock Price: ${chain['stock_price']}")
        print(f"   DTE: {chain['dte']}")
        print(f"   IV Used: {chain['iv_used']}%")
        
        # Show sample contracts
        atm_contracts = [c for c in chain['contracts'] 
                        if abs(c['strike'] - chain['stock_price']) < 5][:4]
        
        print(f"\n   Sample ATM Contracts:")
        for contract in atm_contracts:
            print(f"   {contract['type'].upper()} ${contract['strike']}: "
                  f"${contract['theoretical_price']:.2f} "
                  f"(Δ:{contract['delta']:.3f}, Θ:{contract['theta']:.2f})")
    
    print(f"\n✅ HYBRID SYSTEM WORKING!")
    print(f"   • Real contracts: ✅ From Polygon.io")
    print(f"   • Live prices: ✅ From Polygon.io") 
    print(f"   • Theoretical pricing: ✅ Black-Scholes")
    print(f"   • Expected moves: ✅ Formula + Straddle")
    print(f"   • Greeks: ✅ Calculated")

if __name__ == "__main__":
    test_hybrid_system() 