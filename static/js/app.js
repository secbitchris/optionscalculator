// Options Analysis Dashboard JavaScript

class OptionsAnalysisDashboard {
    constructor() {
        this.currentResults = null;
        this.currentSummary = null;
        this.analysisStartTime = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.checkAPIStatus();
        this.loadConfig();
    }
    
    bindEvents() {
        // Main analysis form
        document.getElementById('analysis-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.runAnalysis();
        });
        
        // Fetch price button
        document.getElementById('fetch-price').addEventListener('click', () => {
            this.fetchLivePrice();
        });
        
        // Detect market IV button
        document.getElementById('detect-iv-btn').addEventListener('click', () => {
            this.detectMarketIV();
        });
        
        // Save and export buttons
        document.getElementById('save-btn').addEventListener('click', () => {
            this.saveResults();
        });
        
        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportCSV();
        });
        
        // Underlying selection change
        document.getElementById('underlying').addEventListener('change', () => {
            this.onUnderlyingChange();
        });
        
        // Enhanced features forms
        document.getElementById('iv-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.calculateIV();
        });
        
        document.getElementById('scenario-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.analyzeScenario();
        });
        
        document.getElementById('greeks-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.compareGreeks();
        });
        
        // Auto-fill scenario base price when main analysis is done
        this.autoFillScenarioPrice();
    }
    
    async checkAPIStatus() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                const hasAPI = data.config.has_polygon_api;
                const statusElement = document.getElementById('api-status');
                
                if (hasAPI) {
                    statusElement.innerHTML = '<i class="fas fa-circle api-live me-1"></i>Live Data Available';
                } else {
                    statusElement.innerHTML = '<i class="fas fa-circle api-fallback me-1"></i>Offline Mode';
                }
            }
        } catch (error) {
            console.error('Error checking API status:', error);
            document.getElementById('api-status').innerHTML = '<i class="fas fa-circle api-error me-1"></i>API Error';
        }
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const data = await response.json();
            
            if (data.success) {
                // Update form defaults if needed
                console.log('Config loaded:', data.config);
            }
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }
    
    async fetchLivePrice() {
        const underlying = document.getElementById('underlying').value;
        const button = document.getElementById('fetch-price');
        const input = document.getElementById('current_price');
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        try {
            const response = await fetch(`/api/live-price/${underlying}`);
            const data = await response.json();
            
            if (data.success) {
                input.value = data.price.toFixed(2);
                
                // Auto-fill scenario base price
                this.updateScenarioBasePrice(data.price.toFixed(2));
                
                // Auto-detect market IV
                await this.fetchMarketIV(underlying, data.price);
                
                // Update API status
                const statusElement = document.getElementById('api-status');
                if (data.source === 'live') {
                    statusElement.innerHTML = '<i class="fas fa-circle api-live me-1"></i>Live Data';
                } else {
                    statusElement.innerHTML = '<i class="fas fa-circle api-fallback me-1"></i>Fallback Data';
                }
            } else {
                this.showAlert('Error fetching price: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error fetching price:', error);
            this.showAlert('Network error fetching price', 'danger');
        } finally {
            // Reset button
            button.innerHTML = '<i class="fas fa-sync-alt"></i>';
            button.disabled = false;
        }
    }

    async fetchMarketIV(underlying, currentPrice) {
        try {
            const response = await fetch('/api/expected-moves-hybrid', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    underlying: underlying,
                    current_price: currentPrice,
                    dte: 7,
                    iv: 0 // Pass 0 to trigger auto-detection
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.iv_source !== 'User Input') {
                // Update IV field with detected market IV
                const ivInput = document.getElementById('iv');
                ivInput.value = data.iv_used.toFixed(1);
                
                // Show IV source info
                this.showIVSource(data.iv_source, data.iv_used);
                
                // Auto-run analysis with market IV
                setTimeout(() => {
                    this.runAnalysis();
                }, 500);
            }
        } catch (error) {
            console.error('Error fetching market IV:', error);
        }
    }

    showIVSource(source, iv) {
        const ivSourceElement = document.getElementById('iv-source');
        if (ivSourceElement) {
            ivSourceElement.innerHTML = `<i class="fas fa-info-circle text-info"></i> IV: ${iv.toFixed(1)}% from ${source}`;
        }
    }

    async detectMarketIV() {
        const underlying = document.getElementById('underlying').value;
        const currentPrice = parseFloat(document.getElementById('current_price').value) || 0;
        const button = document.getElementById('detect-iv-btn');
        
        // Show loading state
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        try {
            const response = await fetch('/api/expected-moves-hybrid', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    underlying: underlying,
                    current_price: currentPrice,
                    dte: 7,
                    iv: 0 // Pass 0 to trigger auto-detection
                })
            });
            
            const data = await response.json();
            
            if (data.iv_source !== 'User Input') {
                // Update IV field with detected market IV
                const ivInput = document.getElementById('iv');
                ivInput.value = data.iv_used.toFixed(1);
                
                // Show IV source info
                this.showIVSource(data.iv_source, data.iv_used);
                
                this.showAlert(`Market IV detected: ${data.iv_used.toFixed(1)}% from ${data.iv_source}`, 'success');
            } else {
                this.showAlert('Could not detect market IV - using fallback', 'warning');
            }
        } catch (error) {
            console.error('Error detecting market IV:', error);
            this.showAlert('Error detecting market IV', 'danger');
        } finally {
            // Reset button
            button.innerHTML = '<i class="fas fa-eye"></i>';
            button.disabled = false;
        }
    }
    
    async runAnalysis() {
        this.analysisStartTime = Date.now();
        
        // Show loading state
        this.showLoading(true);
        this.hideResults();
        
        // Get form data
        const formData = new FormData(document.getElementById('analysis-form'));
        const data = {
            underlying: formData.get('underlying'),
            current_price: formData.get('current_price') || '',
            dte: parseInt(formData.get('dte')),
            iv: parseFloat(formData.get('iv')), // Keep as percentage - backend will convert
            risk_free_rate: parseFloat(formData.get('risk_free_rate')) // Keep as percentage - backend will convert
        };
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.currentResults = result.results;
                this.currentSummary = result.summary;
                this.displayResults(result.results, result.summary);
                this.updateSummaryCards(result.results);
                this.enableActionButtons();
            } else {
                this.showAlert('Analysis error: ' + result.error, 'danger');
            }
        } catch (error) {
            console.error('Error running analysis:', error);
            this.showAlert('Network error during analysis', 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayResults(results, summary) {
        const tbody = document.getElementById('results-tbody');
        tbody.innerHTML = '';
        
        results.forEach(row => {
            const tr = document.createElement('tr');
            
            // Determine score class
            let scoreClass = '';
            if (row.day_trade_score >= 0.4) scoreClass = 'score-excellent';
            else if (row.day_trade_score >= 0.2) scoreClass = 'score-good';
            else scoreClass = 'score-poor';
            
            tr.innerHTML = `
                <td><span class="badge ${row.type === 'CALL' ? 'bg-success' : 'bg-info'}">${row.type}</span></td>
                <td>$${row.strike.toFixed(0)}</td>
                <td>$${row.premium.toFixed(2)}</td>
                <td>${row.delta.toFixed(3)}</td>
                <td>${row.gamma.toFixed(6)}</td>
                <td>${row.theta.toFixed(6)}</td>
                <td>${row.vega.toFixed(4)}</td>
                <td class="${scoreClass}">${row.day_trade_score.toFixed(3)}</td>
                <td>${row.aggressive_rr.toFixed(3)}</td>
                <td>${(row.prob_itm * 100).toFixed(1)}%</td>
            `;
            
            tbody.appendChild(tr);
        });
        
        this.showResults();
    }
    
    updateSummaryCards(results) {
        const totalOptions = results.length;
        const calls = results.filter(r => r.type === 'CALL');
        const puts = results.filter(r => r.type === 'PUT');
        
        const bestCallScore = calls.length > 0 ? Math.max(...calls.map(r => r.day_trade_score)) : 0;
        const bestPutScore = puts.length > 0 ? Math.max(...puts.map(r => r.day_trade_score)) : 0;
        
        const analysisTime = ((Date.now() - this.analysisStartTime) / 1000).toFixed(1);
        
        document.getElementById('total-options').textContent = totalOptions;
        document.getElementById('best-call-score').textContent = bestCallScore.toFixed(3);
        document.getElementById('best-put-score').textContent = bestPutScore.toFixed(3);
        document.getElementById('analysis-time').textContent = analysisTime + 's';
        
        document.getElementById('summary-cards').classList.remove('d-none');
        document.getElementById('summary-cards').classList.add('fade-in');
    }
    
    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.remove('d-none');
        } else {
            loading.classList.add('d-none');
        }
    }
    
    showResults() {
        document.getElementById('welcome-message').classList.add('d-none');
        document.getElementById('results-container').classList.remove('d-none');
        document.getElementById('results-container').classList.add('fade-in');
    }
    
    hideResults() {
        document.getElementById('results-container').classList.add('d-none');
        document.getElementById('summary-cards').classList.add('d-none');
    }
    
    enableActionButtons() {
        document.getElementById('save-btn').disabled = false;
        document.getElementById('export-btn').disabled = false;
    }
    
    async saveResults() {
        if (!this.currentResults) return;
        
        const data = {
            results: this.currentResults,
            summary: this.currentSummary,
            filename: 'web_analysis',
            underlying: document.getElementById('underlying').value
        };
        
        try {
            const response = await fetch('/api/save-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Analysis saved successfully!', 'success');
            } else {
                this.showAlert('Error saving analysis: ' + result.error, 'danger');
            }
        } catch (error) {
            console.error('Error saving analysis:', error);
            this.showAlert('Network error saving analysis', 'danger');
        }
    }
    
    exportCSV() {
        if (!this.currentResults) return;
        
        // Convert results to CSV
        const headers = ['Type', 'Strike', 'Premium', 'Delta', 'Gamma', 'Theta', 'Vega', 'Score', 'R/R Ratio', 'Prob ITM'];
        const csvContent = [
            headers.join(','),
            ...this.currentResults.map(row => [
                row.type,
                row.strike,
                row.premium,
                row.delta,
                row.gamma,
                row.theta,
                row.vega,
                row.day_trade_score,
                row.risk_reward_ratio,
                row.prob_itm
            ].join(','))
        ].join('\n');
        
        // Download CSV
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `options_analysis_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    onUnderlyingChange() {
        // Clear current price when underlying changes
        document.getElementById('current_price').value = '';
    }
    
    autoFillScenarioPrice() {
        // Auto-fill scenario base price when current price is available
        const currentPriceInput = document.getElementById('current_price');
        const scenarioBasePriceInput = document.getElementById('scenario-base-price');
        
        if (currentPriceInput && scenarioBasePriceInput) {
            // Auto-fill on input change
            currentPriceInput.addEventListener('input', () => {
                if (currentPriceInput.value) {
                    scenarioBasePriceInput.value = currentPriceInput.value;
                }
            });
            
            // Auto-fill immediately if current price already has a value
            if (currentPriceInput.value) {
                scenarioBasePriceInput.value = currentPriceInput.value;
            }
        }
    }
    
    // Helper method to update scenario base price from live price fetches
    updateScenarioBasePrice(price) {
        const scenarioBasePriceInput = document.getElementById('scenario-base-price');
        if (scenarioBasePriceInput && price) {
            scenarioBasePriceInput.value = price;
        }
    }
    
    async calculateIV() {
        const marketPrice = parseFloat(document.getElementById('iv-market-price').value);
        const strike = parseFloat(document.getElementById('iv-strike').value);
        const optionType = document.getElementById('iv-option-type').value;
        const dte = parseInt(document.getElementById('iv-dte').value);
        
        const underlying = document.getElementById('underlying').value;
        const currentPrice = parseFloat(document.getElementById('current_price').value) || 0;
        const riskFreeRate = parseFloat(document.getElementById('risk_free_rate').value) / 100; // Convert percentage to decimal
        
        if (!marketPrice || !strike) {
            this.showAlert('Please enter market price and strike price', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/iv-calculator', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    market_price: marketPrice,
                    underlying_price: currentPrice || 600, // fallback
                    strike: strike,
                    dte: dte,
                    risk_free_rate: riskFreeRate,
                    option_type: optionType,
                    underlying: underlying
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                if (result.result.implied_volatility) {
                    document.getElementById('iv-result-value').textContent = `${(result.result.implied_volatility * 100).toFixed(1)}%`;
                    document.getElementById('iv-results').classList.remove('d-none');
                } else {
                    this.showAlert('IV calculation failed: ' + result.result.error, 'warning');
                }
            } else {
                this.showAlert('IV calculation error: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Network error calculating IV', 'danger');
        }
    }
    
    async analyzeScenario() {
        const basePrice = parseFloat(document.getElementById('scenario-base-price').value);
        const adjustment = parseFloat(document.getElementById('scenario-adjustment').value);
        
        if (!basePrice || isNaN(adjustment)) {
            this.showAlert('Please enter base price and price adjustment', 'warning');
            return;
        }
        
        const underlying = document.getElementById('underlying').value;
        const dte = parseInt(document.getElementById('dte').value);
        const iv = parseFloat(document.getElementById('iv').value);
        const riskFreeRate = parseFloat(document.getElementById('risk_free_rate').value);
        
        try {
            const response = await fetch('/api/price-scenario', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    base_price: basePrice,
                    adjustment: adjustment,
                    underlying: underlying,
                    dte: dte,
                    iv: iv,
                    risk_free_rate: riskFreeRate
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const data = result.result;
                const impact = data.options_impact;
                
                const scenarioType = data.scenario_type.charAt(0).toUpperCase() + data.scenario_type.slice(1);
                const percentChange = data.percentage_change;
                
                const content = `
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Price Movement</h6>
                            <p><strong>Scenario:</strong> ${scenarioType}</p>
                            <p><strong>New Price:</strong> $${data.adjusted_price.toFixed(2)}</p>
                            <p><strong>Change:</strong> ${adjustment > 0 ? '+' : ''}$${adjustment.toFixed(2)} (${percentChange > 0 ? '+' : ''}${percentChange.toFixed(1)}%)</p>
                        </div>
                        <div class="col-md-6">
                            <h6>ATM Options Impact ($${impact.atm_strike})</h6>
                            <p><strong>Call:</strong> $${impact.call_original_price.toFixed(2)} → $${impact.call_new_price.toFixed(2)} 
                               <span class="${impact.call_price_change >= 0 ? 'text-success' : 'text-danger'}">
                                   (${impact.call_price_change >= 0 ? '+' : ''}$${impact.call_price_change.toFixed(2)})
                               </span>
                            </p>
                            <p><strong>Put:</strong> $${impact.put_original_price.toFixed(2)} → $${impact.put_new_price.toFixed(2)} 
                               <span class="${impact.put_price_change >= 0 ? 'text-success' : 'text-danger'}">
                                   (${impact.put_price_change >= 0 ? '+' : ''}$${impact.put_price_change.toFixed(2)})
                               </span>
                            </p>
                        </div>
                    </div>
                `;
                document.getElementById('scenario-results-content').innerHTML = content;
                document.getElementById('scenario-results').classList.remove('d-none');
            } else {
                this.showAlert('Scenario analysis error: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Network error analyzing scenario', 'danger');
        }
    }
    
    async compareGreeks() {
        const strike = parseFloat(document.getElementById('greeks-strike').value);
        const optionType = document.getElementById('greeks-option-type').value;
        
        const underlying = document.getElementById('underlying').value;
        const currentPrice = parseFloat(document.getElementById('current_price').value) || 600;
        const dte = parseInt(document.getElementById('dte').value);
        const iv = parseFloat(document.getElementById('iv').value) / 100; // Convert percentage to decimal
        const riskFreeRate = parseFloat(document.getElementById('risk_free_rate').value) / 100; // Convert percentage to decimal
        
        if (!strike) {
            this.showAlert('Please enter strike price', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/greeks-comparison', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    underlying_price: currentPrice,
                    strike: strike,
                    dte: dte,
                    iv: iv,
                    risk_free_rate: riskFreeRate,
                    option_type: optionType,
                    underlying: underlying
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                const tbody = document.getElementById('greeks-results-tbody');
                tbody.innerHTML = '';
                
                Object.entries(result.results).forEach(([scaling, greeks]) => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><small>${scaling}</small></td>
                        <td><small>${greeks.delta.toFixed(4)}</small></td>
                        <td><small>${greeks.gamma.toFixed(6)}</small></td>
                        <td><small>${greeks.theta.toFixed(6)}</small></td>
                        <td><small>${greeks.vega.toFixed(4)}</small></td>
                    `;
                    tbody.appendChild(row);
                });
                
                document.getElementById('greeks-results').classList.remove('d-none');
            } else {
                this.showAlert('Greeks comparison error: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('Network error comparing Greeks', 'danger');
        }
    }
    
    showAlert(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of main content
        const mainContent = document.querySelector('.col-md-9');
        mainContent.insertBefore(alert, mainContent.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// Saved Files Function
async function loadSavedFiles() {
    try {
        const response = await fetch('/api/files');
        const result = await response.json();
        
        const filesList = document.getElementById('files-list');
        
        if (result.success && result.files.length > 0) {
            filesList.innerHTML = result.files.map(file => `
                <div class="d-flex justify-content-between align-items-center mb-1 p-1 border-bottom">
                    <div>
                        <small class="fw-bold">${file.name}</small><br>
                        <small class="text-muted">${(file.size / 1024).toFixed(1)} KB</small>
                    </div>
                    <a href="/api/download/${file.name}" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
            `).join('');
        } else {
            filesList.innerHTML = '<small class="text-muted">No saved files found</small>';
        }
    } catch (error) {
        document.getElementById('files-list').innerHTML = '<small class="text-danger">Error loading files</small>';
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new OptionsAnalysisDashboard();
}); 