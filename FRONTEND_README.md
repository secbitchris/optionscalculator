# Options Analysis Web Frontend

Beautiful, modern web interface for the complete options analysis system.

## 🚀 Quick Start

### 1. Start the Web Application

```bash
python run_webapp.py
```

### 2. Open Your Browser

Navigate to: **http://localhost:5000**

## 🎯 Features

### **Main Dashboard**
- **Live Price Fetching**: Real-time SPY/SPX prices from Polygon.io
- **Parameter Configuration**: Underlying, DTE, IV, Risk-free rate
- **Instant Analysis**: Click "Analyze Options" for comprehensive results
- **Beautiful Results Table**: Color-coded scores, sortable columns
- **Summary Cards**: Key metrics at a glance

### **Enhanced Features**
- **🧮 IV Calculator**: Reverse Black-Scholes to find implied volatility
- **📈 Price Scenarios**: Model different underlying price movements with options impact analysis
- **📐 Greeks Comparison**: Compare daily/per-minute/annual scaling
- **💾 Save/Export**: Save results to data/ directory or export CSV

### **Real-time Integration**
- **API Status Indicator**: Shows live/fallback/offline status
- **Auto-fetch Prices**: One-click live price updates
- **Graceful Fallbacks**: Works offline with sample data

## 🎨 User Interface

### **Modern Design**
- **Bootstrap 5**: Responsive, mobile-friendly design
- **Font Awesome Icons**: Professional iconography
- **Color-coded Results**: Green/yellow/red score highlighting
- **Smooth Animations**: Fade-in effects and loading spinners

### **Responsive Layout**
- **Desktop**: Full sidebar + main content
- **Mobile**: Collapsible navigation, optimized tables
- **Tablet**: Adaptive layout for all screen sizes

## 🔧 Technical Details

### **Frontend Stack**
- **Flask**: Python web framework
- **Bootstrap 5**: CSS framework
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: No heavy frameworks, fast loading

### **Backend Integration**
- **RESTful API**: Clean JSON endpoints
- **Real-time Data**: Polygon.io integration
- **File Management**: Automatic data/ directory organization
- **Error Handling**: Graceful error messages and fallbacks

### **API Endpoints**
```
GET  /                          # Main dashboard
POST /api/analyze               # Run options analysis
GET  /api/live-price/<symbol>   # Fetch live price
POST /api/iv-calculator         # Calculate implied volatility
POST /api/price-scenario        # Analyze price scenarios
POST /api/greeks-comparison     # Compare Greeks scaling
POST /api/save-analysis         # Save results
GET  /api/config                # Get configuration
GET  /api/files                 # List saved files
GET  /api/download/<filename>   # Download saved file
```

## 📱 Usage Examples

### **Basic Analysis**
1. Select underlying (SPY/SPX)
2. Click refresh button to fetch live price (or enter manually)
3. Adjust DTE, IV, risk-free rate as needed
4. Click "Analyze Options"
5. View results table with color-coded scores
6. Save or export results

### **Enhanced Features**
1. **IV Calculator**: Click button → Enter market price, underlying, strike → Get IV
2. **Price Scenarios**: Click button → Auto-filled base price, enter move (+/-) → See detailed options impact
3. **Greeks Comparison**: Click button → Enter parameters → Compare scalings
4. **Saved Files**: Click button → View/download previous analyses

### **Live Data Integration**
- **Green indicator**: Live Polygon.io data
- **Yellow indicator**: Fallback/cached data  
- **Red indicator**: Offline mode
- **Auto-refresh**: Click sync button for latest prices

## 🛠️ Development

### **File Structure**
```
├── app.py                 # Flask application
├── run_webapp.py          # Startup script
├── templates/
│   └── index.html         # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── app.js         # JavaScript application
└── data/                  # Saved analysis files
```

### **Customization**
- **Styling**: Edit `static/css/style.css`
- **Functionality**: Modify `static/js/app.js`
- **Layout**: Update `templates/index.html`
- **Backend**: Extend `app.py` with new endpoints

### **Adding Features**
1. Add new API endpoint in `app.py`
2. Add frontend function in `app.js`
3. Add UI elements in `index.html`
4. Style with CSS in `style.css`

## 🔒 Security

### **API Key Protection**
- ✅ `.env` file automatically ignored by git
- ✅ No API keys in frontend code
- ✅ Server-side API key handling only

### **Input Validation**
- ✅ Frontend form validation
- ✅ Backend parameter sanitization
- ✅ Error handling for invalid inputs

## 🚀 Production Deployment

### **Local Development**
```bash
python run_webapp.py  # Debug mode, auto-reload
```

### **Production Server**
```bash
# Option 1: Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Option 2: uWSGI  
pip install uwsgi
uwsgi --http :5000 --wsgi-file app.py --callable app

# Option 3: Docker
# Create Dockerfile and deploy to cloud
```

### **Environment Variables**
```bash
export POLYGON_API_KEY=your_key_here
export SECRET_KEY=your_secret_key_here
export DEBUG_MODE=false
```

## 🔥 Recent Improvements

### **Enhanced Price Scenarios (v2.0)**
The Price Scenarios feature has been completely redesigned for professional trading analysis:

**🎯 What It Does:**
- **Scenario Modeling**: Analyze "what if" price movements for day trading
- **Options Impact**: See exactly how ATM calls/puts would be affected
- **Auto-fill Integration**: Base price automatically updates from live price fetches
- **Comprehensive Analysis**: Uses your current DTE, IV, and risk-free rate settings

**💡 How to Use:**
1. **Auto-fill**: Base price automatically fills when you fetch live prices
2. **Enter Move**: Type your expected price movement (e.g., `+1.50`, `-2.00`, `0`)
3. **Analyze**: Get detailed breakdown of price impact and options changes
4. **Results**: See bullish/bearish/neutral scenario with precise option price changes

**📊 Example Output:**
```
Price Movement                    ATM Options Impact ($600)
Scenario: Bullish                Call: $4.25 → $5.75 (+$1.50)
New Price: $598.70               Put: $6.25 → $4.75 (-$1.50)  
Change: +$1.50 (+0.3%)
```

**🎯 Trading Applications:**
- **Risk Management**: "If SPY drops $2, how much do I lose?"
- **Profit Targets**: "If I hit my $1.50 target, what's my profit?"
- **Position Sizing**: "Can I afford the risk if it moves against me?"

## 🎉 What You Get

A **professional-grade web application** that provides:

✅ **Institutional-level options analysis** in your browser  
✅ **Real-time market data integration** with live pricing  
✅ **All 4 enhanced features** accessible via beautiful UI  
✅ **Mobile-responsive design** works on any device  
✅ **Professional appearance** suitable for client presentations  
✅ **Complete offline capability** when API unavailable  
✅ **Automatic file management** with organized data storage  
✅ **Export capabilities** for further analysis  

**Perfect for traders, analysts, and anyone needing sophisticated options analysis with a modern interface!** 