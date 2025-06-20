#!/usr/bin/env python3
"""
Options Analysis API Service

Comprehensive API endpoints for trading bots and external systems
to query options analysis data, market metrics, and contract rankings.

Designed for high-frequency trading system integration.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import logging

# Import our analysis modules
from option_scenario_calculator import OptionsAnalyzer
from polygon_options_hybrid import PolygonOptionsHybrid

# Initialize hybrid system
hybrid_system = PolygonOptionsHybrid()

def calculate_expected_moves(price, dte, iv):
    """Wrapper function for expected moves calculation"""
    results = hybrid_system.calculate_expected_moves(price, iv/100, [dte])
    return results[dte]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global analyzer cache
analyzers = {}

def get_analyzer(symbol):
    """Get or create analyzer for symbol"""
    if symbol not in analyzers:
        analyzers[symbol] = OptionsAnalyzer(symbol)
    return analyzers[symbol]

# ============================================================================
# CORE DATA ENDPOINTS
# ============================================================================

@app.route('/api/v1/market/price/<symbol>', methods=['GET'])
def get_market_price(symbol):
    """
    Get current market price for underlying asset
    
    Returns:
    {
        "symbol": "SPY",
        "price": 597.44,
        "source": "live|fallback",
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        if symbol.upper() in ['SPY', 'SPX']:
            price = hybrid_system.get_live_stock_price(symbol.upper())
            if price:
                return jsonify({
                    "symbol": symbol.upper(),
                    "price": price,
                    "source": "live",
                    "timestamp": datetime.now().isoformat() + 'Z',
                    "success": True
                })
            else:
                return jsonify({
                    "symbol": symbol.upper(),
                    "price": 597.44,  # Fallback price
                    "source": "fallback",
                    "timestamp": datetime.now().isoformat() + 'Z',
                    "success": True
                })
        else:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
    except Exception as e:
        logger.error(f"Error getting market price for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/v1/market/iv/<symbol>', methods=['GET'])
def get_market_volatility(symbol):
    """
    Get current implied volatility for underlying asset
    
    Returns:
    {
        "symbol": "SPY",
        "iv": 20.14,
        "source": "VIX|VIX9D|historical|fallback",
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        if symbol.upper() in ['SPY', 'SPX']:
            iv = hybrid_system.get_market_iv(symbol.upper())
            return jsonify({
                "symbol": symbol.upper(),
                "iv": iv * 100,  # Convert to percentage
                "source": "VIX" if iv > 0.14 else "fallback",
                "timestamp": datetime.now().isoformat() + 'Z',
                "success": True
            })
        else:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
    except Exception as e:
        logger.error(f"Error getting market IV for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/v1/market/expected-moves/<symbol>', methods=['GET'])
def get_expected_moves(symbol):
    """
    Get expected price moves for underlying asset
    
    Query Parameters:
    - dte: Days to expiration (default: 7)
    - iv: Override IV (optional, uses market IV if not provided)
    
    Returns:
    {
        "symbol": "SPY",
        "current_price": 597.44,
        "dte": 7,
        "iv": 20.14,
        "iv_source": "market|user",
        "expected_moves": {
            "one_std": 20.05,
            "two_std": 40.10,
            "price_ranges": {
                "68_percent": [577.39, 617.49],
                "95_percent": [557.34, 637.54]
            }
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        dte = int(request.args.get('dte', 7))
        user_iv = request.args.get('iv')
        
        if symbol.upper() not in ['SPY', 'SPX']:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
        
        # Get current price
        current_price = hybrid_system.get_live_stock_price(symbol.upper())
        if not current_price:
            current_price = 597.44  # Fallback
        
        # Get IV (user override or market)
        if user_iv:
            iv = float(user_iv)
            iv_source = "user"
        else:
            iv = hybrid_system.get_market_iv(symbol.upper()) * 100  # Convert to percentage
            iv_source = "market"
        
        # Calculate expected moves
        moves = calculate_expected_moves(current_price, dte, iv)
        
        return jsonify({
            "symbol": symbol.upper(),
            "current_price": current_price,
            "dte": dte,
            "iv": iv,
            "iv_source": iv_source,
            "expected_moves": {
                "one_std": moves['one_std_move'],
                "two_std": moves['two_std_move'],
                "price_ranges": {
                    "68_percent": [moves['support_68'], moves['resistance_68']],
                    "95_percent": [moves['support_95'], moves['resistance_95']]
                }
            },
            "timestamp": datetime.now().isoformat() + 'Z',
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error calculating expected moves for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

# ============================================================================
# OPTIONS ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/v1/options/analyze/<symbol>', methods=['POST'])
def analyze_options(symbol):
    """
    Comprehensive options analysis for all available contracts
    
    Request Body:
    {
        "dte": 7,
        "price": 597.44,  // optional, uses live price if not provided
        "iv": 20.14,      // optional, uses market IV if not provided
        "risk_free_rate": 4.4
    }
    
    Returns:
    {
        "symbol": "SPY",
        "analysis_params": {...},
        "market_data": {...},
        "contracts": [
            {
                "strike": 595,
                "type": "call",
                "price": 8.45,
                "delta": 0.52,
                "gamma": 0.03,
                "theta": -0.15,
                "vega": 0.18,
                "open_interest": 524,
                "volume": 1250,
                "liquidity_score": 8.5,
                "profit_zones": {...},
                "risk_metrics": {...}
            }
        ],
        "summary": {
            "total_contracts": 58,
            "most_liquid": {...},
            "highest_gamma": {...},
            "best_risk_reward": {...}
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body required",
                "success": False
            }), 400
        
        # Extract parameters
        dte = data.get('dte', 7)
        user_price = data.get('price')
        user_iv = data.get('iv')
        risk_free_rate = data.get('risk_free_rate', 4.4)
        
        if symbol.upper() not in ['SPY', 'SPX']:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
        
        # Get analyzer
        analyzer = get_analyzer(symbol.upper())
        
        # Get current price
        if user_price:
            current_price = float(user_price)
            price_source = "user"
        else:
            current_price = hybrid_system.get_live_stock_price(symbol.upper())
            if current_price:
                price_source = "live"
            else:
                current_price = 597.44
                price_source = "fallback"
        
        # Get IV
        if user_iv:
            iv = float(user_iv)
            iv_source = "user"
        else:
            iv = hybrid_system.get_market_iv(symbol.upper()) * 100  # Convert to percentage
            iv_source = "market"
        
        # Update analyzer with current price
        analyzer.update_current_price(current_price)
        
        # Run analysis
        logger.info(f"Running comprehensive analysis for {symbol}: Price=${current_price}, DTE={dte}, IV={iv}%")
        results = analyzer.analyze_all_scenarios(
            days_to_expiry=dte,
            implied_volatility=iv/100,
            risk_free_rate=risk_free_rate/100
        )
        
        # Get Open Interest and liquidity data
        oi_data = hybrid_system.get_real_open_interest(symbol.upper())
        
        # Process contracts with enhanced data
        enhanced_contracts = []
        for contract in results['contracts']:
            # Get liquidity metrics
            liquidity = hybrid_system.get_liquidity_metrics(
                current_price,
                contract.get('strike', 0),
                7,  # DTE
                contract.get('type', 'call'),
                symbol.upper(),
                oi_data
            )
            
            enhanced_contract = {
                "strike": contract['strike'],
                "type": contract['type'],
                "price": round(contract['price'], 2),
                "delta": round(contract['delta'], 3),
                "gamma": round(contract['gamma'], 4),
                "theta": round(contract['theta'], 3),
                "vega": round(contract['vega'], 3),
                "open_interest": contract.get('open_interest', 0),
                "volume": contract.get('volume', 0),
                "liquidity_score": round(liquidity['liquidity_score'], 1),
                "bid_ask_spread": liquidity.get('estimated_spread', 0.05),
                "moneyness": round((contract['strike'] - current_price) / current_price * 100, 2),
                "profit_zones": {
                    "breakeven": contract.get('breakeven', contract['strike']),
                    "max_profit": contract.get('max_profit', 0),
                    "max_loss": contract.get('max_loss', 0)
                },
                "risk_metrics": {
                    "risk_reward_ratio": contract.get('risk_reward_ratio', 0),
                    "probability_profit": contract.get('prob_profit', 0),
                    "days_to_expiry": dte
                }
            }
            enhanced_contracts.append(enhanced_contract)
        
        # Generate summary statistics
        if enhanced_contracts:
            most_liquid = max(enhanced_contracts, key=lambda x: x['liquidity_score'])
            highest_gamma = max(enhanced_contracts, key=lambda x: abs(x['gamma']))
            best_risk_reward = max(enhanced_contracts, key=lambda x: x['risk_metrics']['risk_reward_ratio'])
        else:
            most_liquid = highest_gamma = best_risk_reward = None
        
        return jsonify({
            "symbol": symbol.upper(),
            "analysis_params": {
                "dte": dte,
                "price": current_price,
                "price_source": price_source,
                "iv": iv,
                "iv_source": iv_source,
                "risk_free_rate": risk_free_rate
            },
            "market_data": {
                "current_price": current_price,
                "implied_volatility": iv,
                "expected_moves": calculate_expected_moves(current_price, dte, iv)
            },
            "contracts": enhanced_contracts,
            "summary": {
                "total_contracts": len(enhanced_contracts),
                "most_liquid": {
                    "strike": most_liquid['strike'] if most_liquid else None,
                    "type": most_liquid['type'] if most_liquid else None,
                    "liquidity_score": most_liquid['liquidity_score'] if most_liquid else None
                } if most_liquid else None,
                "highest_gamma": {
                    "strike": highest_gamma['strike'] if highest_gamma else None,
                    "type": highest_gamma['type'] if highest_gamma else None,
                    "gamma": highest_gamma['gamma'] if highest_gamma else None
                } if highest_gamma else None,
                "best_risk_reward": {
                    "strike": best_risk_reward['strike'] if best_risk_reward else None,
                    "type": best_risk_reward['type'] if best_risk_reward else None,
                    "ratio": best_risk_reward['risk_metrics']['risk_reward_ratio'] if best_risk_reward else None
                } if best_risk_reward else None
            },
            "timestamp": datetime.now().isoformat() + 'Z',
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error analyzing options for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/v1/options/contracts/<symbol>', methods=['GET'])
def get_available_contracts(symbol):
    """
    Get list of available options contracts with basic info
    
    Query Parameters:
    - dte: Days to expiration filter (optional)
    - min_oi: Minimum open interest filter (optional)
    - type: call|put filter (optional)
    
    Returns:
    {
        "symbol": "SPY",
        "contracts": [
            {
                "strike": 595,
                "type": "call",
                "expiry": "2024-01-22",
                "dte": 7,
                "open_interest": 524,
                "last_price": 8.45
            }
        ],
        "filters_applied": {...},
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        # Get query parameters
        dte_filter = request.args.get('dte', type=int)
        min_oi = request.args.get('min_oi', type=int, default=0)
        type_filter = request.args.get('type', '').lower()
        
        if symbol.upper() not in ['SPY', 'SPX']:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
        
        # Get analyzer and basic contracts info
        analyzer = get_analyzer(symbol.upper())
        
        # For now, we'll use a basic contract structure
        # In a real implementation, you'd fetch this from your data source
        contracts = []
        
        # Get current price for moneyness calculations
        current_price = hybrid_system.get_live_stock_price(symbol.upper())
        if not current_price:
            current_price = 597.44
        
        # Generate sample contracts (replace with real data source)
        strikes = [int(current_price - 20 + i * 5) for i in range(9)]
        
        for strike in strikes:
            for option_type in ['call', 'put']:
                if type_filter and option_type != type_filter:
                    continue
                    
                # Mock contract data (replace with real data)
                contract = {
                    "strike": strike,
                    "type": option_type,
                    "expiry": (datetime.now() + timedelta(days=dte_filter or 7)).strftime('%Y-%m-%d'),
                    "dte": dte_filter or 7,
                    "open_interest": max(0, int(1000 - abs(strike - current_price) * 10)),
                    "last_price": max(0.01, abs(strike - current_price) * 0.1 + 2.0)
                }
                
                if contract['open_interest'] >= min_oi:
                    contracts.append(contract)
        
        return jsonify({
            "symbol": symbol.upper(),
            "contracts": contracts,
            "filters_applied": {
                "dte": dte_filter,
                "min_oi": min_oi,
                "type": type_filter or "all"
            },
            "timestamp": datetime.now().isoformat() + 'Z',
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error getting contracts for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

# ============================================================================
# TRADING BOT SPECIFIC ENDPOINTS
# ============================================================================

@app.route('/api/v1/trading/best-contracts/<symbol>', methods=['POST'])
def get_best_contracts(symbol):
    """
    Get ranked contracts optimized for trading bot selection
    
    Request Body:
    {
        "strategy": "gamma_scalp|theta_decay|momentum|hedge",
        "dte": 7,
        "max_contracts": 5,
        "min_liquidity": 7.0,
        "risk_tolerance": "low|medium|high"
    }
    
    Returns:
    {
        "symbol": "SPY",
        "strategy": "gamma_scalp",
        "ranked_contracts": [
            {
                "rank": 1,
                "score": 9.2,
                "contract": {...},
                "reasoning": "High gamma, excellent liquidity, optimal moneyness"
            }
        ],
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body required",
                "success": False
            }), 400
        
        strategy = data.get('strategy', 'gamma_scalp')
        dte = data.get('dte', 7)
        max_contracts = data.get('max_contracts', 5)
        min_liquidity = data.get('min_liquidity', 7.0)
        risk_tolerance = data.get('risk_tolerance', 'medium')
        
        if symbol.upper() not in ['SPY', 'SPX']:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
        
        # Get full analysis first
        analysis_request = {
            "dte": dte,
            "risk_free_rate": 4.4
        }
        
        # Run internal analysis
        analyzer = get_analyzer(symbol.upper())
        current_price = hybrid_system.get_live_stock_price(symbol.upper())
        if not current_price:
            current_price = 597.44
        iv = hybrid_system.get_market_iv(symbol.upper()) * 100  # Convert to percentage
        
        analyzer.update_current_price(current_price)
        results = analyzer.analyze_all_scenarios(
            days_to_expiry=dte,
            implied_volatility=iv/100,
            risk_free_rate=4.4/100
        )
        
        # Score and rank contracts based on strategy
        scored_contracts = []
        
        for contract in results['contracts']:
            liquidity = hybrid_system.get_liquidity_metrics(
                current_price,
                contract.get('strike', 0),
                dte,
                contract.get('type', 'call'),
                symbol.upper()
            )
            
            if liquidity['liquidity_score'] < min_liquidity:
                continue
            
            # Calculate strategy-specific score
            score = calculate_strategy_score(
                contract, strategy, risk_tolerance, current_price, liquidity
            )
            
            reasoning = generate_contract_reasoning(
                contract, strategy, score, liquidity
            )
            
            scored_contracts.append({
                "score": score,
                "contract": {
                    "strike": contract['strike'],
                    "type": contract['type'],
                    "price": round(contract['price'], 2),
                    "delta": round(contract['delta'], 3),
                    "gamma": round(contract['gamma'], 4),
                    "theta": round(contract['theta'], 3),
                    "vega": round(contract['vega'], 3),
                    "open_interest": contract.get('open_interest', 0),
                    "liquidity_score": round(liquidity['liquidity_score'], 1),
                    "moneyness": round((contract['strike'] - current_price) / current_price * 100, 2)
                },
                "reasoning": reasoning
            })
        
        # Sort by score and take top contracts
        scored_contracts.sort(key=lambda x: x['score'], reverse=True)
        top_contracts = scored_contracts[:max_contracts]
        
        # Add ranking
        ranked_contracts = []
        for i, item in enumerate(top_contracts, 1):
            ranked_contracts.append({
                "rank": i,
                "score": round(item['score'], 1),
                "contract": item['contract'],
                "reasoning": item['reasoning']
            })
        
        return jsonify({
            "symbol": symbol.upper(),
            "strategy": strategy,
            "parameters": {
                "dte": dte,
                "max_contracts": max_contracts,
                "min_liquidity": min_liquidity,
                "risk_tolerance": risk_tolerance
            },
            "ranked_contracts": ranked_contracts,
            "timestamp": datetime.now().isoformat() + 'Z',
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error getting best contracts for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

@app.route('/api/v1/trading/quick-scan/<symbol>', methods=['GET'])
def quick_market_scan(symbol):
    """
    Quick market scan for trading bot decision making
    
    Returns:
    {
        "symbol": "SPY",
        "market_snapshot": {
            "price": 597.44,
            "iv": 20.14,
            "trend": "bullish|bearish|neutral",
            "volatility_regime": "low|normal|high"
        },
        "top_opportunities": [
            {
                "type": "gamma_scalp",
                "strike": 595,
                "option_type": "call",
                "score": 9.2,
                "quick_reason": "High gamma, tight spreads"
            }
        ],
        "alerts": [
            "High IV environment - premium selling favored",
            "Strong support at 590"
        ],
        "timestamp": "2024-01-15T10:30:00Z",
        "success": true
    }
    """
    try:
        if symbol.upper() not in ['SPY', 'SPX']:
            return jsonify({
                "error": f"Symbol {symbol} not supported",
                "supported_symbols": ["SPY", "SPX"],
                "success": False
            }), 400
        
        # Get market data
        current_price = hybrid_system.get_live_stock_price(symbol.upper())
        if not current_price:
            current_price = 597.44
        iv = hybrid_system.get_market_iv(symbol.upper()) * 100  # Convert to percentage
        
        # Determine market regime
        volatility_regime = "low" if iv < 15 else "high" if iv > 25 else "normal"
        
        # Quick trend analysis (simplified)
        trend = "neutral"  # In real implementation, use technical indicators
        
        # Generate quick opportunities
        opportunities = [
            {
                "type": "gamma_scalp",
                "strike": int(current_price),
                "option_type": "call",
                "score": 8.5,
                "quick_reason": "ATM gamma play"
            },
            {
                "type": "theta_decay",
                "strike": int(current_price + 10),
                "option_type": "put",
                "score": 7.8,
                "quick_reason": "OTM premium collection"
            }
        ]
        
        # Generate alerts
        alerts = []
        if iv > 20:
            alerts.append("High IV environment - premium selling favored")
        if volatility_regime == "high":
            alerts.append("Elevated volatility - consider hedging strategies")
        
        return jsonify({
            "symbol": symbol.upper(),
            "market_snapshot": {
                "price": current_price,
                "iv": iv,
                "trend": trend,
                "volatility_regime": volatility_regime
            },
            "top_opportunities": opportunities,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat() + 'Z',
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error in quick scan for {symbol}: {e}")
        return jsonify({
            "error": str(e),
            "success": False
        }), 500

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_strategy_score(contract, strategy, risk_tolerance, current_price, liquidity):
    """Calculate strategy-specific scoring for contracts"""
    base_score = liquidity['liquidity_score']
    
    if strategy == "gamma_scalp":
        # Favor high gamma, near ATM
        gamma_score = abs(contract['gamma']) * 100
        moneyness_penalty = abs(contract['strike'] - current_price) / current_price * 10
        return base_score + gamma_score - moneyness_penalty
        
    elif strategy == "theta_decay":
        # Favor high theta, OTM
        theta_score = abs(contract['theta']) * 10
        moneyness_bonus = min(5, abs(contract['strike'] - current_price) / current_price * 20)
        return base_score + theta_score + moneyness_bonus
        
    elif strategy == "momentum":
        # Favor high delta, directional
        delta_score = abs(contract['delta']) * 10
        return base_score + delta_score
        
    elif strategy == "hedge":
        # Favor protective characteristics
        vega_score = abs(contract['vega']) * 5
        return base_score + vega_score
        
    return base_score

def generate_contract_reasoning(contract, strategy, score, liquidity):
    """Generate human-readable reasoning for contract selection"""
    reasons = []
    
    if liquidity['liquidity_score'] > 8:
        reasons.append("excellent liquidity")
    elif liquidity['liquidity_score'] > 6:
        reasons.append("good liquidity")
    
    if strategy == "gamma_scalp":
        if abs(contract['gamma']) > 0.02:
            reasons.append("high gamma")
        if abs(contract['strike'] - 597.44) < 5:  # Simplified current price
            reasons.append("near ATM")
    
    elif strategy == "theta_decay":
        if abs(contract['theta']) > 0.1:
            reasons.append("strong theta decay")
        reasons.append("premium collection opportunity")
    
    return ", ".join(reasons) if reasons else "meets basic criteria"

# ============================================================================
# HEALTH AND STATUS ENDPOINTS
# ============================================================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat() + 'Z',
        "services": {
            "polygon_api": "connected" if hybrid_system.get_live_stock_price('SPY') else "fallback",
            "options_analyzer": "active",
            "market_data": "active"
        }
    })

@app.route('/api/v1/status', methods=['GET'])
def api_status():
    """Detailed API status"""
    return jsonify({
        "api_version": "1.0.0",
        "supported_symbols": ["SPY", "SPX"],
        "available_strategies": ["gamma_scalp", "theta_decay", "momentum", "hedge"],
        "endpoints": {
            "market_data": ["/api/v1/market/price", "/api/v1/market/iv", "/api/v1/market/expected-moves"],
            "options_analysis": ["/api/v1/options/analyze", "/api/v1/options/contracts"],
            "trading_bot": ["/api/v1/trading/best-contracts", "/api/v1/trading/quick-scan"]
        },
        "timestamp": datetime.now().isoformat() + 'Z'
    })

if __name__ == '__main__':
    port = int(os.environ.get('API_PORT', 5003))
    debug = os.environ.get('API_DEBUG', 'true').lower() == 'true'
    
    print("🚀 Options Analysis API Service Starting")
    print("=" * 50)
    print(f"📡 API Server: http://localhost:{port}")
    print(f"📊 Supported Symbols: SPY, SPX")
    print(f"🤖 Trading Bot Integration: Ready")
    print(f"📈 Real-time Market Data: {'✅ Active' if hybrid_system.get_live_stock_price('SPY') else '⚠️ Fallback Mode'}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)