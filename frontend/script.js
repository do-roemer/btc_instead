const API_BASE_URL = 'http://localhost:8000';

class PortfolioAnalyzer {
    constructor() {
        this.form = document.getElementById('urlForm');
        this.loading = document.getElementById('loading');
        this.results = document.getElementById('results');
        this.error = document.getElementById('error');
        this.submitBtn = document.getElementById('submitBtn');
        
        this.bindEvents();
    }

    bindEvents() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(this.form);
        const url = formData.get('redditUrl');
        const overwrite = formData.get('overwrite') === 'on';
        
        if (!this.validateRedditUrl(url)) {
            this.showError('Please enter a valid Reddit URL');
            return;
        }

        await this.analyzePortfolio(url, overwrite);
    }

    validateRedditUrl(url) {
        return url && url.includes('reddit.com/r/') && url.includes('/comments/');
    }

    async analyzePortfolio(url, overwrite = false) {
        this.showLoading();
        
        try {
            const payload = {
                url: url,
                custom_parameter: {
                    overwrite: overwrite
                }
            };

            const response = await fetch(`${API_BASE_URL}/api/v1/url-processor/execute-reddit-url-evaluation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            const clonedResponse = response.clone();
            clonedResponse.text().then(text => {
                console.log('API Response:', text);
            });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }

            this.showResults(data);
            
        } catch (error) {
            console.error('API Error:', error);
            this.showError(this.getErrorMessage(error));
        } finally {
            this.hideLoading();
        }
    }

    getErrorMessage(error) {
        if (error.message.includes('Failed to fetch')) {
            return 'Cannot connect to the API server. Make sure it\'s running on localhost:8000';
        }
        return error.message || 'An unexpected error occurred';
    }

    showLoading() {
        this.hideAllMessages();
        this.loading.classList.remove('hidden');
        this.submitBtn.disabled = true;
        this.submitBtn.textContent = 'Processing...';
    }

    hideLoading() {
        this.loading.classList.add('hidden');
        this.submitBtn.disabled = false;
        this.submitBtn.textContent = 'Analyze Portfolio';
    }

    showResults(data) {
        this.hideAllMessages();
        this.results.classList.remove('hidden');
        
        const resultContent = document.getElementById('resultContent');
        resultContent.innerHTML = `
            <div class="success">
                <h3>✅ ${data.message}</h3>
                <p><strong>Status:</strong> ${data.status}</p>
                ${data.result ? this.formatResult(data.result) : ''}
            </div>
        `;
    }

    formatResult(result) {
        if (result.failed) {
            return this.formatFailedResult(result);
        }
        
        return `
            <div class="result-details">
                ${this.formatPortfolioSummary(result)}
                ${this.formatHoldings(result.purchases || [])}
                ${this.formatPerformanceComparison(result)}
                ${this.formatRawData(result)}
            </div>
        `;
    }

    formatFailedResult(result) {
        return `
            <div class="failed-result">
                <h4>❌ Analysis Failed</h4>
                <p><strong>Reason:</strong> ${result.error_message || 'Unknown error'}</p>
                <details>
                    <summary>View Raw Response</summary>
                    <pre>${JSON.stringify(result, null, 2)}</pre>
                </details>
            </div>
        `;
    }

    formatPortfolioSummary(result) {
        if (!result.portfolio_value) return '';
        
        return `
            <div class="portfolio-summary">
                <h4>📊 Portfolio Analysis</h4>
                <div class="stats-grid">
                    <div class="stat-card">
                        <span class="stat-label">Total Value</span>
                        <span class="stat-value">€${result.portfolio_value?.toLocaleString()}</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">BTC Equivalent</span>
                        <span class="stat-value">€${result.btc_equivalent?.toLocaleString()}</span>
                    </div>
                    <div class="stat-card">
                        <span class="stat-label">vs BTC Performance</span>
                        <span class="stat-value ${result.vs_btc_percentage > 0 ? 'positive' : 'negative'}">
                            ${result.vs_btc_percentage?.toFixed(2)}%
                        </span>
                    </div>
                </div>
            </div>
        `;
    }

    formatHoldings(purchases) {
        if (!purchases || purchases.length === 0) return '';
        
        const holdingsHtml = purchases.map(holding => `
            <div class="holding-item">
                <div class="coin-info">
                    <span class="coin-name">${holding.name}</span>
                    <span class="coin-symbol">${holding.abbreviation}</span>
                </div>
                <div class="holding-details">
                    <span class="amount">${holding.amount} coins</span>
                    <span class="value">€${holding.current_value?.toLocaleString()}</span>
                    <span class="change ${holding.price_change_percentage > 0 ? 'positive' : 'negative'}">
                        ${holding.price_change_percentage?.toFixed(2)}%
                    </span>
                </div>
            </div>
        `).join('');
        
        return `
            <div class="holdings-section">
                <h4>💰 Current Holdings</h4>
                <div class="holdings-list">
                    ${holdingsHtml}
                </div>
            </div>
        `;
    }

    formatPerformanceComparison(result) {
        if (!result.performance_comparison) return '';
        
        return `
            <div class="performance-comparison">
                <h4>📈 Performance vs BTC</h4>
                <div class="comparison-chart">
                    <div class="portfolio-bar" style="width: ${Math.abs(result.portfolio_performance || 0)}%">
                        Portfolio: ${result.portfolio_performance?.toFixed(2)}%
                    </div>
                    <div class="btc-bar" style="width: ${Math.abs(result.btc_performance || 0)}%">
                        BTC: ${result.btc_performance?.toFixed(2)}%
                    </div>
                </div>
            </div>
        `;
    }

    formatRawData(result) {
        return `
            <details class="raw-data">
                <summary>🔍 View Raw Response Data</summary>
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </details>
        `;
    }

    showError(message) {
        this.hideAllMessages();
        this.error.classList.remove('hidden');
        document.getElementById('errorMessage').textContent = message;
    }

    hideAllMessages() {
        this.loading.classList.add('hidden');
        this.results.classList.add('hidden');
        this.error.classList.add('hidden');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PortfolioAnalyzer();
});