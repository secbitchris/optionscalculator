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

@app.route('/api/expected-moves', methods=['POST'])
def calculate_expected_moves():
    """Calculate expected moves using different methods"""
    try:
        data = request.get_json()
        
        underlying = data.get('underlying', 'SPY')
        current_price = float(data.get('current_price', 0))
        dte = int(data.get('dte', 7))
        iv = float(data.get('iv', 15)) / 100  # Convert percentage to decimal
        risk_free_rate = float(data.get('risk_free_rate', 4.4)) / 100
        
        # Get analyzer
        analyzer = get_analyzer(underlying)
        
        # Get actual price if not provided
        if current_price <= 0:
            current_price = analyzer.get_current_price()
        
        T = dte / 252
        
        # Calculate using different methods
        formula_moves = analyzer.calculate_expected_move(current_price, iv, T)
        straddle_info = analyzer.get_atm_straddle_price(current_price, T, risk_free_rate, iv)
        comparison = analyzer.compare_expected_move_methods(current_price, T, risk_free_rate, iv)
        
        return jsonify({
            'success': True,
            'formula_moves': formula_moves,
            'straddle_info': straddle_info,
            'comparison': comparison,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/live-straddle/<symbol>')
def get_live_straddle(symbol):
    """Get live straddle pricing from Polygon.io"""
    try:
        dte = int(request.args.get('dte', 7))
        
        # Initialize live demo session
        api_key = os.environ.get('POLYGON_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'No Polygon.io API key configured'
            }), 400
        
        from live_demo_session import LiveDemoSession
        demo = LiveDemoSession(api_key)
        
        # Get live straddle data
        straddle_data = demo.get_live_atm_straddle(symbol.upper(), dte=dte)
        
        if not straddle_data:
            return jsonify({
                'success': False,
                'error': 'No live straddle data available'
            }), 400
        
        return jsonify({
            'success': True,
            'straddle_data': straddle_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/live-expected-moves/<symbol>')
def get_live_expected_moves(symbol):
    """Compare live market expected moves vs formula calculations"""
    try:
        dte = int(request.args.get('dte', 7))
        
        # Initialize live demo session
        api_key = os.environ.get('POLYGON_API_KEY')
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'No Polygon.io API key configured'
            }), 400
        
        from live_demo_session import LiveDemoSession
        demo = LiveDemoSession(api_key)
        
        # Calculate expected moves using multiple methods
        comparison_data = demo.calculate_live_expected_moves(symbol.upper(), dte=dte)
        
        return jsonify({
            'success': True,
            'comparison': comparison_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/auto-update-expected-moves', methods=['POST'])
def auto_update_expected_moves():
    """Automatically update expected moves based on IV calculations"""
    try:
        data = request.get_json()
        
        underlying = data.get('underlying', 'SPY')
        current_price = float(data.get('current_price', 0))
        dte = int(data.get('dte', 7))
        iv = float(data.get('iv', 15)) / 100
        risk_free_rate = float(data.get('risk_free_rate', 4.4)) / 100
        use_formula = data.get('use_formula', True)  # True for formula, False for straddle
        
        # Get analyzer
        analyzer = get_analyzer(underlying)
        
        # Get actual price if not provided
        if current_price <= 0:
            current_price = analyzer.get_current_price()
        
        T = dte / 252
        
        # Update expected moves based on IV
        new_moves = analyzer.update_expected_moves_from_iv(
            current_price, T, risk_free_rate, iv, use_formula
        )
        
        return jsonify({
            'success': True,
            'new_expected_moves': new_moves,
            'method': 'iv_formula' if use_formula else 'straddle_pricing',
            'underlying': underlying,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/expected-moves-hybrid', methods=['POST'])
def calculate_expected_moves_hybrid():
    """Calculate expected moves using hybrid system (works around subscription limits)"""
    try:
        data = request.get_json()
        
        underlying = data.get('underlying', 'SPY')
        current_price = float(data.get('current_price', 0))
        dte = int(data.get('dte', 7))
        iv_input = data.get('iv')  # May be None for auto-detect
        
        # Use hybrid system for expected moves
        from polygon_options_hybrid import PolygonOptionsHybrid
        hybrid = PolygonOptionsHybrid()
        
        # Get live stock price if not provided
        if current_price <= 0:
            current_price = hybrid.get_live_stock_price(underlying)
            if not current_price:
                return jsonify({'error': 'Could not get live stock price'}), 400
        
        # Get real market IV or use provided value
        if iv_input is not None and iv_input > 0:
            iv = float(iv_input) / 100  # Convert percentage to decimal
            iv_source = "User Input"
            print(f"📊 Expected moves request: {underlying}, ${current_price}, {dte} DTE, {iv*100}% IV (user input)")
        else:
            iv = hybrid.get_market_iv(underlying)
            iv_source = "Market Data (VIX/Historical)"
            print(f"📊 Expected moves request: {underlying}, ${current_price}, {dte} DTE, {iv*100}% IV (market)")
        
        if not iv or iv <= 0:
            return jsonify({'error': 'Could not determine implied volatility'}), 400
        
        # Calculate expected moves
        expected_moves = hybrid.calculate_expected_moves(current_price, iv, [1, 3, 7, 14, 30])
        
        # Format for frontend
        formatted_moves = {}
        for dte_key, moves in expected_moves.items():
            formatted_moves[f"{dte_key}_day"] = {
                'formula_1sigma': round(moves['formula_move_1sigma'], 2),
                'formula_2sigma': round(moves['formula_move_2sigma'], 2),
                'straddle_price': round(moves['straddle_price'], 2),
                'confidence_68_range': [round(moves['confidence_68'][0], 2), round(moves['confidence_68'][1], 2)],
                'confidence_95_range': [round(moves['confidence_95'][0], 2), round(moves['confidence_95'][1], 2)],
                'straddle_range': [round(moves['straddle_range'][0], 2), round(moves['straddle_range'][1], 2)],
                'current_price': round(current_price, 2),
                'dte': dte_key
            }
        
        response_data = {
            'underlying': underlying,
            'current_price': round(current_price, 2),
            'iv_used': round(iv * 100, 1),
            'iv_source': iv_source,
            'expected_moves': formatted_moves,
            'summary': {
                'method': 'Hybrid (Formula + Theoretical Straddle)',
                'source': 'Polygon.io + Black-Scholes',
                'formula': 'Price × IV × √(T/252)',
                'iv_source': iv_source
            }
        }
        
        print(f"✅ Expected moves calculated successfully")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error calculating expected moves: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/expiration-dates/<symbol>')
def get_expiration_dates(symbol):
    """Get all valid trading days with economic event information"""
    try:
        from datetime import datetime, timedelta
        import calendar
        
        # Get current date
        today = datetime.now()
        
        expiration_dates = []
        
        # Generate next 90 days of valid trading days
        for day_offset in range(1, 91):  # Next 90 days
            target_date = today + timedelta(days=day_offset)
            
            # Skip weekends
            if target_date.weekday() >= 5:  # Saturday=5, Sunday=6
                continue
            
            # Skip major holidays (basic list)
            month = target_date.month
            day = target_date.day
            
            # Skip obvious holidays
            holidays = [
                (1, 1),   # New Year's Day
                (7, 4),   # Independence Day
                (12, 25), # Christmas
            ]
            
            if (month, day) in holidays:
                continue
            
            dte = day_offset
            year = target_date.year
            
            # Check for economic events and options expirations
            economic_events = []
            expiry_type = "Trading Day"
            is_options_expiry = False
            
            # Accurate 2025 Economic Calendar Data
            if year == 2025:
                date_str = target_date.strftime('%Y-%m-%d')
                
                # CPI Dates (Wednesdays)
                cpi_dates = [
                    '2025-01-08', '2025-02-12', '2025-03-12', '2025-04-09',
                    '2025-05-14', '2025-06-11', '2025-07-09', '2025-08-13',
                    '2025-09-10', '2025-10-08', '2025-11-12', '2025-12-10'
                ]
                if date_str in cpi_dates:
                    economic_events.append("CPI")
                
                # PPI Dates (Thursdays)
                ppi_dates = [
                    '2025-01-09', '2025-02-13', '2025-03-13', '2025-04-10',
                    '2025-05-08', '2025-06-12', '2025-07-10', '2025-08-14',
                    '2025-09-11', '2025-10-09', '2025-11-13', '2025-12-11'
                ]
                if date_str in ppi_dates:
                    economic_events.append("PPI")
                
                # JOLTS Dates (Tuesdays)
                jolts_dates = [
                    '2025-01-07', '2025-02-04', '2025-03-04', '2025-04-01',
                    '2025-05-06', '2025-06-03', '2025-07-01', '2025-08-05',
                    '2025-09-02', '2025-10-07', '2025-11-04', '2025-12-02'
                ]
                if date_str in jolts_dates:
                    economic_events.append("JOLTS")
                
                # FOMC Dates (Wednesdays)
                fomc_dates = [
                    '2025-03-19', '2025-06-18'
                ]
                if date_str in fomc_dates:
                    economic_events.append("FOMC")
                
                # VIX Expiration Dates (Wednesdays)
                vix_dates = [
                    '2025-01-15', '2025-02-19', '2025-03-19', '2025-04-16',
                    '2025-05-14', '2025-06-18', '2025-07-16', '2025-08-13',
                    '2025-09-17', '2025-10-15', '2025-11-19', '2025-12-17'
                ]
                if date_str in vix_dates:
                    economic_events.append("VIXperation")
                
                # Monthly OPEX Dates (3rd Fridays)
                opex_dates = [
                    '2025-01-17', '2025-02-21', '2025-03-21', '2025-04-18',
                    '2025-05-16', '2025-06-20', '2025-07-18', '2025-08-15',
                    '2025-09-19', '2025-10-17', '2025-11-21', '2025-12-19'
                ]
                if date_str in opex_dates:
                    economic_events.append("OPEX")
                    is_options_expiry = True
                    expiry_type = "Monthly Expiry"
                
                # Quad Witching Dates (Quarterly OPEX)
                quad_witching_dates = [
                    '2025-03-21', '2025-06-20', '2025-09-19', '2025-12-19'
                ]
                if date_str in quad_witching_dates:
                    economic_events.append("Quad Witching")
                    expiry_type = "Quarterly Expiry"
                
                # NFP (Jobs Report) Dates (Fridays)
                nfp_dates = [
                    '2025-01-03', '2025-02-07', '2025-03-07', '2025-04-04',
                    '2025-05-02', '2025-06-06', '2025-07-04', '2025-08-01',
                    '2025-09-05', '2025-10-03', '2025-11-07', '2025-12-05'
                ]
                if date_str in nfp_dates:
                    economic_events.append("NFP")
                
                # End of Quarter
                eoq_dates = ['2025-03-31', '2025-06-30', '2025-09-30', '2025-12-31']
                if date_str in eoq_dates:
                    economic_events.append("EoQ")
                
                # Beginning of Quarter  
                boq_dates = ['2025-04-01', '2025-07-01', '2025-10-01']
                if date_str in boq_dates:
                    economic_events.append("BoQ")
            
            # Weekly options expirations (all Fridays)
            if target_date.weekday() == 4:  # Friday
                is_options_expiry = True
                if expiry_type == "Trading Day":  # Not already set to Monthly/Quarterly
                    expiry_type = "Weekly Expiry"
            
            # Format display with events
            display_parts = [target_date.strftime('%a %b %d, %Y')]
            if economic_events:
                events_str = ", ".join(economic_events)
                display_parts.append(f"({events_str})")
            
            display_date = " ".join(display_parts)
            
            # Add special styling for important dates
            priority = 0
            if is_options_expiry:
                priority += 10
            if "OPEX" in economic_events:
                priority += 20
            if "FOMC" in economic_events:
                priority += 15
            if "CPI" in economic_events or "PPI" in economic_events:
                priority += 10
            if "VIXperation" in economic_events:
                priority += 8
            if "Earnings" in economic_events:
                priority += 5
            
            expiration_dates.append({
                'date': target_date.strftime('%Y-%m-%d'),
                'display_date': display_date,
                'dte': dte,
                'expiry_type': expiry_type,
                'economic_events': economic_events,
                'is_options_expiry': is_options_expiry,
                'is_monthly': expiry_type == "Monthly Expiry",
                'is_quarterly': expiry_type == "Quarterly Expiry",
                'priority': priority,
                'weekday': target_date.strftime('%A')
            })
        
        # Sort by date
        expiration_dates.sort(key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'symbol': symbol.upper(),
            'expiration_dates': expiration_dates,
            'total_days': len(expiration_dates),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Run the app
    debug_mode = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000) 