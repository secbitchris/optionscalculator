#!/usr/bin/env python3
"""
IBKR TWS API Trading Bot Integration
===================================

This module integrates the OptionsAnalyzer with Interactive Brokers TWS API for live trading.
Requires: ib_insync, pandas, numpy

Installation:
pip install ib_insync pandas numpy

Setup:
1. Install TWS or IB Gateway
2. Enable API connections in TWS/Gateway
3. Configure API settings (port 7497 for paper, 7496 for live)

"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from ib_insync import *
    IB_AVAILABLE = True
except ImportError:
    print("Warning: ib_insync not installed. Install with: pip install ib_insync")
    IB_AVAILABLE = False

from option_scenario_calculator import OptionsAnalyzer

@dataclass
class OptionPosition:
    """Data class for tracking option positions"""
    symbol: str
    strike: float
    expiry: str
    right: str  # 'C' for call, 'P' for put
    quantity: int
    avg_price: float
    current_price: float
    pnl: float
    day_trade_score: float

class IBKRTradingBot:
    """Live trading bot using IBKR TWS API"""
    
    def __init__(self, underlying: str = 'SPY', paper_trading: bool = True):
        """
        Initialize IBKR trading bot
        
        Args:
            underlying: 'SPY' or 'SPX'
            paper_trading: True for paper trading, False for live
        """
        if not IB_AVAILABLE:
            raise ImportError("ib_insync is required. Install with: pip install ib_insync")
        
        self.ib = IB()
        self.underlying = underlying
        self.paper_trading = paper_trading
        self.analyzer = OptionsAnalyzer(underlying)
        self.positions = []
        self.orders = []
        self.connected = False
        
        # Trading parameters
        self.max_positions = 5
        self.risk_per_trade = 0.02
        self.min_day_trade_score = 0.35
        self.max_premium = 15.0 if underlying == 'SPY' else 150.0
        
    def connect(self, host: str = '127.0.0.1', port: int = None, client_id: int = 1):
        """Connect to TWS/Gateway"""
        if port is None:
            port = 7497 if self.paper_trading else 7496
        
        try:
            self.ib.connect(host, port, clientId=client_id)
            self.connected = True
            print(f"Connected to IBKR {'Paper' if self.paper_trading else 'Live'} at {host}:{port}")
            
            # Set up event handlers
            self.ib.orderStatusEvent += self.on_order_status
            self.ib.positionEvent += self.on_position_update
            
        except Exception as e:
            print(f"Failed to connect to IBKR: {e}")
            self.connected = False
    
    def disconnect(self):
        """Disconnect from TWS/Gateway"""
        if self.connected:
            self.ib.disconnect()
            self.connected = False
            print("Disconnected from IBKR")
    
    def get_current_price(self) -> float:
        """Get current underlying price"""
        try:
            if self.underlying == 'SPY':
                contract = Stock('SPY', 'SMART', 'USD')
            else:  # SPX
                contract = Index('SPX', 'CBOE', 'USD')
            
            self.ib.reqMktData(contract, '', False, False)
            time.sleep(1)  # Wait for data
            
            ticker = self.ib.ticker(contract)
            if ticker and ticker.last:
                return ticker.last
            elif ticker and ticker.close:
                return ticker.close
            else:
                print("Warning: Could not get current price")
                return None
                
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None
    
    def get_implied_volatility(self) -> float:
        """Get implied volatility from market data"""
        try:
            # For simplicity, using VIX as proxy for SPY/SPX IV
            vix_contract = Index('VIX', 'CBOE', 'USD')
            self.ib.reqMktData(vix_contract, '', False, False)
            time.sleep(1)
            
            vix_ticker = self.ib.ticker(vix_contract)
            if vix_ticker and vix_ticker.last:
                return vix_ticker.last / 100  # Convert VIX to decimal
            else:
                return 0.15  # Default fallback
                
        except Exception as e:
            print(f"Error getting IV: {e}")
            return 0.15
    
    def get_account_info(self) -> Dict:
        """Get account information"""
        try:
            account_values = self.ib.accountValues()
            account_info = {}
            
            for av in account_values:
                if av.tag in ['NetLiquidation', 'AvailableFunds', 'BuyingPower']:
                    account_info[av.tag] = float(av.value)
            
            return account_info
            
        except Exception as e:
            print(f"Error getting account info: {e}")
            return {}
    
    def create_option_contract(self, strike: float, expiry: str, right: str) -> Option:
        """Create option contract for IBKR"""
        if self.underlying == 'SPY':
            return Option('SPY', expiry, strike, right, 'SMART')
        else:  # SPX
            return Option('SPX', expiry, strike, right, 'SMART')
    
    def get_option_quotes(self, contracts: List[Option]) -> Dict:
        """Get option quotes from IBKR"""
        quotes = {}
        
        for contract in contracts:
            try:
                self.ib.reqMktData(contract, '', False, False)
                time.sleep(0.5)  # Rate limiting
                
                ticker = self.ib.ticker(contract)
                if ticker:
                    symbol_key = f"{contract.symbol}{contract.strike}{contract.right}"
                    quotes[symbol_key] = {
                        'bid': ticker.bid if ticker.bid else 0,
                        'ask': ticker.ask if ticker.ask else 0,
                        'last': ticker.last if ticker.last else 0,
                        'mid': (ticker.bid + ticker.ask) / 2 if ticker.bid and ticker.ask else 0,
                        'contract': contract
                    }
                    
            except Exception as e:
                print(f"Error getting quote for {contract}: {e}")
                continue
        
        return quotes
    
    def analyze_opportunities(self, dte: int = 7) -> Dict:
        """Analyze current trading opportunities"""
        if not self.connected:
            print("Not connected to IBKR")
            return {}
        
        # Get current market data
        current_price = self.get_current_price()
        if not current_price:
            return {}
        
        iv = self.get_implied_volatility()
        
        # Update analyzer
        self.analyzer.update_config(current_price=current_price)
        
        # Run analysis
        T = dte / 252
        analysis_data = self.analyzer.analyze_options(
            S=current_price,
            T=T,
            r=0.044,
            sigma=iv,
            dte_days=dte,
            output_format='trading_bot'
        )
        
        # Add account sizing
        account_info = self.get_account_info()
        net_liq = account_info.get('NetLiquidation', 25000)  # Default
        
        for signal in analysis_data['trading_signals']:
            max_risk = net_liq * self.risk_per_trade
            signal['max_contracts'] = max(1, int(max_risk / (signal['max_loss'] * 100)))
            signal['total_cost'] = signal['premium'] * signal['max_contracts'] * 100
        
        return analysis_data
    
    def filter_trading_signals(self, signals: List[Dict]) -> List[Dict]:
        """Filter signals based on trading criteria"""
        filtered = []
        
        for signal in signals:
            # Apply filters
            if (signal['day_trade_score'] >= self.min_day_trade_score and 
                signal['premium'] <= self.max_premium and
                abs(signal['delta']) >= 0.3 and
                signal['confidence'] in ['HIGH', 'MEDIUM']):
                
                filtered.append(signal)
        
        # Sort by day trade score
        return sorted(filtered, key=lambda x: x['day_trade_score'], reverse=True)
    
    def place_option_order(self, signal: Dict, quantity: int = 1, order_type: str = 'LMT') -> bool:
        """Place option order"""
        try:
            # Calculate expiry date
            expiry_date = datetime.now() + timedelta(days=7)  # Approximate
            expiry_str = expiry_date.strftime('%Y%m%d')
            
            # Create contract
            right = 'C' if signal['option_type'] == 'CALL' else 'P'
            contract = self.create_option_contract(
                strike=signal['strike'],
                expiry=expiry_str,
                right=right
            )
            
            # Create order
            if order_type == 'LMT':
                order = LimitOrder('BUY', quantity, signal['premium'])
            else:  # Market order
                order = MarketOrder('BUY', quantity)
            
            # Place order
            trade = self.ib.placeOrder(contract, order)
            
            print(f"Placed order: {signal['symbol']} x{quantity} @ ${signal['premium']:.2f}")
            self.orders.append({
                'trade': trade,
                'signal': signal,
                'timestamp': datetime.now()
            })
            
            return True
            
        except Exception as e:
            print(f"Error placing order: {e}")
            return False
    
    def update_positions(self):
        """Update current positions"""
        try:
            positions = self.ib.positions()
            self.positions = []
            
            for pos in positions:
                if pos.contract.secType == 'OPT':
                    # Get current price
                    ticker = self.ib.ticker(pos.contract)
                    current_price = ticker.last if ticker and ticker.last else 0
                    
                    option_pos = OptionPosition(
                        symbol=f"{pos.contract.symbol}{pos.contract.strike}{pos.contract.right}",
                        strike=pos.contract.strike,
                        expiry=pos.contract.lastTradeDateOrContractMonth,
                        right=pos.contract.right,
                        quantity=pos.position,
                        avg_price=pos.avgCost / 100,  # Convert to per-share
                        current_price=current_price,
                        pnl=(current_price - pos.avgCost / 100) * pos.position * 100,
                        day_trade_score=0.0  # Would need to recalculate
                    )
                    
                    self.positions.append(option_pos)
                    
        except Exception as e:
            print(f"Error updating positions: {e}")
    
    def close_position(self, position: OptionPosition, order_type: str = 'LMT') -> bool:
        """Close an option position"""
        try:
            # Create contract
            contract = self.create_option_contract(
                strike=position.strike,
                expiry=position.expiry,
                right=position.right
            )
            
            # Create closing order
            if order_type == 'LMT':
                order = LimitOrder('SELL', abs(position.quantity), position.current_price)
            else:
                order = MarketOrder('SELL', abs(position.quantity))
            
            trade = self.ib.placeOrder(contract, order)
            print(f"Placed closing order for {position.symbol}")
            
            return True
            
        except Exception as e:
            print(f"Error closing position: {e}")
            return False
    
    def run_trading_session(self, max_positions: int = 3, check_interval: int = 300):
        """Run automated trading session"""
        print(f"Starting trading session - Max positions: {max_positions}")
        
        while self.connected:
            try:
                # Update positions
                self.update_positions()
                
                # Check if we can open new positions
                if len(self.positions) < max_positions:
                    # Analyze opportunities
                    opportunities = self.analyze_opportunities()
                    
                    if opportunities and 'trading_signals' in opportunities:
                        signals = self.filter_trading_signals(opportunities['trading_signals'])
                        
                        # Place orders for top signals
                        for signal in signals[:max_positions - len(self.positions)]:
                            quantity = min(signal['max_contracts'], 5)  # Max 5 contracts
                            self.place_option_order(signal, quantity)
                
                # Check for exit conditions on existing positions
                for position in self.positions:
                    # Example exit logic: close if profit > 50% or loss > 25%
                    profit_pct = position.pnl / (position.avg_price * abs(position.quantity) * 100)
                    
                    if profit_pct > 0.5 or profit_pct < -0.25:
                        print(f"Closing position {position.symbol} - P&L: {profit_pct:.1%}")
                        self.close_position(position)
                
                # Wait before next check
                print(f"Waiting {check_interval} seconds for next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("Trading session interrupted by user")
                break
            except Exception as e:
                print(f"Error in trading session: {e}")
                time.sleep(60)  # Wait a minute before retrying
        
        print("Trading session ended")
    
    def on_order_status(self, trade):
        """Handle order status updates"""
        print(f"Order status update: {trade.order.action} {trade.contract.symbol} - {trade.orderStatus.status}")
    
    def on_position_update(self, position):
        """Handle position updates"""
        if position.contract.secType == 'OPT':
            print(f"Position update: {position.contract.symbol} - {position.position} shares")
    
    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary"""
        self.update_positions()
        
        total_pnl = sum(pos.pnl for pos in self.positions)
        total_value = sum(pos.current_price * abs(pos.quantity) * 100 for pos in self.positions)
        
        return {
            'total_positions': len(self.positions),
            'total_pnl': total_pnl,
            'total_value': total_value,
            'positions': [
                {
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_price': pos.avg_price,
                    'current_price': pos.current_price,
                    'pnl': pos.pnl
                } for pos in self.positions
            ]
        }

# Example usage function
def run_ibkr_trading_example():
    """Example of running the IBKR trading bot"""
    print("=== IBKR TRADING BOT EXAMPLE ===")
    print("Make sure TWS/Gateway is running with API enabled")
    
    # Initialize bot
    bot = IBKRTradingBot('SPY', paper_trading=True)
    
    try:
        # Connect to IBKR
        bot.connect()
        
        if not bot.connected:
            print("Failed to connect to IBKR")
            return
        
        # Get account info
        account_info = bot.get_account_info()
        print(f"Account Net Liquidation: ${account_info.get('NetLiquidation', 0):,.2f}")
        
        # Analyze opportunities
        opportunities = bot.analyze_opportunities()
        
        if opportunities and 'trading_signals' in opportunities:
            signals = bot.filter_trading_signals(opportunities['trading_signals'])
            print(f"\nFound {len(signals)} trading opportunities:")
            
            for i, signal in enumerate(signals[:5]):
                print(f"{i+1}. {signal['symbol']}: Score {signal['day_trade_score']:.3f}, "
                      f"Premium ${signal['premium']:.2f}, R/R {signal['small_move_rr']:.2f}")
        
        # Get current portfolio
        portfolio = bot.get_portfolio_summary()
        print(f"\nCurrent Portfolio:")
        print(f"Total Positions: {portfolio['total_positions']}")
        print(f"Total P&L: ${portfolio['total_pnl']:,.2f}")
        
        # Note: Uncomment the line below to run automated trading
        # bot.run_trading_session(max_positions=3, check_interval=300)
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        bot.disconnect()

if __name__ == "__main__":
    run_ibkr_trading_example() 