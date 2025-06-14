#!/usr/bin/env python3
"""
Options Analysis Web Application

Modern Flask web interface for the complete options analysis system.
Provides full access to all functionality through a beautiful UI.
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Import our options analyzer
from option_scenario_calculator import OptionsAnalyzer

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Global analyzer instance
analyzer = None

def get_analyzer(underlying='SPY'):
    """Get or create analyzer instance"""
    global analyzer
    if analyzer is None or analyzer.underlying != underlying:
        analyzer = OptionsAnalyzer(underlying)
    return analyzer

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_options():
    """Main options analysis endpoint"""
    try:
        data = request.get_json()
        print(f"📊 Received analysis request: {data}")
        
        # Validate request data
        if not data:
            raise ValueError("No JSON data received")
        
        # Extract parameters with validation
        underlying = data.get('underlying', 'SPY')
        current_price = data.get('current_price')
        dte = data.get('dte', 7)
        iv = data.get('iv', 15)  # Expecting percentage
        risk_free_rate = data.get('risk_free_rate', 4.4)  # Expecting percentage
        
        print(f"📈 Parameters - Underlying: {underlying}, Price: {current_price}, DTE: {dte}, IV: {iv}%, RFR: {risk_free_rate}%")
        
        # Convert and validate parameters
        try:
            if current_price is not None and current_price != '':
                current_price = float(current_price)
            else:
                current_price = 0
            dte = int(dte)
            iv = float(iv) / 100.0  # Convert percentage to decimal
            risk_free_rate = float(risk_free_rate) / 100.0  # Convert percentage to decimal
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid parameter format: {e}")
        
        # Validate ranges
        if dte <= 0 or dte > 365:
            raise ValueError(f"DTE must be between 1 and 365 days, got {dte}")
        if iv <= 0 or iv > 5:
            raise ValueError(f"IV must be between 0.1% and 500%, got {iv*100}%")
        if risk_free_rate < 0 or risk_free_rate > 0.5:
            raise ValueError(f"Risk-free rate must be between 0% and 50%, got {risk_free_rate*100}%")
        
        # Get analyzer
        analyzer = get_analyzer(underlying)
        print(f"✅ Got analyzer for {underlying}")
        
        # Update configuration if needed
        if current_price > 0:
            analyzer.update_config(current_price=current_price)
            print(f"📊 Updated price to ${current_price}")
        
        # Get the actual price to use
        analysis_price = current_price if current_price > 0 else analyzer.get_current_price()
        print(f"💰 Using price: ${analysis_price}")
        
        # Run analysis
        print(f"🔄 Running analysis...")
        results, summary = analyzer.analyze_options(
            S=analysis_price,
            T=dte/252,
            r=risk_free_rate,
            sigma=iv,
            dte_days=dte
        )
        
        print(f"✅ Analysis complete - {len(results)} options analyzed")
        
        # Convert to JSON-serializable format
        results_dict = results.to_dict('records')
        
        return jsonify({
            'success': True,
            'results': results_dict,
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Analysis error: {error_msg}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 400

@app.route('/api/live-price/<symbol>')
def get_live_price(symbol):
    """Get live price from Polygon.io"""
    try:
        # Try to get live price
        from live_demo_session import LiveDemoSession
        
        api_key = os.environ.get('POLYGON_API_KEY')
        demo = LiveDemoSession(api_key)
        price = demo.get_current_price(symbol.upper())
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'price': price,
            'timestamp': datetime.now().isoformat(),
            'source': 'live' if demo.polygon_client else 'fallback'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/iv-calculator', methods=['POST'])
def calculate_iv():
    """Implied volatility calculator endpoint"""
    try:
        data = request.get_json()
        
        market_price = float(data.get('market_price'))
        underlying_price = float(data.get('underlying_price'))
        strike = float(data.get('strike'))
        dte = int(data.get('dte', 7))
        risk_free_rate = float(data.get('risk_free_rate', 0.044))
        option_type = data.get('option_type', 'call').lower()
        
        # Get analyzer
        underlying = data.get('underlying', 'SPY')
        analyzer = get_analyzer(underlying)
        
        # Calculate IV
        result = analyzer.implied_volatility_calculator(
            market_price, underlying_price, strike, dte/252, risk_free_rate, option_type
        )
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/price-scenario', methods=['POST'])
def price_scenario():
    """Price scenario analysis endpoint"""
    try:
        data = request.get_json()
        
        base_price = float(data.get('base_price'))
        adjustment = float(data.get('adjustment'))
        
        # Get analyzer and other parameters
        underlying = data.get('underlying', 'SPY')
        dte = int(data.get('dte', 7))
        iv = float(data.get('iv', 15)) / 100  # Convert percentage to decimal
        risk_free_rate = float(data.get('risk_free_rate', 4.4)) / 100  # Convert percentage to decimal
        
        analyzer = get_analyzer(underlying)
        
        # Calculate basic scenario info
        scenario_info = analyzer.price_adjustment_scenario(base_price, adjustment)
        new_price = scenario_info['adjusted_price']
        
        # Run options analysis at the new price to show impact
        T = dte / 252  # Convert days to years
        
        # Get a few key strikes around the new price for impact analysis
        strike_increment = analyzer.config['strike_increment']
        atm_strike = round(new_price / strike_increment) * strike_increment
        
        # Analyze ATM call and put at new price
        atm_call = analyzer.black_scholes_price(new_price, atm_strike, T, risk_free_rate, iv, 'call')
        atm_put = analyzer.black_scholes_price(new_price, atm_strike, T, risk_free_rate, iv, 'put')
        
        # Also analyze at original price for comparison
        orig_call = analyzer.black_scholes_price(base_price, atm_strike, T, risk_free_rate, iv, 'call')
        orig_put = analyzer.black_scholes_price(base_price, atm_strike, T, risk_free_rate, iv, 'put')
        
        # Calculate option price changes
        call_change = atm_call['price'] - orig_call['price']
        put_change = atm_put['price'] - orig_put['price']
        
        result = {
            **scenario_info,
            'options_impact': {
                'atm_strike': atm_strike,
                'call_price_change': call_change,
                'put_price_change': put_change,
                'call_new_price': atm_call['price'],
                'put_new_price': atm_put['price'],
                'call_original_price': orig_call['price'],
                'put_original_price': orig_put['price']
            }
        }
        
        return jsonify({
            'success': True,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/greeks-comparison', methods=['POST'])
def greeks_comparison():
    """Greeks scaling comparison endpoint"""
    try:
        data = request.get_json()
        
        underlying_price = float(data.get('underlying_price'))
        strike = float(data.get('strike'))
        dte = int(data.get('dte', 7))
        iv = float(data.get('iv', 0.15))
        risk_free_rate = float(data.get('risk_free_rate', 0.044))
        option_type = data.get('option_type', 'call').lower()
        
        # Get analyzer
        underlying = data.get('underlying', 'SPY')
        analyzer = get_analyzer(underlying)
        
        # Calculate Greeks for different scalings
        scalings = ['daily', 'per_minute', 'annual']
        results = {}
        
        for scaling in scalings:
            analyzer.set_greeks_scaling(scaling)
            greeks = analyzer.black_scholes_price(
                underlying_price, strike, dte/252, risk_free_rate, iv, option_type
            )
            results[scaling] = greeks
        
        # Reset to daily
        analyzer.set_greeks_scaling('daily')
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/save-analysis', methods=['POST'])
def save_analysis():
    """Save analysis results"""
    try:
        data = request.get_json()
        
        results_data = data.get('results')
        summary_data = data.get('summary')
        filename_prefix = data.get('filename', 'web_analysis')
        
        # Convert back to DataFrame
        results_df = pd.DataFrame(results_data)
        
        # Get analyzer for saving
        underlying = data.get('underlying', 'SPY')
        analyzer = get_analyzer(underlying)
        
        # Save files
        files = analyzer.save_analysis((results_df, summary_data), filename_prefix)
        
        return jsonify({
            'success': True,
            'files': files if isinstance(files, tuple) else [files],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    try:
        # Get default analyzer
        analyzer = get_analyzer('SPY')
        
        config = {
            'supported_underlyings': ['SPY', 'SPX'],
            'default_dte': 7,
            'default_iv': 0.15,
            'default_risk_free_rate': 0.044,
            'has_polygon_api': bool(os.environ.get('POLYGON_API_KEY')),
            'spy_config': OptionsAnalyzer('SPY').config,
            'spx_config': OptionsAnalyzer('SPX').config
        }
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/files')
def list_files():
    """List saved analysis files"""
    try:
        data_dir = 'data'
        if not os.path.exists(data_dir):
            return jsonify({'success': True, 'files': []})
        
        files = []
        for filename in os.listdir(data_dir):
            if filename.endswith(('.csv', '.json')):
                filepath = os.path.join(data_dir, filename)
                stat = os.stat(filepath)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'files': files
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/download/<filename>')
def download_file(filename):
    """Download a saved file"""
    try:
        filepath = os.path.join('data', filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Run the app
    debug_mode = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 