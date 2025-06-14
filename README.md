# SPY/SPX Options Analysis System

A comprehensive and flexible options analysis tool for SPY and SPX options, with integrated support for Polygon.io backtesting and IBKR TWS API live trading.

## 🎯 **Overview**

This system helps identify optimal options contracts for any trading strategy with customizable movement expectations. It works **100% locally** with optional external integrations:

### 🏠 **Core Local Features:**
- **Professional Web Interface** with Bootstrap 5 UI and real-time data
- **Advanced Black-Scholes pricing** with complete Greeks calculation
- **Enhanced Price Scenarios** with options impact analysis
- **Probability analysis** (profit probability, ITM probability, breakeven)
- **Multi-scenario R/R analysis** for different move expectations
- **Flexible scoring algorithm** for optimal contract selection
- **Custom movement scenarios** for any trading strategy

### 🌐 **Optional External Integrations:**
- **Polygon.io integration** for historical backtesting (requires API key)
- **IBKR TWS API integration** for live trading automation (requires IBKR account)

## 📁 **File Structure**

```
optionscalculator/
├── 📁 data/                           # All output files (ignored by git)
│   ├── .gitkeep                      # Keeps directory structure in git
│   ├── *.csv                         # Analysis CSV files (auto-generated)
│   ├── *.json                        # Analysis JSON files (auto-generated)
│   └── backtest_*.json               # Backtest results (auto-generated)
├── 📁 templates/                      # Web application templates
│   └── index.html                    # Main dashboard HTML
├── 📁 static/                         # Web application assets
│   ├── css/style.css                 # Custom styling
│   └── js/app.js                     # Frontend JavaScript
├── 📄 .gitignore                     # Protects sensitive data
├── 📄 README.md                      # This documentation
├── 📄 FRONTEND_README.md              # Web application documentation
├── 📄 requirements.txt               # Python dependencies
├── 📄 IBKR_MIGRATION_GUIDE.md        # Guide for updating IBKR APIs
├── 🐍 app.py                         # Flask web application
├── 🐍 run_webapp.py                  # Web application launcher
├── 🐍 option_scenario_calculator.py  # Core analysis engine
├── 🐍 standalone_example.py          # Standalone local usage example
├── 🐍 polygon_backtester_integration.py  # Polygon.io backtesting (optional)
├── 🐍 ibkr_trading_bot_integration.py    # IBKR live trading (optional)
└── 🐍 integration_examples.py        # Advanced integration examples
```

## 🚀 **Quick Start**

### 🌐 **Web Application (Recommended)**
```bash
# Start the beautiful web interface
python run_webapp.py

# Open browser to: http://localhost:5001
# Features: Live prices, enhanced analysis, professional UI
```

### 📱 **Command Line Analysis**
```bash
# Basic SPY analysis with all calculations done locally
python option_scenario_calculator.py --current-price 605.0 --dte 7 --iv 0.15

# SPX analysis with custom parameters
python option_scenario_calculator.py --underlying SPX --current-price 6000 --dte 14 --iv 0.20

# Custom movement scenarios (earnings example)
python option_scenario_calculator.py --expected-moves '{"earnings": 50.0, "normal": 15.0}' --current-price 605.0

# Run standalone example with multiple scenarios
python standalone_example.py
```

### Command Line Analysis
```bash
# SPY analysis (uses default price)
python option_scenario_calculator.py

# SPX analysis 
python option_scenario_calculator.py --underlying SPX

# Custom parameters
python option_scenario_calculator.py --underlying SPY --dte 10 --iv 0.20 --current-price 605.50

# Custom movement scenarios
python option_scenario_calculator.py --expected-moves '{"target": 3.0, "conservative": 1.5, "breakout": 5.0}'

# Save results (automatically saved to data/ directory)
python option_scenario_calculator.py --save --output-format json
```

### Output Formats
- `dataframe`: Standard DataFrame output (default)
- `json`: JSON format for data processing
- `trading_bot`: Optimized for live trading integration
- `backtester`: Structured for backtesting frameworks

### 📁 **Data Organization**
All output files are automatically saved to the `data/` directory:
- Analysis results: `data/options_analysis_SPY_YYYYMMDD_HHMMSS.csv`
- JSON summaries: `data/options_analysis_summary_SPY_YYYYMMDD_HHMMSS.json`  
- Backtest data: `data/polygon_backtest_SPY_YYYYMMDD_HHMMSS.json`

The `data/` directory is ignored by git to keep your repository clean while preserving all analysis locally.

## 🔧 **Installation**

### Quick Setup
```bash
# Clone repository
git clone git@github.com:secbitchris/optionscalculator.git
cd optionscalculator

# Install core dependencies
pip install -r requirements.txt
```

### Additional Dependencies (Optional)
```bash
# For Polygon.io backtesting
pip install polygon-api-client

# For IBKR live trading - choose one:
pip install ib_async           # Modern async wrapper (recommended)
pip install ibapi             # Official IBKR Python API
# OR download from: https://interactivebrokers.github.io/
```

### Standalone Local Installation (Recommended)
```bash
# Core requirements only - works completely offline
pip install numpy pandas scipy
```

**That's it!** The calculator works 100% locally with just these packages. No external APIs, internet connection, or additional setup required.

## 💻 **Standalone Local Operation**

The calculator is designed to work **completely offline** with no external dependencies beyond basic Python packages:

### ✅ **What Works Locally:**
- **Complete Black-Scholes analysis** with all Greeks
- **Multi-scenario R/R calculations** for any custom movements
- **Probability analysis** (profit probability, ITM probability, breakeven)
- **Flexible scoring** for strategy optimization
- **All output formats** (CSV, JSON, trading signals, backtester)

### 📝 **You Only Need to Provide:**
- **Current underlying price** (from any source: broker, Yahoo Finance, etc.)
- **Days to expiration**
- **Implied volatility** (estimate from VIX, historical volatility, etc.)
- **Risk-free rate** (optional, defaults to 4.4%)

### 🎯 **Perfect For:**
- **Strategy development** without market data costs
- **Educational purposes** and learning options pricing
- **Offline analysis** when traveling or without internet
- **Paper trading** and theoretical analysis
- **Custom data integration** from your own sources

### 📋 **Example Usage:**
```python
# See standalone_example.py for complete examples
from option_scenario_calculator import OptionsAnalyzer

analyzer = OptionsAnalyzer('SPY')
results, summary = analyzer.analyze_options(
    S=605.0,        # Current price
    T=7/252,        # 7 days to expiration
    r=0.044,        # 4.4% risk-free rate  
    sigma=0.15,     # 15% implied volatility
    dte_days=7
)
```

## 📊 **Core Features**

### 1. **Enhanced Black-Scholes Implementation**
- Complete Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Proper handling of edge cases (expiration, extreme parameters)
- Optimized for both SPY and SPX scaling

### 2. **Intelligent Strike Selection**
- **SPY**: $2.50 increments, ±$35 range around ATM
- **SPX**: $25 increments, ±$350 range around ATM
- Dynamic range adjustment based on DTE

### 3. **Flexible Scoring Algorithm**
```python
Option_Score = (
    abs(Delta) * 0.4 +           # 40% - Directional exposure
    R_R_Ratio * 0.3 +            # 30% - Risk/reward for target move
    Affordability * 0.2 +         # 20% - Capital efficiency
    Prob_ITM * 0.1               # 10% - Win probability
)
```

### 4. **Customizable Multi-Scenario Analysis**
Define any movement scenarios you want to analyze:
- **Default SPY**: Target $2.0, Conservative $1.0, Aggressive $3.0
- **Default SPX**: Target $20.0, Conservative $10.0, Aggressive $30.0
- **Custom**: Any movements via `--expected-moves '{"breakout": 5.0, "pullback": 2.0}'`

## 🔍 **Analysis Output**

### Key Metrics Provided:
- **Premium**: Option cost
- **Delta**: Price sensitivity to underlying movement
- **Gamma**: Delta acceleration
- **Theta**: Daily time decay
- **Vega**: Volatility sensitivity
- **Breakeven**: Required underlying price for profitability
- **Prob_Profit**: Probability of profit at expiration
- **Prob_ITM**: Probability of finishing in-the-money
- **R/R Ratios**: Risk/reward for different move scenarios

### Sample Output:
```
=== TOP 5 CALL OPTIONS ===
$605: Premium $5.86, Delta 0.515, Score 0.320
$602: Premium $7.21, Delta 0.585, Score 0.347
$600: Premium $8.73, Delta 0.652, Score 0.374
```

## 📈 **Polygon.io Backtesting Integration**

### Setup
1. Get Polygon.io API key from [polygon.io](https://polygon.io/)
2. Install: `pip install polygon-api-client`

### Usage
```python
from polygon_backtester_integration import PolygonBacktester

# Initialize
backtester = PolygonBacktester(api_key="YOUR_API_KEY", underlying='SPY')

# Run backtest
results = backtester.run_backtest(
    start_date="2024-11-01",
    end_date="2024-11-30",
    dte=7,
    rebalance_frequency='daily'
)

# Analyze performance
performance = backtester.analyze_backtest_performance(results)
```

### Features:
- **Historical price data** retrieval
- **Implied volatility calculation** from historical moves
- **Automated rebalancing** (daily/weekly/monthly)
- **Performance analytics** and reporting
- **Export capabilities** for further analysis

## 🤖 **IBKR TWS API Live Trading**

### Setup
1. **Install TWS or IB Gateway** from [Interactive Brokers](https://www.interactivebrokers.com/en/trading/tws.php)
2. **Enable API connections** in TWS/Gateway settings
3. **Choose your Python API**:

#### Option A: ib_async (Recommended - Modern Async)
```bash
pip install ib_async
```

#### Option B: Official IBKR API
```bash
# Via pip (if available)
pip install ibapi

# OR download directly from IBKR
# Visit: https://interactivebrokers.github.io/
# Download the Python API package
```

### Configuration:
- **Paper Trading**: Port 7497 (default)
- **Live Trading**: Port 7496  
- **Client ID**: Each connection needs unique ID (0-32)
- **API Settings**: Enable "Download open orders on connection"

### Usage with ib_async
```python
from ibkr_trading_bot_integration import IBKRTradingBot

# Initialize
bot = IBKRTradingBot('SPY', paper_trading=True)

# Connect and analyze
bot.connect()
opportunities = bot.analyze_opportunities(dte=7)

# Filter and place orders
signals = bot.filter_trading_signals(opportunities['trading_signals'])
for signal in signals[:3]:
    bot.place_option_order(signal, quantity=1)

# Run automated session
bot.run_trading_session(max_positions=3, check_interval=300)
```

### Usage with Official IBKR API (ibapi)
```python
# For direct integration with official IBKR API
from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import Connection

# Example connection setup
conn = Connection.create(port=7497, clientId=0)
conn.connect()

# Create option contract
contract = Contract()
contract.m_symbol = "SPY"
contract.m_secType = "OPT"
contract.m_expiry = "20241220"
contract.m_strike = 605.0
contract.m_right = "C"  # Call
contract.m_exchange = "SMART"

# Place order
order = Order()
order.m_action = "BUY"
order.m_totalQuantity = 1
order.m_orderType = "MKT"

conn.placeOrder(1, contract, order)
```

### Features:
- **Real-time market data** integration
- **Automated opportunity scanning**
- **Risk-based position sizing**
- **Portfolio management** and P&L tracking
- **Event-driven order management**
- **Multiple API options** for different use cases

## ⚙️ **Configuration Options**

### OptionsAnalyzer Configuration:
```python
analyzer = OptionsAnalyzer('SPY')
analyzer.update_config(
    current_price=605.0,
    strike_increment=2.5,
    strike_range_width=35,
    expected_moves={
        'target_move': 2.0,      # Your primary expected move
        'conservative': 1.0,     # Conservative scenario
        'aggressive': 3.0        # Aggressive scenario
    },
    min_premium=0.05,
    max_premium=50.0
)
```

### Trading Bot Parameters:
```python
bot = IBKRTradingBot('SPY')
bot.risk_per_trade = 0.02           # 2% risk per trade
bot.min_score = 0.35               # Minimum score threshold
bot.max_premium = 15.0              # Maximum premium per contract
bot.max_positions = 5               # Maximum concurrent positions

# Note: Current integration uses ib_insync - update to ib_async for latest version
```

## 📋 **Strategy Guidelines & Filtering**

### Sample Filtering Criteria:
```python
# Entry Criteria (customize for your strategy)
option_score > 0.35              # Minimum composite score
abs(delta) > 0.3                 # Sufficient directional exposure
premium < $15 (SPY) / $150 (SPX) # Affordable premium
prob_profit > 0.25               # Reasonable win probability

# Position Sizing (example)
max_risk = account_size * 0.02
contracts = max_risk / (premium * 100)

# Exit Rules (customize based on your strategy)
profit_target = 50% of premium paid    # For quick scalps
stop_loss = 25% of premium paid       # Risk management
time_stop = 1-2 hours before close    # Theta decay protection
```

### DTE Considerations:
- **3-5 DTE**: High gamma, rapid time decay, more directional
- **7-10 DTE**: Balanced theta/delta exposure
- **14+ DTE**: Lower gamma, more time value, less responsive
- **Choose based on your strategy**: Short-term moves vs longer-term positions

## 🎛️ **Command Line Interface**

```bash
# Full option list
python option_scenario_calculator.py --help

# Key parameters
--underlying {SPY,SPX}           # Underlying asset
--current-price FLOAT            # Current underlying price  
--dte INT                        # Days to expiration
--iv FLOAT                       # Implied volatility
--rate FLOAT                     # Risk-free rate
--expected-moves STRING          # Custom moves as JSON
--output-format {dataframe,json,trading_bot,backtester}
--save                           # Save results to file
```

## 📊 **Sample Integration Workflows**

### 1. Daily Analysis Routine
```python
# Morning analysis
analyzer = OptionsAnalyzer('SPY')
current_price = get_market_price()  # From your data source
analysis = analyzer.analyze_options(current_price, T=7/252, r=0.044, sigma=0.15, dte_days=7)

# Filter top opportunities
top_calls = analysis[0][analysis[0]['type'] == 'CALL'].head(3)
top_puts = analysis[0][analysis[0]['type'] == 'PUT'].head(3)
```

### 2. Backtesting Pipeline
```python
# Historical analysis
backtester = PolygonBacktester(api_key, 'SPY')
results = backtester.run_backtest('2024-01-01', '2024-12-01', dte=7)
performance = backtester.analyze_backtest_performance(results)
```

### 3. Live Trading Loop
```python
# Automated trading
bot = IBKRTradingBot('SPY', paper_trading=True)
bot.connect()
bot.run_trading_session(max_positions=3, check_interval=300)
```

## 🚨 **Risk Management**

### Built-in Risk Controls:
1. **Position Sizing**: Automatic calculation based on account risk
2. **Premium Limits**: Configurable maximum premium per contract
3. **Concentration Limits**: Maximum number of concurrent positions
4. **Score Thresholds**: Minimum day trading score requirements

### Recommended Additional Controls:
- Daily loss limits
- Sector concentration limits
- Volatility environment adjustments
- Time-of-day restrictions

## 🔬 **Technical Details**

### Black-Scholes Implementation:
- Uses `scipy.stats.norm` for high precision
- Handles edge cases (T≤0, extreme volatility)
- Proper theta calculation (daily decay)
- Vega scaled to 1% volatility change

### Performance Optimizations:
- Vectorized calculations where possible
- Efficient strike range generation
- Minimal API calls with rate limiting
- Caching of frequently used calculations

## 🆘 **Troubleshooting**

### Common Issues:

**"KeyError: 'Premium'"**
- Solution: Ensure column names are lowercase in DataFrame operations

**IBKR Connection Failed**
- Check TWS/Gateway is running and logged in
- Verify API settings enabled in Global Configuration
- Confirm correct port (7497 paper, 7496 live)
- Ensure unique Client ID (0-32, no duplicates)
- Check firewall/antivirus blocking connections
- For ib_async: `pip install ib_async` (not ib_insync)
- For ibapi: Download from official IBKR site if pip fails

**Polygon.io Rate Limits**
- Add delays between API calls
- Use higher-tier subscription for more requests
- Implement exponential backoff

**Low Option Scores**
- Adjust expected move parameters for your strategy
- Check current volatility environment
- Verify strike range includes optimal contracts

## 📈 **Performance Expectations**

### Typical Option Scores:
- **>0.40**: Excellent opportunities (rare)
- **0.30-0.40**: Good opportunities
- **0.20-0.30**: Marginal opportunities
- **<0.20**: Poor opportunities (avoid)

### Expected R/R Ratios:
Varies based on your expected moves and market conditions:
- **Small moves**: 0.05-0.15 typical
- **Medium moves**: 0.15-0.30 typical
- **Large moves**: 0.30+ possible

## 📁 **Data Management**

### Automatic File Organization
All output files are automatically organized in the `data/` directory:

```
data/
├── options_analysis_SPY_20241201_143022.csv     # Analysis results
├── options_analysis_summary_SPY_20241201_143022.json  # Summary data
├── polygon_backtest_SPY_20241201_150000.json    # Backtest results
└── trading_signals_SPY_20241201_160000.json     # Trading bot signals
```

### Git Integration
The repository is configured to:
- ✅ **Include** source code and documentation
- ✅ **Include** empty `data/` directory structure
- ❌ **Exclude** all generated files (`*.csv`, `*.json`, logs, etc.)
- ❌ **Exclude** API keys and sensitive configuration

### File Naming Convention
```
{analysis_type}_{underlying}_{YYYYMMDD}_{HHMMSS}.{extension}
```

Examples:
- `options_analysis_SPY_20241201_143022.csv`
- `polygon_backtest_SPX_20241201_150000.json`
- `trading_signals_SPY_20241201_160000.json`

### Cleanup Commands
```bash
# Remove all data files (keep directory structure)
rm data/*.csv data/*.json

# Remove files older than 7 days
find data/ -name "*.csv" -mtime +7 -delete
find data/ -name "*.json" -mtime +7 -delete
```

## 🔄 **Version History**

### v2.0 (Current)
- Added SPY/SPX dual support
- Polygon.io backtesting integration  
- IBKR TWS API live trading
- Enhanced scoring algorithm
- Multi-scenario analysis
- Automatic data directory management
- Git repository structure

### v1.0
- Basic Black-Scholes implementation
- Single underlying support
- CSV output only

## 📞 **Support & Contributing**

This system is designed for educational and research purposes. Always test thoroughly in paper trading before live implementation.

### Key Dependencies:
- `numpy >= 1.21.0`
- `pandas >= 1.3.0`
- `scipy >= 1.7.0`
- `polygon-api-client >= 1.0.0` (optional)
- `ib_insync >= 0.9.86` (optional)

---

**⚠️ Disclaimer**: This software is for educational purposes only. Options trading involves substantial risk of loss. Always conduct your own analysis and risk management before trading. 