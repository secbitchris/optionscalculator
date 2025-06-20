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
        this.loadExpirationDates();
    }
    
    bindEvents() {
        // Form submissions
        document.getElementById('analysis-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.runAnalysis();
        });
        
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
        
        // Button clicks
        document.getElementById('fetch-price-btn').addEventListener('click', () => {
            this.fetchLivePrice();
        });
        
        document.getElementById('detect-iv-btn').addEventListener('click', () => {
            this.detectMarketIV();
        });
        
        document.getElementById('save-btn').addEventListener('click', () => {
            this.saveResults();
        });
        
        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportCSV();
        });
        
        document.getElementById('export-json-btn').addEventListener('click', () => {
            this.exportJSON();
        });
        
        // Underlying symbol change
        document.getElementById('underlying').addEventListener('change', () => {
            this.onUnderlyingChange();
            this.loadExpirationDates();
        });
        
        // Expiration date change
        document.getElementById('expiration-date').addEventListener('change', () => {
            this.onExpirationDateChange();
        });
        
        // Auto-fill scenario price when current price changes
        document.getElementById('current_price').addEventListener('input', () => {
            this.autoFillScenarioPrice();
        });
        
        // Filter controls
        document.querySelectorAll('input[name="options-filter"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.switchView(e.target.id);
            });
        });
        
        // Sort dropdown
        document.getElementById('sort-options').addEventListener('change', (e) => {
            console.log('Sort dropdown changed to:', e.target.value);
            this.applySorting();
        });
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
        const button = document.getElementById('fetch-price-btn');
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
        
        // Check if real-data-only mode is enabled
        const realDataOnly = document.getElementById('real-data-only') && document.getElementById('real-data-only').checked;
        const endpoint = realDataOnly ? '/api/analyze-real-only' : '/api/analyze';
        
        try {
            const response = await fetch(endpoint, {
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
                
                // Show data quality indicator
                if (result.data_quality === 'REAL_ONLY') {
                    this.showAlert('Analysis completed with REAL DATA ONLY - all estimated values filtered out', 'success');
                }
            } else {
                // Enhanced error message for real-data-only mode
                if (realDataOnly && result.error.includes('Available DTEs:')) {
                    const match = result.error.match(/Available DTEs: \[(.*?)\]/);
                    if (match) {
                        const availableDTEs = match[1];
                        this.showAlert(`Real Data Only Mode: No contracts found for ${data.dte} DTE. Available DTEs: ${availableDTEs}. Try one of these DTE values.`, 'warning');
                    } else {
                        this.showAlert('Real Data Only Mode - ' + result.error, 'warning');
                    }
                } else {
                    this.showAlert('Analysis error: ' + result.error, 'danger');
                }
            }
        } catch (error) {
            console.error('Error running analysis:', error);
            this.showAlert('Network error during analysis', 'danger');
        } finally {
            this.showLoading(false);
        }
    }
    
    displayResults(results, summary) {
        // Store current price for ATM detection
        const currentPrice = parseFloat(document.getElementById('current_price').value);
        
        // Separate calls and puts
        const calls = results.filter(r => r.type === 'CALL').sort((a, b) => a.strike - b.strike);
        const puts = results.filter(r => r.type === 'PUT').sort((a, b) => a.strike - b.strike);
        
        // Store for view switching and sorting
        this.callsData = calls;
        this.putsData = puts;
        this.currentPrice = currentPrice;
        this.currentResults = results;  // Store original results for sorting
        this.currentSummary = summary;  // Store summary for re-display
        
        // Update current price display
        document.getElementById('current-spot-price').textContent = `Spot: $${currentPrice.toFixed(2)}`;
        
        // Show filter controls
        document.getElementById('filter-controls').classList.remove('d-none');
        
        // Build chain view (default)
        this.buildChainView(calls, puts, currentPrice);
        
        // Build individual views for switching
        this.buildCallsView(calls);
        this.buildPutsView(puts);
        
        this.showResults();
    }
    
    buildChainView(calls, puts, currentPrice) {
        const tbody = document.getElementById('chain-tbody');
        tbody.innerHTML = '';
        
        // Get all unique strikes, sorted
        const allStrikes = [...new Set([...calls.map(c => c.strike), ...puts.map(p => p.strike)])].sort((a, b) => a - b);
        
        allStrikes.forEach(strike => {
            const call = calls.find(c => c.strike === strike);
            const put = puts.find(p => p.strike === strike);
            
            // Skip strikes that have neither call nor put (shouldn't happen but safety check)
            if (!call && !put) return;
            
            const tr = document.createElement('tr');
            
            // Determine if this is ATM (within $5 of current price)
            const isATM = Math.abs(strike - currentPrice) <= 5;
            if (isATM) {
                tr.classList.add('atm-row');
            }
            
            // Determine ITM status
            const callITM = strike < currentPrice;
            const putITM = strike > currentPrice;
            
            tr.innerHTML = `
                <!-- Call Side -->
                <td class="${callITM ? 'itm-call' : ''}">${call ? this.formatScore(call.day_trade_score) : '-'}</td>
                <td class="${callITM ? 'itm-call' : ''}">${call ? this.formatPremium(call.premium) : '-'}</td>
                <td class="${callITM ? 'itm-call' : ''}">${call ? this.formatDelta(call.delta) : '-'}</td>
                <td class="${callITM ? 'itm-call' : ''}">${call ? call.gamma.toFixed(6) : '-'}</td>
                <td class="${callITM ? 'itm-call' : ''}">${call ? this.formatOI(call) : '-'}</td>
                <td class="${callITM ? 'itm-call' : ''}">${call ? this.formatVolume(call) : '-'}</td>
                
                <!-- Strike Column -->
                <td class="strike-column">$${strike.toFixed(0)}</td>
                
                <!-- Put Side -->
                <td class="${putITM ? 'itm-put' : ''}">${put ? this.formatScore(put.day_trade_score) : '-'}</td>
                <td class="${putITM ? 'itm-put' : ''}">${put ? this.formatPremium(put.premium) : '-'}</td>
                <td class="${putITM ? 'itm-put' : ''}">${put ? this.formatDelta(put.delta) : '-'}</td>
                <td class="${putITM ? 'itm-put' : ''}">${put ? put.gamma.toFixed(6) : '-'}</td>
                <td class="${putITM ? 'itm-put' : ''}">${put ? this.formatOI(put) : '-'}</td>
                <td class="${putITM ? 'itm-put' : ''}">${put ? this.formatVolume(put) : '-'}</td>
            `;
            
            tbody.appendChild(tr);
        });
    }
    
    buildCallsView(calls) {
        const tbody = document.getElementById('calls-tbody');
        tbody.innerHTML = '';
        
        calls.forEach(call => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>$${call.strike.toFixed(0)}</td>
                <td>${this.formatPremium(call.premium)}</td>
                <td>${this.formatDelta(call.delta)}</td>
                <td>${call.gamma.toFixed(6)}</td>
                <td>${call.theta.toFixed(6)}</td>
                <td>${call.vega.toFixed(4)}</td>
                <td>${this.formatOI(call)}</td>
                <td>${this.formatVolume(call)}</td>
                <td>${this.formatScore(call.day_trade_score)}</td>
                <td>${call.aggressive_rr.toFixed(3)}</td>
                <td>${(call.prob_itm * 100).toFixed(1)}%</td>
            `;
            
            tbody.appendChild(tr);
        });
    }
    
    buildPutsView(puts) {
        const tbody = document.getElementById('puts-tbody');
        tbody.innerHTML = '';
        
        puts.forEach(put => {
            const tr = document.createElement('tr');
            
            tr.innerHTML = `
                <td>$${put.strike.toFixed(0)}</td>
                <td>${this.formatPremium(put.premium)}</td>
                <td>${this.formatDelta(put.delta)}</td>
                <td>${put.gamma.toFixed(6)}</td>
                <td>${put.theta.toFixed(6)}</td>
                <td>${put.vega.toFixed(4)}</td>
                <td>${this.formatOI(put)}</td>
                <td>${this.formatVolume(put)}</td>
                <td>${this.formatScore(put.day_trade_score)}</td>
                <td>${put.aggressive_rr.toFixed(3)}</td>
                <td>${(put.prob_itm * 100).toFixed(1)}%</td>
            `;
            
            tbody.appendChild(tr);
        });
    }
    
    switchView(filterId) {
        // Hide all views
        document.getElementById('chain-view').classList.add('d-none');
        document.getElementById('calls-view').classList.add('d-none');
        document.getElementById('puts-view').classList.add('d-none');
        
        // Show selected view
        switch(filterId) {
            case 'filter-all':
                document.getElementById('chain-view').classList.remove('d-none');
                break;
            case 'filter-calls':
                document.getElementById('calls-view').classList.remove('d-none');
                break;
            case 'filter-puts':
                document.getElementById('puts-view').classList.remove('d-none');
                break;
        }
    }
    
    applySorting() {
        if (!this.currentResults) {
            console.log('No current results to sort');
            return;
        }
        
        const sortBy = document.getElementById('sort-options').value;
        console.log('Sorting by:', sortBy);
        
        // Get sorting function
        const getSortFunction = (sortBy) => {
            switch(sortBy) {
                case 'day_trade_score':
                    return (a, b) => b.day_trade_score - a.day_trade_score;
                case 'premium_asc':
                    return (a, b) => a.premium - b.premium;
                case 'premium_desc':
                    return (a, b) => b.premium - a.premium;
                case 'delta_desc':
                    return (a, b) => Math.abs(b.delta) - Math.abs(a.delta);
                case 'gamma_desc':
                    return (a, b) => b.gamma - a.gamma;
                case 'prob_profit':
                    return (a, b) => (b.prob_itm || 0) - (a.prob_itm || 0);
                case 'liquidity_score':
                    return (a, b) => (b.liquidity_score || 0) - (a.liquidity_score || 0);
                case 'open_interest':
                    return (a, b) => (b.open_interest || 0) - (a.open_interest || 0);
                case 'target_rr':
                    return (a, b) => (b.aggressive_rr || 0) - (a.aggressive_rr || 0);
                default:
                    return (a, b) => b.day_trade_score - a.day_trade_score;
            }
        };
        
        const sortFunction = getSortFunction(sortBy);
        
        // Sort the data arrays
        const originalCallsLength = this.callsData.length;
        const originalPutsLength = this.putsData.length;
        
        this.callsData = [...this.callsData].sort(sortFunction);
        this.putsData = [...this.putsData].sort(sortFunction);
        
        console.log(`Sorted ${originalCallsLength} calls and ${originalPutsLength} puts`);
        
        // Rebuild the current view
        const activeView = document.querySelector('input[name="options-filter"]:checked').id;
        console.log('Active view:', activeView);
        
        switch(activeView) {
            case 'filter-all':
                this.buildChainView(this.callsData, this.putsData, this.currentPrice);
                break;
            case 'filter-calls':
                this.buildCallsView(this.callsData);
                break;
            case 'filter-puts':
                this.buildPutsView(this.putsData);
                break;
        }
        
        console.log('Sorting complete');
        
        // Show a brief visual feedback for sorting
        const sortDropdown = document.getElementById('sort-options');
        const originalBg = sortDropdown.style.backgroundColor;
        sortDropdown.style.backgroundColor = '#28a745';
        sortDropdown.style.color = 'white';
        setTimeout(() => {
            sortDropdown.style.backgroundColor = originalBg;
            sortDropdown.style.color = '';
        }, 500);
    }
    
    // Helper methods for formatting
    formatScore(score) {
        let className = '';
        if (score >= 0.4) className = 'score-excellent';
        else if (score >= 0.2) className = 'score-good';
        else className = 'score-poor';
        
        return `<span class="${className}">${score.toFixed(3)}</span>`;
    }
    
    formatPremium(premium) {
        let className = '';
        if (premium >= 5) className = 'premium-high';
        else if (premium >= 1) className = 'premium-medium';
        else className = 'premium-low';
        
        return `<span class="${className}">$${premium.toFixed(2)}</span>`;
    }
    
    formatDelta(delta) {
        const absDelta = Math.abs(delta);
        let className = '';
        if (absDelta >= 0.5) className = 'delta-high';
        else if (absDelta >= 0.3) className = 'delta-medium';
        else className = 'delta-low';
        
        return `<span class="${className}">${delta.toFixed(3)}</span>`;
    }
    
    formatOI(option) {
        const badge = option.oi_source === 'REAL' ? 
            `<span class="badge bg-success" title="Real data from Polygon.io">${option.open_interest.toLocaleString()}</span>` :
            `<span class="badge bg-warning" title="Estimated">${option.open_interest.toLocaleString()}</span>`;
        return badge;
    }
    
    formatVolume(option) {
        if (option.volume === null || option.volume_source === 'NONE') {
            return `<span class="badge bg-dark" title="Real data only mode - volume excluded">N/A</span>`;
        }
        const badge = option.volume_source === 'REAL' ? 
            `<span class="badge bg-success" title="Real volume data">${option.volume.toLocaleString()}</span>` :
            `<span class="badge bg-secondary" title="Estimated from OI">${option.volume.toLocaleString()}</span>`;
        return badge;
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
        document.getElementById('export-json-btn').disabled = false;
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
        const headers = ['Type', 'Strike', 'Premium', 'Delta', 'Gamma', 'Theta', 'Vega', 'Open Interest', 'Volume', 'OI Source', 'Vol Source', 'Score', 'R/R Ratio', 'Prob ITM'];
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
                row.open_interest || 0,
                row.volume || 0,
                row.oi_source || 'N/A',
                row.volume_source || 'N/A',
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
    
    exportJSON() {
        if (!this.currentResults || !this.currentSummary) return;
        
        // Create complete JSON export with both summary and full results
        const exportData = {
            analysis_metadata: {
                export_timestamp: new Date().toISOString(),
                export_source: 'Options Analysis Web App',
                total_options: this.currentResults.length
            },
            summary: this.currentSummary,
            complete_options_data: this.currentResults,
            calls: this.currentResults.filter(r => r.type === 'CALL'),
            puts: this.currentResults.filter(r => r.type === 'PUT')
        };
        
        // Download JSON
        const jsonString = JSON.stringify(exportData, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `options_analysis_complete_${new Date().toISOString().slice(0, 10)}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
        
        this.showAlert('Complete JSON data exported successfully!', 'success');
    }
    
    onUnderlyingChange() {
        // Clear current price when underlying changes
        document.getElementById('current_price').value = '';
    }
    
    async loadExpirationDates() {
        const underlying = document.getElementById('underlying').value;
        const select = document.getElementById('expiration-date');
        
        // Show loading
        select.innerHTML = '<option value="">Loading trading days...</option>';
        
        try {
            const response = await fetch(`/api/expiration-dates/${underlying}`);
            const data = await response.json();
            
            if (data.success) {
                // Clear existing options
                select.innerHTML = '';
                
                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select any trading day...';
                select.appendChild(defaultOption);
                
                // Group dates by importance for better organization
                const highPriority = [];
                const mediumPriority = [];
                const standardDays = [];
                
                data.expiration_dates.forEach(exp => {
                    if (exp.priority >= 20) {
                        highPriority.push(exp);
                    } else if (exp.priority >= 10) {
                        mediumPriority.push(exp);
                    } else {
                        standardDays.push(exp);
                    }
                });
                
                // Add high priority dates first (OPEX, major events)
                if (highPriority.length > 0) {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = '📅 Major Events & Options Expirations';
                    highPriority.forEach(exp => {
                        optgroup.appendChild(this.createDateOption(exp));
                    });
                    select.appendChild(optgroup);
                }
                
                // Add medium priority dates (weekly expirations, economic events)
                if (mediumPriority.length > 0) {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = '📊 Economic Events & Weekly Expirations';
                    mediumPriority.forEach(exp => {
                        optgroup.appendChild(this.createDateOption(exp));
                    });
                    select.appendChild(optgroup);
                }
                
                // Add standard trading days
                if (standardDays.length > 0) {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = '📈 All Trading Days';
                    standardDays.forEach(exp => {
                        optgroup.appendChild(this.createDateOption(exp));
                    });
                    select.appendChild(optgroup);
                }
                
                // Auto-select the next options expiration (Friday) within 14 days
                const nextExpiry = data.expiration_dates.find(exp => 
                    exp.is_options_expiry && exp.dte <= 14
                );
                
                if (nextExpiry) {
                    select.value = nextExpiry.date;
                    this.onExpirationDateChange();
                } else {
                    // Fallback to first high priority date
                    if (highPriority.length > 0) {
                        select.value = highPriority[0].date;
                        this.onExpirationDateChange();
                    }
                }
                
            } else {
                select.innerHTML = '<option value="">Error loading dates</option>';
                this.showAlert('Error loading trading days: ' + data.error, 'danger');
            }
        } catch (error) {
            console.error('Error loading expiration dates:', error);
            select.innerHTML = '<option value="">Error loading dates</option>';
            this.showAlert('Network error loading trading days', 'danger');
        }
    }
    
    createDateOption(exp) {
        const option = document.createElement('option');
        option.value = exp.date;
        option.dataset.dte = exp.dte;
        option.dataset.expiryType = exp.expiry_type;
        option.dataset.economicEvents = JSON.stringify(exp.economic_events);
        option.dataset.isMonthly = exp.is_monthly;
        option.dataset.isQuarterly = exp.is_quarterly;
        option.dataset.isOptionsExpiry = exp.is_options_expiry;
        option.dataset.priority = exp.priority;
        option.dataset.weekday = exp.weekday;
        
        // Use the pre-formatted display date that includes events
        option.textContent = exp.display_date;
        
        // Add special styling for high priority dates
        if (exp.priority >= 20) {
            option.style.fontWeight = 'bold';
            option.style.color = '#dc3545'; // Bootstrap danger color
        } else if (exp.priority >= 15) {
            option.style.fontWeight = 'bold';
            option.style.color = '#fd7e14'; // Bootstrap warning color
        } else if (exp.priority >= 10) {
            option.style.fontWeight = '500';
            option.style.color = '#0d6efd'; // Bootstrap primary color
        }
        
        return option;
    }
    
    onExpirationDateChange() {
        const select = document.getElementById('expiration-date');
        const selectedOption = select.selectedOptions[0];
        
        if (selectedOption && selectedOption.value) {
            const dte = selectedOption.dataset.dte;
            const expiryType = selectedOption.dataset.expiryType;
            const economicEvents = JSON.parse(selectedOption.dataset.economicEvents || '[]');
            const isOptionsExpiry = selectedOption.dataset.isOptionsExpiry === 'true';
            const weekday = selectedOption.dataset.weekday;
            const priority = parseInt(selectedOption.dataset.priority || '0');
            
            // Update display elements
            document.getElementById('dte-display').textContent = `${dte} DTE`;
            
            // Enhanced expiry type display
            let expiryDisplay = expiryType;
            if (isOptionsExpiry) {
                expiryDisplay += ` 📅`;
            }
            if (weekday) {
                expiryDisplay += ` (${weekday})`;
            }
            document.getElementById('expiry-type').textContent = expiryDisplay;
            
            // Update economic events display with enhanced styling
            const eventsElement = document.getElementById('economic-events');
            if (economicEvents.length > 0) {
                eventsElement.innerHTML = economicEvents.map(event => {
                    let badgeClass = 'bg-secondary text-white';
                    let icon = '';
                    
                    // Color code and add icons by importance
                    switch(event) {
                        case 'FOMC':
                            badgeClass = 'bg-danger text-white';
                            icon = '🏛️ ';
                            break;
                        case 'CPI':
                            badgeClass = 'bg-danger text-white';
                            icon = '📊 ';
                            break;
                        case 'OPEX':
                            badgeClass = 'bg-warning text-dark';
                            icon = '⚡ ';
                            break;
                        case 'VIXperation':
                            badgeClass = 'bg-warning text-dark';
                            icon = '📈 ';
                            break;
                        case 'PPI':
                            badgeClass = 'bg-info text-white';
                            icon = '🏭 ';
                            break;
                        case 'Earnings':
                            badgeClass = 'bg-success text-white';
                            icon = '💰 ';
                            break;
                        case 'Fed Speech':
                            badgeClass = 'bg-primary text-white';
                            icon = '🎤 ';
                            break;
                        default:
                            badgeClass = 'bg-secondary text-white';
                            icon = '📅 ';
                    }
                    
                    return `<span class="badge ${badgeClass} ms-1" title="${event}">${icon}${event}</span>`;
                }).join('');
            } else {
                eventsElement.innerHTML = '<span class="text-muted">No major events</span>';
            }
            
            // Add priority indicator
            if (priority >= 20) {
                eventsElement.innerHTML += ' <span class="badge bg-danger text-white ms-1">🔥 HIGH</span>';
            } else if (priority >= 15) {
                eventsElement.innerHTML += ' <span class="badge bg-warning text-dark ms-1">⚠️ MEDIUM</span>';
            }
            
            // Update the form's dte field for backend compatibility
            const hiddenDTE = document.getElementById('dte') || this.createHiddenDTEField();
            hiddenDTE.value = dte;
            
        } else {
            // Clear displays
            document.getElementById('dte-display').textContent = '-';
            document.getElementById('expiry-type').textContent = '-';
            document.getElementById('economic-events').innerHTML = '';
        }
    }
    
    createHiddenDTEField() {
        // Create hidden DTE field for backend compatibility
        const hiddenField = document.createElement('input');
        hiddenField.type = 'hidden';
        hiddenField.id = 'dte';
        hiddenField.name = 'dte';
        document.getElementById('analysis-form').appendChild(hiddenField);
        return hiddenField;
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