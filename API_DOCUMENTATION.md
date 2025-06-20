# Options Analysis API Documentation

## Overview

The Options Analysis API provides comprehensive endpoints for trading bots and external systems to query options analysis data, market metrics, and contract rankings. This API is designed for high-frequency trading system integration and provides real-time market data with sophisticated analysis capabilities.

## Base URL
```
http://localhost:5003/api/v1
```

## Authentication
Currently no authentication required (add your preferred auth method for production)

---

## Core Data Endpoints

### 1. Get Market Price
**GET** `/market/price/{symbol}`

Get current market price for underlying asset.

**Parameters:**
- `symbol` (path): Asset symbol (SPY, SPX)

**Response:**
```json
{
  "symbol": "SPY",
  "price": 597.44,
  "source": "live",
  "timestamp": "2024-01-15T10:30:00Z",
  "success": true
}
```

### 2. Get Market Implied Volatility
**GET** `/market/iv/{symbol}`

Get current implied volatility for underlying asset.

**Parameters:**
- `symbol` (path): Asset symbol (SPY, SPX)

**Response:**
```json
{
  "symbol": "SPY",
  "iv": 20.14,
  "source": "VIX",
  "timestamp": "2024-01-15T10:30:00Z",
  "success": true
}
```

### 3. Get Expected Moves
**GET** `/market/expected-moves/{symbol}?dte=7&iv=20.1`

Get expected price moves for underlying asset.

**Parameters:**
- `symbol` (path): Asset symbol (SPY, SPX)
- `dte` (query): Days to expiration (default: 7)
- `iv` (query): Override IV (optional, uses market IV if not provided)

**Response:**
```json
{
  "symbol": "SPY",
  "current_price": 597.44,
  "dte": 7,
  "iv": 20.14,
  "iv_source": "market",
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
```

---

## Options Analysis Endpoints

### 4. Comprehensive Options Analysis
**POST** `/options/analyze/{symbol}`

Comprehensive options analysis for all available contracts.

**Request Body:**
```json
{
  "dte": 7,
  "price": 597.44,
  "iv": 20.14,
  "risk_free_rate": 4.4
}
```

**Response:**
```json
{
  "symbol": "SPY",
  "analysis_params": {
    "dte": 7,
    "price": 597.44,
    "price_source": "live",
    "iv": 20.14,
    "iv_source": "market",
    "risk_free_rate": 4.4
  },
  "market_data": {
    "current_price": 597.44,
    "implied_volatility": 20.14,
    "expected_moves": {
      "one_std_move": 20.05,
      "support_68": 577.39,
      "resistance_68": 617.49
    }
  },
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
      "bid_ask_spread": 0.05,
      "moneyness": -0.41,
      "profit_zones": {
        "breakeven": 603.45,
        "max_profit": 1000,
        "max_loss": 845
      },
      "risk_metrics": {
        "risk_reward_ratio": 1.18,
        "probability_profit": 0.48,
        "days_to_expiry": 7
      }
    }
  ],
  "summary": {
    "total_contracts": 58,
    "most_liquid": {
      "strike": 595,
      "type": "call",
      "liquidity_score": 8.5
    },
    "highest_gamma": {
      "strike": 597,
      "type": "call",
      "gamma": 0.035
    },
    "best_risk_reward": {
      "strike": 600,
      "type": "put",
      "ratio": 2.1
    }
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "success": true
}
```

### 5. Get Available Contracts
**GET** `/options/contracts/{symbol}?dte=7&min_oi=100&type=call`

Get list of available options contracts with basic info.

**Parameters:**
- `symbol` (path): Asset symbol (SPY, SPX)
- `dte` (query): Days to expiration filter (optional)
- `min_oi` (query): Minimum open interest filter (optional)
- `type` (query): call|put filter (optional)

**Response:**
```json
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
  "filters_applied": {
    "dte": 7,
    "min_oi": 100,
    "type": "call"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "success": true
}
```

---

## Trading Bot Specific Endpoints

### 6. Get Best Contracts (Strategy-Optimized)
**POST** `/trading/best-contracts/{symbol}`

Get ranked contracts optimized for specific trading strategies.

**Request Body:**
```json
{
  "strategy": "gamma_scalp",
  "dte": 7,
  "max_contracts": 5,
  "min_liquidity": 7.0,
  "risk_tolerance": "medium"
}
```

**Available Strategies:**
- `gamma_scalp`: High gamma, near ATM contracts
- `theta_decay`: High theta, OTM premium collection
- `momentum`: High delta, directional plays
- `hedge`: Protective characteristics

**Response:**
```json
{
  "symbol": "SPY",
  "strategy": "gamma_scalp",
  "parameters": {
    "dte": 7,
    "max_contracts": 5,
    "min_liquidity": 7.0,
    "risk_tolerance": "medium"
  },
  "ranked_contracts": [
    {
      "rank": 1,
      "score": 9.2,
      "contract": {
        "strike": 597,
        "type": "call",
        "price": 9.15,
        "delta": 0.51,
        "gamma": 0.035,
        "theta": -0.18,
        "vega": 0.19,
        "open_interest": 612,
        "liquidity_score": 9.1,
        "moneyness": -0.07
      },
      "reasoning": "high gamma, excellent liquidity, near ATM"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "success": true
}
```

### 7. Quick Market Scan
**GET** `/trading/quick-scan/{symbol}`

Quick market scan for trading bot decision making.

**Response:**
```json
{
  "symbol": "SPY",
  "market_snapshot": {
    "price": 597.44,
    "iv": 20.14,
    "trend": "neutral",
    "volatility_regime": "normal"
  },
  "top_opportunities": [
    {
      "type": "gamma_scalp",
      "strike": 597,
      "option_type": "call",
      "score": 9.2,
      "quick_reason": "ATM gamma play"
    },
    {
      "type": "theta_decay",
      "strike": 607,
      "option_type": "put",
      "score": 7.8,
      "quick_reason": "OTM premium collection"
    }
  ],
  "alerts": [
    "High IV environment - premium selling favored"
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "success": true
}
```

---

## Health and Status Endpoints

### 8. Health Check
**GET** `/health`

API health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "polygon_api": "connected",
    "options_analyzer": "active",
    "market_data": "active"
  }
}
```

### 9. API Status
**GET** `/status`

Detailed API status and capabilities.

**Response:**
```json
{
  "api_version": "1.0.0",
  "supported_symbols": ["SPY", "SPX"],
  "available_strategies": ["gamma_scalp", "theta_decay", "momentum", "hedge"],
  "endpoints": {
    "market_data": ["/api/v1/market/price", "/api/v1/market/iv", "/api/v1/market/expected-moves"],
    "options_analysis": ["/api/v1/options/analyze", "/api/v1/options/contracts"],
    "trading_bot": ["/api/v1/trading/best-contracts", "/api/v1/trading/quick-scan"]
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": "Error message description",
  "success": false
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (unsupported symbol)
- `500`: Internal Server Error

---

## Rate Limiting

Currently no rate limiting implemented. Add as needed for production.

---

## Data Freshness

- **Stock Prices**: Real-time from Polygon.io API
- **Implied Volatility**: Real-time VIX data (30-day IV)
- **Open Interest**: End of previous trading day
- **Volume**: Estimated based on OI patterns
- **Greeks**: Calculated in real-time using Black-Scholes

---

## Trading Bot Integration Examples

See `trading_bot_examples.py` for complete integration examples including:
- Gamma scalping bot
- Theta decay bot  
- Momentum trading bot
- Portfolio hedging bot 