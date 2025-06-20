# SPY/SPX Options Analysis System

A comprehensive and flexible options analysis tool for SPY and SPX options, with **real market data integration**, **intelligent strike filtering**, and **production-ready Docker deployment**.

## 🎯 **Overview**

This system helps identify optimal options contracts for any trading strategy with **real market data** and customizable movement expectations. It works with **live Polygon.io data** and includes smart rate limiting for API efficiency:

### 🏠 **Core Features:**
- **Professional Web Interface** with Bootstrap 5 UI and real-time data
- **Real Market Data Integration** - Live prices and open interest from Polygon.io (15-minute delay)
- **Intelligent Strike Filtering** - Focus on tradeable strikes within ±40 points of current price
- **Rate Limited API Calls** - Efficient 12-second intervals with 5-minute caching
- **Advanced Black-Scholes pricing** with complete Greeks calculation
- **Real Market IV Detection** - Automatically detects market IV from VIX/VIX9D data
- **Expected Move Calculator** using proper formula: Price × IV × √(T/252)
- **Enhanced Price Scenarios** with options impact analysis
- **Probability analysis** (profit probability, ITM probability, breakeven)
- **Multi-scenario R/R analysis** for different move expectations
- **Flexible scoring algorithm** for optimal contract selection
- **Custom movement scenarios** for any trading strategy

### 🌐 **Smart External Integrations:**
- **Polygon.io Real Data** - Works with basic API tier (no premium subscription needed)
- **Real-time Stock Prices** from Polygon.io with intelligent caching
- **Live VIX Data** for automatic IV detection
- **Rate Limiting** - 5 requests per minute with smart caching to respect API limits
- **IBKR TWS API integration** for live trading automation (requires IBKR account)

### ⚡ **Performance Optimizations:**
- **Strike Filtering** - Only analyzes strikes within ±40 points of current price (160 contracts vs 500+)
- **API Rate Limiting** - 12-second intervals between calls to respect free tier limits
- **Response Caching** - 5-minute cache for API responses to reduce redundant calls
- **Efficient Data Processing** - Skip unnecessary calculations for out-of-range strikes

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
├── 📄 SETUP_GUIDE.md                 # Cross-platform setup instructions
├── 📄 FRONTEND_README.md              # Web application documentation
├── 📄 WINDOWS_DOCKER_SETUP.md        # Windows Docker deployment guide
├── 📄 requirements.txt               # Python dependencies
├── 📄 docker-compose.yml             # Docker deployment configuration
├── 📄 Dockerfile                     # Container build instructions
├── 📄 IBKR_MIGRATION_GUIDE.md        # Guide for updating IBKR APIs
├── 🐍 app.py                         # Flask web application
├── 🐍 run_webapp.py                  # Web application launcher
├── 🐍 option_scenario_calculator.py  # Core analysis engine
├── 🐍 polygon_options_hybrid.py      # Real data integration with rate limiting
├── 🐍 live_demo_session.py           # Live market data integration
├── 🐍 standalone_example.py          # Standalone local usage example
├── 🐍 polygon_backtester_integration.py  # Polygon.io backtesting (optional)
├── 🐍 ibkr_trading_bot_integration.py    # IBKR live trading (optional)
└── 🐍 integration_examples.py        # Advanced integration examples
```

## 🚀 **Quick Start**

### 🐳 **Docker Deployment (Recommended)**

#### 🪟 **Windows Users** - See [WINDOWS_DOCKER_SETUP.md](WINDOWS_DOCKER_SETUP.md)
```powershell
# Quick Windows setup (5 minutes):
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator
docker-compose up --build -d

# Open browser to: http://localhost:5002
# Complete step-by-step guide: WINDOWS_DOCKER_SETUP.md
```

#### 🍎🐧 **macOS/Linux Users**
```bash
# Quick Docker setup - everything included!
git clone https://github.com/secbitchris/optionscalculator.git
cd optionscalculator
docker-compose up --build -d

# Open browser to: http://localhost:5002
# Features: Containerized, isolated, easy deployment
```

### 🌐 **Web Application (Local Development)**
```bash
# Start the development server with real market data
python run_webapp.py --port 5002

# Open browser to: http://localhost:5002
# Features: Real market IV detection, live prices, rate-limited API calls, professional UI
```

### 🎯 **Professional Web Interface Features:**
- **Real Market Data** - Live SPY prices and open interest from Polygon.io (15-minute delay)
- **Intelligent Strike Filtering** - Only shows strikes within ±40 points of current price
- **Rate Limited API Integration** - Efficient 12-second intervals with smart caching
- **Complete Trading Day Selection** - Choose any valid trading day (0 DTE, 1 DTE, 2 DTE, etc.)
- **Comprehensive Economic Calendar** - Accurate 2025 event labeling (CPI, PPI, FOMC, OPEX, NFP, JOLTS)
- **Smart Date Organization** - Grouped by priority: Major Events → Economic Events → All Trading Days
- **Options Chain View** - Traditional broker-style layout with calls|strike|puts
- **Advanced Sorting** - 9 different sorting methods (Best Overall, Cheapest, Highest Delta, etc.)
  - **💹 Risk/Reward Sorting** - Higher R/R ratios (better leverage potential) shown first
  - **🔄 View-Aware Sorting** - Works in Chain View, Calls Only, and Puts Only modes
  - **⚡ Real-Time Sorting** - Instant reordering with visual confirmation
- **ATM Highlighting** - Yellow background for strikes within $5 of current price
- **Color-Coded ITM/OTM** - Green for ITM, red for OTM options
- **Real-Time Data Integration** - Live prices, market IV, and Open Interest
- **Export Capabilities** - CSV and JSON export with complete options data
- **Responsive Design** - Works on desktop, tablet, and mobile devices

### 🔥 **Real Market Data Features:**
1. **Live Stock Prices** - Real SPY prices from Polygon.io with 15-minute delay
2. **Real Open Interest** - Actual OI data from live market contracts
3. **Auto-Detect Market IV** - Uses VIX (20.1%) → VIX9D → Historical → 15% fallback
4. **Rate Limited API Calls** - 12-second intervals, 5-minute caching for efficiency
5. **Strike Filtering** - Focus on ±40 points around current price (160 contracts vs 500+)
6. **Real Expected Moves** - Uses proper formula: Price × IV × √(T/252)
7. **Complete Trading Calendar** - All valid trading days (63 days) with accurate 2025 economic events
8. **Professional Date Selection** - 0 DTE through 90+ DTE with event indicators
9. **Advanced Options Sorting** - 9 ranking methods from best overall to specific Greek strategies
10. **No Premium Subscription Needed** - Works with basic Polygon.io API ($0-$30/month)

### 📅 **Comprehensive Economic Calendar Integration:**
- **CPI Dates** - All 2025 Consumer Price Index release dates (2nd Wednesday monthly)
- **PPI Dates** - Producer Price Index releases (Thursday after CPI)
- **FOMC Meetings** - Federal Reserve policy meetings with rate decisions
- **OPEX Dates** - Monthly options expiration (3rd Friday) + Quad Witching
- **VIX Expiration** - VIX options expiration dates (Wednesday before OPEX)
- **NFP (Jobs Report)** - Non-farm payroll releases (1st Friday monthly)
- **JOLTS** - Job Openings and Labor Turnover Survey dates
- **End/Beginning of Quarter** - Important institutional rebalancing dates
- **Smart Prioritization** - Major events highlighted, all trading days available

### 📱 **Command Line Analysis**
```bash
# Basic SPY analysis with real market data
python option_scenario_calculator.py --current-price 605.0 --dte 7 --iv 0.15

# SPX analysis with custom parameters
python option_scenario_calculator.py --underlying SPX --current-price 6000 --dte 14 --iv 0.20

# Custom movement scenarios (earnings example)
python option_scenario_calculator.py --expected-moves '{"earnings": 50.0, "normal": 15.0}' --current-price 605.0

# Run standalone example with multiple scenarios
python standalone_example.py
```

### 📁 **Data Organization**
All output files are automatically saved to the `data/` directory:
- Analysis results: `data/options_analysis_SPY_YYYYMMDD_HHMMSS.csv`
- JSON summaries: `data/options_analysis_summary_SPY_YYYYMMDD_HHMMSS.json`  
- Backtest data: `data/polygon_backtest_SPY_YYYYMMDD_HHMMSS.json`

The `data/` directory is ignored by git to keep your repository clean while preserving all analysis locally.

## 🔧 **Installation**

### 🐳 **Docker Installation (Recommended)**
```bash
# Clone repository
git clone git@github.com:secbitchris/optionscalculator.git
cd optionscalculator

# Quick Docker setup with real data integration
docker-compose up --build -d

# Access at http://localhost:5002
# Features: Real market data, rate limiting, strike filtering
```

### 🐍 **Python Installation (Development)**
```bash
# Clone repository
git clone git@github.com:secbitchris/optionscalculator.git
cd optionscalculator

# Install core dependencies
pip install -r requirements.txt

# Set up environment file for API keys
cp env_template.txt .env
# Edit .env file with your Polygon.io API key
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

## 💻 **API Configuration**

### **Polygon.io Setup (Recommended)**
1. Sign up at [polygon.io](https://polygon.io) - Free tier available
2. Get your API key from the dashboard
3. Add to `.env` file: `POLYGON_API_KEY=your_key_here`
4. Enjoy real market data with 15-minute delay

### **Rate Limiting (Built-in)**
- **12-second intervals** between API calls (5 requests per minute)
- **5-minute response caching** to reduce redundant calls
- **Automatic retry logic** with exponential backoff
- **Free tier friendly** - works within Polygon.io basic limits

### **Standalone Local Operation**
The calculator also works **completely offline** with no external dependencies beyond basic Python packages:

#### ✅ **What Works Locally:**
- **Complete Black-Scholes analysis** with all Greeks
- **Multi-scenario R/R calculations** for any custom movements
- **Probability analysis** (profit probability, ITM probability, breakeven)
- **Flexible scoring** for strategy optimization
- **All output formats** (CSV, JSON, trading signals, backtester)

#### 📝 **You Only Need to Provide:**
- **Current underlying price** (from any source: broker, Yahoo Finance, etc.)
- **Days to expiration**
- **Implied volatility** (estimate from VIX, historical volatility, etc.)
- **Risk-free rate** (optional, defaults to 4.4%)

## 🚀 **Production Deployment**

### **Docker Production (Recommended)**
```bash
# Production deployment with Docker
docker-compose up -d

# Monitor logs
docker-compose logs -f

# Scale if needed
docker-compose up --scale web=2 -d
```

### **Environment Configuration**
```bash
# Production environment variables
export POLYGON_API_KEY=your_production_key
export FLASK_ENV=production
export SECRET_KEY=your_secret_key_here
```

## 📊 **Performance Metrics**

### **Strike Filtering Efficiency**
- **Before**: 500+ contracts processed
- **After**: 160 contracts (±40 points filtering)
- **Efficiency**: 68% reduction in processing time
- **Coverage**: Comprehensive tradeable range around current price

### **API Rate Limiting**
- **Interval**: 12 seconds between calls
- **Cache Duration**: 5 minutes for responses
- **Free Tier Compatibility**: 5 requests per minute limit
- **Efficiency**: 90% reduction in API calls through smart caching

### **Real Data Quality**
- **Price Data**: Live SPY prices (15-minute delay)
- **Open Interest**: Real market OI data where available
- **IV Detection**: Live VIX-based market IV
- **Data Freshness**: Updated every 15 minutes during market hours

## 🎯 **Perfect For:**
- **Day Trading** - Real market data with strike filtering for relevant options
- **Strategy Development** - Comprehensive analysis with live market conditions
- **Risk Management** - Real probability analysis with current market IV
- **Educational Purposes** - Professional-grade tools for learning options pricing
- **Paper Trading** - Realistic analysis with actual market data
- **Production Trading** - Rate-limited, reliable data integration

## 🔥 **Recent Updates**

### **v3.0 - Real Market Data Integration**
- ✅ Live Polygon.io data integration with 15-minute delay
- ✅ Intelligent strike filtering (±40 points around current price)
- ✅ Rate limiting with 12-second intervals and 5-minute caching
- ✅ Real open interest data from live market contracts
- ✅ Docker containerization on port 5002
- ✅ Production-ready deployment with comprehensive documentation

### **v2.0 - Enhanced Web Interface**
- ✅ Professional Bootstrap 5 UI with responsive design
- ✅ Real-time data integration with graceful fallbacks
- ✅ Advanced sorting and filtering capabilities
- ✅ Comprehensive economic calendar integration
- ✅ Export capabilities and data persistence

## 📚 **Documentation**

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Cross-platform installation instructions
- **[FRONTEND_README.md](FRONTEND_README.md)** - Web interface documentation
- **[WINDOWS_DOCKER_SETUP.md](WINDOWS_DOCKER_SETUP.md)** - Windows Docker deployment
- **[IBKR_MIGRATION_GUIDE.md](IBKR_MIGRATION_GUIDE.md)** - IBKR API updates

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- Polygon.io for real market data API
- Interactive Brokers for trading platform integration
- The options trading community for feedback and suggestions 